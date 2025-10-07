import os
import sys

import logging
import requests
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from Config import config
from Logger import Logger
from Downloader import JabPageParser, DownloadPackage, Downloader

logger = Logger(config.log_dir).get_logger(__name__, logging.INFO)

class Page(Enum):

    OTHERPAGE = auto()
    CAPTACHA = auto()
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
            url : Optional[str] = None,
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

if __name__ == '__main__':
    url = 'https://jable.tv/videos/ABW-087/'
    crawler = JabVideoCrawler(url = url)
    import m3u8
    from Downloader import DownloadStatus
    # crawler.download_video_with_id('ABW-087')
    package = crawler.parse()
    # package = DownloadPackage(
    #     id = 'ABW-087',
    #     name = 'ABW-087',
    #     actress = 'ABW-087',
    #     hash_tag = ('ABW-087',),
    #     hls_url = 'https://jable.tv/videos/ABW-087/hls/index.m3u8',
    #     cover_url = 'https://jable.tv/videos/ABW-087/cover.jpg',
    #     src = 'jable.tv',
    #     time_length='10:00',
    #     release_date='2021-08-25',
    #     has_chinese=False,
    # )
    loader = Downloader(package)
    decrypt_info = loader._load_tmp(package=package, tmp_file_type='m3u8')
    undownload_segments = loader._get_undownload_ts(
        package = package,
        m3u8_obj = m3u8.loads(decrypt_info),
    )
    dirs = loader._init_dir(package=package)
    for segment in undownload_segments:
        print(segment.uri)
    while len(undownload_segments) != 0:
        loader._redownload(package=package)
        undownload_segments = loader._get_undownload_ts(
            package = package,
            m3u8_obj = m3u8.loads(decrypt_info),
        )
    package.status = DownloadStatus.MERGING
    logger.info("所有ts文件已下载完成")
    loader._merge_ts(package=package, list_file_path=dirs['list_file_path'], m3u8_obj=m3u8.loads(decrypt_info))
    package.status = DownloadStatus.FINISHED
    loader._clear_all_tmp(package=package)
