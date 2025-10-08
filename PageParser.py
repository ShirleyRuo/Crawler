import re
from typing import Tuple

class JabPageParser:

    def __init__(self, html_text : str) -> None:
        self._html_text = html_text
    
    def parse_id_name_actress(self) -> Tuple[str, str, str]:
        name_str = re.search(r'<title>(.*?)</title>', self._html_text).group(1)
        id = name_str.split()[0]

        name_and_actress = name_str.split('- Jable.TV')[0]

        actress = re.search(r'name\s*=\s*"keywords"\s*content\s*=\s*"(.*?)"', self._html_text).group(1).split(',')[-1].strip()
        actress_ = name_and_actress.split()[-1]

        if actress == actress_:
            name = " ".join(name_and_actress.split()[1:-1]).strip()
        else:
            name = " ".join(name_and_actress.split()[1:]).strip()
        return id, name, actress
    
    def parse_hls_url(self) -> str:
        return re.search(r"hlsUrl\s*=\s*'(https?://.*?\.m3u8)'", self._html_text).group(1)
    
    def parse_cover_url(self) -> str:
        cover_url = re.search(r'"og:image"\s*content\s*=\s*"(.*?)"', self._html_text).group(1)
        return cover_url

    def parse_hash_tag(self) -> Tuple[str]:
        hashtags = re.search(r'name\s*=\s*"keywords"\s*content\s*=\s*"(.*?)"', self._html_text).group(1)
        return tuple(hashtags.split(',')[:-1])

    def parse_release_date(self) -> str:
        return "Unknown"

    def parse_time_length(self) -> str:
        return "Unknown"

    def parse_has_chinese(self) -> bool:
        chinese_description = re.search(r'name\s*=\s*"description"\s*content\s*=\s*"(.*?)"', self._html_text)
        if "中文" not in chinese_description.group(1):
            return False
        return True