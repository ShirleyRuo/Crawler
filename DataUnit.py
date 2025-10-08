from dataclasses import dataclass
from typing import Tuple

from EnumType import DownloadStatus

@dataclass
class DownloadPackage:
    id : str
    name : str
    actress : str
    hash_tag : Tuple[str]
    hls_url : str
    cover_url : str
    src : str = 'Unknown'
    status : DownloadStatus = DownloadStatus.PENDING
    has_chinese : bool = False
    release_date : str = None
    time_length : str = None

    def __hash__(self):
        string = f"{self.id}{self.name}{self.actress}{self.hls_url}{self.cover_url}{self.src}"
        return hash(string)
    
    def __eq__(self, other):
        if not isinstance(other, DownloadPackage):
            return False
        return hash(self) == hash(other)

    def __post_init__(self) -> None:
        self.base_url = self.hls_url.rsplit('/', 1)[0] + '/'
    
    def update(self, hls_url : str = None) -> None:
        if hls_url:
            self.hls_url = hls_url
            self.base_url = self.hls_url.rsplit('/', 1)[0] + '/'

@dataclass
class InfoPackage:
    id : str
    name : str
    actress : str
    hash_tag : Tuple[str]
    has_chinese : bool
    release_date : str
    time_length : str
    src : str
