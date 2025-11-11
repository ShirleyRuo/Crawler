import re
from typing import Dict, Tuple

from ...utils.EnumType import Page

missav_parttern : Dict[str, re.Pattern] = {
    'uuid' : re.compile(r'urls:\s*\["https:\\/\\/.*?.com\\/([a-z0-9-]+)'),
    'playlist' : re.compile(r'#EXT-X-STREAM-INF:BANDWIDTH=(\d+).*?RESOLUTION=(\d+x\d+)\s*\n*\s*?(\d+p/video.m3u8)'),
    'id_name_actress' : re.compile(r'<meta property="og:title" content="(.*?)"\s*'),
    'actress_name' : re.compile(r''),
    'cover_url' : re.compile(r'<meta property="og:image" content="(.*?)"\s*'),
    'hash_tags' : re.compile(r'<meta name="keywords" content="(.*?)"\s*'),
}