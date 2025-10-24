import re
import time
from typing import Tuple, Dict, Optional, List, Any, Union

from ..Config import config
from ..Logger import Logger

from ..EnumType import Page
from ..DataUnit import VideoPackage

logger = Logger(config.log_dir).get_logger(__name__)

jab_pattern : Dict[str, re.Pattern] = {
    "title" : re.compile(r'<title>(.*?)</title>'),
    "actress" : re.compile(r'name\s*=\s*"keywords"\s*content\s*=\s*"(.*?)"'),
    "hls_url" : re.compile(r"hlsUrl\s*=\s*'(https?://.*?\.m3u8)'"),
    "cover_url" : re.compile(r'"og:image"\s*content\s*=\s*"(.*?)"'),
    "hash_tags" : re.compile(r'name\s*=\s*"keywords"\s*content\s*=\s*"(.*?)"'),
    "chinese" : re.compile(r'name\s*=\s*"description"\s*content\s*=\s*"(.*?)"'),
    "videos" : re.compile(r'<span\s*class\s*=\s*"inactive-color fs-2 mb-0">(\d+).*?</span>'),
    "time_length" : re.compile(r'<span\s*class\s*=\s*"label">(.*?)</span>'),
    "url_and_name" : re.compile(r'<h6 class="title"><a\s*href\s*=\s*"(.*?)">\s*(.*?)\s*</a>'),
    "cover_url_via_api" : re.compile(r'data-src\s*=\s*"(.*?)"'),
    "search_page" : re.compile(r'<div\s*id="list_videos_videos_list_search_result">'),
    "has_search_result" : re.compile(r'<span class="inactive-color fs-2 mb-0">(\d+).*?</span>'),
    "no_search_result" : re.compile(r'<h5 class="inactive-color">.*?</h5>')
}

class JabPageParser:

    def __init__(
            self, 
            html_text : Optional[str] = None,
            videos_per_page : int = 24,
            ) -> None:
        self._html_text = html_text
        self._videos_per_page = videos_per_page
    
    @staticmethod
    def validation(url : str) -> str:
        '''
        使用seleniumwire获取网页源代码并获取User-Agent同步到config.headers
        '''
        try:
            from seleniumwire import webdriver
            driver = webdriver.Chrome()
            driver.get(url=url)
            time.sleep(10)
            for request in driver.requests:
                if request.response:
                    config.headers['User-Agent'] = request.headers.get('User-Agent')
                    break
            html_text = driver.page_source
            config.cookie = driver.get_cookies()
            driver.quit()
            return html_text
        except:
            logger.error('请安装Chrome浏览器并配置环境变量')
            return ""
    
    def _get_page_type(self) -> Page:
        if jab_pattern["search_page"].search(self._html_text):
            return Page.SEARCH_RESULT
        if jab_pattern["videos"].search(self._html_text):
            return Page.VIDEO_LIST
        if jab_pattern["hls_url"].search(self._html_text).group(1):
            return Page.SINGLE_VIDEO
        if 'just a moment' in self._html_text.lower():
            return Page.CAPTACHA
        else:
            return Page.OTHERPAGE

    def _parse_id_name_actress(self) -> Tuple[str, str, str]:
        name_str = jab_pattern["title"].search(self._html_text).group(1)
        id = name_str.split()[0]

        name_and_actress = name_str.split('- Jable.TV')[0]

        actress = jab_pattern["actress"].search(self._html_text).group(1).split(',')[-1].strip()
        actress_ = name_and_actress.split()[-1]

        if actress == actress_:
            name = " ".join(name_and_actress.split()[1:-1]).strip()
        else:
            name = " ".join(name_and_actress.split()[1:]).strip()
        return id, name, actress
    
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

    def _parse_single_video(self) -> Dict:
        id, name, actress = self._parse_id_name_actress()
        hls_url = self._parse_hls_url()
        cover_url = self._parse_cover_url()
        hash_tags = self._parse_hash_tag()
        release_date = self._parse_release_date()
        time_length = self._parse_time_length()
        has_chinese = self._parse_has_chinese()
        return {
            "id" : id,
            "name" : name,
            "actress" : actress,
            "hls_url" : hls_url,
            "cover_url" : cover_url,
            "hash_tag" : hash_tags,
            "release_date" : release_date,
            "time_length" : time_length,
            "has_chinese" : has_chinese
        }
    
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
    
    def parse(self) -> Any:
        _page_type = self._get_page_type()
        if _page_type == Page.VIDEO_LIST:
            return self._parse_video_list()
        elif _page_type == Page.SINGLE_VIDEO:
            return self._parse_single_video()
        elif _page_type == Page.SEARCH_RESULT:
            return self._parse_search_result()
        else:
            return None
