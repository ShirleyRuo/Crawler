from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Union

from ..utils.EnumType import Page

class PageParserBase(ABC):

    def __init__(
            self, 
            html_text : str
            ) -> None:
        self._html_text = html_text
    
    def parse(self) -> Union[Any, None]:
        _page_type = self._get_page_type()
        if _page_type == Page.SINGLE_VIDEO:
            return self._parse_single_video()
        elif _page_type == Page.VIDEO_LIST:
            return self._parse_video_list()
        elif _page_type == Page.SEARCH_RESULT:
            return self._parse_search_result()
        else:
            return None

    @abstractmethod
    def _get_page_type(self) -> Page:
        raise NotImplementedError
    
    @abstractmethod
    def _parse_id_name_actress(self) -> Tuple[str, str, str]:
        raise NotImplementedError
    
    @abstractmethod
    def _parse_hls_url(self) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def _parse_cover_url(self) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def _parse_hash_tags(self) -> Tuple[str]:
        raise NotImplementedError
    
    @abstractmethod
    def _parse_release_date(self) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def _parse_has_chinese(self) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def _parse_time_length(self) -> str:
        raise NotImplementedError
    
    def _parse_single_video(self) -> Dict:
        id, name, actress = self._parse_id_name_actress()
        hls_url = self._parse_hls_url()
        cover_url = self._parse_cover_url()
        hash_tags = self._parse_hash_tags()
        release_date = self._parse_release_date()
        has_chinese = self._parse_has_chinese()
        time_length = self._parse_time_length()
        return {
            'id': id,
            'name': name,
            'actress': actress,
            'hls_url': hls_url,
            'cover_url': cover_url,
            'hash_tags': hash_tags,
            'release_date': release_date,
            'has_chinese': has_chinese,
            'time_length': time_length
        }
    
    @abstractmethod
    def _parse_video_list(self) -> Tuple[Dict]:
        raise NotImplementedError
    
    @abstractmethod
    def _parse_search_result(self) -> Tuple[Dict]:
        raise NotImplementedError
