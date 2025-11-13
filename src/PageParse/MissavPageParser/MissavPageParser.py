import requests
from typing import Tuple, List, Union, Dict

from ...Bases.PageParserBase import PageParserBase
from ...Config.Config import config
from ...utils.Logger import Logger
from ...utils.EnumType import Page
from ..utils.MissavPageParseUtils import missav_parttern, _get_page_type

logger = Logger(config.log_dir).get_logger(__name__)

class MissavPageParser(PageParserBase):

    def __init__(self, html_text : str) -> None:
        self._html_text = html_text
    
    def _get_uuid(self) -> str:
        if uuid_match := missav_parttern['uuid'].search(self._html_text):
            return uuid_match.group(1)
        else:
            return " "

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
    
    def _parse_search_result(self):
        pass

    def _parse_video_list(self) -> Tuple[Dict]:
        pass
    
    def _parse_cover_url(self) -> str:
        if cover_url_match := missav_parttern['cover_url'].search(self._html_text):
            return cover_url_match.group(1)
    
    def _parse_hash_tags(self) -> Tuple[str]:
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
    
    def _get_page_type(self) -> Page | None:
        return _get_page_type(self._html_text)