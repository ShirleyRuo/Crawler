from dataclasses import dataclass, field
from typing import Tuple

from .EnumType import DownloadStatus

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

    def __hash__(self):
        string = f"{self.id}{self.name}{self.actress}{self.has_chinese}{self.release_date}{self.time_length}{self.src}"
        return hash(string)
    
    def __eq__(self, other):
        if not isinstance(other, InfoPackage):
            return False
        return hash(self) == hash(other)

@dataclass
class VideoPackage:
    '''
    储存视频信息的类,其中影片名称以及演员名称仅作参考,可能由于参演人数多于1出现误差.
    '''
    id : str = ''
    name : str = ''
    actress : str = ''
    url : str = ''
    cover_url : str = ''
    time_length : str = ''
    src : str = ''

    def __hash__(self):
        string = f"{self.id}{self.name}{self.actress}{self.cover_url}{self.url}{self.time_length}{self.src}"
        return hash(string)
    
    def __eq__(self, other):
        if not isinstance(other, VideoPackage):
            return False
        return hash(self) == hash(other)

@dataclass
class Parameters:
    '''
    网络下载时的参数集合
    '''
    mode : str = 'async'
    function : str = 'get_block'
    block_id : str = ''
    from_ : int = 0
    sort_by : str = ''
    _ : int = 0
