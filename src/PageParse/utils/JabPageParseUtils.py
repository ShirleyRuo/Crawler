import re
from typing import Dict, Tuple

from ...utils.EnumType import Page

SRC : Tuple[str] = (
    'jable',
)

jab_pattern : Dict[str, re.Pattern] = {
    "title" : re.compile(r'<title>(.*?)</title>'),
    "actress" : re.compile(r'name\s*=\s*"keywords"\s*content\s*=\s*"(.*?)"'),
    "actress_new" : re.compile(r'data-toggle="tooltip" data-placement="bottom" title="(.*?)"'),
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
    "no_search_result" : re.compile(r'<h5 class="inactive-color">.*?</h5>'),
    "model_id" : re.compile(r'<a class="model" href="(.*?)">'),
    "model_name" : re.compile(r'<span class="placeholder rounded-circle" data-toggle="tooltip" data-placement="bottom" title="(.*?)">'),
    "model_select" : re.compile(r'<div id="list_models_models_list">'),
    "model_select_id" : re.compile(r'<a href="https://jable.tv/models/(.*?)/">'),
    "model_select_name" : re.compile(r'<h6 class="title">(.*?)</h6>'),
    "actress_home" : re.compile(r'<div id="list_videos_common_videos_list">'),
    "actress_id" : re.compile(r'<a class="page-link" href="/models/(.*?)/.*?"'),
    "actress_name" : re.compile(r'<h2 class="h3-md mb-1">(.*?)</h2>'),
    'tag' : re.compile(r'<a class="tag text-light" href="https://jable.tv/tags/(.*)/">(.*)</a>'),
    'tag_title' : re.compile(r'<h2 class="h3-md">(.*)</h2>'),
}

src_tag : Dict[str, Dict[str, re.Pattern]] = {
    'jable' : jab_pattern,
}

src_prefix : Dict[str, str] = {
    'jable' : '<h2 class="h3-md">',
}

def _get_page_type(html_text : str) -> Page:
    '''
    解析页面类型,正则表达式有包含关系,需关注顺序
    '''
    if jab_pattern["actress_home"].search(html_text):
        return Page.ACTRESS_HOME
    if jab_pattern["model_select"].search(html_text):
        return Page.MODEL_SELECT
    if jab_pattern["search_page"].search(html_text):
        return Page.SEARCH_RESULT
    if jab_pattern["videos"].search(html_text):
        return Page.VIDEO_LIST
    if jab_pattern["hls_url"].search(html_text).group(1):
        return Page.SINGLE_VIDEO
    if 'just a moment' in html_text.lower():
        return Page.CAPTACHA
    else:
        return Page.OTHERPAGE