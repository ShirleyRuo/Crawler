import os
import sys

import logging
import requests
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Dict, Any

from Config import config
from Logger import Logger
from Downloader import JabPageParser, DownloadPackage, Downloader

logger = Logger(config.log_dir).get_logger(__name__, logging.INFO)

class Page(Enum):

    SINGLE_VIDEO = auto()
    WEBSITE_HOME = auto()
    ACTRESS_HOME = auto()
    VIDEO_LIST = auto()

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
            url : str,
            src : str = 'jable.tv',
            ):
        super().__init__(url, src)
    
    def _get_headers(self) -> None:
        if self._validate_src():
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Origin' : 'https://jable.tv',
                'Referer' : 'https://jable.tv/',
                'Priority' : 'u=1, i',
            }
            config.headers.update(headers)
        else:
            logger.error(f'不支持的视频网站: {self.src}')
            sys.exit(1)
    
    def _set_proxy(self) -> None:
        #TODO
        return
    
    def _get_html_text(self) -> str:
        self._get_headers()
        self._set_proxy()
        try:
            response = requests.get(self.url, headers=config.headers, proxies=config.proxies, timeout=10)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                logger.error(f'请求视频页面被禁止: {response.status_code}')
                sys.exit(1)
            else:
                logger.error(f'请求视频页面失败: {response.status_code}')
        except requests.exceptions.RequestException as e:
            logger.error(f'请求视频页面失败: {e}')
            sys.exit(1)
    
    def _parse_page_content(self) -> Page:
        if 'videos' in self.url:
            return Page.SINGLE_VIDEO
        else:
            logger.error(f'不支持的视频链接: {self.url}')
            sys.exit(1)

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
        page = self._parse_page_content()
        if page == Page.SINGLE_VIDEO:
            html_text = self._get_html_text()
            print(html_text[:500])
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

if __name__ == '__main__':
    url = "https://jable.tv/videos/abp-933/"
    crawler = JabVideoCrawler(url)
    package = crawler.parse()
    package.hls_url = 'https://jable.tv/videos/abp-933/hls/index.m3u8'
    downloader = Downloader(package)
    downloader._redownload(package=package)
