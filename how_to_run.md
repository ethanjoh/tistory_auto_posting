
## 📖 처음부터 하루 15개 자동 등록 방법

### STEP 1. 설정 변경 (config.json)

* 아래의 설정을 자신의 환경에 맞게 수정한 뒤, config.json으로 저장합니다.
* blog_name은 tistory.com의 앞부분 주소만
* backup_dir은 백업받은 티스토리 데이터가 있는 폴더

```
{
  "blog_name": "blog_name",
  "user_data_dir": "./user_data",
  "backup_dir": "c:/tistory_backup",
  "headless": false,
  "daily_limit": 5,
  "min_delay_seconds": 30,
  "max_delay_seconds": 60,
  "selectors": {
    "title_textarea": "#post-title-inp",
    "editor_mode_dropdown": "button:has-text('기본모드'), span:has-text('기본모드')",
    "editor_mode_html": "button:has-text('HTML'), li:has-text('HTML'), a:has-text('HTML')",
    "html_textarea": ".textarea_html, textarea.textarea_html",
    "file_input": "input[type='file']",
    "publish_button": "#publish-layer-btn, button:has-text('완료')",
    "confirm_publish_button": "button:has-text('발행'), .btn_confirm",
    "category_select": ".select_category, select[name='category']",
    "tag_input": ".tag_input, input#tag-input"
  }
}
```

* blog_name, backup_dir 필수입력

| 설정 | 의미 | 현재값 |
|------|------|--------|
| `blog_name` | 포스팅할 블로그 주소 | |
| `backup_dir` | 백업한 티스토리 HTML 폴더 경로 | |
| `daily_limit` | 하루 최대 등록 개수 | `15` (최대 15)|
| `min_delay_seconds` | 글 간 최소 대기 시간 | `30` (30초) |
| `max_delay_seconds` | 글 간 최대 대기 시간 | `60` (1분) |
| `visibility` | 공개 설정 | `"private"` (비공개) |

### STEP 2. 세션 로그인 (최초 1회 또는 세션 만료 시)

```powershell
cd [작업폴더 경로]
.venv\Scripts\python login.py
```

* 브라우저 창이 열리면 카카오 계정으로 **직접 로그인**
* 완전히 로그인된 상태를 확인 후 터미널에서 프로그램 종료

---

### STEP 3. 자동 발행 실행

```powershell
.venv\Scripts\python publish.py
```

실행 시 자동으로:

1. 미발행 폴더 중 **첫 번째 글**부터 순서대로 발행
2. 글 1개 발행 완료 → **30초~1분 랜덤 딜레이** → 다음 글 발행
3. **하루 50개** 발행 완료 시 자동 종료
4. 캡차 발생 시 → 콘솔에 경고 출력, 브라우저에서 수동으로 캡차 해결 후 자동 계속 진행

---

### STEP 4. 다음날 다시 실행

```powershell
.venv\Scripts\python publish.py
```

* DB에 오늘 날짜 기준으로 카운트가 리셋되므로, 다음날 다시 실행하면 자동으로 남은 폴더부터 50개씩 계속 발행합니다.

---

### 주의. 글 등록 제한

* 티스토리 게시글은 "작성"과 "발행"으로 나뉩니다.
여기서 작성은 "비공개 작성, 공개 발행, 예약 공개 발행, 블로그 공지/페이지/키워드 작성"을 모두 포함한 것을 말합니다.
이 중 발행은 모든 사람이 볼 수 있도록 작성 및 공개(예약 포함)한 것입니다.
모든 계정은 하루에 15/30건(가입 시기의 차이)까지 공개 발행을 포함한 50개의 작성 수 제한이 적용됩니다.
* 자동 포스팅으로 작성 시 비공개로 저장이 됩니다. 따라서, 중간에 등록한 글들을 공개를 해버리면 그만큼 작성할 수 있는 숫자가 줄어듭니다.
따라서, 공개는 등록이 모두 끝난 뒤에 하고 우선은 하루 50개씩 비공개로 저장만 하는 것이 좋습니다.
