import os

import re
import json
from collections import namedtuple
from typing import List

from ...Config.Config import config
from ...utils.Logger import Logger
from ...utils.EnumType import Page
from ..utils.JabPageParseUtils import _get_page_type, jab_pattern

logger = Logger(config.log_dir).get_logger(__name__)

ActessInfo = namedtuple('ActressInfo', ['actress_id', 'actress_name'], defaults=["", ""])

class JabActressId:

    def __init__(
            self, 
            html_text : str,
            actress_info : List[ActessInfo] = None
            ) -> None:
        self._page_type = _get_page_type(html_text=html_text)
        self.html_text = html_text
        self.actress_info = actress_info
        self._file_path = os.path.join(config.assets_dir, 'actress_id.json')
        os.makedirs(config.assets_dir, exist_ok=True)

    def _parse(self) -> None:
        if self._page_type == Page.SINGLE_VIDEO:
            if model_match := jab_pattern['model_id'].search(self._html_text):
                _actress_id = model_match.group(1).split('/')[-2]
            if actress_name_match := jab_pattern['model_name'].search(self._html_text):
                _actress_name = actress_name_match.group(1)
            self.actress_info = [ActessInfo(_actress_id, _actress_name)]
            return
        if self._page_type == Page.ACTRESS_HOME:
            if actress_id_match := jab_pattern['actress_id'].search(self._html_text):
                _actress_id = actress_id_match.group(1)
            if actress_name_match := jab_pattern['actress_name'].search(self._html_text):
                _actress_name = actress_name_match.group(1)
            self.actress_info = [ActessInfo(_actress_id, _actress_name)]
            return
        if self._page_type == Page.MODEL_SELECT:
            self.actress_info = []
            prefix = '<div class="horizontal-img-box ml-3 mb-3">'
            model_blocks = self._html_text.split(prefix)[1:]
            for block in model_blocks:
                if id_match := jab_pattern["model_select_id"].search(block):
                    _actress_id = id_match.group(1)
                if name_match := re.search(r'<h6 class="title">(.*?)</h6>', block):
                    _actress_name = name_match.group(1)
                self.actress_info.append(ActessInfo(_actress_id, _actress_name))
            return
        logger.error(f"无效的页面,无法解析出演员id.")
        raise ValueError("无效的页面,无法解析出演员id.")

    def _dump(self) -> None:
        self._parse()
        if os.path.exists(self._file_path):
            _old_actress_info = self.load()
            id_list = [i.actress_id for i in self.actress_info]
            for _actress_info in _old_actress_info:
                if _actress_info.actress_id in id_list:
                    continue
                else:
                    self.actress_info.append(_actress_info)
            with open(self._file_path, 'w', encoding = 'utf-8') as f:
                json.dump(self.actress_info, f, ensure_ascii=False, indent=4)
            return
        with open(self._file_path, 'w', encoding = 'utf-8') as f:
            json.dump(self.actress_info, f, ensure_ascii=False, indent=4)
    
    def load(self) -> List[ActessInfo]:
        _load_list = []
        with open(self._file_path, 'r', encoding = 'utf-8') as f:
            actress_info_list = json.load(f)
        for actress_info in actress_info_list:
            if not isinstance(actress_info, list) or len(actress_info) != 2:
                logger.error(f"actress_info 格式错误, {actress_info}")
                raise ValueError("actress_info 格式错误")
            else:
                _load_list.append(ActessInfo(actress_info[0], actress_info[1]))
        return _load_list
    
    @property
    def html_text(self) -> str:
        return self._html_text

    @html_text.setter
    def html_text(self, value: str) -> None:
        if not (self._page_type == Page.SINGLE_VIDEO 
                or self._page_type == Page.ACTRESS_HOME 
                or self._page_type == Page.MODEL_SELECT):
            logger.error(f"无效的页面,无法解析出演员id.")
            raise ValueError("无效的页面,无法解析出演员id.")
        self._html_text = value