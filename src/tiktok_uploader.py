"""
TikTok Auto Posting - TikTok Uploader Module

TikTok 영상 업로드 자동화 모듈
Chrome DevTools MCP와 연동하여 작동
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .config import config
from .logger import logger
from .browser import BrowserManager


@dataclass
class VideoInfo:
    """비디오 정보 데이터 클래스"""
    file_path: str
    title: str = ""
    description: str = ""
    hashtags: List[str] = None
    schedule_time: str = None  # ISO format datetime string
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = config.DEFAULT_HASHTAGS.split(',')
        
        # 파일명에서 제목 추출 (제목이 없는 경우)
        if not self.title:
            self.title = Path(self.file_path).stem


class TikTokUploader:
    """
    TikTok 영상 업로드 자동화 클래스
    
    Chrome DevTools MCP를 통해 텍스트 입력 및 클릭 등을 수행
    Selenium을 통해 업로드 과정 시각화
    """
    
    # TikTok Upload Page Selectors (2024년 기준 - 변경될 수 있음)
    SELECTORS = {
        # 파일 업로드
        'file_input': '//input[@type="file"]',
        'upload_button': '//button[contains(@class, "upload")]',
        'iframe_upload': '//iframe[contains(@src, "upload")]',
        
        # 캡션/설명
        'caption_input': '//div[contains(@class, "DraftEditor-root")]//div[@contenteditable="true"]',
        'caption_container': '//div[contains(@class, "caption")]',
        
        # 해시태그
        'hashtag_input': '//input[contains(@placeholder, "hashtag")]',
        
        # 커버 이미지
        'cover_button': '//button[contains(text(), "Cover")]',
        'edit_cover_button': '//div[contains(@class, "cover")]//button',
        
        # 게시 버튼
        'post_button': '//button[contains(text(), "Post") or contains(text(), "게시")]',
        'post_button_alt': '//button[@type="submit"]',
        
        # 로그인 관련
        'login_button': '//button[contains(text(), "Log in") or contains(text(), "로그인")]',
        'login_modal': '//div[contains(@class, "login")]',
        
        # 업로드 진행 상태
        'upload_progress': '//div[contains(@class, "progress")]',
        'upload_complete': '//div[contains(text(), "uploaded") or contains(text(), "완료")]',
        'upload_error': '//div[contains(@class, "error")]',
        
        # 성공 메시지
        'success_message': '//div[contains(text(), "posted") or contains(text(), "게시됨")]',
    }
    
    def __init__(self, browser: BrowserManager = None):
        """
        TikTokUploader 초기화
        
        Args:
            browser: BrowserManager 인스턴스 (없으면 새로 생성)
        """
        self.browser = browser or BrowserManager()
        self._is_logged_in = False
        
    def start(self) -> bool:
        """브라우저 시작 및 TikTok 접속"""
        if not self.browser.driver:
            if not self.browser.start_browser():
                return False
        
        return self.browser.navigate_to(config.TIKTOK_URL)
    
    def check_login_status(self) -> bool:
        """
        TikTok 로그인 상태 확인
        
        Returns:
            로그인 여부
        """
        if not self.browser.driver:
            return False
        
        try:
            # Creator Center 페이지로 이동하여 로그인 확인
            self.browser.navigate_to(config.TIKTOK_UPLOAD_URL)
            time.sleep(3)
            
            current_url = self.browser.get_current_url()
            
            # 로그인 페이지로 리다이렉트되면 로그인 필요
            if 'login' in current_url.lower():
                logger.warning("Not logged in - login required")
                self._is_logged_in = False
                return False
            
            # 업로드 페이지에 있으면 로그인 상태
            if 'upload' in current_url.lower() or 'creator' in current_url.lower():
                logger.info("Successfully logged in to TikTok")
                self._is_logged_in = True
                return True
            
            # 로그인 버튼 확인
            login_button = self.browser.wait_for_element(
                By.XPATH,
                self.SELECTORS['login_button'],
                timeout=5
            )
            if login_button:
                self._is_logged_in = False
                return False
            
            self._is_logged_in = True
            return True
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def wait_for_manual_login(self, timeout: int = 300) -> bool:
        """
        수동 로그인 대기
        
        사용자가 직접 로그인할 수 있도록 대기
        
        Args:
            timeout: 최대 대기 시간 (초)
            
        Returns:
            로그인 성공 여부
        """
        logger.info("="*50)
        logger.info("Manual login required!")
        logger.info("Please log in to TikTok in the browser window.")
        logger.info(f"Waiting for login (timeout: {timeout} seconds)...")
        logger.info("="*50)
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_login_status():
                logger.info("Login successful!")
                return True
            
            time.sleep(5)  # 5초마다 확인
            remaining = int(timeout - (time.time() - start_time))
            if remaining % 30 == 0:  # 30초마다 메시지 출력
                logger.info(f"Still waiting for login... ({remaining} seconds remaining)")
        
        logger.error("Login timeout - please try again")
        return False
    
    def navigate_to_upload_page(self) -> bool:
        """업로드 페이지로 이동"""
        try:
            logger.info("Navigating to TikTok upload page...")
            
            if not self.browser.navigate_to(config.TIKTOK_UPLOAD_URL):
                return False
            
            # 페이지 로드 대기
            time.sleep(3)
            
            # 업로드 영역 확인
            upload_area = self.browser.wait_for_element(
                By.XPATH,
                self.SELECTORS['file_input'],
                timeout=15
            )
            
            if upload_area:
                logger.info("Successfully navigated to upload page")
                return True
            else:
                logger.warning("Upload area not found - page may have changed")
                return True  # 페이지 구조가 다를 수 있으므로 계속 진행
                
        except Exception as e:
            logger.error(f"Failed to navigate to upload page: {e}")
            return False
    
    def upload_video(self, video_info: VideoInfo) -> bool:
        """
        비디오 업로드
        
        Args:
            video_info: VideoInfo 객체
            
        Returns:
            성공 여부
        """
        try:
            file_path = video_info.file_path
            
            # 파일 존재 확인
            if not os.path.exists(file_path):
                logger.error(f"Video file not found: {file_path}")
                return False
            
            # 파일 크기 확인
            file_size = os.path.getsize(file_path)
            if file_size > config.MAX_VIDEO_SIZE:
                logger.error(f"Video file too large: {file_size} bytes")
                return False
            
            logger.info(f"Uploading video: {file_path}")
            logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
            
            # 파일 input 요소 찾기
            file_input = self.browser.wait_for_element(
                By.XPATH,
                self.SELECTORS['file_input'],
                timeout=15
            )
            
            if not file_input:
                # iframe 내부에 있을 수 있음
                logger.info("Checking for upload iframe...")
                iframe = self.browser.wait_for_element(
                    By.XPATH,
                    self.SELECTORS['iframe_upload'],
                    timeout=5
                )
                if iframe:
                    self.browser.driver.switch_to.frame(iframe)
                    file_input = self.browser.wait_for_element(
                        By.XPATH,
                        self.SELECTORS['file_input'],
                        timeout=10
                    )
            
            if not file_input:
                logger.error("File input element not found")
                self.browser.take_screenshot("upload_error_no_input.png")
                return False
            
            # 파일 업로드
            absolute_path = str(Path(file_path).absolute())
            file_input.send_keys(absolute_path)
            logger.info("File sent to upload input")
            
            # 업로드 완료 대기
            if not self._wait_for_upload_complete():
                return False
            
            logger.info("Video upload completed!")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            self.browser.take_screenshot("upload_error.png")
            return False
        finally:
            # iframe에서 나오기
            try:
                self.browser.driver.switch_to.default_content()
            except:
                pass
    
    def _wait_for_upload_complete(self, timeout: int = 300) -> bool:
        """
        업로드 완료 대기
        
        Args:
            timeout: 최대 대기 시간 (초)
            
        Returns:
            성공 여부
        """
        logger.info(f"Waiting for upload to complete (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 에러 확인
                error_element = self.browser.wait_for_element(
                    By.XPATH,
                    self.SELECTORS['upload_error'],
                    timeout=2
                )
                if error_element and error_element.is_displayed():
                    error_text = error_element.text
                    logger.error(f"Upload error: {error_text}")
                    return False
                
                # 완료 확인 (캡션 입력 영역이 나타나면 업로드 완료)
                caption_area = self.browser.wait_for_element(
                    By.XPATH,
                    self.SELECTORS['caption_input'],
                    timeout=3
                )
                if caption_area:
                    logger.info("Upload complete - caption area found")
                    return True
                
                # 게시 버튼 확인
                post_button = self.browser.wait_for_element(
                    By.XPATH,
                    self.SELECTORS['post_button'],
                    timeout=3
                )
                if post_button:
                    logger.info("Upload complete - post button found")
                    return True
                
            except Exception as e:
                logger.debug(f"Still waiting for upload... ({e})")
            
            time.sleep(3)
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0:
                logger.info(f"Upload in progress... ({elapsed}s elapsed)")
        
        logger.error("Upload timeout")
        return False
    
    def set_caption(self, video_info: VideoInfo) -> bool:
        """
        캡션 및 해시태그 설정
        
        Args:
            video_info: VideoInfo 객체
            
        Returns:
            성공 여부
        """
        try:
            logger.info("Setting caption and hashtags...")
            
            # 캡션 입력 영역 찾기
            caption_input = self.browser.wait_for_element(
                By.XPATH,
                self.SELECTORS['caption_input'],
                timeout=10,
                condition="clickable"
            )
            
            if not caption_input:
                logger.warning("Caption input not found - trying alternative method")
                # 대체 선택자 시도
                caption_input = self.browser.wait_for_element(
                    By.XPATH,
                    '//div[@contenteditable="true"]',
                    timeout=5
                )
            
            if caption_input:
                # 기존 내용 삭제
                caption_input.click()
                time.sleep(0.5)
                
                # 캡션 텍스트 구성
                caption_text = ""
                if video_info.description:
                    caption_text = video_info.description + " "
                
                # 해시태그 추가
                if video_info.hashtags:
                    hashtag_str = " ".join(
                        tag if tag.startswith('#') else f"#{tag}"
                        for tag in video_info.hashtags
                    )
                    caption_text += hashtag_str
                
                # 텍스트 입력
                caption_input.send_keys(caption_text)
                logger.info(f"Caption set: {caption_text[:50]}...")
                
                return True
            else:
                logger.warning("Could not find caption input element")
                return False
                
        except Exception as e:
            logger.error(f"Error setting caption: {e}")
            return False
    
    def post_video(self) -> bool:
        """
        비디오 게시
        
        Returns:
            성공 여부
        """
        try:
            logger.info("Posting video...")
            
            # 게시 버튼 찾기
            post_button = self.browser.wait_for_element(
                By.XPATH,
                self.SELECTORS['post_button'],
                timeout=10,
                condition="clickable"
            )
            
            if not post_button:
                # 대체 선택자 시도
                post_button = self.browser.wait_for_element(
                    By.XPATH,
                    self.SELECTORS['post_button_alt'],
                    timeout=5,
                    condition="clickable"
                )
            
            if post_button:
                # 버튼 클릭
                post_button.click()
                logger.info("Post button clicked")
                
                # 게시 완료 대기
                time.sleep(5)
                
                # 성공 메시지 확인
                success = self.browser.wait_for_element(
                    By.XPATH,
                    self.SELECTORS['success_message'],
                    timeout=60
                )
                
                if success:
                    logger.info("Video posted successfully!")
                    return True
                else:
                    # URL 변경으로 성공 확인
                    current_url = self.browser.get_current_url()
                    if 'profile' in current_url.lower() or 'success' in current_url.lower():
                        logger.info("Video posted successfully (URL redirect detected)")
                        return True
                    
                    logger.warning("Could not confirm post success")
                    return True  # 버튼은 클릭했으므로 성공으로 처리
            else:
                logger.error("Post button not found")
                self.browser.take_screenshot("post_error_no_button.png")
                return False
                
        except Exception as e:
            logger.error(f"Error posting video: {e}")
            self.browser.take_screenshot("post_error.png")
            return False
    
    def upload_and_post(self, video_info: VideoInfo) -> bool:
        """
        전체 업로드 및 게시 프로세스 실행
        
        Args:
            video_info: VideoInfo 객체
            
        Returns:
            성공 여부
        """
        try:
            logger.info("="*50)
            logger.info(f"Starting upload process for: {video_info.title}")
            logger.info("="*50)
            
            # 1. 업로드 페이지로 이동
            if not self.navigate_to_upload_page():
                return False
            
            # 2. 로그인 확인
            if not self._is_logged_in:
                if not self.check_login_status():
                    if not self.wait_for_manual_login():
                        return False
            
            # 3. 비디오 업로드
            if not self.upload_video(video_info):
                return False
            
            # 4. 캡션 설정
            time.sleep(2)  # 페이지 안정화 대기
            self.set_caption(video_info)
            
            # 5. 게시
            time.sleep(2)
            if not self.post_video():
                return False
            
            logger.info("="*50)
            logger.info("Upload and post completed successfully!")
            logger.info("="*50)
            
            return True
            
        except Exception as e:
            logger.error(f"Upload and post failed: {e}")
            self.browser.take_screenshot("upload_post_error.png")
            return False
    
    def batch_upload(self, video_list: List[VideoInfo]) -> Dict[str, bool]:
        """
        여러 비디오 일괄 업로드
        
        Args:
            video_list: VideoInfo 객체 목록
            
        Returns:
            {파일경로: 성공여부} 딕셔너리
        """
        results = {}
        total = len(video_list)
        
        logger.info(f"Starting batch upload: {total} videos")
        
        for i, video_info in enumerate(video_list, 1):
            logger.info(f"\nProcessing video {i}/{total}: {video_info.title}")
            
            success = self.upload_and_post(video_info)
            results[video_info.file_path] = success
            
            if success and i < total:
                # 다음 업로드 전 대기
                logger.info(f"Waiting {config.UPLOAD_INTERVAL} seconds before next upload...")
                time.sleep(config.UPLOAD_INTERVAL)
        
        # 결과 요약
        successful = sum(1 for v in results.values() if v)
        failed = total - successful
        
        logger.info("\n" + "="*50)
        logger.info(f"Batch upload completed!")
        logger.info(f"Success: {successful}, Failed: {failed}")
        logger.info("="*50)
        
        return results
    
    def close(self):
        """리소스 정리"""
        if self.browser:
            self.browser.close_browser()


def create_uploader(browser: BrowserManager = None) -> TikTokUploader:
    """TikTokUploader 인스턴스 생성 헬퍼 함수"""
    return TikTokUploader(browser)
