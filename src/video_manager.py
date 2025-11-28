"""
TikTok Auto Posting - Video Manager Module

비디오 파일 관리 모듈
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
import json

from .config import config
from .logger import logger
from .tiktok_uploader import VideoInfo


@dataclass
class VideoMetadata:
    """비디오 메타데이터"""
    file_path: str
    file_name: str
    file_size: int
    file_hash: str
    uploaded: bool = False
    upload_time: str = None
    tiktok_url: str = None


class VideoManager:
    """
    비디오 파일 관리 클래스
    
    Features:
        - 비디오 파일 스캔
        - 업로드 상태 추적
        - 중복 업로드 방지
    """
    
    def __init__(self, video_directory: Path = None):
        """
        VideoManager 초기화
        
        Args:
            video_directory: 비디오 파일이 있는 디렉토리
        """
        self.video_directory = video_directory or config.VIDEO_DIRECTORY
        self.metadata_file = config.SESSIONS_DIR / "video_metadata.json"
        self.metadata: Dict[str, VideoMetadata] = {}
        
        # 디렉토리 생성
        self.video_directory.mkdir(parents=True, exist_ok=True)
        config.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 메타데이터 로드
        self._load_metadata()
    
    def _load_metadata(self):
        """저장된 메타데이터 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = {
                        k: VideoMetadata(**v) for k, v in data.items()
                    }
                logger.debug(f"Loaded metadata for {len(self.metadata)} videos")
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.metadata = {}
    
    def _save_metadata(self):
        """메타데이터 저장"""
        try:
            data = {k: asdict(v) for k, v in self.metadata.items()}
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("Metadata saved")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            # 대용량 파일을 위해 청크 단위로 읽기
            for chunk in iter(lambda: f.read(4096 * 1024), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def scan_videos(self) -> List[Path]:
        """
        비디오 디렉토리 스캔
        
        Returns:
            비디오 파일 경로 목록
        """
        videos = []
        
        for ext in config.SUPPORTED_VIDEO_FORMATS:
            videos.extend(self.video_directory.glob(f"*{ext}"))
            videos.extend(self.video_directory.glob(f"*{ext.upper()}"))
        
        logger.info(f"Found {len(videos)} video files in {self.video_directory}")
        return sorted(videos)
    
    def get_pending_videos(self) -> List[Path]:
        """
        아직 업로드되지 않은 비디오 목록 반환
        
        Returns:
            업로드 대기 중인 비디오 파일 경로 목록
        """
        all_videos = self.scan_videos()
        pending = []
        
        for video_path in all_videos:
            file_hash = self._calculate_file_hash(video_path)
            
            if file_hash not in self.metadata or not self.metadata[file_hash].uploaded:
                pending.append(video_path)
        
        logger.info(f"Found {len(pending)} pending videos")
        return pending
    
    def register_video(self, video_path: Path) -> VideoMetadata:
        """
        비디오 파일 등록
        
        Args:
            video_path: 비디오 파일 경로
            
        Returns:
            VideoMetadata 객체
        """
        file_hash = self._calculate_file_hash(video_path)
        
        if file_hash in self.metadata:
            return self.metadata[file_hash]
        
        metadata = VideoMetadata(
            file_path=str(video_path),
            file_name=video_path.name,
            file_size=video_path.stat().st_size,
            file_hash=file_hash
        )
        
        self.metadata[file_hash] = metadata
        self._save_metadata()
        
        return metadata
    
    def mark_as_uploaded(
        self,
        video_path: Path,
        tiktok_url: str = None
    ) -> bool:
        """
        비디오를 업로드 완료로 표시
        
        Args:
            video_path: 비디오 파일 경로
            tiktok_url: 업로드된 TikTok URL (선택)
            
        Returns:
            성공 여부
        """
        try:
            file_hash = self._calculate_file_hash(video_path)
            
            if file_hash not in self.metadata:
                self.register_video(video_path)
            
            from datetime import datetime
            self.metadata[file_hash].uploaded = True
            self.metadata[file_hash].upload_time = datetime.now().isoformat()
            if tiktok_url:
                self.metadata[file_hash].tiktok_url = tiktok_url
            
            self._save_metadata()
            logger.info(f"Marked as uploaded: {video_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking video as uploaded: {e}")
            return False
    
    def get_video_info_list(
        self,
        video_paths: List[Path] = None,
        description: str = "",
        hashtags: List[str] = None
    ) -> List[VideoInfo]:
        """
        VideoInfo 객체 목록 생성
        
        Args:
            video_paths: 비디오 파일 경로 목록 (없으면 대기 중인 파일 사용)
            description: 기본 설명
            hashtags: 해시태그 목록
            
        Returns:
            VideoInfo 객체 목록
        """
        if video_paths is None:
            video_paths = self.get_pending_videos()
        
        video_info_list = []
        
        for video_path in video_paths:
            video_info = VideoInfo(
                file_path=str(video_path),
                title=video_path.stem,
                description=description,
                hashtags=hashtags
            )
            video_info_list.append(video_info)
        
        return video_info_list
    
    def get_upload_history(self) -> List[VideoMetadata]:
        """
        업로드 히스토리 반환
        
        Returns:
            업로드된 VideoMetadata 목록
        """
        return [
            m for m in self.metadata.values()
            if m.uploaded
        ]
    
    def clear_upload_history(self):
        """업로드 히스토리 초기화"""
        for metadata in self.metadata.values():
            metadata.uploaded = False
            metadata.upload_time = None
            metadata.tiktok_url = None
        
        self._save_metadata()
        logger.info("Upload history cleared")


def create_video_manager(video_directory: Path = None) -> VideoManager:
    """VideoManager 인스턴스 생성 헬퍼 함수"""
    return VideoManager(video_directory)
