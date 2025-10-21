import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from .Config import config
from .Logger import Logger
from .EnumType import Page
from .PageParse.PageParser import JabPageParser
from .DataUnit import DownloadPackage
from .Exception import ForbiddenError, NotFoundError
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
            ):
        super().__init__(url, src)
    
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
                'Origin' : 'https://jable.tv',
                'Referer' : 'https://jable.tv/',
                'Priority' : 'u=1, i',
            }
            headers.update(kwargs)
            config.headers.update(headers)
        else:
            logger.error(f'不支持的视频网站: {self.src}')
            raise ValueError(f'不支持的视频网站: {self.src}')
    
    def _set_proxy(self) -> None:
        #TODO
        return
    
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
            logger.info(f"解析页面: \n{html_text[:500]}")
            parser = JabPageParser(html_text)
            package_info_dict = parser.parse()
            return self._init_download_package(package_info_dict)
        else:
            logger.error(f'不支持的视频链接: {self.url}')
    
    def download_video(self):
        package = self.parse()
        downloader = Downloader(package)
        downloader.download()
    
    @staticmethod
    def download_video_with_id(id : str) -> None:
        url = f'https://jable.tv/videos/{id}/'
        crawler = JabVideoCrawler(url)
        crawler.download_video()

    def _validate_src(self):
        return self.src == 'jable.tv' and self.src in self.url