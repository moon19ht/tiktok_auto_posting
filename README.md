# TikTok Auto Posting

TikTok 영상 자동 업로드 프로그램 - WSL 환경에 최적화

## 📋 개요

이 프로그램은 TikTok에 영상을 자동으로 업로드하는 Python 자동화 도구입니다.

### 주요 특징

- **WSL 환경 최적화**: WSL2에서 Linux Chrome + WSLg를 사용하여 안정적으로 작동
- **Chrome DevTools MCP 연동**: MCP를 통한 텍스트 입력 및 클릭 자동화
- **JavaScript 자동화**: 마우스 이벤트 시뮬레이션을 통한 정교한 클릭 자동화
- **자동 로그인**: 이메일/비밀번호를 통한 자동 로그인 지원 (JavaScript 기반)
- **WebAuthn 비활성화**: Passkey/보안키 팝업 자동 차단
- **이메일 인증번호 처리**: 600초(10분) 대기 시간으로 콘솔에서 인증번호 입력 가능
- **캡차 처리 지원**: 300초(5분) 대기 시간으로 캡차 수동 해결 가능
- **시각화된 업로드**: headless 모드가 아닌 GUI 모드로 업로드 과정 확인 가능
- **대화형 콘솔 UI**: Rich 라이브러리를 활용한 컬러풀한 터미널 인터페이스
- **로그인 상태 유지**: Chrome 프로필을 사용하여 로그인 상태 유지
- **일괄 업로드 지원**: 여러 영상 연속 업로드 가능
- **업로드 히스토리 관리**: 중복 업로드 방지

## 🔧 시스템 요구사항

- **OS**: Windows 10/11 with WSL2 (Ubuntu 20.04+)
- **Python**: 3.8 이상
- **Chrome**: Linux용 Google Chrome (WSL 내 설치)
- **WSLg**: Windows 11 또는 WSL2 GUI 지원 필요
- **ChromeDriver**: 자동 설치됨 (webdriver-manager 사용)

## 📁 프로젝트 구조

\`\`\`
tiktok_auto_posting/
├── main.py                 # 메인 실행 파일
├── requirements.txt        # Python 의존성
├── .env.example           # 환경 변수 샘플
├── .gitignore             # Git 제외 파일
├── README.md              # 프로젝트 문서
├── src/
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   ├── logger.py          # 로깅 유틸리티
│   ├── browser.py         # Selenium 브라우저 관리 + JavaScript 자동화
│   ├── tiktok_uploader.py # TikTok 업로드 자동화
│   ├── video_manager.py   # 비디오 파일 관리
│   └── console_ui.py      # 대화형 콘솔 UI
├── videos/                # 업로드할 비디오 파일
├── logs/                  # 로그 파일
├── chrome_data/           # Chrome 프로필 데이터
├── sessions/              # 세션 데이터
└── uploads/               # 업로드 완료 파일
\`\`\`

## 🚀 설치 방법

### 1. 저장소 클론

\`\`\`bash
git clone https://github.com/moon19ht/tiktok_auto_posting.git
cd tiktok_auto_posting
\`\`\`

### 2. Python 가상환경 생성 (권장)

\`\`\`bash
python3 -m venv venv
source venv/bin/activate
\`\`\`

### 3. 의존성 설치

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. 환경 변수 설정

\`\`\`bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 편집하여 설정 변경
nano .env
\`\`\`

### 5. Linux Chrome 설치 (WSL 환경)

WSL에서 Linux용 Chrome을 설치합니다:

\`\`\`bash
# Chrome 설치
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# 설치 확인
google-chrome --version
\`\`\`

### 6. .env 파일 설정

\`\`\`bash
# TikTok 로그인 정보
TIKTOK_EMAIL=your_email@example.com
TIKTOK_PASSWORD=your_password

# Linux Chrome 실행 파일 경로
CHROME_BINARY_PATH=/usr/bin/google-chrome

# Chrome 사용자 데이터 디렉토리 (로그인 유지용)
CHROME_USER_DATA_DIR=/home/your_username/tiktok_auto_posting/chrome_data

# Chrome DevTools 디버깅 포트 (MCP 연동용)
CHROME_DEBUG_PORT=9222
\`\`\`

## 📖 사용 방법

### 대화형 모드 (권장)

\`\`\`bash
source venv/bin/activate
python3 main.py
\`\`\`

대화형 콘솔 UI에서 다음 기능을 사용할 수 있습니다:

\`\`\`
┌──────────────────────────────────────────────────────────────────┐
│                    TikTok 자동 포스팅 시스템                      │
├──────────────────────────────────────────────────────────────────┤
│  1. 🔐 로그인            - TikTok 로그인 (이메일/비밀번호)        │
│  2. 📤 단일 업로드       - 선택한 영상 1개 업로드                 │
│  3. 📦 일괄 업로드       - 대기 중인 모든 영상 업로드             │
│  4. 🔍 브라우저 테스트   - 브라우저 동작 테스트                   │
│  5. 📋 업로드 대기 목록  - 업로드 예정 영상 확인                  │
│  6. 📊 업로드 히스토리   - 업로드 완료 내역 확인                  │
│  7. ⚙️  설정            - 프로그램 설정                          │
│  0. 🚪 종료              - 프로그램 종료                          │
└──────────────────────────────────────────────────────────────────┘
\`\`\`

### 자동 로그인 프로세스

1. 메뉴에서 **1. 로그인** 선택
2. 브라우저가 \`https://www.tiktok.com/login/phone-or-email/email\` 페이지로 이동
3. **JavaScript 자동화**로 이메일/비밀번호 자동 입력
4. **마우스 이벤트 시뮬레이션**으로 로그인 버튼 클릭
5. 필요시 이메일 인증번호 입력 (10분 대기)
6. 필요시 캡차 수동 해결 (5분 대기)

### 명령줄 옵션

\`\`\`bash
# 단일 비디오 업로드
python3 main.py --video /path/to/video.mp4 --caption "영상 설명" --hashtags "#fyp #viral"

# 일괄 업로드
python3 main.py --batch

# 로그인만 수행
python3 main.py --login-only

# 브라우저 테스트
python3 main.py --test-browser

# 디버그 모드
python3 main.py --debug --video /path/to/video.mp4
\`\`\`

## 🔌 Chrome DevTools MCP 연동

이 프로그램은 Chrome DevTools Protocol을 활성화하여 MCP와 연동할 수 있습니다.

### 포트 설정

기본 디버깅 포트: \`9222\`

\`.env\` 파일에서 변경 가능:
\`\`\`bash
CHROME_DEBUG_PORT=9222
\`\`\`

### MCP 도구 사용 예시

| 도구 | 설명 |
|------|------|
| \`mcp_chromedevtool_click\` | 요소 클릭 |
| \`mcp_chromedevtool_fill\` | 입력 필드 채우기 |
| \`mcp_chromedevtool_take_screenshot\` | 스크린샷 캡처 |
| \`mcp_chromedevtool_take_snapshot\` | 페이지 구조 가져오기 |
| \`mcp_chromedevtool_upload_file\` | 파일 업로드 |
| \`mcp_chromedevtool_wait_for\` | 텍스트 대기 |

## 🔐 로그인 자동화 기술

### JavaScript 자동화

- **입력 필드**: \`element.value\` 설정 + \`input\` 이벤트 트리거
- **버튼 클릭**: 마우스 이벤트 시뮬레이션 (mouseover → mousedown → mouseup → click)

### WebAuthn/Passkey 비활성화

Chrome 옵션으로 보안키 팝업 차단:
\`\`\`
--disable-web-security
--disable-features=WebAuthentication
\`\`\`

### 인증 처리

| 인증 유형 | 대기 시간 | 처리 방법 |
|-----------|----------|----------|
| 이메일 인증번호 | 600초 (10분) | 콘솔에서 6자리 코드 입력 |
| 캡차 | 300초 (5분) | 브라우저에서 수동 해결 |

## ⚙️ 설정 옵션

### 환경 변수 (.env)

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| \`TIKTOK_EMAIL\` | TikTok 로그인 이메일 | (필수 설정) |
| \`TIKTOK_PASSWORD\` | TikTok 로그인 비밀번호 | (필수 설정) |
| \`CHROME_BINARY_PATH\` | Chrome 실행 파일 경로 | \`/usr/bin/google-chrome\` |
| \`CHROME_USER_DATA_DIR\` | Chrome 프로필 디렉토리 | 프로젝트 내 \`chrome_data\` |
| \`CHROME_DEBUG_PORT\` | DevTools 디버깅 포트 | \`9222\` |
| \`VIDEO_DIRECTORY\` | 비디오 파일 디렉토리 | \`./videos\` |
| \`DEFAULT_HASHTAGS\` | 기본 해시태그 | \`#fyp,#viral,#tiktok\` |
| \`UPLOAD_INTERVAL\` | 연속 업로드 간격 (초) | \`60\` |
| \`LOG_LEVEL\` | 로그 레벨 | \`INFO\` |
| \`VERIFICATION_TIMEOUT\` | 인증번호 입력 대기 시간 | \`600\` |
| \`CAPTCHA_TIMEOUT\` | 캡차 해결 대기 시간 | \`300\` |

## 📝 주의사항

1. **로그인 정보 설정**: \`.env\` 파일에 \`TIKTOK_EMAIL\`과 \`TIKTOK_PASSWORD\` 설정 필수
2. **이메일 인증**: 새로운 기기/IP에서 로그인 시 이메일 인증이 필요할 수 있음
3. **Chrome 프로필**: 로그인 상태 유지를 위해 별도의 Chrome 프로필 사용
4. **업로드 제한**: TikTok의 업로드 제한 정책을 준수하세요
5. **비디오 형식**: 지원 형식: \`.mp4\`, \`.mov\`, \`.avi\`, \`.webm\`
6. **파일 크기**: 최대 10GB까지 지원
7. **보안**: \`.env\` 파일은 절대 Git에 커밋하지 마세요 (\`.gitignore\`에 포함됨)

## 🐛 문제 해결

### Chrome이 시작되지 않음

\`\`\`bash
# Linux Chrome 설치 확인
which google-chrome

# Chrome이 설치되지 않은 경우 설치
sudo apt-get update
sudo apt-get install -y google-chrome-stable
\`\`\`

### ChromeDriver 오류

\`\`\`bash
# webdriver-manager 캐시 삭제
rm -rf ~/.wdm

# pip 패키지 재설치
pip install --upgrade webdriver-manager selenium
\`\`\`

### WSL에서 GUI가 표시되지 않음

WSLg가 제대로 작동하는지 확인:

\`\`\`bash
# X11 앱 테스트
sudo apt-get install -y x11-apps
xclock

# WSLg가 없는 경우 DISPLAY 설정
export DISPLAY=:0
\`\`\`

### 보안키/Passkey 팝업이 나타남

Chrome이 \`--disable-features=WebAuthentication\` 옵션으로 시작되는지 확인하세요.
프로그램이 자동으로 이 옵션을 설정합니다.

### 로그인 버튼이 클릭되지 않음

JavaScript 마우스 이벤트 시뮬레이션이 적용되어 있습니다.
문제가 지속되면 MCP를 통해 직접 클릭할 수 있습니다.

## 📄 라이선스

MIT License

## 🤝 기여

버그 리포트 및 기능 제안은 GitHub Issues를 통해 제출해 주세요.

---

**개발자**: [@moon19ht](https://github.com/moon19ht)
