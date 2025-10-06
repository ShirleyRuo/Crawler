import os
import sys

import re
import queue
import signal
import asyncio
import aiohttp
import subprocess
from threading import Thread
import requests
import m3u8
import logging
from pathlib import Path
from urllib.parse import urljoin
from enum import Enum
from Crypto.Cipher import AES
from dataclasses import dataclass
from typing import List, Optional, Callable, Any, Union, Tuple, Dict, overload

from Config import config
from Logger import Logger

logger = Logger(config.log_dir).get_logger(__name__, logging.INFO)

class DownloadStatus(Enum):

    PENDING = 1
    DOWNLOADING = 2
    PAUSED = 3
    DECRYPTING = 4
    MERGING = 5
    FINISHED = 6
    FAILED = 7

class DecrptyType(Enum):
    AES = 1

@dataclass
class DownloadPackage:
    id : str
    name : str
    actress : str
    hash_tag : Tuple[str]
    hls_url : str
    cover_url : str
    src : str = 'Unknown'
    status : DownloadStatus = DownloadStatus.PENDING
    has_chinese : bool = False
    release_date : str = None
    time_length : str = None

    def __post_init__(self) -> None:
        self.base_url = self.hls_url.rsplit('/', 1)[0] + '/'
    
    def update(self, hls_url : str = None) -> None:
        if hls_url:
            self.hls_url = hls_url
            self.base_url = self.hls_url.rsplit('/', 1)[0] + '/'

class Decrypter:

    def __init__(
            self,
            decrpty_type : DecrptyType,
            **kwargs : Any
            ) -> None:
        self._decrypty_type = decrpty_type
    
    def decrypt(
            self,
            file_obj : Optional[bytes] = None,
            key : Optional[bytes] = None,
            iv : Optional[str] = None,
            **kwargs : Any
            ) -> bytes:
        if iv.startswith('0x'):
            iv = bytes.fromhex(iv[2:])
        else:
            iv = bytes.fromhex(iv)
        if self._decrypty_type == DecrptyType.AES:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(file_obj)
            return decrypted_data
        else:
            raise ValueError("不支持的解密类型")
        
class JabPageParser:

    def __init__(self, html_text : str) -> None:
        self._html_text = html_text
    
    def parse_id_name_actress(self) -> Tuple[str, str, str]:
        name_str = re.search(r'<title>(.*?)</title>', self._html_text).group(1)
        name_and_actress = name_str.split('- Jable.TV')[0]
        actress = name_and_actress.split()[-1]
        id = name_str.split()[0]
        name = " ".join(name_and_actress.split()[1:-1]).strip()
        return id, name, actress
    
    def parse_hls_url(self) -> str:
        return re.search(r"hlsUrl\s*=\s*'(https?://.*?\.m3u8)'", self._html_text).group(1)
    
    def parse_cover_url(self) -> str:
        cover_url = re.search(r'"og:image"\s*content\s*=\s*"(.*?)"', self._html_text).group(1)
        return cover_url

    def parse_hash_tag(self) -> Tuple[str]:
        hashtags = re.search(r'name\s*=\s*"keywords"\s*content\s*=\s*"(.*?)"', self._html_text).group(1)
        return tuple(hashtags.split(',')[:-1])

    def parse_release_date(self) -> str:
        return "Unknown"

    def parse_time_length(self) -> str:
        return "Unknown"

    def parse_has_chinese(self) -> bool:
        return False

    def parse(self) -> Dict:
        id, name, actress = self.parse_id_name_actress()
        hls_url = self.parse_hls_url()
        cover_url = self.parse_cover_url()
        hash_tag = self.parse_hash_tag()
        release_date = self.parse_release_date()
        time_length = self.parse_time_length()
        has_chinese = self.parse_has_chinese()
        return {
            'id' : id,
            'name' : name,
            'actress' : actress,
            'hash_tag' : hash_tag,
            'hls_url' : hls_url,
            'cover_url' : cover_url,
            'release_date' : release_date,
            'time_length' : time_length,
            'has_chinese' : has_chinese,
        }

class Downloader:
    '''
    m3u8下载器
    '''
    def __init__(
            self,
            packages : Union[DownloadPackage, List[DownloadPackage]],
            *,
            decrypter : Decrypter = Decrypter(DecrptyType.AES),
            headers : Dict = None,
            proxies : Dict = None,
            use_ffmpeg : bool = True,
            **kwargs : Any
            ) -> None:
        self._packages = packages if isinstance(packages, list) else [packages]
        self._decrypter = decrypter
        self._headers = headers or {}
        self._proxies = proxies or {}
        self._use_ffmpeg = use_ffmpeg
        self._kwargs = kwargs
    
    @staticmethod
    def _ts_is_corrupted(
        file_path : Path,
        ) -> bool:
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                return len(data) % 16 != 0
        except UnicodeDecodeError:
            return True
    
    @staticmethod
    def _undownload_ts(
        m3u8_obj : m3u8.M3U8, 
        tmp_ts_dir : Path,
        ts_start_filename : str,
        ) -> m3u8.SegmentList:
        # 当只是改变m3u8链接而不改变视频分割时
        if prefix_match := re.search(r"(\d+)0.ts", ts_start_filename):
            prefix = prefix_match.group(1)
        downloaded_ts_index = []
        undownload_ts = []
        for file in tmp_ts_dir.iterdir():
            if file.is_file() and file.name.endswith('.ts'):
                ts_index_match = re.search(prefix + r"(\d+).ts", file.name)
                index = int(ts_index_match.group(1))
                if Downloader._ts_is_corrupted(file):
                    logger.warning(f"文件损坏,文件名:{file.name}")
                    continue
                if index >= 0:
                    downloaded_ts_index.append(index)
                else:
                    logger.warning(f"文件名错误,文件名:{file.name}")
        downloaded_ts_index.sort()
        for i, segment in enumerate(m3u8_obj.segments):
            if i in downloaded_ts_index:
                continue
            undownload_ts.append(segment)
        return undownload_ts

    def _pause_exit_handler(self, signum, frame) -> None:
        logger.info("收到暂停信号,暂停下载...")
        pass
    
    def _init_dir(
        self,
        package : DownloadPackage,
        ) -> Dict:
        tmp_m3u8 = config.tmp_m3u8_dir / f'{package.id.lower()}.m3u8'
        tmp_key = config.tmp_key_dir / f'{package.id.lower()}.key'
        tmp_iv = config.tmp_iv_dir / f'{package.id.lower()}.iv'
        tmp_ts_dir = config.tmp_ts_dir / f'{package.id.lower()}'
        tmp_ts_dir.mkdir(parents=True, exist_ok=True)
        if self._use_ffmpeg:
            list_file_path = config.tmp_dir / f'{package.id.lower()}.txt'
        else:
            list_file_path = None
        return {
            'tmp_m3u8' : tmp_m3u8,
            'tmp_key' : tmp_key,
            'tmp_iv' : tmp_iv,
            'tmp_ts_dir' : tmp_ts_dir,
            'list_file_path' : list_file_path,
        }
    
    def _init_request_headers(self) -> None:
        config.headers.update(self._headers)
        config.proxies.update(self._proxies)
    
    def _init_session(
            self, 
            session : Union[requests.Session, aiohttp.ClientSession], 
            is_async : bool = False
            ) -> None:
        if not is_async:
            session.proxies.update(config.proxies)
        session.headers.update(config.headers)
    
    def decrypt_ts(
            self,
            tmp_ts_dir : Path,
            key : bytes,
            iv : str,
            ts_name : str,
            ) -> None:
        ts_path = tmp_ts_dir / ts_name
        with open(ts_path, 'rb') as f:
            decrypted_data = self._decrypter.decrypt(f.read(), key, iv)
        with open(ts_path, 'wb') as f:
            f.write(decrypted_data)
    
    @staticmethod
    def _write_tmp_file(
            file_path : Path, 
            content : Union[bytes, str], 
            ) -> None:
        if isinstance(content, str):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        if isinstance(content, bytes):
            with open(file_path, 'wb') as f:
                f.write(content)
    
    @staticmethod
    def _write_tmp(
        write_dict : Dict[Path, Union[str, bytes]]
        ) -> None:
        for key, value in write_dict.items():
            Downloader._write_tmp_file(key, value)
    
    @staticmethod
    def _load_tmp(
        package : DownloadPackage,
        tmp_file_type : Union[str, List[str]],
    ) -> Union[bytes, str, Dict, None]:
        if isinstance(tmp_file_type, str):
            if tmp_file_type == 'm3u8':
                file_path = config.tmp_m3u8_dir / f'{package.id.lower()}.m3u8'
            elif tmp_file_type == 'key':
                file_path = config.tmp_key_dir / f'{package.id.lower()}.key'
            elif tmp_file_type == 'iv':
                file_path = config.tmp_iv_dir / f'{package.id.lower()}.iv'
            else:
                logger.error("不支持的临时文件类型, 仅支持m3u8, key, iv")
                return None
            if file_path.exists():
                if tmp_file_type == 'm3u8' or tmp_file_type == 'iv':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
        elif isinstance(tmp_file_type, list):
            tmp_file_dict = {}
            for tf in tmp_file_type:
                if tf == 'm3u8':
                    file_path = config.tmp_m3u8_dir / f'{package.id.lower()}.m3u8'
                elif tf == 'key':
                    file_path = config.tmp_key_dir / f'{package.id.lower()}.key'
                elif tf == 'iv':
                    file_path = config.tmp_iv_dir / f'{package.id.lower()}.iv'
                else:
                    logger.error("不支持的临时文件类型, 仅支持m3u8, key, iv")
                    continue
                if file_path.exists():
                    if tf == 'm3u8' or tf == 'iv':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            tmp_file_dict[tf] = f.read()
                    else:
                        with open(file_path, 'rb') as f:
                            tmp_file_dict[tf] = f.read()
                else:
                    tmp_file_dict[tf] = None
            return tmp_file_dict
    
    def _validate_load_tmp(
        self,
        package : DownloadPackage,
        tmp_file_types : Union[str, List[str]],
        callback : Callable,
        ) -> Any:
        '''
        检验临时文件是否存在,根据不同文件的存在与否返回不同的重加载方法
        '''
        if isinstance(tmp_file_types, str):
            tmp_file = self._load_tmp(package, tmp_file_types)
            if not tmp_file and callback:
                return callback()
            return tmp_file
        elif isinstance(tmp_file_types, list):
            tmp_files = self._load_tmp(package, tmp_file_types)
            if 'm3u8' in tmp_file_types and not tmp_files.get('m3u8', None):
                return callback()
            if 'key' in tmp_file_types and not tmp_files.get('key', None):
                return callback()
            if 'iv' in tmp_file_types and not tmp_files.get('iv', None):
                if 'm3u8' in tmp_files:
                    iv = m3u8.loads(tmp_files['m3u8']).keys[0].iv
                    tmp_files['iv'] = iv
                else:    
                    return callback()
            return tmp_files
    
    def _update_hls_url(
            self,
            package : DownloadPackage,
    ) -> str:
        # TODO: 实现更新hls_url的逻辑
        domain = package.src
        if domain.endswith('/'):
            domain = domain[:-1]
        video_address = urljoin(domain, f"/videos/{package.id.lower()}/")
        response = requests.get(video_address, headers=config.headers, proxies=config.proxies, timeout=10)
        if response.status_code == 200:
            page_parser = JabPageParser(response.text)
            return page_parser.parse_hls_url()
        elif response.status_code == 403:
            logger.error(f"获取视频地址失败,url:{video_address},状态码:{response.status_code}")
        else:
            logger.error(f"获取视频地址失败,url:{video_address},状态码:{response.status_code}")
    
    async def _async_download_ts(
                self, 
                package : DownloadPackage,
                segments : m3u8.SegmentList,
                base_url : str,
                tmp_folder_name : str,
                key_bytes : bytes,
                iv : str,
                ) -> None:
        tmp_ts_dir = config.tmp_ts_dir / tmp_folder_name
        tmp_ts_dir.mkdir(parents=True, exist_ok=True)
        async with aiohttp.ClientSession() as session:
            logger.info('开始下载ts文件...')
            self._init_session(session=session, is_async=True)
            semaphore = asyncio.Semaphore(config.max_ts_concurrency)

            tasks = []
            for segment in segments:
                task = self._download_single_ts(
                    session=session,
                    segment=segment,
                    base_url=base_url,
                    tmp_ts_dir=tmp_ts_dir,
                    key_bytes=key_bytes,
                    iv=iv,
                    semaphore=semaphore
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _download_single_ts(
            self,
            session : aiohttp.ClientSession,
            segment : m3u8.Segment,
            tmp_ts_dir : Path,
            base_url : str,
            key_bytes : bytes,
            iv : str,
            semaphore : asyncio.Semaphore,
            ) -> None:
        async with semaphore:
            ts_url = urljoin(base_url, segment.uri)
            logger.info(f"下载ts文件: {segment.uri}")
            try:
                async with session.get(ts_url, proxy=config.proxies['http']) as ts_response:
                    if ts_response.status == 200:
                        with open(tmp_ts_dir / segment.uri, "wb") as f:
                            while True:
                                chunk = await ts_response.content.read(8 * 1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                        self.decrypt_ts(
                            tmp_ts_dir = tmp_ts_dir,
                            key = key_bytes,
                            iv = iv,
                            ts_name = segment.uri
                        )
                    elif ts_response.status == 403:
                        logger.error(f"下载ts文件失败,url:{ts_url},状态码:{ts_response.status}")
                        raise Exception(f"403 forbidden, url:{ts_url}")
                    elif ts_response.status == 410:
                        logger.info("m3u8文件已过期,将重新下载")
                        # TODO: 实现重新下载m3u8文件的逻辑
                    else:
                        logger.error(f"下载ts文件失败,url:{ts_url},状态码:{ts_response.status}")
            except aiohttp.ClientError:
                logger.error(f"下载ts文件失败,url:{ts_url}")
    
    def _merge_ts_without_ffmpeg(
            self,
            package : DownloadPackage,
            ) -> None:
        ts_file_path = config.tmp_ts_dir / package.id.lower()
        ts_files = []
        for file in ts_file_path.iterdir():
            if self._ts_is_corrupted(file):
                logger.warning(f"文件损坏,文件名:{file.name}")
                continue
            ts_files.append(file)
        ts_files.sort(key=lambda x: int(x.name.split('.')[0]))
        with open(config.video_dir / f'{package.id.lower()}.mp4', 'wb') as f:
            for file in ts_files:
                with open(file, 'rb') as ts_file:
                    while True:
                        chunk = ts_file.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

    def _merge_ts_with_ffmpeg(
            self,
            package : DownloadPackage, 
            list_file_path : Path, 
            m3u8_obj : m3u8.M3U8
            ) -> None:
        with open(list_file_path, 'w') as f:
            for segment in m3u8_obj.segments:
                filename : Path = list_file_path / f'{segment.uri}'
                if os.path.exists(filename):
                    filename : str = filename.replace('\\', '\\\\')
                    f.write(f"file '{filename}'\n")
                else:
                    logger.warning('文件不存在')
        try:
            merge_command = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', list_file_path,
                '-c', 'copy',
                '-y',
                config.video_dir / f'{package.id.lower()}.mp4'
            ]
            subprocess.run(merge_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            logger.error(f"合并视频片段失败:{e.stderr.decode('utf-8')}")
        else:
            logger.error(f"视频合并完成,输出文件:{config.video_dir / f'{package.id.lower()}.mp4'}")
    
    @overload
    def _merge_ts(self, package : DownloadPackage) -> None:...

    @overload
    def _merge_ts(self, package : DownloadPackage, list_file_path : Path, m3u8_obj : m3u8.M3U8) -> None:...

    def _merge_ts(
        self,
        package : DownloadPackage,
        list_file_path : Optional[Path] = None,
        m3u8_obj : Optional[m3u8.M3U8] = None,
        ) -> None:
        if self._use_ffmpeg and list_file_path and m3u8_obj:
            self._merge_ts_with_ffmpeg(
                package=package,
                list_file_path=list_file_path,
                m3u8_obj=m3u8_obj,
            )
        else:
            self._merge_ts_without_ffmpeg(package=package)
    
    def _download_m3u8(
            self,
            hls_url : str,
            package : DownloadPackage,
    ) -> None:
        dirs = self._init_dir(package)
        try:
            m3u8_str = requests.get(hls_url, headers = config.headers, proxies = config.proxies).text
            m3u8_obj = m3u8.loads(m3u8_str)
            if os.path.exists(dirs['tmp_m3u8']):
                with open(dirs['tmp_m3u8'], 'r') as f:
                    m3u8_file_str = f.read()
                if (
                    hash(m3u8_file_str) == hash(m3u8_str)
                    and hash(hls_url) == hash(package.hls_url) 
                    and os.path.exists(dirs['tmp_key']) 
                    and os.path.exists(dirs['tmp_iv'])
                    ):
                    logger.info("m3u8文件未变化, 跳过下载")
                    return
                else:
                    package.update(hls_url=hls_url)
                    iv = m3u8_obj.keys[0].iv
                    key_uri = m3u8_obj.keys[0].uri
                    key_bytes = requests.get(urljoin(package.base_url, key_uri), headers=config.headers, proxies=config.proxies).content
                    write_dict = {
                        dirs['tmp_m3u8'] : m3u8_str,
                        dirs['tmp_key'] : key_bytes,
                        dirs['tmp_iv'] : iv
                    }
                    logger.info("m3u8文件已变化, 重新下载")
                    self._write_tmp(write_dict)
            else:
                package.update(hls_url=hls_url)
                iv = m3u8_obj.keys[0].iv
                key_uri = m3u8_obj.keys[0].uri
                key_bytes = requests.get(urljoin(package.base_url, key_uri), headers=config.headers, proxies=config.proxies).content
                write_dict = {
                    dirs['tmp_m3u8'] : m3u8_str,
                    dirs['tmp_key'] : key_bytes,
                    dirs['tmp_iv'] : iv
                }
                logger.info("m3u8文件不存在, 下载")
                self._write_tmp(write_dict)
        except requests.exceptions.RequestException:
            logger.error("下载m3u8文件失败")   

    def _download_cover(
            self, 
            package : DownloadPackage
            ) -> None:
        cover_url = package.cover_url
        response = requests.get(cover_url, headers=config.headers, proxies=config.proxies, timeout=10)
        if response.status_code == 200:
            with open(config.cover_dir / f'{package.id.lower()}.jpg', 'wb') as f:
                f.write(response.content)
        else:
            logger.error(f"下载封面失败,url:{cover_url},状态码:{response.status_code}")

    def single_downloader(
            self,
            package : DownloadPackage,
            ) -> None:
        session = requests.Session()
        self._init_request_headers()
        self._init_session(session=session, is_async=False)
        dirs = self._init_dir(package)
        with session as s:
            self._download_m3u8(
                package=package,
                hls_url=package.hls_url, 
                )
            self._download_cover(package=package)
            decypt_info_dict = self._load_tmp(
                package=package,
                tmp_file_type=['m3u8', 'key', 'iv']
            )
            asyncio.run(self._async_download_ts(
                package=package,
                segments=m3u8.loads(decypt_info_dict['m3u8']).segments, 
                base_url=package.base_url, 
                tmp_folder_name=package.id.lower(),
                key_bytes=decypt_info_dict['key'],
                iv=decypt_info_dict['iv']
                ))
        self._merge_ts(package=package, list_file_path=dirs['list_file_path'], m3u8_obj=m3u8.loads(decypt_info_dict['m3u8']))
    
    def _redownload(
            self,
            package : DownloadPackage,
            tmp_ts_dir : Path,
            ts_start_filename : str,
            ) -> None:
        hls_url = self._update_hls_url(package=package)
        self._download_m3u8(hls_url=hls_url, package=package)
        decrpt_info = self._load_tmp(
            package=package,
            tmp_file_type=['m3u8', 'key', 'iv']
        )
        undownload_segments = self._undownload_ts(
            m3u8_obj=m3u8.loads(decrpt_info['m3u8']), 
            tmp_ts_dir=tmp_ts_dir, 
            ts_start_filename=ts_start_filename
        )
        if len(undownload_segments) == 0:
            logger.info("所有ts文件已下载完成")
            return
        logger.info(f'未下载的ts文件数量: {len(undownload_segments)}')
        asyncio.run(self._async_download_ts(
            package=package,
            segments=undownload_segments,
            base_url=package.base_url,
            tmp_folder_name=package.id.lower(),
            key_bytes=decrpt_info['key'],
            iv=decrpt_info['iv']
            ))
                
    async def async_downloader(self) -> None:
        pass

    def threaded_downloader(self) -> None:
        pass

    def download(self) -> None:
        if len(self._packages) == 1:
            self.single_downloader()
            return
        else:
            raise ValueError("不支持的下载类型")

if __name__ == '__main__':
    # package = DownloadPackage(
    #     id = 'MVSD-652',
    #     name = 'test1',
    #     hls_url = 'https://akuma-trstin.mushroomtrack.com/hls/g7_t_mbwonVQZs8sR-r4UQ/1759664954/52000/52898/52898.m3u8',
    #     hash_tag = tuple(),
    #     actress = 'Unkown',
    #     cover_url = None
    # )
    headers = {
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Origin' : "https://jable.tv",
        'Referer' : "https://jable.tv",
        'Priority' : 'u=1, i'
    }
    # packages = [package]
    # downloader = Downloader(
    #     packages=packages,
    #     download_type=DownloadType.ASYNC,
    #     headers=headers,
    # )
    # with open(r"D:\桌面\Video\tmp\m3u8\mvsd-652.m3u8", 'r') as f:
    #     m3u8_str = f.read()
    # m3u8_obj = m3u8.loads(m3u8_str)
    # tmp_ts_dir = config.tmp_ts_dir / 'MVSD-652'.lower()
    # ts_start_filename = m3u8_obj.segments[0].uri
    # downloader._redownload(
    #     package=package,
    #     tmp_ts_dir=tmp_ts_dir,
    #     ts_start_filename=ts_start_filename
    # )
    # downloader._merge_ts(
    #     package=package
    # )
    with open("test.txt", 'r', encoding='utf-8') as f:
        html_text = f.read()
    pageparser = JabPageParser(html_text=html_text)
    print(pageparser.parse_id_name_actress())
    print(pageparser.parse_hash_tag())
    print(pageparser.parse_cover_url())