from typing import Dict, Union

from .Crawler import JabVideoCrawler, MissavVideoCrawler

CRAWLERTYPES = Union[
    JabVideoCrawler,
    MissavVideoCrawler
]

CRAWLERS : Dict[str, CRAWLERTYPES] = {
    'jable': JabVideoCrawler,
    'missav': MissavVideoCrawler
}

class AutoCrawler:

    def __init__(self) -> None:
        pass

