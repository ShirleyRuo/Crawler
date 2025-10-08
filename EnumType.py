from enum import Enum, auto

class DownloadStatus(Enum):

    PENDING = 1
    DOWNLOADING = 2
    PAUSED = 3
    DECRYPTING = 4
    MERGING = 5
    FINISHED = 6
    FAILED = 7

class DecrptyType(Enum):
    AES = 1

class Page(Enum):

    OTHERPAGE = auto()
    CAPTACHA = auto()
    SINGLE_VIDEO = auto()
    WEBSITE_HOME = auto()
    ACTRESS_HOME = auto()
    VIDEO_LIST = auto()