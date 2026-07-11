# 티스토리 자동 포스팅 도구

로컬에 백업된 티스토리 HTML 게시글을 자동으로 티스토리 블로그에 재발행하는 Python/Playwright 기반 자동화 프로그램입니다.

## 주요 기능

- **세션 재사용**: 카카오 로그인을 최초 1회만 수행하고 브라우저 프로필을 저장하여 이후 로그인 없이 자동 실행
- **이미지 자동 업로드**: 로컬 이미지를 티스토리에 업로드하고 카카오 CDN URL로 본문 내 경로를 자동 치환
- **일일 발행 제한**: 하루 최대 발행 개수를 제한하여 스팸 방지 정책 우회 (기본 10개/일)
  → config.json 파일에서 daily_limit을 변경하면 변경한 갯수만큼 발행합니다. (최대 15/일)
- **인간적인 딜레이**: 글 발행 간 5~15분 랜덤 대기로 자동화 감지 회피
- **캡차 반자동 처리**: DKAPTCHA 발생 시 알림 후 사용자 수동 해결 → 자동 재개
- **발행 이력 관리**: SQLite DB로 중복 발행 방지 및 발행 상태 추적

## 파일 구조

```
tistory_auto_posting/
├── login.py          # 최초 로그인 및 세션 저장
├── publish.py        # 자동 발행 메인 엔진
├── parser_utils.py   # 백업 HTML 및 이미지 경로 파서
├── db_utils.py       # SQLite 발행 이력 관리
├── config.json       # 설정 파일
├── user_data/        # 브라우저 세션 저장 폴더 (gitignore)
└── database.db       # 발행 이력 DB (gitignore)
```

## 사전 요구사항

- Python 3.10+
- [Playwright](https://playwright.dev/python/)

```powershell
pip install playwright
playwright install chromium
```

## 사용 방법

### STEP 1. 로그인 (최초 1회)

```powershell
python login.py
```

브라우저가 열리면 카카오 계정으로 직접 로그인합니다. 로그인 완료 후 터미널에서 Enter를 눌러 세션을 저장합니다.

### STEP 2. 자동 발행 실행

```powershell
python publish.py
```

- 미발행 폴더를 순서대로 탐색하여 하루 최대 10개씩 자동 발행
- 글 발행 후 5~15분 랜덤 대기 → 다음 글 발행 반복
- 하루 한도 도달 시 자동 종료

### STEP 3. 다음날 이어서 실행

```powershell
python publish.py
```

DB에 날짜 기준으로 카운트가 초기화되므로, 다음날 다시 실행하면 남은 게시글부터 이어서 발행합니다.

## 설정 (`config.json`)

| 항목                | 설명                    | 기본값       |
| --------------------- | ------------------------- | -------------- |
| `blog_name`         | 포스팅할 티스토리 블로그 이름    | -            |
| `backup_dir`        | 백업한 HTML 폴더 경로   |              |
| `daily_limit`       | 하루 최대 발행 개수     | `10`         |
| `min_delay_seconds` | 글 간 최소 대기 시간    | `300` (5분)  |
| `max_delay_seconds` | 글 간 최대 대기 시간    | `900` (15분) |
| `headless`          | 브라우저 숨김 실행 여부 | `false`      |

## 동작 원리

1. 숫자로 된 백업 폴더(예: `523/`, `524/`)에서 HTML 파싱 → 제목·본문·태그·이미지 추출
2. Playwright로 티스토리 글쓰기 페이지 진입
3. 로컬 이미지 업로드 → 네트워크 응답 가로채기로 카카오 CDN URL 획득
4. TinyMCE API(`setContent`)로 본문 직접 주입
5. 발행 완료 후 SQLite DB에 이력 기록
