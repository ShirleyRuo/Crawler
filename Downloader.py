import os
import sys

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
from tqdm import tqdm
from Crypto.Cipher import AES
from dataclasses import dataclass
from typing import List, Optional, Callable, Any, Union, Tuple, Dict

from Config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
    )
logger = logging.getLogger(__name__)

class DownloadStatus(Enum):

    PENDING = 1
    DOWNLOADING = 2
    PAUSED = 3
    DECRYPTING = 4
    MERGING = 5
    FINISHED = 6
    FAILED = 7

class DownloadType(Enum):

    ASYNC = 1
    THREADED = 2

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

class DownloaderQueue(queue.Queue):
    '''
    根据下载的类型以及下载包的集合，给出对应的下载包
    '''
    def __init__(
            self, 
            packages : List[DownloadPackage],
            download_type : DownloadType,
            ) -> None:
        super().__init__(maxsize=config.max_concurrency)
        self._packages = set()
        for package in packages:
            self._packages.add(package)
        self._download_type = download_type
    
    def to_task(self) -> List[DownloadPackage]:
        if len(self._packages) == 1:
            return self._packages
        if self._download_type == DownloadType.ASYNC:
            return self._packages
        elif self._download_type == DownloadType.THREADED:
            return self._packages
        else:
            raise ValueError("不支持的下载类型")

class TsQueue(queue.Queue):

    def __init__(
            self, 
            maxsize=config.max_ts_concurrency
            ) -> None:
        super.__init__(maxsize=maxsize)

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

class Downloader:
    '''
    m3u8下载器
    '''
    def __init__(
            self,
            packages : Union[DownloadPackage, List[DownloadPackage]],
            download_type : DownloadType,
            *,
            decrypter : Decrypter = Decrypter(DecrptyType.AES),
            headers : Dict = None,
            proxies : Dict = None,
            **kwargs : Any
            ) -> None:
        self._packages = packages if isinstance(packages, list) else [packages]
        self._decrypter = decrypter
        self._headers = headers or {}
        self._proxies = proxies or {}
        self._download_type = download_type
        self._kwargs = kwargs
    
    @staticmethod
    def _average_ts_file_size(tmp_ts_dir: Path) -> int:
        ts_files = list(tmp_ts_dir.glob('*.ts'))
        if not ts_files:
            return 0
        total_size = sum(file.stat().st_size for file in ts_files)
        return total_size // len(ts_files)

    @staticmethod
    def _ts_is_corrupted(
        file_path : Path,
        average_size : int,
        ) -> bool:
        file_size = file_path.stat().st_size
        return file_size < average_size // 2  # 如果文件大小小于平均值的一半，认为是损坏的
    
    @staticmethod
    def _undownload_ts_index(
        m3u8_obj : m3u8.M3U8, 
        tmp_ts_dir : Path,
        ts_start_filename : str,
        ) -> List[int]:
        # 当只是改变m3u8链接而不改变视频分割时
        ts_start_index = int(ts_start_filename.split('.')[0])
        downloaded_ts_index = []
        download_ts_index = []
        average_size = Downloader._average_ts_file_size(tmp_ts_dir)
        for file in tmp_ts_dir.iterdir():
            if file.is_file() and file.name.endswith('.ts'):
                ts_index = int(file.name.split('.')[0])
                index = ts_index - ts_start_index
                if Downloader._ts_is_corrupted(file, average_size):
                    logger.warning(f"文件损坏，文件名：{file.name}")
                    continue
                if index >= 0:
                    downloaded_ts_index.append(index)
                else:
                    logger.warning(f"文件名错误，文件名：{file.name}")
        for i in range(len(m3u8_obj.segments)):
            if i in downloaded_ts_index:
                continue
            download_ts_index.append(i)
        return download_ts_index
      
    def _pre_process(self) -> None:
        '''
        下载包中的m3u8文件进行预处理
        '''
        pass
    
    def _dump_key_iv(self, key : bytes, iv : str) -> None:
        pass
    
    def _pause_exit_handler(self, signum, frame) -> None:
        logger.info("收到暂停信号，暂停下载...")
        pass
    
    @staticmethod
    def _init_dir(
        package : DownloadPackage,
        use_ffmpeg: bool = True,
        ) -> Dict:
        tmp_m3u8 = config.tmp_m3u8_dir / f'{package.id.lower()}.m3u8'
        tmp_key = config.tmp_key_dir / f'{package.id.lower()}.key'
        tmp_iv = config.tmp_iv_dir / f'{package.id.lower()}.iv'
        tmp_ts_dir = config.tmp_ts_dir / f'{package.id.lower()}'
        tmp_ts_dir.mkdir(parents=True, exist_ok=True)
        if use_ffmpeg:
            list_file_path = config.tmp_dir / f'{package.id.lower()}.txt'
        else:
            list_file_path = None
        return {
            'tmp_m3u8' : tmp_m3u8,
            'tmp_key' : tmp_key,
            'tmp_iv' : tmp_iv,
            'tmp_ts_dir' : tmp_ts_dir,
            'list_file_path' : list_file_path,
            'use_ffmpeg' : use_ffmpeg,
        }
    
    def _init_request_headers(self) -> None:
        config.headers.update(self._headers)
        config.proxies.update(self._proxies)
    

    def _init_session(self, session : Union[requests.Session, aiohttp.ClientSession]) -> None:
        session.headers.update(config.headers)
        session.proxies.update(config.proxies)
    
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
    
    async def _async_download_ts(self, segments : m3u8.SegmentList) -> None:
        async with aiohttp.ClientSession() as session:
            self._init_session(session=session)
            tasks = []
            for segment in segments:
                tasks.append(session.get(segment.uri))
            responses = await asyncio.gather(*tasks)
            for resp in responses:
                if resp.status == 200:
                    ts_data = await resp.read()
                    ts_name = resp.url.name
                    self._write_tmp_file(dirs['tmp_ts_dir'] / ts_name, ts_data)

    def single_downloader(self) -> None:
        self._init_request_headers()
        session = requests.Session()
        self._init_session(session=session)
        dirs = self._init_dir(self._packages[0], use_ffmpeg=True)
        with session as s:
            try:
                m3u8_str = s.get(self._packages[0].hls_url).text
                m3u8_obj = m3u8.loads(m3u8_str)
                if os.path.exists(dirs['tmp_m3u8']):
                    with open(dirs['tmp_m3u8'], 'r') as f:
                        m3u8_file_str = f.read()
                    if (
                        hash(m3u8_file_str) == hash(m3u8_str) 
                        and os.path.exists(dirs['tmp_key']) 
                        and os.path.exists(dirs['tmp_iv'])
                        ):
                        with open(dirs['tmp_key'], 'rb') as f:
                            key_bytes = f.read()
                        with open(dirs['tmp_iv'], 'r') as f:
                            iv = f.read()
                    else:
                        iv = m3u8_obj.keys[0].iv
                        key_uri = m3u8_obj.keys[0].uri
                        key_bytes = s.get(urljoin(self._packages[0].base_url, key_uri)).content
                        write_dict = {
                            dir['tmp_m3u8'] : m3u8_str,
                            dir['tmp_key'] : key_bytes,
                            dir['tmp_iv'] : iv
                        }
                        Downloader._write_tmp(write_dict)
                else:
                    iv = m3u8_obj.keys[0].iv
                    key_uri = m3u8_obj.keys[0].uri
                    key_bytes = s.get(urljoin(self._packages[0].base_url, key_uri)).content
                    write_dict = {
                        dir['tmp_m3u8'] : m3u8_str,
                        dir['tmp_key'] : key_bytes,
                        dir['tmp_iv'] : iv
                    }
                    Downloader._write_tmp(write_dict)                    
            except requests.exceptions.RequestException:
                logger.error("下载m3u8文件失败")
            for fragment in tqdm(m3u8_obj.segments):
                url = urljoin(self._packages[0].base_url, fragment.uri)
                try:
                    ts_io = s.get(url, stream=True)
                    with open(dirs['tmp_ts_dir'] / f'{fragment.uri}', 'wb') as f:
                        for chunk in ts_io.iter_content(chunk_size= 8 * 1024):
                            if chunk:
                                f.write(chunk)
                    self.decrypt_ts(
                        tmp_ts_dir = dirs['tmp_ts_dir'],
                        key = key_bytes,
                        iv = iv,
                        ts_name = fragment.uri
                    )
                except requests.exceptions.RequestException:
                    logger.error("下载ts文件失败")
        with open(dirs['list_file_path'], 'w') as f:
            for segment in m3u8_obj.segments:
                filename : Path = dirs['tmp_ts_dir'] / f'{segment.uri}'
                if os.path.exists(filename):
                    filename : str = filename.replace('\\', '\\\\')
                    f.write(f"file '{filename}'\n")
                else:
                    print('文件不存在')
        try:
            # 使用ffmpeg的concat协议合并
            # `-safe 0` 用于避免“不安全的文件名”错误
            merge_command = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', dirs['list_file_path'],
                '-c', 'copy',  # 直接复制流，无需重新编码，速度快
                '-y',  # 覆盖输出文件
                config.download_dir / f'{self._packages[0].id.lower()}.mp4'
            ]
            subprocess.run(merge_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"合并视频片段失败：{e.stderr.decode('utf-8')}")
        else:
            print(f"视频合并完成，输出文件：{config.download_dir / f'{self._packages[0].id.lower()}.mp4'}")
                
    async def async_downloader(self) -> None:
        pass

    def threaded_downloader(self) -> None:
        pass

    def download(self) -> None:
        if len(self._packages) == 1:
            self.single_downloader()
            return
        if self._download_type == DownloadType.ASYNC:
            asyncio.run(self.async_downloader())
        elif self._download_type == DownloadType.THREADED:
            self.threaded_downloader()
        else:
            raise ValueError("不支持的下载类型")

if __name__ == '__main__':
    # package = DownloadPackage(
    #     id = 'GVH-778',
    #     name = 'test1',
    #     hls_url = 'https://honi-moly-yami.mushroomtrack.com/hls/LszpgGPcY_4B2-dQZib2HA/1759422490/53000/53265/53265.m3u8',
    #     hash_tag = tuple(),
    #     actress = 'Unkown',
    #     cover_url = None
    # )
    # headers = {
    #     'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    #     'Origin' : "https://jable.tv",
    #     'Referer' : "https://jable.tv",
    #     'Priority' : 'u=1, i'
    # }
    # packages = [package]
    # downloader = Downloader(
    #     packages=packages,
    #     download_type=DownloadType.ASYNC,
    #     headers=headers,
    # )
    # downloader.download()
    with open(r'D:\桌面\Video\tmp\m3u8\gvh-778.m3u8', 'r') as f:
        m3u8_str = f.read()
    print(hash(m3u8_str))
    print(hash(m3u8_str))