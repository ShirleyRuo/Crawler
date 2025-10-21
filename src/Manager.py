import os
import sys

import json
from pathlib import Path
from typing import List, Dict, Optional

from .Config import config
from .Logger import Logger
from .DataUnit import DownloadPackage, InfoPackage

logger = Logger(config.log_dir).get_logger(__name__)

class DownloadInfoManager:

    def __init__(
            self,
            download_info_file : Path,
            ) -> None:
        self.download_info_file = download_info_file
    
    def _load_download_info(self) -> List[InfoPackage]:
        '''
        加载下载信息文件,并返回下载视频信息的列表

        Returns:
            List[InfoPackage]: 下载视频信息的列表
        '''
        if not self.download_info_file.exists():
            logger.error(f"下载信息文件不存在: {self.download_info_file}")
            raise FileNotFoundError(f"下载信息文件不存在: {self.download_info_file}")
        infos = []
        with open(self.download_info_file, 'r', encoding='utf-8') as f:
            download_info : Dict = json.load(f)
        for id, list_ in download_info.items():
            infos.append(InfoPackage(
                id=id,
                name=list_[-1]['name'],
                actress=list_[-1]['actress'],
                hash_tag=tuple(list_[-1]['hash_tag']),
                has_chinese=list_[-1]['has_chinese'],
                release_date=list_[-1]['release_date'],
                time_length=list_[-1]['time_length'],
                src=list_[-1]['src'],
            ))
        return infos
    
    def _save_download_info(self, package : DownloadPackage) -> None:
        '''
        保存下载信息到文件
        Args:
            package(DownloadPackage): 下载包信息

        Returns:
            None
        '''
        package_data = {
            'name' : package.name,
            'actress' : package.actress,
            'hash_tag' : package.hash_tag,
            'hls_url' : package.hls_url,
            'cover_url' : package.cover_url,
            'src' : package.src,
            'status' : package.status.name,
            'has_chinese' : package.has_chinese,
            'release_date' : package.release_date,
            'time_length' : package.time_length,
        }
        dump_data = {package.id.lower() : [package_data]}
        if self.download_info_file.exists():
            with open(self.download_info_file, 'r', encoding='utf-8') as f:
                origin_data : Dict[str, List[Dict]] = json.load(f)
            if package.id.lower() in origin_data:
                origin_data[package.id.lower()].append(package_data)
            else:
                origin_data.update(dump_data)
            with open(self.download_info_file, 'w', encoding='utf-8') as f:
                json.dump(origin_data, f, indent=4, ensure_ascii=False)
        else:
            with open(self.download_info_file, 'w', encoding='utf-8') as f:
                json.dump(dump_data, f, indent=4, ensure_ascii=False)

    @property
    def download_info_file(self) -> Path:
        return self._download_info_file
    
    @download_info_file.setter
    def download_info_file(self, value : Path) -> None:
        if not isinstance(value, Path):
            logger.error(f"下载信息文件错误！")
            raise FileNotFoundError(f"下载信息文件类型错误！{type(value)}不是 Path 类型")
        self._download_info_file = value

class VideoManager:

    def __init__(self) -> None:
        pass
    
    def _extract_video_info(self) -> None:
        pass

    def init(
            self,
            video_dir : Path,
            cover_dir : Optional[Path] = None,
            ):
        if not video_dir.exists():
            logger.error(f"不存在的视频目录: {video_dir}")
            raise FileNotFoundError(f"不存在的视频目录: {video_dir}")
        if cover_dir and not cover_dir.exists():
            logger.error(f"不存在的封面目录: {cover_dir}")
            raise FileNotFoundError(f"不存在的封面目录: {cover_dir}")
        
    
    def _dump_downloaded(
            self, 
            package : DownloadPackage,
            video_path : Path,
            cover_path : Path
            ) -> None:
        pass

    def send_to_mobile(self) -> None:
        try:
            from Sender.SenderConfig import sender_config
            from Sender.sender import start_server
        except ModuleNotFoundError:
            module_path = os.path.abspath(os.path.dirname(__file__))
            root_dir = os.path.dirname(module_path)
            sys.path.append(root_dir)
            from Sender.SenderConfig import sender_config
            from Sender.sender import start_server
        sender_config.upload_folder = os.path.abspath(str(config.download_dir / 'video'))
        start_server()