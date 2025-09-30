import os
from pathlib import Path

class Config:

    def __init__(
            self,
            download_dir: str,
            tmp_dir: str,
            ) -> None:
        self.download_dir = Path(download_dir).absolute().resolve()
        self.tmp_dir = Path(tmp_dir).absolute().resolve()
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        self.max_concurrency = 5
        self.max_retries = 3
        self.retry_wait_time = 5

config = Config(
    download_dir = r'./downloads',
    tmp_dir = r'./tmp'
)