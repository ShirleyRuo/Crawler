from enum import Enum, auto

class DownloadStatus(Enum):

    PENDING = 1
    DOWNLOADING = 2
    PAUSED = 3
    MERGING = 4
    FINISHED = 5
    FAILED = 6

class DecrptyType(Enum):
    AES = 1

class Page(Enum):

    OTHERPAGE = auto()
    CAPTACHA = auto()
    SINGLE_VIDEO = auto()
    WEBSITE_HOME = auto()
    ACTRESS_HOME = auto()
    MODEL_SELECT = auto()
    VIDEO_LIST = auto()
    SEARCH_RESULT = auto()