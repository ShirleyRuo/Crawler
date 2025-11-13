import time
from typing import Tuple, Dict, Optional, List, Any, Union

from ...Bases.PageParserBase import PageParserBase
from ...Config.Config import config
from ...utils.Logger import Logger
from ...utils.EnumType import Page
from ...utils.DataUnit import VideoPackage
from ..utils.JabPageParseUtils import jab_pattern, _get_page_type

logger = Logger(config.log_dir).get_logger(__name__)

class JabPageParser(PageParserBase):

    def __init__(
            self, 
            html_text : Optional[str] = None,
            videos_per_page : int = 24,
            ) -> None:
        self._html_text = html_text
        self._videos_per_page = videos_per_page

    def _parse_id_name_actress(self) -> Tuple[str, str, str]:
        id, name = self._parse_id_name()
        actress = self._parse_actress()
        return id, name, actress
    
    def _parse_id_name(self) -> Tuple[str, str]:
        if name_str := jab_pattern["title"].search(self._html_text).group(1):
            id = name_str.split()[0]
            name = " ".join(name_str.split()[1:]).split('- Jable.TV')[0].strip()
        else:
            id = "Unknown"
            name = "Unknown"
        return id, name
    
    def _parse_actress(self) -> str:
        if actresses := jab_pattern["actress_new"].findall(self._html_text):
            actress_list = [actress.strip() for actress in actresses]
            actress = ", ".join(actress_list).rstrip()
            return actress
        else:
            return "Unknown"
    
    def _parse_hls_url(self) -> str:
        return jab_pattern["hls_url"].search(self._html_text).group(1)
    
    def _parse_cover_url(self) -> str:
        cover_url = jab_pattern["cover_url"].search(self._html_text).group(1)
        return cover_url

    def _parse_hash_tag(self) -> Tuple[str]:
        hashtags = jab_pattern["hash_tags"].search(self._html_text).group(1)
        return tuple(hashtags.split(',')[:-1])

    def _parse_release_date(self) -> str:
        return "Unknown"

    def _parse_time_length(self) -> str:
        return "Unknown"

    def _parse_has_chinese(self) -> bool:
        chinese_description = jab_pattern["chinese"].search(self._html_text)
        if "中文" not in chinese_description.group(1):
            return False
        return True
    
    def _parse_videos_num(self) -> int:
        if videos := jab_pattern["videos"].search(self._html_text):
            return int(videos.group(1))
        return 0
    
    def _parse_video_list(self) -> List[VideoPackage]:
        videos = []
        prefix = '<span class="label">'
        video_blocks = self._html_text.split(prefix)[1:]
        for block in video_blocks:
            block = prefix + block
            if url_and_name := jab_pattern["url_and_name"].search(block):
                url = url_and_name.group(1)
                name_str = url_and_name.group(2)
                id = name_str.split()[0]
                actress = name_str.split()[-1]
                name = " ".join(name_str.split()[1:-1])
            if time_length := jab_pattern["time_length"].search(block):
                time_length = time_length.group(1)
            if cover_url := jab_pattern["cover_url_via_api"].search(block):
                cover_url = cover_url.group(1)
            videos.append(VideoPackage(
                id=id,
                name=name,
                actress=actress,
                url=url,
                time_length=time_length,
                cover_url=cover_url,
                src="jable"
            ))
        return videos
    
    def _parse_search_result(self) -> Tuple[int, int, Union[List[VideoPackage], None]]:
        '''
        返回搜索结果的总视频数，页数，视频列表
        '''
        if has_search_result := jab_pattern["has_search_result"].search(self._html_text):
            total_videos = int(has_search_result.group(1))
            pages, rest = divmod(total_videos, self._videos_per_page)
            if rest > 0:
                pages += 1
            total_pages = pages
            videos = self._parse_video_list()
            return total_videos, total_pages, videos
        elif jab_pattern["no_search_result"].search(self._html_text):
            total_videos = 0
            total_pages = 0
            videos = None
            return total_videos, total_pages, videos
        else:
            logger.error("未知页面类型")
            raise ValueError("未知页面类型")
    
    def _get_page_type(self) -> Page | None:
        return _get_page_type(self._html_text)