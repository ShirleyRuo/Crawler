import os

import json
from typing import Dict, Optional, Union, List

from ...Config.Config import config
from ..utils.JabPageParseUtils import SRC, src_tag, src_prefix

class JabTagParser:

    def __init__(
            self, 
            html_text : str = None,
            src : Optional[str] = None,
            ) -> None:
        self.html_text = html_text
        self.src = src
    
    @staticmethod
    def _tag_filter(standard_tag_mapping : Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        del_tag_titles = []
        for tag_title in standard_tag_mapping.keys():
            if standard_tag_mapping[tag_title] == {}:
                del_tag_titles.append(tag_title)
        for tag_title in del_tag_titles:
            del standard_tag_mapping[tag_title]
        return standard_tag_mapping
    
    @staticmethod
    def _input_tag2_hant(*tags : str) -> Union[List[str], str]:
        from zhconv import convert
        normal_tags = []
        for tag in tags:
            for char in tag:
                if char.isdigit() or char.isalpha():
                    continue
                else:
                    break
            normal_tags.append(convert(tag, 'zh-tw'))
        return normal_tags
    
    def _parse_src(self) -> None:
        if not self.src:
            for src in SRC:
                if src.lower() in self.html_text.lower():
                    self.src = src
                    return
            raise ValueError(f'无法确定来源，请指定来源!支持的来源有{" ".join(SRC)}')
        else:
            if '.' in self.src:
                self.src = self.src.split('.')[0]
            if self.src.lower() not in SRC:
                raise ValueError(f'不支持的来源!支持的来源有{" ".join(SRC)},给定的来源为{self.src}')
    
    def parse(self) -> Dict[str, Dict[str, str]]:
        self._parse_src()
        patterns = src_tag[self.src]
        prefix = src_prefix[self.src]
        blocks = self.html_text.split(prefix)[1:]
        standard_tag_mapping = {}
        for block in blocks:
            block = prefix + block
            if tag_title := patterns['tag_title'].search(block):
                tag_name = tag_title.group(1)
                tag_mapping = {}
                if tags := patterns['tag'].findall(block):
                    for tag in tags:
                        tag_mapping[tag[1]] = tag[0]
                standard_tag_mapping[tag_name] = tag_mapping
        standard_tag_mapping = self._tag_filter(standard_tag_mapping)
        return standard_tag_mapping
    
    def _dump(self, standard_tag_mapping : Dict[str, Dict[str, str]]) -> None:
        filename = 'tag_mapping.json'
        file_path = os.path.abspath(os.path.join(config.assets_dir, filename))
        if not os.path.exists(file_path):
            mapping = {
                self.src : standard_tag_mapping
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=4)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            if self.src in mapping:
                mapping[self.src].update(standard_tag_mapping)
            else:
                mapping[self.src] = standard_tag_mapping
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=4)