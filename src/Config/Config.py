import json
from pathlib import Path

class Config:

    def __init__(
            self,
            download_dir: str,
            tmp_dir: str,
            log_dir: str,
            assets_dir : str,
            config_dir : str,
            **kwargs
            ) -> None:

        self.download_dir = Path(download_dir).absolute().resolve()
        self.log_dir = Path(log_dir).absolute().resolve()
        self.tmp_dir = Path(tmp_dir).absolute().resolve()
        self.assets_dir = Path(assets_dir).absolute().resolve()
        self.config_dir = Path(config_dir).absolute().resolve()

        self.tmp_m3u8_dir = self.tmp_dir / 'm3u8'
        self.tmp_key_dir = self.tmp_dir / 'key'
        self.tmp_iv_dir = self.tmp_dir / 'iv'
        self.tmp_ts_dir = self.tmp_dir / 'ts'

        self.tmp_subdirs = {
            'tmp_m3u8_dir' : 'm3u8',
            'tmp_key_dir' : 'key',
            'tmp_iv_dir' : 'iv',
            'tmp_ts_dir' : 'ts',
        }

        self.download_subdirs = {
            'video_dir' : 'video',
            'cover_dir' : 'cover',
        }

        for dir_name, sub_dir in self.tmp_subdirs.items():
            dir_path : Path = self.tmp_dir / sub_dir
            setattr(self, dir_name, dir_path)
        for dir_name, sub_dir in self.download_subdirs.items():
            dir_path : Path = self.download_dir / sub_dir
            setattr(self, dir_name, dir_path)
        self._create_dir()

        self.max_concurrency = 2
        self.max_ts_concurrency = 5
        self.max_retries = 3
        self.retry_wait_time = 5
        self.headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        }
        self.proxies = {
            'http' : 'http://127.0.0.1:10809',
        }
        self.cookie = ''

    def _create_dir(self) -> None:
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        for dir_name in self.tmp_subdirs.keys():
            dir_path : Path = getattr(self, dir_name)
            dir_path.mkdir(parents=True, exist_ok=True)
        for dir_name in self.download_subdirs.keys():
            dir_path : Path = getattr(self, dir_name)
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_headers(self) -> None:
        with open(self.config_dir / 'headers.json', 'w', encoding='utf-8') as f:
            json.dump(self.headers, f, ensure_ascii=False, indent=4)

    def load_headers(self) -> None:
        with open(self.config_dir / 'headers.json', 'r', encoding='utf-8') as f:
            self.headers = json.load(f)

    def disable_proxies(self) -> None:
        self.proxies = {'http' : None}

config = Config(
    download_dir = r'./downloads',
    tmp_dir = r'./tmp',
    log_dir = r'./logs',
    assets_dir = r'./assets',
    config_dir = r'./conf',
    )