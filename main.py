#!/usr/bin/env python3
"""
TikTok Auto Posting - Main Entry Point

TikTok 영상 자동 업로드 프로그램
WSL 환경에 최적화, Chrome DevTools MCP 연동
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.logger import logger
from src.browser import BrowserManager
from src.tiktok_uploader import TikTokUploader, VideoInfo
from src.video_manager import VideoManager


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='TikTok Auto Posting - 영상 자동 업로드 프로그램',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 단일 비디오 업로드
  python main.py --video /path/to/video.mp4 --caption "My video" --hashtags "#fyp #viral"
  
  # 모든 대기 중인 비디오 업로드
  python main.py --batch
  
  # 로그인만 수행
  python main.py --login-only
  
  # 브라우저 테스트
  python main.py --test-browser
  
  # 자동 로그인 (MCP 사용)
  python main.py --auto-login
        """
    )
    
    parser.add_argument(
        '--video', '-v',
        type=str,
        help='업로드할 비디오 파일 경로'
    )
    
    parser.add_argument(
        '--caption', '-c',
        type=str,
        default='',
        help='비디오 캡션/설명'
    )
    
    parser.add_argument(
        '--hashtags', '-t',
        type=str,
        default='',
        help='해시태그 (공백으로 구분, 예: "#fyp #viral")'
    )
    
    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='videos 폴더의 모든 대기 중인 비디오 일괄 업로드'
    )
    
    parser.add_argument(
        '--login-only', '-l',
        action='store_true',
        help='브라우저를 열고 수동 로그인만 수행'
    )
    
    parser.add_argument(
        '--auto-login', '-a',
        action='store_true',
        help='Chrome DevTools MCP를 사용하여 자동 로그인'
    )
    
    parser.add_argument(
        '--test-browser',
        action='store_true',
        help='브라우저 연결 테스트'
    )
    
    parser.add_argument(
        '--video-dir',
        type=str,
        default=None,
        help='비디오 파일 디렉토리 경로'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='디버그 모드 활성화'
    )
    
    return parser.parse_args()


def test_browser():
    """브라우저 연결 테스트"""
    logger.info("Testing browser connection...")
    
    browser = BrowserManager()
    
    try:
        if browser.start_browser():
            logger.info("✓ Browser started successfully")
            
            if browser.navigate_to("https://www.google.com"):
                logger.info("✓ Navigation successful")
            
            logger.info(f"✓ Current URL: {browser.get_current_url()}")
            logger.info(f"✓ DevTools Protocol enabled on port {config.CHROME_DEBUG_PORT}")
            
            input("\nPress Enter to close browser...")
            return True
        else:
            logger.error("✗ Failed to start browser")
            return False
    finally:
        browser.close_browser()


def login_only():
    """로그인만 수행"""
    logger.info("Starting login-only mode...")
    
    uploader = TikTokUploader()
    
    try:
        if uploader.start():
            logger.info("Browser started. Navigating to TikTok...")
            
            if uploader.wait_for_manual_login(timeout=600):  # 10분 대기
                logger.info("Login successful!")
                logger.info("You can now use this session for uploads.")
                input("\nPress Enter to close browser...")
                return True
            else:
                logger.error("Login failed or timed out")
                return False
        else:
            logger.error("Failed to start browser")
            return False
    finally:
        uploader.close()


def auto_login():
    """자동 로그인 (MCP 사용)"""
    from src.tiktok_login import TikTokLoginMCP, EmailVerificationHandler
    
    logger.info("Starting auto login mode with MCP...")
    
    login_helper = TikTokLoginMCP()
    verification_handler = EmailVerificationHandler(timeout=300)
    
    # 자격 증명 확인
    if not login_helper.has_credentials():
        logger.error("Login credentials not configured!")
        logger.info("Please set TIKTOK_EMAIL and TIKTOK_PASSWORD in .env file")
        return False
    
    email, password = login_helper.get_credentials()
    logger.info(f"Login email: {email[:3]}***{email[-10:]}")
    
    browser = BrowserManager()
    
    try:
        if browser.start_browser():
            logger.info("✓ Browser started successfully")
            
            # TikTok 메인 페이지로 이동
            logger.info("Navigating to TikTok...")
            if browser.navigate_to(config.TIKTOK_URL):
                logger.info("✓ TikTok loaded")
                logger.info(f"✓ Current URL: {browser.get_current_url()}")
                logger.info(f"✓ DevTools Protocol enabled on port {config.CHROME_DEBUG_PORT}")
                
                print("\n" + "="*60)
                print("  MCP Auto Login Ready")
                print("="*60)
                print("\n  Browser is ready. Use MCP tools to complete login:")
                print("\n  Step 1: Take snapshot")
                print("    mcp_chromedevtool_take_snapshot")
                print("\n  Step 2: Click login button (find uid from snapshot)")
                print("    mcp_chromedevtool_click(uid='login_button_uid')")
                print("\n  Step 3: Click '전화 또는 이메일 사용'")
                print("    mcp_chromedevtool_click(uid='email_option_uid')")
                print("\n  Step 4: Click '이메일 또는 아이디로 로그인'")
                print("    mcp_chromedevtool_click(uid='email_tab_uid')")
                print("\n  Step 5: Fill email")
                print(f"    mcp_chromedevtool_fill(uid='email_input_uid', value='{email}')")
                print("\n  Step 6: Fill password")
                print("    mcp_chromedevtool_fill(uid='password_input_uid', value='***')")
                print("\n  Step 7: Click login button")
                print("    mcp_chromedevtool_click(uid='submit_button_uid')")
                print("\n" + "="*60)
                
                input("\nPress Enter after clicking login button...")
                
                # 이메일 인증번호 처리
                print("\n" + "="*60)
                print("  Email Verification")
                print("="*60)
                need_verification = input("\n이메일 인증번호가 필요합니까? (y/N): ").strip().lower()
                
                if need_verification == 'y':
                    print("\n이메일 인증번호 입력 모드 (300초 제한)")
                    print("이메일에서 인증번호를 확인하고 아래에 입력하세요.")
                    print("-" * 40)
                    
                    verification_code = verification_handler.wait_and_get_code()
                    
                    if verification_code:
                        print(f"\n✓ 인증번호 입력됨: {verification_code}")
                        print("\nMCP를 사용하여 인증번호를 입력하세요:")
                        print(f"  mcp_chromedevtool_fill(uid='verification_input_uid', value='{verification_code}')")
                        print("\n그리고 확인 버튼을 클릭하세요:")
                        print("  mcp_chromedevtool_click(uid='verify_button_uid')")
                        
                        input("\n인증 완료 후 Enter를 누르세요...")
                    else:
                        print("\n⚠️ 인증번호 입력이 취소되었거나 시간 초과되었습니다.")
                
                print("\n✓ 로그인 프로세스 완료!")
                return True
            else:
                logger.error("Failed to load TikTok")
                return False
        else:
            logger.error("Failed to start browser")
            return False
    finally:
        keep_open = input("Keep browser open? (y/N): ").strip().lower()
        if keep_open != 'y':
            browser.close_browser()


def upload_single_video(video_path: str, caption: str, hashtags: str):
    """단일 비디오 업로드"""
    logger.info(f"Uploading single video: {video_path}")
    
    # 해시태그 파싱
    hashtag_list = hashtags.split() if hashtags else None
    
    video_info = VideoInfo(
        file_path=video_path,
        description=caption,
        hashtags=hashtag_list
    )
    
    uploader = TikTokUploader()
    video_manager = VideoManager()
    
    try:
        if uploader.start():
            success = uploader.upload_and_post(video_info)
            
            if success:
                video_manager.mark_as_uploaded(Path(video_path))
                logger.info("Upload completed successfully!")
                return True
            else:
                logger.error("Upload failed")
                return False
        else:
            logger.error("Failed to start browser")
            return False
    finally:
        uploader.close()


def batch_upload(video_dir: str = None):
    """비디오 일괄 업로드"""
    logger.info("Starting batch upload...")
    
    video_directory = Path(video_dir) if video_dir else None
    video_manager = VideoManager(video_directory)
    
    # 대기 중인 비디오 목록 가져오기
    pending_videos = video_manager.get_pending_videos()
    
    if not pending_videos:
        logger.info("No pending videos found")
        return True
    
    logger.info(f"Found {len(pending_videos)} pending videos")
    
    # VideoInfo 목록 생성
    video_info_list = video_manager.get_video_info_list(pending_videos)
    
    uploader = TikTokUploader()
    
    try:
        if uploader.start():
            results = uploader.batch_upload(video_info_list)
            
            # 결과 처리
            for file_path, success in results.items():
                if success:
                    video_manager.mark_as_uploaded(Path(file_path))
            
            successful = sum(1 for v in results.values() if v)
            logger.info(f"Batch upload completed: {successful}/{len(results)} successful")
            
            return successful == len(results)
        else:
            logger.error("Failed to start browser")
            return False
    finally:
        uploader.close()


def interactive_mode():
    """대화형 모드"""
    print("\n" + "="*60)
    print("  TikTok Auto Posting - Interactive Mode")
    print("="*60)
    
    while True:
        print("\nOptions:")
        print("  1. Upload single video")
        print("  2. Batch upload all pending videos")
        print("  3. Login to TikTok")
        print("  4. Test browser connection")
        print("  5. View upload history")
        print("  6. Exit")
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == '1':
            video_path = input("Enter video file path: ").strip()
            caption = input("Enter caption (optional): ").strip()
            hashtags = input("Enter hashtags (optional, space-separated): ").strip()
            
            if video_path:
                upload_single_video(video_path, caption, hashtags)
            else:
                print("Video path is required")
        
        elif choice == '2':
            batch_upload()
        
        elif choice == '3':
            login_only()
        
        elif choice == '4':
            test_browser()
        
        elif choice == '5':
            video_manager = VideoManager()
            history = video_manager.get_upload_history()
            
            if history:
                print(f"\nUpload History ({len(history)} videos):")
                for i, meta in enumerate(history, 1):
                    print(f"  {i}. {meta.file_name}")
                    print(f"     Uploaded: {meta.upload_time}")
                    if meta.tiktok_url:
                        print(f"     URL: {meta.tiktok_url}")
            else:
                print("\nNo upload history found")
        
        elif choice == '6':
            print("\nGoodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")


def main():
    """메인 함수"""
    # 필요한 디렉토리 생성
    config.ensure_directories()
    
    # 명령줄 인자 파싱
    args = parse_arguments()
    
    # 디버그 모드 설정
    if args.debug:
        import logging
        logger.setLevel(logging.DEBUG)
    
    # 설정 검증
    errors = config.validate()
    if errors:
        for error in errors:
            logger.warning(f"Config warning: {error}")
    
    try:
        # 명령 실행
        if args.test_browser:
            success = test_browser()
        
        elif args.login_only:
            success = login_only()
        
        elif args.auto_login:
            success = auto_login()
        
        elif args.video:
            success = upload_single_video(
                args.video,
                args.caption,
                args.hashtags
            )
        
        elif args.batch:
            success = batch_upload(args.video_dir)
        
        else:
            # 인자가 없으면 새로운 대화형 콘솔 UI 실행
            from src.console_ui import run_interactive_console
            run_interactive_console()
            success = True
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

