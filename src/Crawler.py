import os

import time
import json
import logging
import requests
from threading import Thread, Lock
from collections import namedtuple
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union

from .Config.Config import config
from .utils.Logger import Logger
from .utils.EnumType import Page
from .PageParse.actressId import ActressId
from .utils.DataUnit import DownloadPackage, VideoPackage
from .PageParse.PageParser import JabPageParser
from .PageParse.tagMapping import TagParser
from .Error.Exception import ForbiddenError, NotFoundError
from .Downloader import Downloader

logger = Logger(config.log_dir).get_logger(__name__, logging.INFO)

class VideoCrawlerBase(ABC):

    def __init__(
            self, 
            url : str,
            src : str,
            ) -> None:
        self.url = url
        self.src = src

    @abstractmethod
    def _parse_page_content(self) -> Any:
        raise NotImplementedError
    
    @abstractmethod
    def _init_download_package(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def parse(self) -> DownloadPackage:
        raise NotImplementedError
    
    @abstractmethod
    def download_video(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def _validate_src(self) -> bool:
        raise NotImplementedError

class JabVideoCrawler(VideoCrawlerBase):

    def __init__(
            self, 
            url : Optional[str] = None,
            src : str = 'jable.tv',
            videos_per_page : int = 24,
            ):
        super().__init__(url, src)
        self.videos_per_page = videos_per_page
        self._download_list = []
    
    def _get_headers(
            self,
            **kwargs,
            ) -> None:
        '''
        设置请求头
        Args:
            **kwargs: 请求头参数
        Returns:
            None
        Raises:
            ValueError: 不支持的视频网站
        '''
        if self._validate_src():
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                'Origin' : 'https://jable.tv',
                'Referer' : 'https://jable.tv/',
                'Priority' : 'u=1, i',
            }
            headers.update({**kwargs})
            try:
                config.load_headers()
                logger.info(f'加载请求头成功!')
            except FileNotFoundError:
                pass
            config.headers.update(headers)
        else:
            logger.error(f'不支持的视频网站: {self.src}')
            raise ValueError(f'不支持的视频网站: {self.src}')
    
    def _set_proxy(self, proxies : Optional[Dict] = None) -> None:
        if not proxies:
            return
        config.proxies.update(proxies)
    
    def _is_available(self, type : str) -> bool:
        '''
        判断视频
        '''
        if type == 'video':
            pass
        elif type == 'cover':
            pass
        else:
            logger.error(f'不支持的类型: {type}')
            raise ValueError(f'不支持的类型: {type}')
    
    def _get_html_text(self) -> str:
        '''
        获取html文本

        Returns:
            str: html文本
        Raises:
            NotFoundError: 请求视频页面不存在
            ForbiddenError: 请求视频页面被禁止
            Exception: 请求视频页面失败
        '''
        self._get_headers()
        self._set_proxy()
        NotFound_count = 0
        for retry_count in range(config.max_retries):
            try:
                response = requests.get(self.url, headers=config.headers, proxies=config.proxies, timeout=10)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 403:
                    if self._parse_page_content(response.text) == Page.CAPTACHA:
                        logger.info(f'请求视频页面被拦截,正在验证...')
                        if html_text := JabPageParser.validation(self.url):
                            logger.info(f'验证成功,继续请求...')
                            cookies_list = [f"{cookies['name']}={cookies['value']}" for cookies in config.cookie]
                            config.headers.update({'Cookie': '; '.join(cookies_list)})
                            config.save_headers()
                            return html_text
                        else:
                            logger.error('验证失败')
                            raise ForbiddenError('验证失败')
                    logger.error(f'请求视频页面被禁止: {response.status_code}')
                    raise ForbiddenError(f'请求视频页面被禁止: {response.status_code}')
                elif response.status_code == 404:
                    NotFound_count += 1
                    logger.warning(f'请求视频页面不存在: {response.status_code}')
                else:
                    logger.error(f'请求视频页面失败: {response.status_code},正在重试...')
            except requests.exceptions.RequestException as e:
                logger.error(f'请求视频页面失败: {e},正在重试...')
            wait_time = config.retry_wait_time * (2 ** retry_count + 1)
            logger.info(f'等待 {wait_time} 秒后重试...')
            time.sleep(wait_time)
        logger.error(f'请求视频页面失败: 超过最大重试次数')
        if NotFound_count >= config.max_retries:
            raise NotFoundError(f'请求视频页面不存在: {response.status_code}')
        raise Exception(f'请求视频页面失败: 超过最大重试次数')
                
    def _parse_page_content(
            self,
            html_text : str = None,
            ) -> Page:
        '''
        获取页面类型
        Args:
            html_text(str): 页面文本,默认为None
        Returns:
            Page: 页面类型
        Raises:
            ValueError: 不支持的视频链接
        '''
        if html_text:
            if 'just a moment' in html_text.lower():
                return Page.CAPTACHA
            else:
                logger.error('未知错误')
                raise ValueError('未知错误')
        if 'videos' in self.url:
            return Page.SINGLE_VIDEO
        else:
            logger.error(f'不支持的视频链接: {self.url}')
            raise ValueError(f'不支持的视频链接: {self.url}')

    def _init_download_package(
            self,
            package_info_dict : Dict,
            ) -> DownloadPackage:
        package = DownloadPackage(
            id = package_info_dict['id'],
            name = package_info_dict['name'],
            actress = package_info_dict['actress'],
            hash_tag = package_info_dict['hash_tag'],
            hls_url = package_info_dict['hls_url'],
            cover_url = package_info_dict['cover_url'],
            src = self.src,
            time_length=package_info_dict['time_length'],
            release_date=package_info_dict['release_date'],
            has_chinese=package_info_dict['has_chinese'],
        )
        return package
    
    def parse(self) -> Any:
        '''
        解析html页面,根据页面信息返回不同操作

        Returns:
            DownloadPackage: 下载信息
        '''
        page = self._parse_page_content()
        if page == Page.SINGLE_VIDEO:
            html_text = self._get_html_text()
            _actress_id = ActressId(html_text=html_text)
            _actress_id._parse()
            _actress_id._dump()
            logger.info(f"解析页面: \n{html_text[:500]}")
            parser = JabPageParser(html_text)
            package_info_dict = parser.parse()
            return self._init_download_package(package_info_dict)
        else:
            logger.error(f'不支持的视频链接: {self.url}')
    
    def _tag2link(
            self,
            tag_title : str,
            tag : str,
    ) -> str:
        '''
        根据标签名称获取标签链接,用于标签名固定的情况下使用

        Args:
            tag_title(str): 标签名称
            tag(str): 标签关键词
        Returns:
            str: 标签链接
        '''
        _tag_parser = TagParser()
        tag_title, tag = _tag_parser._input_tag2_hant(tag_title, tag)
        if os.path.exists(config.assets_dir / 'tag_mapping.json'):
            with open(config.assets_dir / 'tag_mapping.json', 'r', encoding='utf-8') as f:
                tag_mapping = json.load(f)
            if 'jable' in tag_mapping:
                tags : Dict = tag_mapping['jable']
                if tag_title in tags:
                    if tag in tags[tag_title]:
                        return f'https://jable.tv/tags/{tags[tag_title][tag]}/'
                    else:
                        logger.error(f"{tag} 不在 {tag_title} 标签下")
                        raise ValueError(f"{tag} 不在 {tag_title} 标签下")
                else:
                    logger.error(f'不支持的标签: {tag_title}')
                    raise ValueError(f'不支持的标签: {tag_title}')
        else:
            logger.error(f'标签映射文件不存在: {config.assets_dir / "tag_mapping.json"}')
            raise FileNotFoundError(f'标签映射文件不存在: {config.assets_dir / "tag_mapping.json"}')
    
    def _search(self, search_word : str) -> Tuple[int, int, Union[List[VideoPackage], None]]:
        '''
        根据提供的标签关键词搜索视频,返回搜索得到的视频数和页数以及第一页视频.
        '''
        SearchInfo = namedtuple('SearchInfo', ['videos', 'pages', 'first_page_videos'])
        parser = JabPageParser()
        search_api = f'https://jable.tv/search/{search_word}'
        for retry_count in range(config.max_retries):
            try:
                response = requests.get(search_api, headers=config.headers, proxies=config.proxies, timeout=10)
                if response.status_code == 200:
                    html_text = response.text
                    parser._html_text = html_text
                    videos = parser._parse_videos_num()
                    video_list = parser.parse()
                    pages, remainder = divmod(videos, self.videos_per_page)
                    if remainder > 0:
                        pages += 1
                    logger.info(f'搜索成功!')
                    return SearchInfo(videos=videos, pages=pages, first_page_videos=video_list)
                elif response.status_code == 404:
                    logger.error(f'搜索失败: {response.status_code}')
                    raise NotFoundError(f'搜索失败: {response.status_code}')
                elif response.status_code == 403:
                    logger.info(f"请求搜索页面被拦截,正在验证...")
                    if html_text := JabPageParser.validation(search_api):
                        logger.info(f"验证成功,继续请求...")
                        cookies_list = [f"{cookies['name']}={cookies['value']}" for cookies in config.cookie]
                        config.headers.update({'Cookie': '; '.join(cookies_list)})
                        parser._html_text = html_text
                        videos = parser._parse_videos_num()
                        video_list = parser.parse()
                        pages, remainder = divmod(videos, self.videos_per_page)
                        if remainder > 0:
                            pages += 1
                        logger.info(f'搜索成功!')
                        return SearchInfo(videos=videos, pages=pages, first_page_videos=video_list)
                    else:
                        logger.error(f"验证失败")
                        raise ForbiddenError(f"验证失败")
                else:
                    logger.error(f'搜索失败: {response.status_code}')
                    raise Exception(f'搜索失败: {response.status_code}')
            except requests.exceptions.RequestException as e:
                wait_time = config.retry_wait_time * (2 ** retry_count + 1)
                logger.info(f'搜索失败: 等待 {wait_time} 秒后重试...')
                time.sleep(wait_time)
                continue
        
    def _search_with_tag(
            self, 
            tag_title : str,
            tag : str,
            ) -> Tuple[str, int, List[VideoPackage]]:
        '''
        根据提供的标签关键词搜索视频,返回标签对应的url,页数以及第一页视频.
        '''
        TagInfo = namedtuple('TagInfo', ['url', 'pages', 'videos'])
        parser = JabPageParser()
        search_api = self._tag2link(tag_title, tag)
        for retry_count in range(config.max_retries):
            try:
                response = requests.get(search_api, headers=config.headers, proxies=config.proxies, timeout=10)
                if response.status_code == 200:
                    html_text = response.text
                    parser._html_text = html_text
                    videos = parser._parse_videos_num()
                    video_list = parser.parse()
                    pages, remainder = divmod(videos, self.videos_per_page)
                    if remainder > 0:
                        pages += 1
                    tag_info = TagInfo(url=search_api, pages=pages, videos=video_list)
                    logger.info(f'搜索成功!')
                    return tag_info
                elif response.status_code == 404:
                    logger.error(f'搜索失败: {response.status_code}')
                    raise NotFoundError(f'搜索失败: {response.status_code}')
                elif response.status_code == 403:
                    logger.info(f"请求搜索页面被拦截,正在验证...")
                    if html_text := JabPageParser.validation(search_api):
                        logger.info(f"验证成功,继续请求...")
                        cookies_list = [f"{cookies['name']}={cookies['value']}" for cookies in config.cookie]
                        config.headers.update({'Cookie': '; '.join(cookies_list)})
                        parser._html_text = html_text
                        videos = parser._parse_videos_num()
                        video_list = parser.parse()
                        pages, remainder = divmod(videos, self.videos_per_page)
                        if remainder > 0:
                            pages += 1
                        tag_info = TagInfo(url=search_api, pages=pages, videos=video_list)
                        logger.info(f'搜索成功!')
                        return tag_info
                    else:
                        logger.error(f"验证失败")
                        raise ForbiddenError(f"验证失败")
                else:
                    logger.error(f'搜索失败: {response.status_code}')
                    raise Exception(f'搜索失败: {response.status_code}')
            except requests.exceptions.RequestException as e:
                wait_time = config.retry_wait_time * (2 ** retry_count + 1)
                logger.info(f'搜索失败: 等待 {wait_time} 秒后重试...')
                time.sleep(wait_time)
                continue

    def download_video(self):
        package = self.parse()
        downloader = Downloader(package)
        downloader.download()
    
    @staticmethod
    def download_video_with_id(id : str) -> None:
        url = f'https://jable.tv/videos/{id}/'
        crawler = JabVideoCrawler(url)
        crawler.download_video()
    
    def add_task(self, download_package : DownloadPackage) -> None:
        self._download_list.append(download_package)
    
    def display_tasks(self, downloader : Downloader, wait_time : int = 1) -> None:
        total = ''
        for name, counter in downloader._counters.items():
            total += f"\r{name} : {counter.current_id} / {counter.total_num}\n"
        print(total, end='')
        time.sleep(wait_time)

    def run_tasks(self) -> None:
        if self._download_list:
            downloader = Downloader(self._download_list)
            task = Thread(target=self.display_tasks, args=(downloader, 5))
            task.start()
            downloader.download()
        else:
            logger.error('下载列表为空')
            raise ValueError('下载列表为空')
    
    def muti_download(
            self, 
            ids : List[str],
            quiet : bool = False,
            ) -> None:
        if quiet:
            Logger(config.log_dir).disable_stream_handler('src.Downloader')
        for id in ids:
            url = f'https://jable.tv/videos/{id}/'
            crawler = JabVideoCrawler(url)
            package = crawler.parse()
            self.add_task(package)
        self.run_tasks()

    def _validate_src(self):
        return self.src == 'jable.tv' and self.src in self.url