"""
TikTok Auto Posting - MCP Integration Module

Chrome DevTools MCP와의 통합을 위한 유틸리티 모듈
MCP를 통해 브라우저 제어 시 사용
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .config import config
from .logger import logger


@dataclass
class MCPElementInfo:
    """MCP 요소 정보"""
    uid: str
    tag_name: str
    text: str = ""
    attributes: Dict[str, str] = None


class MCPIntegration:
    """
    Chrome DevTools MCP 통합 클래스
    
    MCP 서버와 통신하여 브라우저 제어
    Selenium과 병행하여 사용 가능
    """
    
    def __init__(self):
        """MCPIntegration 초기화"""
        self.debug_port = config.CHROME_DEBUG_PORT
        self._connected = False
        
    def get_debug_url(self) -> str:
        """DevTools 디버그 URL 반환"""
        return f"http://localhost:{self.debug_port}"
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        MCP 연결 정보 반환
        
        Returns:
            연결 정보 딕셔너리
        """
        return {
            "debug_port": self.debug_port,
            "debug_url": self.get_debug_url(),
            "ws_url": f"ws://localhost:{self.debug_port}",
        }
    
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """
        페이지 로드 대기 (MCP 환경에서 사용)
        
        Args:
            timeout: 최대 대기 시간 (초)
            
        Returns:
            성공 여부
        """
        logger.info(f"Waiting for page load (timeout: {timeout}s)...")
        # MCP의 wait_for 기능 사용을 위한 래퍼
        return True
    
    def log_action(self, action: str, element_info: str = None):
        """
        MCP 액션 로깅
        
        Args:
            action: 수행한 액션
            element_info: 요소 정보 (선택)
        """
        if element_info:
            logger.info(f"MCP Action: {action} on {element_info}")
        else:
            logger.info(f"MCP Action: {action}")


class TikTokMCPHelper:
    """
    TikTok 업로드를 위한 MCP 헬퍼 클래스
    
    자주 사용되는 TikTok 페이지 요소들에 대한 MCP 작업 도우미
    """
    
    # TikTok 페이지 요소 정보
    PAGE_ELEMENTS = {
        'upload_page': {
            'url': 'https://www.tiktok.com/creator-center/upload',
            'wait_text': 'Upload',
        },
        'login_page': {
            'url': 'https://www.tiktok.com/login',
            'wait_text': 'Log in',
        },
        'home_page': {
            'url': 'https://www.tiktok.com/',
            'wait_text': 'For You',
        }
    }
    
    @staticmethod
    def get_upload_instructions() -> str:
        """
        MCP를 통한 업로드 절차 안내 반환
        
        Returns:
            업로드 절차 설명 문자열
        """
        return """
TikTok Video Upload via MCP:

1. Navigate to upload page:
   - Use mcp_chromedevtool_navigate to go to https://www.tiktok.com/creator-center/upload

2. Wait for page load:
   - Use mcp_chromedevtool_wait_for with text "Upload"

3. Upload video:
   - Use mcp_chromedevtool_upload_file with the file input element

4. Set caption:
   - Take snapshot to find caption input element
   - Use mcp_chromedevtool_click to focus on caption area
   - Use mcp_chromedevtool_fill to enter caption text

5. Add hashtags:
   - Include hashtags in caption or use hashtag input if available

6. Post video:
   - Find and click the Post button
   - Wait for success message
"""
    
    @staticmethod
    def get_element_selectors() -> Dict[str, str]:
        """
        TikTok 페이지 요소 선택자 반환
        
        Returns:
            요소 선택자 딕셔너리
        """
        return {
            'file_input': 'input[type="file"]',
            'caption_area': '[contenteditable="true"]',
            'post_button': 'button[type="submit"]',
            'cover_edit': '[class*="cover"]',
        }


def get_mcp_helper() -> TikTokMCPHelper:
    """TikTokMCPHelper 인스턴스 반환"""
    return TikTokMCPHelper()


def print_mcp_usage():
    """MCP 사용법 출력"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Chrome DevTools MCP Integration Guide              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  This program integrates with Chrome DevTools MCP for        ║
║  browser automation. The following tools are available:      ║
║                                                              ║
║  • mcp_chromedevtool_click - Click elements                  ║
║  • mcp_chromedevtool_fill - Fill input fields               ║
║  • mcp_chromedevtool_take_screenshot - Capture screen       ║
║  • mcp_chromedevtool_take_snapshot - Get page structure     ║
║  • mcp_chromedevtool_upload_file - Upload files             ║
║  • mcp_chromedevtool_wait_for - Wait for text               ║
║                                                              ║
║  Debug Port: 9222 (configurable in .env)                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
