import time
import requests
from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from ..utils.EnumType import Page
from ..utils.Logger import Logger
from ..Config.Config import config
from ..Error.Exception import NotFoundError, ForbiddenError
from ..PageParse.utils.PageValidation import validation
from ..utils.DataUnit import DownloadPackage
from ..Downloader import Downloader

logger = Logger(config.log_dir).get_logger(__name__)

class VideoCrawlerBase(ABC):

    def __init__(
            self, 
            url : str,
            src : str,
            ) -> None:
        self.url = url
        self.src = src
    
    @abstractmethod
    def _get_headers(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _set_proxy(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _parse_page_content(self) -> Any:
        raise NotImplementedError
    
    @abstractmethod
    def parse(self) -> DownloadPackage:
        raise NotImplementedError
    
    @abstractmethod
    def _validate_src(self) -> bool:
        raise NotImplementedError
    
    def _init_download_package(self, package_info_dict : Dict) -> DownloadPackage:
        package = DownloadPackage(
            id = package_info_dict['id'],
            name = package_info_dict['name'],
            actress = package_info_dict['actress'],
            hash_tag = package_info_dict['hash_tags'],
            hls_url = package_info_dict['hls_url'],
            cover_url = package_info_dict['cover_url'],
            src = self.src,
            time_length=package_info_dict['time_length'],
            release_date=package_info_dict['release_date'],
            has_chinese=package_info_dict['has_chinese'],
        )
        return package
    
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
                        if html_text := validation(self.url):
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
                if 'ConnectionResetError(10054' in str(e):
                    if html_text := validation(self.url):
                        logger.info(f'验证成功,继续请求...')
                        cookies_list = [f"{cookies['name']}={cookies['value']}" for cookies in config.cookie]
                        config.headers.update({'Cookie': '; '.join(cookies_list)})
                        config.save_headers()
                        return html_text
                    else:
                        logger.error('验证失败,继续重试...')
            wait_time = config.retry_wait_time * (2 ** retry_count + 1)
            logger.info(f'等待 {wait_time} 秒后重试...')
            time.sleep(wait_time)
        logger.error(f'请求视频页面失败: 超过最大重试次数')
        if NotFound_count >= config.max_retries:
            raise NotFoundError(f'请求视频页面不存在: {response.status_code}')
        raise Exception(f'请求视频页面失败: 超过最大重试次数')
    
    def download_video(self) -> None:
        package = self.parse()
        downloader = Downloader(package)
        downloader.download()