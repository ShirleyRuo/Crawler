import re
import time
from typing import Tuple, Dict, Optional

from ..Config import config
from ..Logger import Logger

logger = Logger(config.log_dir).get_logger(__name__)

jab_pattern : Dict[str, re.Pattern] = {
    "title" : re.compile(r'<title>(.*?)</title>'),
    "actress" : re.compile(r'name\s*=\s*"keywords"\s*content\s*=\s*"(.*?)"'),
    "hls_url" : re.compile(r"hlsUrl\s*=\s*'(https?://.*?\.m3u8)'"),
    "cover_url" : re.compile(r'"og:image"\s*content\s*=\s*"(.*?)"'),
    "hash_tags" : re.compile(r'name\s*=\s*"keywords"\s*content\s*=\s*"(.*?)"'),
    "chinese" : re.compile(r'name\s*=\s*"description"\s*content\s*=\s*"(.*?)"')
}

class JabPageParser:

    def __init__(
            self, 
            html_text : Optional[str] = None
            ) -> None:
        self._html_text = html_text
    
    @staticmethod
    def validation(url : str) -> str:
        try:
            from selenium import webdriver
            driver = webdriver.Chrome()
            driver.get(url=url)
            time.sleep(10)
            html_text = driver.page_source
            config.cookie = driver.get_cookies()
            driver.quit()
            return html_text
        except:
            logger.error('请安装Chrome浏览器并配置环境变量')
            return ""
    
    def parse_id_name_actress(self) -> Tuple[str, str, str]:
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
    
    def parse_hls_url(self) -> str:
        return jab_pattern["hls_url"].search(self._html_text).group(1)
    
    def parse_cover_url(self) -> str:
        cover_url = jab_pattern["cover_url"].search(self._html_text).group(1)
        return cover_url

    def parse_hash_tag(self) -> Tuple[str]:
        hashtags = jab_pattern["hash_tags"].search(self._html_text).group(1)
        return tuple(hashtags.split(',')[:-1])

    def parse_release_date(self) -> str:
        return "Unknown"

    def parse_time_length(self) -> str:
        return "Unknown"

    def parse_has_chinese(self) -> bool:
        chinese_description = jab_pattern["chinese"].search(self._html_text)
        if "中文" not in chinese_description.group(1):
            return False
        return True
    
    def parse(self) -> Dict:
        id, name, actress = self.parse_id_name_actress()
        hls_url = self.parse_hls_url()
        cover_url = self.parse_cover_url()
        hash_tags = self.parse_hash_tag()
        release_date = self.parse_release_date()
        time_length = self.parse_time_length()
        has_chinese = self.parse_has_chinese()
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