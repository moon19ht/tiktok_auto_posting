"""
TikTok Auto Posting - Browser Module

WSL 환경에 최적화된 Chrome Selenium 브라우저 관리 모듈
업로드 과정이 보이도록 headless 모드를 사용하지 않음
"""

import os
import time
import subprocess
import platform
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException
)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.os_manager import ChromeType
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False

from .config import config
from .logger import logger


class BrowserManager:
    """
    WSL 환경에 최적화된 Chrome 브라우저 관리 클래스
    
    Features:
        - WSL에서 Windows Chrome 사용 지원
        - DevTools Protocol 활성화 (MCP 연결용)
        - 업로드 과정 시각화 (non-headless)
        - 로그인 상태 유지
    """
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self._is_wsl = self._check_wsl_environment()
        self._chrome_process = None
        
    def _check_wsl_environment(self) -> bool:
        """Check if running in WSL environment"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except FileNotFoundError:
            return False
    
    def _wsl_to_windows_path(self, wsl_path: str) -> str:
        """WSL 경로를 Windows 경로로 변환"""
        if not self._is_wsl:
            return wsl_path
        
        try:
            # wslpath 명령어 사용
            result = subprocess.run(
                ['wslpath', '-w', wsl_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"wslpath conversion failed: {e}")
        
        # 수동 변환 (fallback)
        if wsl_path.startswith('/mnt/'):
            # /mnt/c/path -> C:\path
            parts = wsl_path.split('/')
            drive = parts[2].upper()
            rest = '\\'.join(parts[3:])
            return f"{drive}:\\{rest}"
        elif wsl_path.startswith('/home/'):
            # /home/user/path -> \\wsl$\Ubuntu\home\user\path
            return f"\\\\wsl$\\Ubuntu{wsl_path.replace('/', '\\')}"
        
        return wsl_path
    
    def _get_windows_chromedriver(self) -> str:
        """Windows용 ChromeDriver 경로 가져오기 (Windows 경로에 저장)"""
        # Windows의 C:\tiktok_drivers 폴더에 저장
        if self._is_wsl:
            drivers_wsl_path = Path('/mnt/c/tiktok_drivers')
            drivers_wsl_path.mkdir(exist_ok=True)
            chromedriver_wsl_path = drivers_wsl_path / 'chromedriver.exe'
            chromedriver_win_path = 'C:\\tiktok_drivers\\chromedriver.exe'
        else:
            drivers_dir = Path(config.BASE_DIR) / 'drivers'
            drivers_dir.mkdir(exist_ok=True)
            chromedriver_wsl_path = drivers_dir / 'chromedriver.exe'
            chromedriver_win_path = str(chromedriver_wsl_path)
        
        if chromedriver_wsl_path.exists():
            logger.info(f"Using existing ChromeDriver: {chromedriver_win_path}")
            return chromedriver_win_path
        
        # ChromeDriver 다운로드
        logger.info("Downloading Windows ChromeDriver...")
        try:
            import urllib.request
            import zipfile
            import json
            
            # Chrome 버전 확인
            chrome_version = self._get_chrome_version()
            logger.info(f"Detected Chrome version: {chrome_version}")
            
            # ChromeDriver 다운로드 URL (Chrome for Testing)
            cft_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
            
            with urllib.request.urlopen(cft_url, timeout=30) as response:
                data = json.loads(response.read().decode())
            
            # Stable 버전 ChromeDriver URL 가져오기
            stable = data['channels']['Stable']
            chromedriver_downloads = stable['downloads'].get('chromedriver', [])
            
            win64_url = None
            for item in chromedriver_downloads:
                if item['platform'] == 'win64':
                    win64_url = item['url']
                    break
            
            if not win64_url:
                raise Exception("Windows ChromeDriver URL not found")
            
            logger.info(f"Downloading from: {win64_url}")
            
            # 다운로드
            zip_path = chromedriver_wsl_path.parent / 'chromedriver_win64.zip'
            urllib.request.urlretrieve(win64_url, zip_path)
            
            # 압축 해제
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith('chromedriver.exe'):
                        source = zip_ref.open(file)
                        target = open(chromedriver_wsl_path, 'wb')
                        target.write(source.read())
                        source.close()
                        target.close()
                        break
            
            # zip 파일 삭제
            zip_path.unlink()
            
            logger.info(f"ChromeDriver downloaded: {chromedriver_win_path}")
            return chromedriver_win_path
            
        except Exception as e:
            logger.error(f"Failed to download ChromeDriver: {e}")
            raise
    
    def _get_chrome_version(self) -> str:
        """Chrome 버전 확인"""
        try:
            if self._is_wsl:
                # Windows Chrome 버전 확인
                chrome_path = config.CHROME_BINARY_PATH
                result = subprocess.run(
                    ['powershell.exe', '-Command', 
                     f'(Get-Item "{chrome_path}").VersionInfo.FileVersion'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    # 주 버전만 추출 (예: 120.0.6099.109 -> 120)
                    return version.split('.')[0]
        except Exception as e:
            logger.debug(f"Failed to get Chrome version: {e}")
        
        return "stable"
    
    def _get_chrome_options(self) -> Options:
        """
        WSL 환경에 최적화된 Chrome 옵션 생성
        
        Returns:
            Chrome Options 객체
        """
        options = Options()
        
        # WSL에서 Windows Chrome 사용 시 바이너리 경로 설정
        if self._is_wsl:
            chrome_path = config.CHROME_BINARY_PATH
            # Windows 경로로 변환
            if chrome_path.startswith('/mnt/'):
                windows_chrome_path = self._wsl_to_windows_path(chrome_path)
                options.binary_location = windows_chrome_path
                logger.info(f"Using Chrome binary: {windows_chrome_path}")
            else:
                options.binary_location = chrome_path
                logger.info(f"Using Chrome binary: {chrome_path}")
        
        # Chrome 사용자 데이터 디렉토리 (Windows 경로 사용)
        user_data_dir = config.CHROME_USER_DATA_DIR
        if self._is_wsl:
            windows_user_data = self._wsl_to_windows_path(user_data_dir)
            options.add_argument(f'--user-data-dir={windows_user_data}')
            logger.info(f"Using user data dir: {windows_user_data}")
        else:
            options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # Chrome 프로필
        options.add_argument(f'--profile-directory={config.CHROME_PROFILE}')
        
        # DevTools Protocol 포트 설정 (MCP 연결용)
        options.add_argument(f'--remote-debugging-port={config.CHROME_DEBUG_PORT}')
        
        # 기본 Chrome 옵션
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--start-maximized')
        
        # WebAuthn/Passkey 비활성화 (보안키 팝업 방지)
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=WebAuthentication')
        
        # GPU 관련 옵션 (WSL 호환성)
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        
        # 자동화 탐지 우회를 위한 추가 설정
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent 설정 (봇 탐지 우회)
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.0.0 Safari/537.36'
        )
        
        return options
    
    def _get_chrome_service(self) -> Service:
        """
        ChromeDriver 서비스 생성 (WSL 환경용)
        
        Returns:
            Chrome Service 객체
        """
        if self._is_wsl:
            try:
                # Windows용 ChromeDriver 사용 (이미 Windows 경로 반환)
                chromedriver_win_path = self._get_windows_chromedriver()
                logger.info(f"Using Windows ChromeDriver: {chromedriver_win_path}")
                return Service(executable_path=chromedriver_win_path)
            except Exception as e:
                logger.error(f"Failed to get Windows ChromeDriver: {e}")
                raise
        
        # Linux 환경
        if HAS_WEBDRIVER_MANAGER:
            try:
                driver_path = ChromeDriverManager().install()
                logger.info(f"ChromeDriver installed at: {driver_path}")
                return Service(driver_path)
            except Exception as e:
                logger.warning(f"Failed to use webdriver-manager: {e}")
        
        return Service()
    
    def start_browser(self) -> bool:
        """
        Chrome 브라우저 시작
        
        WSL 환경에서는 Linux Chrome을 사용 (WSLg 지원)
        업로드 과정이 보이도록 GUI 모드로 실행
        
        Returns:
            성공 여부
        """
        try:
            logger.info("Starting Chrome browser...")
            
            # 필요한 디렉토리 생성
            config.ensure_directories()
            
            # Chrome 사용자 데이터 디렉토리 생성
            user_data_path = Path(config.CHROME_USER_DATA_DIR)
            user_data_path.mkdir(parents=True, exist_ok=True)
            
            # WSL에서는 Linux Chrome 사용 (WSLg를 통해 GUI 표시)
            return self._start_browser_linux()
            
        except WebDriverException as e:
            logger.error(f"Failed to start Chrome browser: {e}")
            self._print_troubleshooting_tips()
            return False
        except Exception as e:
            logger.error(f"Unexpected error starting browser: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _start_browser_linux(self) -> bool:
        """Linux Chrome 사용 (WSLg를 통해 GUI 표시)"""
        # Chrome 옵션 설정
        options = Options()
        
        # Linux Chrome 바이너리 경로
        linux_chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
        ]
        
        chrome_binary = None
        for path in linux_chrome_paths:
            if Path(path).exists():
                chrome_binary = path
                break
        
        if chrome_binary:
            options.binary_location = chrome_binary
            logger.info(f"Using Chrome binary: {chrome_binary}")
        
        # Chrome 사용자 데이터 디렉토리
        user_data_dir = config.CHROME_USER_DATA_DIR
        options.add_argument(f'--user-data-dir={user_data_dir}')
        options.add_argument(f'--profile-directory={config.CHROME_PROFILE}')
        
        # DevTools Protocol 포트 설정 (MCP 연결용)
        options.add_argument(f'--remote-debugging-port={config.CHROME_DEBUG_PORT}')
        
        # 기본 Chrome 옵션
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--start-maximized')
        
        # WebAuthn/Passkey 비활성화 (보안키 팝업 방지)
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=WebAuthentication')
        
        # WSL/Linux 관련 옵션
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # 자동화 탐지 우회
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent 설정
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.0.0 Safari/537.36'
        )
        
        # ChromeDriver 서비스
        if HAS_WEBDRIVER_MANAGER:
            try:
                driver_path = ChromeDriverManager().install()
                logger.info(f"ChromeDriver: {driver_path}")
                service = Service(driver_path)
            except Exception as e:
                logger.warning(f"webdriver-manager failed: {e}")
                service = Service()
        else:
            service = Service()
        
        logger.info("Creating WebDriver...")
        
        # WebDriver 생성
        self.driver = webdriver.Chrome(
            service=service,
            options=options
        )
        
        # 타임아웃 설정
        self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        self.driver.set_script_timeout(config.SCRIPT_TIMEOUT)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        
        # WebDriverWait 객체 생성
        self.wait = WebDriverWait(self.driver, config.IMPLICIT_WAIT)
        
        # 자동화 탐지 우회 스크립트 실행
        self._execute_stealth_scripts()
        
        logger.info(f"Chrome browser started successfully!")
        logger.info(f"DevTools Protocol enabled on port {config.CHROME_DEBUG_PORT}")
        
        return True
    
    def _is_port_in_use(self, port: int) -> bool:
        """포트가 사용 중인지 확인"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    
    def _print_troubleshooting_tips(self):
        """문제 해결 팁 출력"""
        print("\n" + "="*60)
        print("  🔧 브라우저 시작 문제 해결 방법")
        print("="*60)
        print("\n  1. 기존 Chrome 프로세스 종료:")
        print("     - Windows 작업 관리자에서 모든 Chrome 종료")
        print("     - 또는: taskkill /F /IM chrome.exe")
        print("\n  2. Chrome 사용자 데이터 디렉토리 확인:")
        print(f"     - 경로: {config.CHROME_USER_DATA_DIR}")
        print("     - 해당 폴더가 다른 Chrome에서 사용 중이면 오류 발생")
        print("\n  3. ChromeDriver 재다운로드:")
        print("     - drivers/chromedriver.exe 삭제 후 재시도")
        print("\n  4. Chrome 버전 확인:")
        print("     - Chrome과 ChromeDriver 버전이 일치해야 함")
        print("="*60 + "\n")
    
    def _execute_stealth_scripts(self):
        """자동화 탐지 우회를 위한 JavaScript 실행"""
        if not self.driver:
            return
        
        stealth_scripts = [
            # webdriver 속성 숨기기
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            
            # plugins 속성 수정
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            })
            """,
            
            # languages 속성 설정
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            })
            """,
            
            # Chrome 런타임 객체 추가
            """
            window.chrome = {
                runtime: {}
            }
            """,
            
            # permissions 속성 수정
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            )
            """
        ]
        
        for script in stealth_scripts:
            try:
                self.driver.execute_script(script)
            except Exception as e:
                logger.debug(f"Stealth script execution warning: {e}")
    
    def navigate_to(self, url: str) -> bool:
        """
        지정된 URL로 이동
        
        Args:
            url: 이동할 URL
            
        Returns:
            성공 여부
        """
        if not self.driver:
            logger.error("Browser not started")
            return False
        
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # 페이지 로드 완료 대기
            self.wait.until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            logger.info(f"Successfully navigated to: {url}")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout while loading: {url}")
            return False
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    def wait_for_element(
        self,
        by: By,
        value: str,
        timeout: int = None,
        condition: str = "presence"
    ):
        """
        요소가 나타날 때까지 대기
        
        Args:
            by: 검색 방법 (By.ID, By.XPATH 등)
            value: 검색 값
            timeout: 대기 시간 (초)
            condition: 대기 조건 ("presence", "visible", "clickable")
            
        Returns:
            WebElement or None
        """
        if not self.driver:
            return None
        
        timeout = timeout or config.IMPLICIT_WAIT
        wait = WebDriverWait(self.driver, timeout)
        
        conditions = {
            "presence": EC.presence_of_element_located,
            "visible": EC.visibility_of_element_located,
            "clickable": EC.element_to_be_clickable
        }
        
        ec_condition = conditions.get(condition, EC.presence_of_element_located)
        
        try:
            element = wait.until(ec_condition((by, value)))
            return element
        except TimeoutException:
            logger.warning(f"Element not found: {by}={value}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for element: {e}")
            return None
    
    def click_element(self, by: By, value: str, timeout: int = None) -> bool:
        """
        요소 클릭
        
        Args:
            by: 검색 방법
            value: 검색 값
            timeout: 대기 시간
            
        Returns:
            성공 여부
        """
        element = self.wait_for_element(by, value, timeout, "clickable")
        if element:
            try:
                element.click()
                logger.debug(f"Clicked element: {by}={value}")
                return True
            except Exception as e:
                logger.error(f"Failed to click element: {e}")
                # JavaScript로 클릭 시도
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except:
                    return False
        return False
    
    def input_text(self, by: By, value: str, text: str, timeout: int = None) -> bool:
        """
        텍스트 입력
        
        Args:
            by: 검색 방법
            value: 검색 값
            text: 입력할 텍스트
            timeout: 대기 시간
            
        Returns:
            성공 여부
        """
        element = self.wait_for_element(by, value, timeout, "visible")
        if element:
            try:
                element.clear()
                element.send_keys(text)
                logger.debug(f"Input text to element: {by}={value}")
                return True
            except Exception as e:
                logger.error(f"Failed to input text: {e}")
                return False
        return False
    
    def upload_file(self, by: By, value: str, file_path: str, timeout: int = None) -> bool:
        """
        파일 업로드 (input[type=file] 요소 사용)
        
        Args:
            by: 검색 방법
            value: 검색 값
            file_path: 업로드할 파일 경로
            timeout: 대기 시간
            
        Returns:
            성공 여부
        """
        element = self.wait_for_element(by, value, timeout, "presence")
        if element:
            try:
                # WSL에서 Windows 경로로 변환
                if self._is_wsl and file_path.startswith('/'):
                    # /home/user/file -> 그대로 사용 또는 Windows 경로로 변환
                    pass
                
                element.send_keys(file_path)
                logger.info(f"File uploaded: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to upload file: {e}")
                return False
        return False
    
    def take_screenshot(self, filename: str = None) -> Optional[str]:
        """
        스크린샷 저장
        
        Args:
            filename: 파일명 (없으면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if not self.driver:
            return None
        
        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            
            screenshot_path = config.LOGS_DIR / filename
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def get_current_url(self) -> Optional[str]:
        """현재 URL 반환"""
        return self.driver.current_url if self.driver else None
    
    def get_page_source(self) -> Optional[str]:
        """현재 페이지 소스 반환"""
        return self.driver.page_source if self.driver else None
    
    def execute_script(self, script: str, *args):
        """JavaScript 실행"""
        if self.driver:
            return self.driver.execute_script(script, *args)
        return None
    
    def js_click_element(self, selector: str, selector_type: str = "css") -> bool:
        """
        JavaScript로 요소 클릭 (마우스 이벤트 시뮬레이션)
        
        Args:
            selector: CSS 선택자 또는 XPath
            selector_type: "css" 또는 "xpath"
            
        Returns:
            성공 여부
        """
        if not self.driver:
            return False
        
        try:
            if selector_type == "xpath":
                script = f"""
                    var element = document.evaluate("{selector}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (element) {{
                        // 마우스 이벤트 시뮬레이션
                        var rect = element.getBoundingClientRect();
                        var centerX = rect.left + rect.width / 2;
                        var centerY = rect.top + rect.height / 2;
                        
                        var mouseoverEvent = new MouseEvent('mouseover', {{
                            bubbles: true, cancelable: true, view: window,
                            clientX: centerX, clientY: centerY
                        }});
                        var mousedownEvent = new MouseEvent('mousedown', {{
                            bubbles: true, cancelable: true, view: window,
                            clientX: centerX, clientY: centerY, button: 0
                        }});
                        var mouseupEvent = new MouseEvent('mouseup', {{
                            bubbles: true, cancelable: true, view: window,
                            clientX: centerX, clientY: centerY, button: 0
                        }});
                        var clickEvent = new MouseEvent('click', {{
                            bubbles: true, cancelable: true, view: window,
                            clientX: centerX, clientY: centerY, button: 0
                        }});
                        
                        element.dispatchEvent(mouseoverEvent);
                        element.dispatchEvent(mousedownEvent);
                        element.dispatchEvent(mouseupEvent);
                        element.dispatchEvent(clickEvent);
                        return true;
                    }}
                    return false;
                """
            else:
                script = f"""
                    var element = document.querySelector('{selector}');
                    if (element) {{
                        // 마우스 이벤트 시뮬레이션
                        var rect = element.getBoundingClientRect();
                        var centerX = rect.left + rect.width / 2;
                        var centerY = rect.top + rect.height / 2;
                        
                        var mouseoverEvent = new MouseEvent('mouseover', {{
                            bubbles: true, cancelable: true, view: window,
                            clientX: centerX, clientY: centerY
                        }});
                        var mousedownEvent = new MouseEvent('mousedown', {{
                            bubbles: true, cancelable: true, view: window,
                            clientX: centerX, clientY: centerY, button: 0
                        }});
                        var mouseupEvent = new MouseEvent('mouseup', {{
                            bubbles: true, cancelable: true, view: window,
                            clientX: centerX, clientY: centerY, button: 0
                        }});
                        var clickEvent = new MouseEvent('click', {{
                            bubbles: true, cancelable: true, view: window,
                            clientX: centerX, clientY: centerY, button: 0
                        }});
                        
                        element.dispatchEvent(mouseoverEvent);
                        element.dispatchEvent(mousedownEvent);
                        element.dispatchEvent(mouseupEvent);
                        element.dispatchEvent(clickEvent);
                        return true;
                    }}
                    return false;
                """
            result = self.driver.execute_script(script)
            if result:
                logger.debug(f"JS clicked element with mouse events: {selector}")
            return result
        except Exception as e:
            logger.error(f"JS click failed: {e}")
            return False
    
    def js_input_text(self, selector: str, text: str, selector_type: str = "css") -> bool:
        """
        JavaScript로 텍스트 입력
        
        Args:
            selector: CSS 선택자 또는 XPath
            text: 입력할 텍스트
            selector_type: "css" 또는 "xpath"
            
        Returns:
            성공 여부
        """
        if not self.driver:
            return False
        
        try:
            if selector_type == "xpath":
                script = f"""
                    var element = document.evaluate("{selector}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (element) {{
                        element.focus();
                        element.value = '{text}';
                        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                """
            else:
                script = f"""
                    var element = document.querySelector('{selector}');
                    if (element) {{
                        element.focus();
                        element.value = '{text}';
                        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                """
            result = self.driver.execute_script(script)
            if result:
                logger.debug(f"JS input text to: {selector}")
            return result
        except Exception as e:
            logger.error(f"JS input failed: {e}")
            return False
    
    def js_element_exists(self, selector: str, selector_type: str = "css") -> bool:
        """
        JavaScript로 요소 존재 여부 확인
        
        Args:
            selector: CSS 선택자 또는 XPath
            selector_type: "css" 또는 "xpath"
            
        Returns:
            존재 여부
        """
        if not self.driver:
            return False
        
        try:
            if selector_type == "xpath":
                script = f"""
                    var element = document.evaluate("{selector}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    return element !== null;
                """
            else:
                script = f"""
                    return document.querySelector('{selector}') !== null;
                """
            return self.driver.execute_script(script)
        except Exception as e:
            logger.error(f"JS element check failed: {e}")
            return False
    
    def js_wait_for_element(self, selector: str, timeout: int = 10, selector_type: str = "css") -> bool:
        """
        JavaScript로 요소가 나타날 때까지 대기
        
        Args:
            selector: CSS 선택자 또는 XPath
            timeout: 대기 시간 (초)
            selector_type: "css" 또는 "xpath"
            
        Returns:
            요소 발견 여부
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.js_element_exists(selector, selector_type):
                return True
            time.sleep(0.5)
        return False
    
    def js_get_element_text(self, selector: str, selector_type: str = "css") -> Optional[str]:
        """
        JavaScript로 요소 텍스트 가져오기
        
        Args:
            selector: CSS 선택자 또는 XPath
            selector_type: "css" 또는 "xpath"
            
        Returns:
            요소 텍스트 또는 None
        """
        if not self.driver:
            return None
        
        try:
            if selector_type == "xpath":
                script = f"""
                    var element = document.evaluate("{selector}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    return element ? element.textContent : null;
                """
            else:
                script = f"""
                    var element = document.querySelector('{selector}');
                    return element ? element.textContent : null;
                """
            return self.driver.execute_script(script)
        except Exception as e:
            logger.error(f"JS get text failed: {e}")
            return None
    
    def tiktok_login(self, email: str, password: str) -> dict:
        """
        TikTok 이메일 로그인 자동화 (JavaScript 기반)
        
        Args:
            email: 이메일 주소
            password: 비밀번호
            
        Returns:
            결과 딕셔너리 {
                'success': bool,
                'needs_verification': bool,
                'needs_captcha': bool,
                'message': str
            }
        """
        result = {
            'success': False,
            'needs_verification': False,
            'needs_captcha': False,
            'message': ''
        }
        
        if not self.driver:
            result['message'] = '브라우저가 시작되지 않음'
            return result
        
        try:
            # TikTok 이메일 로그인 페이지로 이동
            login_url = "https://www.tiktok.com/login/phone-or-email/email"
            logger.info(f"Navigating to: {login_url}")
            self.navigate_to(login_url)
            time.sleep(3)
            
            # 세션 유지 확인 (로그인 페이지가 아니면 이미 로그인됨)
            current_url = self.get_current_url()
            if '/login' not in current_url:
                result['success'] = True
                result['message'] = '이미 로그인되어 있음 (세션 유지)'
                logger.info("Already logged in (session maintained)")
                return result
            
            logger.info("Login required, starting automation...")
            
            # 이메일 입력 필드 대기 및 입력
            email_selectors = [
                'input[name="username"]',
                'input[placeholder*="이메일"]',
                'input[placeholder*="Email"]',
                'input[placeholder*="email"]',
                'input[type="text"]'
            ]
            
            email_entered = False
            for selector in email_selectors:
                if self.js_wait_for_element(selector, timeout=5):
                    time.sleep(0.5)
                    if self.js_input_text(selector, email):
                        email_entered = True
                        logger.info("Email entered successfully")
                        break
            
            if not email_entered:
                result['message'] = '이메일 입력 필드를 찾을 수 없음'
                return result
            
            time.sleep(1)
            
            # 비밀번호 입력 필드 찾기 및 입력
            password_selectors = [
                'input[type="password"]',
                'input[placeholder*="비밀번호"]',
                'input[placeholder*="Password"]',
                'input[placeholder*="password"]'
            ]
            
            password_entered = False
            for selector in password_selectors:
                if self.js_wait_for_element(selector, timeout=5):
                    time.sleep(0.5)
                    if self.js_input_text(selector, password):
                        password_entered = True
                        logger.info("Password entered successfully")
                        break
            
            if not password_entered:
                result['message'] = '비밀번호 입력 필드를 찾을 수 없음'
                return result
            
            time.sleep(1)
            
            # 로그인 버튼 클릭 (JavaScript 마우스 이벤트 시뮬레이션)
            login_button_script = """
                // 로그인 버튼 찾기 (다양한 선택자 시도)
                var button = null;
                
                // 1. type="submit" 버튼
                button = document.querySelector('button[type="submit"]');
                
                // 2. data-e2e 속성
                if (!button) {
                    button = document.querySelector('button[data-e2e="login-button"]');
                }
                
                // 3. 텍스트로 찾기
                if (!button) {
                    var buttons = document.querySelectorAll('button');
                    for (var btn of buttons) {
                        var text = btn.textContent.trim();
                        if (text === '로그인' || text === 'Log in' || text === 'Login') {
                            button = btn;
                            break;
                        }
                    }
                }
                
                if (button) {
                    // 마우스 이벤트 시뮬레이션
                    var rect = button.getBoundingClientRect();
                    var centerX = rect.left + rect.width / 2;
                    var centerY = rect.top + rect.height / 2;
                    
                    var mouseoverEvent = new MouseEvent('mouseover', {
                        bubbles: true, cancelable: true, view: window,
                        clientX: centerX, clientY: centerY
                    });
                    var mousedownEvent = new MouseEvent('mousedown', {
                        bubbles: true, cancelable: true, view: window,
                        clientX: centerX, clientY: centerY, button: 0
                    });
                    var mouseupEvent = new MouseEvent('mouseup', {
                        bubbles: true, cancelable: true, view: window,
                        clientX: centerX, clientY: centerY, button: 0
                    });
                    var clickEvent = new MouseEvent('click', {
                        bubbles: true, cancelable: true, view: window,
                        clientX: centerX, clientY: centerY, button: 0
                    });
                    
                    // 포커스 및 이벤트 발생
                    button.focus();
                    button.dispatchEvent(mouseoverEvent);
                    button.dispatchEvent(mousedownEvent);
                    button.dispatchEvent(mouseupEvent);
                    button.dispatchEvent(clickEvent);
                    
                    // 추가로 직접 클릭도 시도
                    button.click();
                    
                    return true;
                }
                return false;
            """
            
            login_clicked = self.driver.execute_script(login_button_script)
            
            if not login_clicked:
                result['message'] = '로그인 버튼을 찾을 수 없음'
                return result
            
            logger.info("Login button clicked, waiting for response...")
            time.sleep(3)
            
            # 로그인 결과 확인
            current_url = self.get_current_url()
            
            # 인증번호 입력창 확인
            verification_selectors = [
                'input[placeholder*="인증"]',
                'input[placeholder*="코드"]',
                'input[placeholder*="code"]',
                'input[placeholder*="verification"]'
            ]
            
            for selector in verification_selectors:
                if self.js_element_exists(selector):
                    result['needs_verification'] = True
                    result['message'] = '이메일 인증번호 입력 필요'
                    logger.info("Email verification required")
                    return result
            
            # 캡챠 확인
            captcha_indicators = [
                'iframe[src*="captcha"]',
                '[class*="captcha"]',
                '[id*="captcha"]',
                'div[class*="Captcha"]'
            ]
            
            for selector in captcha_indicators:
                if self.js_element_exists(selector):
                    result['needs_captcha'] = True
                    result['message'] = '캡챠 인증 필요'
                    logger.info("Captcha verification required")
                    return result
            
            # 로그인 성공 확인
            if '/login' not in current_url:
                result['success'] = True
                result['message'] = '로그인 성공'
                logger.info("Login successful!")
                return result
            
            # 에러 메시지 확인
            error_selectors = [
                '[class*="error"]',
                '[class*="Error"]',
                'div[class*="message"]'
            ]
            
            for selector in error_selectors:
                error_text = self.js_get_element_text(selector)
                if error_text:
                    result['message'] = f'로그인 오류: {error_text[:100]}'
                    return result
            
            result['message'] = '로그인 진행 중...'
            return result
            
        except Exception as e:
            logger.error(f"Login automation error: {e}")
            result['message'] = f'오류 발생: {str(e)}'
            return result
    
    def tiktok_input_verification_code(self, code: str) -> bool:
        """
        TikTok 인증번호 입력 (JavaScript 기반)
        
        Args:
            code: 6자리 인증번호
            
        Returns:
            성공 여부
        """
        if not self.driver:
            return False
        
        try:
            # 인증번호 입력 필드 찾기
            verification_selectors = [
                'input[placeholder*="인증"]',
                'input[placeholder*="코드"]',
                'input[placeholder*="code"]',
                'input[placeholder*="verification"]',
                'input[maxlength="6"]',
                'input[type="tel"]'
            ]
            
            for selector in verification_selectors:
                if self.js_wait_for_element(selector, timeout=5):
                    if self.js_input_text(selector, code):
                        logger.info(f"Verification code entered: {code[:2]}****")
                        time.sleep(1)
                        
                        # 확인/인증 버튼 클릭
                        submit_script = """
                            var buttons = document.querySelectorAll('button');
                            for (var btn of buttons) {
                                var text = btn.textContent.toLowerCase();
                                if (text.includes('인증') || text.includes('확인') || 
                                    text.includes('verify') || text.includes('submit') ||
                                    text.includes('제출')) {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        """
                        self.driver.execute_script(submit_script)
                        return True
            
            logger.warning("Verification code input field not found")
            return False
            
        except Exception as e:
            logger.error(f"Verification code input error: {e}")
            return False
    
    def tiktok_check_login_status(self) -> bool:
        """
        TikTok 로그인 상태 확인
        
        Returns:
            로그인 여부
        """
        if not self.driver:
            return False
        
        current_url = self.get_current_url()
        if current_url and '/login' not in current_url:
            # 추가 확인: 프로필 아이콘 등 로그인 지표 확인
            logged_in_indicators = [
                '[data-e2e="profile-icon"]',
                '[class*="avatar"]',
                '[class*="Avatar"]'
            ]
            
            for selector in logged_in_indicators:
                if self.js_element_exists(selector):
                    return True
            
            # URL만으로 판단
            return True
        
        return False

    def refresh(self):
        """페이지 새로고침"""
        if self.driver:
            self.driver.refresh()
    
    def close_browser(self):
        """브라우저 종료"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def __enter__(self):
        """Context manager entry"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_browser()


# Convenience function to create browser instance
def create_browser() -> BrowserManager:
    """Create and return a BrowserManager instance"""
    return BrowserManager()
