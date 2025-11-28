"""
TikTok Auto Posting - Configuration Module

WSL 환경에 최적화된 설정 관리 모듈
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Application configuration class"""
    
    # Base directory
    BASE_DIR = BASE_DIR
    
    # ==========================================
    # Chrome Browser Settings (WSL Optimized)
    # ==========================================
    
    # WSL에서 Windows Chrome 사용 시 경로
    CHROME_BINARY_PATH = os.getenv(
        'CHROME_BINARY_PATH',
        '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe'
    )
    
    # Chrome user data directory
    CHROME_USER_DATA_DIR = os.getenv(
        'CHROME_USER_DATA_DIR',
        str(BASE_DIR / 'chrome_data')
    )
    
    # Chrome profile
    CHROME_PROFILE = os.getenv('CHROME_PROFILE', 'Default')
    
    # Chrome debugging port for DevTools Protocol (MCP 연결용)
    CHROME_DEBUG_PORT = int(os.getenv('CHROME_DEBUG_PORT', '9222'))
    
    # ==========================================
    # Selenium Settings
    # ==========================================
    
    # Implicit wait time
    IMPLICIT_WAIT = int(os.getenv('IMPLICIT_WAIT', '10'))
    
    # Page load timeout
    PAGE_LOAD_TIMEOUT = int(os.getenv('PAGE_LOAD_TIMEOUT', '60'))
    
    # Script timeout
    SCRIPT_TIMEOUT = int(os.getenv('SCRIPT_TIMEOUT', '30'))
    
    # ==========================================
    # TikTok Settings
    # ==========================================

    TIKTOK_URL = "https://www.tiktok.com/"
    TIKTOK_LOGIN_URL = "https://www.tiktok.com/login/phone-or-email/email"
    TIKTOK_UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=webapp"
    TIKTOK_STUDIO_URL = "https://www.tiktok.com/tiktokstudio"
    TIKTOK_USERNAME = os.getenv('TIKTOK_USERNAME', '')
    
    # TikTok Login Credentials
    TIKTOK_EMAIL = os.getenv('TIKTOK_EMAIL', '')
    TIKTOK_PASSWORD = os.getenv('TIKTOK_PASSWORD', '')
    
    # ==========================================
    # Video Settings
    # ==========================================
    
    VIDEO_DIRECTORY = Path(os.getenv(
        'VIDEO_DIRECTORY',
        str(BASE_DIR / 'videos')
    ))
    
    DEFAULT_HASHTAGS = os.getenv('DEFAULT_HASHTAGS', '#fyp,#viral,#tiktok')
    UPLOAD_INTERVAL = int(os.getenv('UPLOAD_INTERVAL', '60'))
    
    # Supported video formats
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.webm']
    
    # Maximum video file size (in bytes) - 10GB
    MAX_VIDEO_SIZE = 10 * 1024 * 1024 * 1024
    
    # ==========================================
    # Logging Settings
    # ==========================================
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = Path(os.getenv(
        'LOG_FILE',
        str(BASE_DIR / 'logs' / 'app.log')
    ))
    
    # ==========================================
    # Directory Paths
    # ==========================================
    
    LOGS_DIR = BASE_DIR / 'logs'
    VIDEOS_DIR = BASE_DIR / 'videos'
    UPLOADS_DIR = BASE_DIR / 'uploads'
    SESSIONS_DIR = BASE_DIR / 'sessions'
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.LOGS_DIR,
            cls.VIDEOS_DIR,
            cls.UPLOADS_DIR,
            cls.SESSIONS_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_chrome_options_args(cls):
        """
        WSL 환경에 최적화된 Chrome 옵션 반환
        
        Returns:
            list: Chrome 옵션 인자 목록
        """
        options = [
            # DevTools Protocol 활성화 (MCP 연결용)
            f'--remote-debugging-port={cls.CHROME_DEBUG_PORT}',
            
            # 사용자 데이터 디렉토리 설정 (로그인 유지)
            f'--user-data-dir={cls.CHROME_USER_DATA_DIR}',
            
            # 프로필 설정
            f'--profile-directory={cls.CHROME_PROFILE}',
            
            # WSL 환경 최적화 옵션
            '--no-sandbox',
            '--disable-dev-shm-usage',
            
            # GPU 관련 설정 (WSL에서 안정성 향상)
            '--disable-gpu',
            '--disable-software-rasterizer',
            
            # 창 크기 설정
            '--window-size=1920,1080',
            '--start-maximized',
            
            # 자동화 탐지 우회
            '--disable-blink-features=AutomationControlled',
            
            # 알림 비활성화
            '--disable-notifications',
            
            # 팝업 차단
            '--disable-popup-blocking',
            
            # 보안 관련
            '--disable-web-security',
            '--allow-running-insecure-content',
            
            # 인포바 비활성화
            '--disable-infobars',
            
            # 확장 프로그램 비활성화
            '--disable-extensions',
            
            # 로그 레벨
            '--log-level=3',
        ]
        
        return options
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        # Check Chrome binary path
        chrome_path = Path(cls.CHROME_BINARY_PATH)
        if not chrome_path.exists():
            errors.append(f"Chrome binary not found at: {cls.CHROME_BINARY_PATH}")
        
        # Check video directory
        if not cls.VIDEO_DIRECTORY.exists():
            cls.VIDEO_DIRECTORY.mkdir(parents=True, exist_ok=True)
        
        return errors


# Configuration instance
config = Config()
