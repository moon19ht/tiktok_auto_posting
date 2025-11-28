"""
TikTok Auto Posting - TikTok Login Module

Chrome DevTools MCP를 활용한 TikTok 자동 로그인 모듈
"""

import time
from typing import Optional, Tuple

from .config import config
from .logger import logger


class TikTokLoginMCP:
    """
    Chrome DevTools MCP를 활용한 TikTok 로그인 클래스
    
    MCP 도구를 통해 로그인 프로세스 자동화:
    1. TikTok 이메일 로그인 페이지 직접 접속
    2. 세션 유지 확인 (메인 페이지로 리다이렉트 시 이미 로그인됨)
    3. 이메일 입력 필드 클릭 → 이메일 입력
    4. 비밀번호 입력 필드 클릭 → 비밀번호 입력
    5. 로그인 버튼 클릭
    6. (필요시) 이메일 인증번호 입력 (10분 대기)
    7. (필요시) 캡챠 인증 대기 (5분 대기)
    """
    
    # 인증번호 대기 시간 (초) - 10분
    VERIFICATION_TIMEOUT = 600
    
    # 캡챠 대기 시간 (초) - 5분
    CAPTCHA_TIMEOUT = 300
    
    def __init__(self):
        """TikTokLoginMCP 초기화"""
        self.email = config.TIKTOK_EMAIL
        self.password = config.TIKTOK_PASSWORD
        self._is_logged_in = False
        self._verification_code = None
    
    def get_credentials(self) -> Tuple[str, str]:
        """
        로그인 자격 증명 반환
        
        Returns:
            (email, password) 튜플
        """
        return self.email, self.password
    
    def has_credentials(self) -> bool:
        """
        자격 증명이 설정되어 있는지 확인
        
        Returns:
            자격 증명 설정 여부
        """
        return bool(self.email and self.password and 
                   self.email != 'your_email@example.com' and
                   self.password != 'your_password')
    
    def prompt_verification_code(self, timeout: int = None) -> Optional[str]:
        """
        콘솔에서 이메일 인증번호 입력 받기
        
        Args:
            timeout: 대기 시간 (초), 기본값은 VERIFICATION_TIMEOUT
            
        Returns:
            입력받은 인증번호 또는 None
        """
        timeout = timeout or self.VERIFICATION_TIMEOUT
        
        print("\n" + "="*60)
        print("  📧 이메일 인증번호 입력 필요")
        print("="*60)
        print(f"\n  이메일로 전송된 6자리 인증번호를 입력해주세요.")
        print(f"  이메일: {self.email}")
        print(f"  대기 시간: {timeout}초")
        print("\n  인증번호가 오지 않으면 스팸함을 확인해주세요.")
        print("="*60)
        
        try:
            # 타임아웃 없이 입력 대기 (사용자가 직접 입력)
            code = input("\n  > 인증번호 (6자리): ").strip()
            
            if code and len(code) == 6 and code.isdigit():
                self._verification_code = code
                logger.info(f"Verification code entered: {code[:2]}****")
                return code
            else:
                logger.warning("Invalid verification code format")
                print("  ⚠️ 올바른 6자리 숫자를 입력해주세요.")
                return None
                
        except KeyboardInterrupt:
            logger.info("Verification code input cancelled")
            print("\n  취소되었습니다.")
            return None
    
    def get_verification_code(self) -> Optional[str]:
        """저장된 인증번호 반환"""
        return self._verification_code
    
    def clear_verification_code(self):
        """인증번호 초기화"""
        self._verification_code = None
    
    def get_login_instructions(self) -> str:
        """
        MCP를 통한 로그인 절차 안내 반환 (클릭 기반)
        
        Returns:
            로그인 절차 설명 문자열
        """
        return """
╔══════════════════════════════════════════════════════════════════╗
║         TikTok 자동 로그인 프로세스 (MCP - 클릭 기반)             ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1단계: TikTok 이메일 로그인 페이지 직접 접속                    ║
║     - https://www.tiktok.com/login/phone-or-email/email         ║
║     - ⭐ 메인 페이지로 리다이렉트 시 → 세션 유지됨 (로그인 완료) ║
║                                                                  ║
║  2단계: 이메일 입력 (클릭 후 키보드 입력)                        ║
║     - 이메일 입력 필드 클릭 → 키보드로 이메일 입력               ║
║                                                                  ║
║  3단계: 비밀번호 입력 (클릭 후 키보드 입력)                      ║
║     - 비밀번호 입력 필드 클릭 → 키보드로 비밀번호 입력           ║
║                                                                  ║
║  4단계: 로그인 완료 (클릭)                                       ║
║     - "로그인" 버튼 클릭                                         ║
║     - 로그인 성공 확인                                           ║
║                                                                  ║
║  5단계: 이메일 인증 (필요시 - 클릭 후 키보드 입력)               ║
║     - 인증번호 입력 필드 클릭 → 키보드로 인증번호 입력           ║
║     - 300초 대기                                                 ║
║                                                                  ║
║  ⚠️ 모든 요소 선택은 '클릭'으로만 진행합니다!                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    
    def print_mcp_commands(self):
        """MCP 명령어 가이드 출력"""
        print("""
═══════════════════════════════════════════════════════════════════
                    MCP 로그인 명령어 가이드 (클릭 기반)
═══════════════════════════════════════════════════════════════════

1. 페이지 스냅샷 촬영 (요소 uid 확인):
   mcp_chromedevtool_take_snapshot

2. 요소 클릭 (모든 요소 선택에 사용):
   mcp_chromedevtool_click(uid="요소_uid")

3. 키보드 입력 (클릭 후 텍스트 입력):
   mcp_chromedevtool_press_key(key="텍스트")
   또는 키보드로 직접 입력

4. 특정 텍스트 대기:
   mcp_chromedevtool_wait_for(text="대기할_텍스트")

5. 인증번호 입력 (인증창 감지 후):
   - 인증번호 입력 필드 클릭
   - 키보드로 인증번호 입력

⚠️ 주의: fill 대신 click + 키보드 입력 방식 사용!

═══════════════════════════════════════════════════════════════════
""")


class EmailVerificationHandler:
    """
    이메일 인증번호 처리 클래스
    
    로그인 후 이메일 인증이 필요한 경우 처리
    """
    
    # 인증번호 관련 텍스트 패턴
    VERIFICATION_PATTERNS = {
        'code_input_placeholder': '6자리 코드 입력',
        'verification_title': '인증',
        'code_sent_text': '코드 전송',
        'verify_button': '인증하기',
    }
    
    def __init__(self, timeout: int = 300):
        """
        EmailVerificationHandler 초기화
        
        Args:
            timeout: 인증번호 입력 대기 시간 (초)
        """
        self.timeout = timeout
        self._code = None
    
    def wait_and_get_code(self) -> Optional[str]:
        """
        인증번호 입력 대기 및 반환
        
        콘솔에서 사용자에게 인증번호를 입력받음
        
        Returns:
            입력받은 인증번호 또는 None
        """
        print("\n" + "🔔"*30)
        print("\n  ⚠️  이메일 인증번호 입력이 필요합니다!")
        print("\n" + "🔔"*30)
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    📧 이메일 인증번호 입력                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  TikTok에서 이메일로 인증번호를 전송했습니다.                    ║
║                                                                  ║
║  1. 이메일 받은편지함을 확인하세요                               ║
║  2. TikTok에서 보낸 6자리 인증번호를 찾으세요                    ║
║  3. 아래에 인증번호를 입력하세요                                 ║
║                                                                  ║
║  ⏰ 대기 시간: {self.timeout}초                                      ║
║                                                                  ║
║  💡 팁: 스팸함도 확인해보세요!                                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            remaining = int(self.timeout - (time.time() - start_time))
            
            try:
                code = input(f"\n  [{remaining}초 남음] 인증번호 입력 (6자리): ").strip()
                
                if code.lower() == 'q' or code.lower() == 'quit':
                    print("  인증 취소됨")
                    return None
                
                if code and len(code) == 6 and code.isdigit():
                    self._code = code
                    print(f"\n  ✓ 인증번호 입력됨: {code}")
                    logger.info(f"Verification code entered: {code[:2]}****")
                    return code
                else:
                    print("  ⚠️ 6자리 숫자를 입력해주세요. (취소: q)")
                    
            except KeyboardInterrupt:
                print("\n  인증 취소됨")
                return None
        
        print("\n  ⏰ 시간 초과! 인증번호 입력 시간이 만료되었습니다.")
        return None
    
    def get_code(self) -> Optional[str]:
        """저장된 인증번호 반환"""
        return self._code
    
    def clear_code(self):
        """인증번호 초기화"""
        self._code = None
    
    def print_verification_instructions(self):
        """인증번호 입력 후 MCP 명령어 안내 (클릭 기반)"""
        if self._code:
            print(f"""
═══════════════════════════════════════════════════════════════════
             인증번호 입력 MCP 명령어 (클릭 기반)
═══════════════════════════════════════════════════════════════════

인증번호: {self._code}

1. 페이지 스냅샷으로 인증번호 입력 필드 uid 확인:
   mcp_chromedevtool_take_snapshot

2. 인증번호 입력 필드 클릭:
   mcp_chromedevtool_click(uid="인증번호_입력필드_uid")

3. 키보드로 인증번호 입력:
   → {self._code}

4. 인증 버튼 클릭 (있는 경우):
   mcp_chromedevtool_click(uid="인증버튼_uid")

⚠️ fill 대신 click + 키보드 입력 방식 사용!

═══════════════════════════════════════════════════════════════════
""")


class TikTokLoginSteps:
    """
    TikTok 로그인 단계별 실행 클래스 (클릭 기반)
    
    각 단계를 개별적으로 실행하거나 전체 프로세스를 자동으로 실행
    모든 요소 선택은 클릭 방식으로 진행
    이메일 로그인 페이지로 직접 접속하여 단계 간소화
    """
    
    # 로그인 관련 선택자 (텍스트 기반 - 클릭용)
    SELECTORS = {
        # 입력 필드 placeholder (클릭 후 키보드 입력)
        'email_placeholder': '이메일 또는 TikTok ID',
        'password_placeholder': '비밀번호',
        
        # 로그인 버튼 (클릭)
        'login_button_text': '로그인',
        
        # 인증번호 관련 (클릭 후 키보드 입력)
        'verification_code_placeholder': '6자리 코드 입력',
        'verification_title': '인증',
        
        # 로그인 완료 확인 (URL 기반)
        'login_success_url_patterns': ['tiktok.com/foryou', 'tiktok.com/@', 'tiktok.com/explore'],
    }
    
    def __init__(self):
        self.login_mcp = TikTokLoginMCP()
        self.verification_handler = EmailVerificationHandler()
        self.current_step = 0
        self.total_steps = 5  # 간소화된 단계
    
    def get_step_description(self, step: int) -> str:
        """단계별 설명 반환 (클릭 기반 - 간소화)"""
        descriptions = {
            1: "TikTok 이메일 로그인 페이지 직접 접속 (세션 확인)",
            2: "이메일 입력 필드 클릭 → 키보드로 이메일 입력",
            3: "비밀번호 입력 필드 클릭 → 키보드로 비밀번호 입력",
            4: "로그인 버튼 클릭",
            5: "이메일 인증번호 입력 (필요시 - 클릭 후 키보드 입력)",
        }
        return descriptions.get(step, "알 수 없는 단계")
    
    def print_progress(self):
        """진행 상황 출력"""
        progress = "█" * self.current_step + "░" * (self.total_steps - self.current_step)
        percentage = (self.current_step / self.total_steps) * 100
        print(f"\n  진행률: [{progress}] {percentage:.0f}%")
        if self.current_step < self.total_steps:
            print(f"  현재 단계: {self.get_step_description(self.current_step + 1)}")
    
    def handle_verification_if_needed(self) -> Optional[str]:
        """
        인증번호 입력이 필요한 경우 처리
        
        Returns:
            인증번호 또는 None
        """
        return self.verification_handler.wait_and_get_code()


def get_login_helper() -> TikTokLoginMCP:
    """TikTokLoginMCP 인스턴스 반환"""
    return TikTokLoginMCP()


def get_login_steps() -> TikTokLoginSteps:
    """TikTokLoginSteps 인스턴스 반환"""
    return TikTokLoginSteps()


def get_verification_handler(timeout: int = 300) -> EmailVerificationHandler:
    """EmailVerificationHandler 인스턴스 반환"""
    return EmailVerificationHandler(timeout)
