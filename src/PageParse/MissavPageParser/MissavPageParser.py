import re
import time
import requests
from typing import Tuple, Dict, Optional, List, Any, Union

from ...Config.Config import config
from ...utils.Logger import Logger
from ...utils.EnumType import Page
from ...utils.DataUnit import VideoPackage
from ..utils.MissavPageParseUtils import missav_parttern

logger = Logger(config.log_dir).get_logger(__name__)

class MissavPageParser:

    def __init__(self, html_text : str) -> None:
        self._html_text = html_text
    
    def _get_uuid(self) -> str:
        if uuid_match := missav_parttern['uuid'].search(self._html_text):
            return uuid_match.group(1)
        else:
            return " "
    
    @staticmethod
    def validation(url : str) -> str:
        '''
        使用seleniumwire获取网页源代码并获取User-Agent同步到config.headers
        '''
        try:
            from selenium import webdriver
            from selenium.webdriver import ChromeOptions
            options = ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument(f'user-agent={config.headers["User-Agent"]}')
            options.add_argument('--incognito')
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.get(url=url)
            time.sleep(20)
            html_text = driver.page_source
            config.cookie = driver.get_cookies()
            driver.quit()
            return html_text
        except Exception as e:
            logger.error(f'请安装Chrome浏览器并配置环境变量,{e}')
            return ""

    def _fetch_playlist(self) -> str:
        uuid = self._get_uuid()
        if not uuid:
            logger.error('无法获取uuid')
            raise ValueError('无法获取uuid')
        playlist_url = f'https://surrit.com/{uuid}/playlist.m3u8'
        return playlist_url
    
    def _parse_video_info(self, playlist_info : str) -> Union[List[Tuple[str, str, str]], None]:
        if not playlist_info:
            logger.error('无法获取播放列表信息')
            return None
        resolution_info = []
        for match_ in missav_parttern['playlist'].finditer(playlist_info):
            bandwith = match_.group(1)
            resolution = match_.group(2)
            m3u8_url_end = match_.group(3)
            m3u8_url_end = f'https://surrit.com/{self._get_uuid()}/{m3u8_url_end}'
            resolution_info.append((bandwith, resolution, m3u8_url_end))
        resolution_info.sort(key=lambda x: int(x[0]), reverse=True)
        return resolution_info
    
    def _parse_id_name_actress(self) -> Tuple[str, str, str]:
        if name_str_match := missav_parttern['id_name_actress'].search(self._html_text):
            name_str = name_str_match.group(1)
            id = name_str.split()[0]
            actress = name_str.split()[-1]
            name = ' '.join(name_str.split()[1:-1]).split("：MGS")[0]
            return id, name, actress
        else:
            logger.warning('无法获取视频名称')
            return "Unknown", "Unknown", "Unknown"
    
    def _parse_actress_name(self) -> str:
        pass
    
    def _parse_cover_url(self) -> str:
        if cover_url_match := missav_parttern['cover_url'].search(self._html_text):
            return cover_url_match.group(1)
    
    def _parse_hash_tag(self) -> Tuple[str]:
        if hash_tag_match := missav_parttern['hash_tags'].search(self._html_text):
            return tuple(hash_tag_match.group(1).split(',')[1:-1])
    
    def _parse_time_length(self) -> str:
        return "Unknown"
    
    def _parse_release_date(self) -> str:
        return "Unknown"
    
    def _parse_has_chinese(self) -> bool:
        return False
    
    def _parse_hls_url(self) -> str:
        playlist_url = self._fetch_playlist()
        id, _, __ = self._parse_id_name_actress()
        headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Origin' : 'https://missav.live',
            'Referer' : f"https://missav.live/{id.strip().lower()}"
        }
        response = requests.get(playlist_url, headers=headers)
        if response.status_code != 200:
            logger.error(f'无法获取播放列表信息，状态码：{response.status_code}')
        else:
            playlist_info = response.text
            return self._parse_video_info(playlist_info)[0][-1]
    
    def _parse_single_video(self) -> Dict:
        id, name, actress = self._parse_id_name_actress()
        cover_url = self._parse_cover_url()
        hls_url = self._parse_hls_url()
        time_length = self._parse_time_length()
        release_date = self._parse_release_date()
        has_chinese = self._parse_has_chinese()
        hash_tags = self._parse_hash_tag()
        return {
            "id" : id,
            "name" : name,
            "actress" : actress,
            "cover_url" : cover_url,
            "hls_url" : hls_url,
            "time_length" : time_length,
            "hash_tags" : hash_tags,
            "release_date" : release_date,
            "has_chinese" : has_chinese,
        }
    
    def parse(self) -> Any:
        return self._parse_single_video()