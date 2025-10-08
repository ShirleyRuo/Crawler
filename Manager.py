import os
import sys

from pathlib import Path

from Config import config
from DataUnit import DownloadPackage

class VideoManager:

    def __init__(self) -> None:
        pass

    
    def _dump_downloaded(
            self, 
            package : DownloadPackage,
            video_path : Path,
            cover_path : Path
            ) -> None:
        pass