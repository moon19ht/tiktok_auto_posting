"""
TikTok Auto Posting - Console UI Module

대화형 콘솔 인터페이스
"""

import os
import sys
import time
from typing import Optional, List, Callable
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.box import ROUNDED, DOUBLE
    from rich.live import Live
    from rich.layout import Layout
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from .config import config
from .logger import logger
from .tiktok_login import EmailVerificationHandler


class ConsoleUI:
    """
    대화형 콘솔 UI 클래스
    
    Rich 라이브러리를 사용한 향상된 터미널 UI 제공
    Rich가 없는 경우 기본 터미널 출력 사용
    """
    
    # 색상 테마
    COLORS = {
        'primary': 'cyan',
        'secondary': 'magenta',
        'success': 'green',
        'warning': 'yellow',
        'error': 'red',
        'info': 'blue',
        'muted': 'dim white',
    }
    
    def __init__(self):
        """ConsoleUI 초기화"""
        self.console = Console() if HAS_RICH else None
        self._width = 70
        
    def clear_screen(self):
        """화면 지우기"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """메인 배너 출력"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ████████╗██╗██╗  ██╗████████╗ ██████╗ ██╗  ██╗                ║
║   ╚══██╔══╝██║██║ ██╔╝╚══██╔══╝██╔═══██╗██║ ██╔╝                ║
║      ██║   ██║█████╔╝    ██║   ██║   ██║█████╔╝                 ║
║      ██║   ██║██╔═██╗    ██║   ██║   ██║██╔═██╗                 ║
║      ██║   ██║██║  ██╗   ██║   ╚██████╔╝██║  ██╗                ║
║      ╚═╝   ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝                ║
║                                                                  ║
║            █████╗ ██╗   ██╗████████╗ ██████╗                    ║
║           ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗                   ║
║           ███████║██║   ██║   ██║   ██║   ██║                   ║
║           ██╔══██║██║   ██║   ██║   ██║   ██║                   ║
║           ██║  ██║╚██████╔╝   ██║   ╚██████╔╝                   ║
║           ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝                    ║
║                                                                  ║
║          ██████╗  ██████╗ ███████╗████████╗██╗███╗   ██╗        ║
║          ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝██║████╗  ██║        ║
║          ██████╔╝██║   ██║███████╗   ██║   ██║██╔██╗ ██║        ║
║          ██╔═══╝ ██║   ██║╚════██║   ██║   ██║██║╚██╗██║        ║
║          ██║     ╚██████╔╝███████║   ██║   ██║██║ ╚████║        ║
║          ╚═╝      ╚═════╝ ╚══════╝   ╚═╝   ╚═╝╚═╝  ╚═══╝        ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║       🎬 TikTok Video Auto Upload Automation System 🎬           ║
║                                                                  ║
║   • WSL Optimized        • Chrome DevTools MCP Enabled          ║
║   • Visual Upload        • Login Session Persistence            ║
╚══════════════════════════════════════════════════════════════════╝
"""
        if HAS_RICH:
            self.console.print(banner, style="cyan")
        else:
            print(banner)
    
    def print_header(self, title: str, subtitle: str = None):
        """헤더 출력"""
        if HAS_RICH:
            header_text = Text(title, style="bold cyan")
            if subtitle:
                header_text.append(f"\n{subtitle}", style="dim")
            panel = Panel(
                header_text,
                box=DOUBLE,
                border_style="cyan",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print("\n" + "="*self._width)
            print(f"  {title}")
            if subtitle:
                print(f"  {subtitle}")
            print("="*self._width)
    
    def print_menu(self, options: List[tuple], title: str = "메뉴 선택"):
        """메뉴 출력"""
        if HAS_RICH:
            table = Table(
                show_header=False,
                box=ROUNDED,
                border_style="cyan",
                padding=(0, 2),
                title=f"[bold cyan]{title}[/]",
                title_justify="left"
            )
            table.add_column("번호", style="bold yellow", width=6)
            table.add_column("옵션", style="white")
            table.add_column("설명", style="dim")
            
            for num, name, desc in options:
                table.add_row(f"[{num}]", name, desc)
            
            self.console.print()
            self.console.print(table)
            self.console.print()
        else:
            print(f"\n  {title}")
            print("-" * self._width)
            for num, name, desc in options:
                print(f"  [{num}] {name:<20} - {desc}")
            print()
    
    def print_status(self, message: str, status: str = "info"):
        """상태 메시지 출력"""
        icons = {
            "success": "✓",
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ",
            "loading": "⋯",
        }
        
        colors = {
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "info": "blue",
            "loading": "cyan",
        }
        
        icon = icons.get(status, "•")
        color = colors.get(status, "white")
        
        if HAS_RICH:
            self.console.print(f"  [{color}]{icon}[/] {message}")
        else:
            print(f"  {icon} {message}")
    
    def print_success(self, message: str):
        """성공 메시지 출력"""
        self.print_status(message, "success")
    
    def print_error(self, message: str):
        """에러 메시지 출력"""
        self.print_status(message, "error")
    
    def print_warning(self, message: str):
        """경고 메시지 출력"""
        self.print_status(message, "warning")
    
    def print_info(self, message: str):
        """정보 메시지 출력"""
        self.print_status(message, "info")
    
    def print_table(self, title: str, headers: List[str], rows: List[List[str]]):
        """테이블 출력"""
        if HAS_RICH:
            table = Table(
                title=f"[bold]{title}[/]",
                box=ROUNDED,
                border_style="cyan",
                header_style="bold cyan"
            )
            
            for header in headers:
                table.add_column(header)
            
            for row in rows:
                table.add_row(*row)
            
            self.console.print()
            self.console.print(table)
            self.console.print()
        else:
            print(f"\n  {title}")
            print("-" * self._width)
            
            # 헤더
            header_str = " | ".join(f"{h:<15}" for h in headers)
            print(f"  {header_str}")
            print("  " + "-" * len(header_str))
            
            # 데이터
            for row in rows:
                row_str = " | ".join(f"{str(cell):<15}" for cell in row)
                print(f"  {row_str}")
            print()
    
    def prompt(self, message: str, default: str = None) -> str:
        """사용자 입력 받기"""
        if HAS_RICH:
            return Prompt.ask(f"  [cyan]>[/] {message}", default=default or "")
        else:
            prompt_text = f"  > {message}"
            if default:
                prompt_text += f" [{default}]"
            prompt_text += ": "
            response = input(prompt_text).strip()
            return response if response else (default or "")
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """확인 질문"""
        if HAS_RICH:
            return Confirm.ask(f"  [cyan]?[/] {message}", default=default)
        else:
            yn = "[Y/n]" if default else "[y/N]"
            response = input(f"  ? {message} {yn}: ").strip().lower()
            if not response:
                return default
            return response in ('y', 'yes', '예', 'ㅇ')
    
    def select_option(self, message: str = "옵션을 선택하세요") -> str:
        """옵션 선택"""
        return self.prompt(message)
    
    def show_progress(self, description: str, total: int = 100):
        """진행률 표시 컨텍스트 매니저"""
        if HAS_RICH:
            return Progress(
                SpinnerColumn(),
                TextColumn("[bold cyan]{task.description}"),
                BarColumn(bar_width=40),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            )
        else:
            return DummyProgress()
    
    def show_spinner(self, message: str):
        """로딩 스피너 표시"""
        if HAS_RICH:
            with self.console.status(f"[cyan]{message}[/]", spinner="dots"):
                pass
    
    def print_video_list(self, videos: List[Path], title: str = "비디오 목록"):
        """비디오 목록 출력"""
        if not videos:
            self.print_warning("비디오 파일이 없습니다.")
            return
        
        rows = []
        for i, video in enumerate(videos, 1):
            size_mb = video.stat().st_size / (1024 * 1024)
            rows.append([
                str(i),
                video.name[:30] + "..." if len(video.name) > 30 else video.name,
                f"{size_mb:.1f} MB"
            ])
        
        self.print_table(title, ["#", "파일명", "크기"], rows)
    
    def print_upload_result(self, results: dict):
        """업로드 결과 출력"""
        successful = sum(1 for v in results.values() if v)
        failed = len(results) - successful
        
        if HAS_RICH:
            result_panel = Panel(
                f"""
[bold green]성공: {successful}[/]  |  [bold red]실패: {failed}[/]  |  [bold]총: {len(results)}[/]
                """,
                title="[bold cyan]업로드 결과[/]",
                border_style="cyan",
                box=ROUNDED
            )
            self.console.print(result_panel)
        else:
            print("\n" + "="*self._width)
            print(f"  업로드 결과: 성공 {successful} / 실패 {failed} / 총 {len(results)}")
            print("="*self._width)
    
    def print_config_info(self):
        """설정 정보 출력"""
        info = [
            ["Chrome 경로", str(config.CHROME_BINARY_PATH)[:40]],
            ["디버그 포트", str(config.CHROME_DEBUG_PORT)],
            ["비디오 디렉토리", str(config.VIDEO_DIRECTORY)[:40]],
            ["기본 해시태그", config.DEFAULT_HASHTAGS[:30]],
            ["로그 레벨", config.LOG_LEVEL],
        ]
        
        self.print_table("현재 설정", ["항목", "값"], info)
    
    def print_separator(self, char: str = "─"):
        """구분선 출력"""
        if HAS_RICH:
            self.console.print(char * self._width, style="dim")
        else:
            print(char * self._width)
    
    def wait_for_key(self, message: str = "계속하려면 Enter를 누르세요..."):
        """키 입력 대기"""
        if HAS_RICH:
            self.console.print(f"\n  [dim]{message}[/]")
        else:
            print(f"\n  {message}")
        input()


class DummyProgress:
    """Rich가 없을 때 사용하는 더미 Progress 클래스"""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def add_task(self, description, total=100):
        print(f"  ⋯ {description}")
        return 0
    
    def update(self, task_id, advance=1):
        pass


class InteractiveConsole:
    """
    대화형 콘솔 메인 클래스
    
    메뉴 기반 사용자 인터페이스 제공
    """
    
    def __init__(self):
        """InteractiveConsole 초기화"""
        self.ui = ConsoleUI()
        self.running = True
        
        # 지연 import (순환 참조 방지)
        self._browser = None
        self._uploader = None
        self._video_manager = None
    
    @property
    def browser(self):
        if self._browser is None:
            from .browser import BrowserManager
            self._browser = BrowserManager()
        return self._browser
    
    @property
    def uploader(self):
        if self._uploader is None:
            from .tiktok_uploader import TikTokUploader
            self._uploader = TikTokUploader()
        return self._uploader
    
    @property
    def video_manager(self):
        if self._video_manager is None:
            from .video_manager import VideoManager
            self._video_manager = VideoManager()
        return self._video_manager
    
    def run(self):
        """메인 실행 루프"""
        self.ui.clear_screen()
        self.ui.print_banner()
        
        time.sleep(1)
        
        while self.running:
            self.show_main_menu()
    
    def show_main_menu(self):
        """메인 메뉴 표시"""
        menu_options = [
            ("1", "🔑 TikTok 로그인", "브라우저에서 TikTok 로그인"),
            ("2", "🎬 단일 비디오 업로드", "하나의 비디오 파일 업로드"),
            ("3", "📁 일괄 업로드", "대기 중인 모든 비디오 업로드"),
            ("4", "🧪 브라우저 테스트", "Chrome 연결 테스트"),
            ("5", "📋 비디오 목록", "업로드 대기 중인 비디오 확인"),
            ("6", "📊 업로드 히스토리", "업로드 완료 내역 확인"),
            ("7", "⚙️  설정 확인", "현재 설정 정보 확인"),
            ("8", "🔄 히스토리 초기화", "업로드 기록 초기화"),
            ("0", "🚪 종료", "프로그램 종료"),
        ]
        
        self.ui.print_menu(menu_options, "🎯 메인 메뉴")
        
        choice = self.ui.select_option("선택")
        
        actions = {
            "1": self.login_tiktok,
            "2": self.upload_single_video,
            "3": self.batch_upload,
            "4": self.test_browser,
            "5": self.show_video_list,
            "6": self.show_upload_history,
            "7": self.show_config,
            "8": self.clear_history,
            "0": self.exit_program,
            "q": self.exit_program,
            "quit": self.exit_program,
        }
        
        action = actions.get(choice.lower())
        if action:
            self.ui.clear_screen()
            action()
        else:
            self.ui.print_error("잘못된 선택입니다.")
            time.sleep(1)
    
    def upload_single_video(self):
        """단일 비디오 업로드"""
        self.ui.print_header("🎬 단일 비디오 업로드", "하나의 비디오 파일을 TikTok에 업로드합니다")
        
        # 비디오 파일 경로 입력
        video_path = self.ui.prompt("비디오 파일 경로")
        
        if not video_path:
            self.ui.print_error("비디오 경로가 필요합니다.")
            self.ui.wait_for_key()
            return
        
        video_path = Path(video_path).expanduser()
        
        if not video_path.exists():
            self.ui.print_error(f"파일을 찾을 수 없습니다: {video_path}")
            self.ui.wait_for_key()
            return
        
        # 캡션 입력
        caption = self.ui.prompt("캡션 (선택사항)")
        
        # 해시태그 입력
        hashtags = self.ui.prompt("해시태그 (공백으로 구분, 선택사항)", config.DEFAULT_HASHTAGS)
        
        # 확인
        self.ui.print_separator()
        self.ui.print_info(f"파일: {video_path.name}")
        self.ui.print_info(f"캡션: {caption or '(없음)'}")
        self.ui.print_info(f"해시태그: {hashtags}")
        self.ui.print_separator()
        
        if not self.ui.confirm("업로드를 시작하시겠습니까?"):
            self.ui.print_warning("취소되었습니다.")
            self.ui.wait_for_key()
            return
        
        # 업로드 실행
        self.ui.print_info("업로드를 시작합니다...")
        
        from .tiktok_uploader import VideoInfo
        
        hashtag_list = hashtags.split() if hashtags else None
        video_info = VideoInfo(
            file_path=str(video_path),
            description=caption,
            hashtags=hashtag_list
        )
        
        try:
            if self.uploader.start():
                success = self.uploader.upload_and_post(video_info)
                
                if success:
                    self.video_manager.mark_as_uploaded(video_path)
                    self.ui.print_success("업로드가 완료되었습니다!")
                else:
                    self.ui.print_error("업로드에 실패했습니다.")
            else:
                self.ui.print_error("브라우저를 시작할 수 없습니다.")
        except Exception as e:
            self.ui.print_error(f"오류 발생: {e}")
        finally:
            self.uploader.close()
            self._uploader = None
        
        self.ui.wait_for_key()
    
    def batch_upload(self):
        """일괄 업로드"""
        self.ui.print_header("📁 일괄 업로드", "대기 중인 모든 비디오를 업로드합니다")
        
        pending = self.video_manager.get_pending_videos()
        
        if not pending:
            self.ui.print_warning("업로드할 비디오가 없습니다.")
            self.ui.print_info(f"비디오 디렉토리: {config.VIDEO_DIRECTORY}")
            self.ui.wait_for_key()
            return
        
        self.ui.print_video_list(pending, f"업로드 대기 중인 비디오 ({len(pending)}개)")
        
        if not self.ui.confirm(f"{len(pending)}개의 비디오를 업로드하시겠습니까?"):
            self.ui.print_warning("취소되었습니다.")
            self.ui.wait_for_key()
            return
        
        # 해시태그 입력
        hashtags = self.ui.prompt("공통 해시태그 (선택사항)", config.DEFAULT_HASHTAGS)
        hashtag_list = hashtags.split() if hashtags else None
        
        # 업로드 실행
        self.ui.print_info("일괄 업로드를 시작합니다...")
        
        video_info_list = self.video_manager.get_video_info_list(pending, hashtags=hashtag_list)
        
        try:
            if self.uploader.start():
                results = self.uploader.batch_upload(video_info_list)
                
                for file_path, success in results.items():
                    if success:
                        self.video_manager.mark_as_uploaded(Path(file_path))
                
                self.ui.print_upload_result(results)
            else:
                self.ui.print_error("브라우저를 시작할 수 없습니다.")
        except Exception as e:
            self.ui.print_error(f"오류 발생: {e}")
        finally:
            self.uploader.close()
            self._uploader = None
        
        self.ui.wait_for_key()
    
    def login_tiktok(self):
        """TikTok 로그인 (JavaScript 자동화)"""
        self.ui.print_header("🔑 TikTok 로그인", "JavaScript를 사용하여 자동으로 TikTok에 로그인합니다")
        
        from .tiktok_login import TikTokLoginMCP, EmailVerificationHandler
        
        login_helper = TikTokLoginMCP()
        
        # 자격 증명 확인
        if not login_helper.has_credentials():
            self.ui.print_error("로그인 자격 증명이 설정되지 않았습니다.")
            self.ui.print_info("'.env' 파일에 TIKTOK_EMAIL과 TIKTOK_PASSWORD를 설정해주세요.")
            self.ui.print_separator()
            self.ui.print_info("예시:")
            self.ui.print_info("  TIKTOK_EMAIL=your_email@example.com")
            self.ui.print_info("  TIKTOK_PASSWORD=your_password")
            self.ui.wait_for_key()
            return
        
        email, password = login_helper.get_credentials()
        self.ui.print_info(f"로그인 이메일: {email[:3]}***{email[-10:]}")
        self.ui.print_separator()
        
        self.ui.print_info("자동 로그인 프로세스:")
        self.ui.print_info("  1. TikTok 이메일 로그인 페이지 접속")
        self.ui.print_info("  2. 세션 유지 확인 (메인 페이지로 이동 시 이미 로그인됨)")
        self.ui.print_info("  3. 이메일 자동 입력")
        self.ui.print_info("  4. 비밀번호 자동 입력")
        self.ui.print_info("  5. 로그인 버튼 자동 클릭")
        self.ui.print_info("  6. 📧 이메일 인증번호 입력 (필요시 - 10분 대기)")
        self.ui.print_info("  7. 🤖 캡챠 인증 대기 (필요시 - 5분 대기)")
        self.ui.print_separator()
        
        if not self.ui.confirm("로그인을 시작하시겠습니까?"):
            self.ui.print_warning("취소되었습니다.")
            self.ui.wait_for_key()
            return
        
        verification_handler = EmailVerificationHandler(timeout=600)  # 10분 대기
        
        try:
            self.ui.print_info("브라우저 시작 중...")
            
            if self.browser.start_browser():
                self.ui.print_success("브라우저 시작 성공")
                self.ui.print_separator()
                
                # TikTok 자동 로그인 실행
                self.ui.print_info("🚀 자동 로그인 시작...")
                result = self.browser.tiktok_login(email, password)
                
                if result['success']:
                    self.ui.print_success(f"✅ {result['message']}")
                    self.ui.print_separator()
                    
                    if self.ui.confirm("업로드 페이지로 이동하시겠습니까?"):
                        self.browser.navigate_to(config.TIKTOK_UPLOAD_URL)
                        self.ui.print_success("업로드 페이지로 이동 완료!")
                
                elif result['needs_verification']:
                    # 이메일 인증번호 입력 필요
                    self.ui.print_warning(f"📧 {result['message']}")
                    self.ui.print_separator()
                    self.ui.print_info("이메일에서 6자리 인증번호를 확인하세요.")
                    self.ui.print_info("대기 시간: 10분 (600초)")
                    self.ui.print_separator()
                    
                    verification_code = verification_handler.wait_and_get_code()
                    
                    if verification_code:
                        self.ui.print_info(f"인증번호 입력 중: {verification_code}")
                        
                        if self.browser.tiktok_input_verification_code(verification_code):
                            self.ui.print_success("인증번호 입력 완료!")
                            time.sleep(3)
                            
                            # 캡챠 확인
                            current_url = self.browser.get_current_url()
                            if self.browser.js_element_exists('[class*="captcha"]') or \
                               self.browser.js_element_exists('iframe[src*="captcha"]'):
                                self._handle_captcha()
                            
                            # 로그인 완료 확인
                            time.sleep(2)
                            if self.browser.tiktok_check_login_status():
                                self.ui.print_success("🎉 로그인 완료!")
                                
                                if self.ui.confirm("업로드 페이지로 이동하시겠습니까?"):
                                    self.browser.navigate_to(config.TIKTOK_UPLOAD_URL)
                                    self.ui.print_success("업로드 페이지로 이동 완료!")
                            else:
                                self.ui.print_warning("로그인 상태를 확인할 수 없습니다.")
                        else:
                            self.ui.print_error("인증번호 입력 실패")
                    else:
                        self.ui.print_warning("인증번호 입력이 취소되었거나 시간 초과되었습니다.")
                
                elif result['needs_captcha']:
                    # 캡챠 인증 필요
                    self.ui.print_warning(f"🤖 {result['message']}")
                    self._handle_captcha()
                    
                    # 로그인 완료 확인
                    time.sleep(2)
                    if self.browser.tiktok_check_login_status():
                        self.ui.print_success("🎉 로그인 완료!")
                        
                        if self.ui.confirm("업로드 페이지로 이동하시겠습니까?"):
                            self.browser.navigate_to(config.TIKTOK_UPLOAD_URL)
                            self.ui.print_success("업로드 페이지로 이동 완료!")
                    else:
                        self.ui.print_warning("로그인 상태를 확인할 수 없습니다.")
                
                else:
                    self.ui.print_error(f"❌ {result['message']}")
            else:
                self.ui.print_error("브라우저 시작 실패")
        except Exception as e:
            self.ui.print_error(f"오류 발생: {e}")
            import traceback
            traceback.print_exc()
        
        # 브라우저 유지 여부 확인
        self.ui.print_separator()
        if not self.ui.confirm("브라우저를 닫으시겠습니까?", default=False):
            self.ui.print_info("브라우저를 유지합니다. 메인 메뉴로 돌아갑니다.")
        else:
            self.browser.close_browser()
            self._browser = None
    
    def _handle_captcha(self):
        """캡챠 인증 대기 처리"""
        self.ui.print_warning("캡챠 인증 대기 모드 (5분 대기)")
        self.ui.print_info("브라우저에서 캡챠를 직접 완료해주세요.")
        self.ui.print_separator()
        
        captcha_timeout = 300  # 5분
        start_time = time.time()
        
        while time.time() - start_time < captcha_timeout:
            remaining = int(captcha_timeout - (time.time() - start_time))
            
            # 캡챠가 완료되었는지 자동 확인
            if self.browser.tiktok_check_login_status():
                self.ui.print_success("캡챠 인증 완료 감지!")
                return
            
            try:
                response = input(f"  [{remaining}초 남음] 캡챠 완료 후 'done' 입력 (취소: q): ").strip().lower()
                
                if response == 'done':
                    self.ui.print_success("캡챠 인증 완료!")
                    return
                elif response == 'q':
                    self.ui.print_warning("캡챠 인증 취소됨")
                    return
            except KeyboardInterrupt:
                self.ui.print_warning("캡챠 인증 취소됨")
                return
            
            time.sleep(1)
        
        self.ui.print_warning("캡챠 대기 시간 초과")
    
    def test_browser(self):
        """브라우저 테스트"""
        self.ui.print_header("🧪 브라우저 테스트", "Chrome 연결 상태를 확인합니다")
        
        try:
            self.ui.print_info("Chrome 브라우저를 시작하는 중...")
            
            if self.browser.start_browser():
                self.ui.print_success("브라우저 시작 성공")
                
                self.ui.print_info("Google로 이동 중...")
                if self.browser.navigate_to("https://www.google.com"):
                    self.ui.print_success("페이지 이동 성공")
                
                self.ui.print_success(f"현재 URL: {self.browser.get_current_url()}")
                self.ui.print_success(f"DevTools 포트: {config.CHROME_DEBUG_PORT}")
                
                self.ui.print_separator()
                self.ui.print_success("모든 테스트 통과!")
            else:
                self.ui.print_error("브라우저 시작 실패")
        except Exception as e:
            self.ui.print_error(f"오류 발생: {e}")
        finally:
            self.ui.wait_for_key("브라우저를 닫으려면 Enter를 누르세요...")
            self.browser.close_browser()
            self._browser = None
    
    def show_video_list(self):
        """비디오 목록 표시"""
        self.ui.print_header("📋 비디오 목록", f"디렉토리: {config.VIDEO_DIRECTORY}")
        
        pending = self.video_manager.get_pending_videos()
        self.ui.print_video_list(pending, "업로드 대기 중")
        
        self.ui.wait_for_key()
    
    def show_upload_history(self):
        """업로드 히스토리 표시"""
        self.ui.print_header("📊 업로드 히스토리", "업로드 완료된 비디오 내역")
        
        history = self.video_manager.get_upload_history()
        
        if not history:
            self.ui.print_warning("업로드 히스토리가 없습니다.")
        else:
            rows = []
            for i, meta in enumerate(history, 1):
                rows.append([
                    str(i),
                    meta.file_name[:25] + "..." if len(meta.file_name) > 25 else meta.file_name,
                    meta.upload_time[:16] if meta.upload_time else "N/A"
                ])
            
            self.ui.print_table(
                f"업로드 완료 ({len(history)}개)",
                ["#", "파일명", "업로드 시간"],
                rows
            )
        
        self.ui.wait_for_key()
    
    def show_config(self):
        """설정 정보 표시"""
        self.ui.print_header("⚙️ 설정 정보", "현재 프로그램 설정")
        self.ui.print_config_info()
        self.ui.wait_for_key()
    
    def clear_history(self):
        """히스토리 초기화"""
        self.ui.print_header("🔄 히스토리 초기화", "업로드 기록을 초기화합니다")
        
        if self.ui.confirm("정말로 업로드 히스토리를 초기화하시겠습니까?", default=False):
            self.video_manager.clear_upload_history()
            self.ui.print_success("히스토리가 초기화되었습니다.")
        else:
            self.ui.print_warning("취소되었습니다.")
        
        self.ui.wait_for_key()
    
    def exit_program(self):
        """프로그램 종료"""
        if self.ui.confirm("정말로 종료하시겠습니까?"):
            self.ui.print_info("프로그램을 종료합니다. 감사합니다! 👋")
            self.running = False
        

def run_interactive_console():
    """대화형 콘솔 실행"""
    console = InteractiveConsole()
    console.run()
