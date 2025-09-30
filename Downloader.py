
import os

import asyncio
import requests
import m3u8
import logging
from enum import Enum
from Crypto.Cipher import AES
from dataclasses import dataclass
from typing import List, Optional, Callable, Any, Union, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
    )
logger = logging.getLogger(__name__)

class DownloadStatus(Enum):

    PENDING = 1
    DOWNLOADING = 2
    PAUSED = 3
    DECRYPTING = 4
    MERGING = 5
    FINISHED = 6
    FAILED = 7

class DownloadType(Enum):

    ASYNC = 1
    THREADED = 2

class DecrptyType(Enum):
    AES = 1

@dataclass
class DownloadPackage:
    id : str
    name : str
    actress : str
    hash_tag : Tuple[str]
    hls_url : str
    cover_url : str
    src : str = 'Unknown'
    has_chinese : bool = False
    release_date : str = None
    time_length : str = None
    save_path : str = None

class Decrypter:

    def __init__(
            self,
            file_obj : bytes,
            decrpty_type : DecrptyType,
            *,
            key : Optional[bytes] = None,
            iv : Optional[str] = None,
            tmp_file_path : Optional[str] = None,
            **kwargs : Any
            ) -> None:
        self._file_obj = file_obj
        self._decrypty_type = decrpty_type
        self.key = key
        self.iv = iv
        self.tmp_file_path = tmp_file_path
        self._kwargs = kwargs
        self.__file_size = len(file_obj)
    
    def decrypt(self) -> bytes:
        if self._decrypty_type == DecrptyType.AES:
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            decrypted_data = cipher.decrypt(self._file_obj)
            return decrypted_data
        else:
            raise ValueError("不支持的解密类型")
    
    @property
    def key(self) -> bytes:
        return self._key
    
    @key.setter
    def key(self, value : bytes) -> None:
        if not value and not self.tmp_file_path:
            raise ValueError("请给出key或文件地址")
        if value:
            self._key = value
        if self.tmp_file_path:
            with open(self.tmp_file_path, 'rb') as f:
                self._key = f.read()
    
    @property
    def iv(self) -> str:
        return self._iv
    
    @iv.setter
    def iv(self, value : str) -> None:
        if not value and not self.tmp_file_path:
            raise ValueError("请给出iv或文件地址")
        if value:
            self._iv = value
        if self.tmp_file_path:
            with open(self.tmp_file_path, 'rb') as f:
                self._iv = f.read()


class Downloader:
    '''
    m3u8下载器
    '''
    def __init__(
            self,
            packages : Union[DownloadPackage, List[DownloadPackage]],
            download_type : DownloadType,
            *,
            concurrency : Optional[int] = 5,
            max_retries : Optional[int] = 3,
            output_dir : Optional[str] = None,
            tmp_dir : Optional[str] = None,
            **kwargs : Any
            ) -> None:
        self._packages = packages if isinstance(packages, list) else [packages]
        self._concurrency = concurrency
        self._max_retries = max_retries
        self._output_dir = output_dir
        self._tmp_dir = tmp_dir
        self._download_type = download_type
        self._kwargs = kwargs
    
    def _pre_process(self) -> None:
        '''
        下载包中的m3u8文件进行预处理
        '''
        pass

    
    def _dump_key_iv(self, key : bytes, iv : str) -> None:
        if not os.path.exists(self._tmp_dir):
            os.makedirs(self._tmp_dir)
    
    def single_downloader(self) -> None:
        pass

    async def async_downloader(self) -> None:
        pass

    def threaded_downloader(self) -> None:
        pass

if __name__ == '__main__':
    import signal
    import sys

    def signal_handler(sig, frame):
        print('\n收到终止信号，执行清理操作...')
        # 清理代码
        sys.exit(0)

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # 终止信号

    print("程序运行中，按 Ctrl+C 退出...")
    while True:
        # 你的主循环
        pass
