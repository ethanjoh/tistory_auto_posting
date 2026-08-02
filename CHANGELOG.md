# CHANGELOG

## [2026-08-02]

### 수정 목적

- 본문 HTML 내 `represent="true"` 속성 부여 방식을 삭제하고, 발행 레이어의 '대표이미지 추가' 기능을 통해 첫 번째 이미지를 업로드하도록 수정.

### 수정한 파일

- [publish.py](publish.py): 본문 가공 및 JS 주입 단의 represent 속성 부여 로직 삭제, 완료 버튼 클릭 후 발행 레이어 단계에서 `images[0]["absolute_path"]` 파일 업로드 로직(10.1 단계) 추가.

### 테스트 결과

- `python -m py_compile publish.py` 구문 검증 완료.

## [2026-08-01] (2)

### 수정 목적

- 대표 이미지(썸네일) 설정이 지속적으로 실패하는 원인 파악 및 수정.

### 원인 분석

- **TinyMCE sanitize 문제**: `editor.setContent(html)`이 호출될 때 TinyMCE 에디터가 내부적으로 HTML을 파싱·정규화하는 과정에서 `represent`, `data-represent` 같은 비표준(HTML 스펙 외) 속성을 허용 목록에 없다는 이유로 자동 제거함.
- **결과**: BeautifulSoup으로 `represent="true"`를 아무리 정교하게 삽입해도, `setContent()` 시점에 속성이 사라지므로 대표 이미지가 인식되지 않았음.
- **부가 문제**: `str(soup)` 출력 시 `<html><body>` 래퍼가 추가되는 부작용 및 `editor.getContent()` 직렬화도 동일하게 비표준 속성을 제거함.

### 해결 방법

- `setContent()` 이후 별도의 `page.evaluate()`를 사용하는 대신, 동일 JS 블록 내에서 `editor.getBody().querySelector('img')`로 첫 번째 이미지를 찾아 `setAttribute()`로 DOM에 직접 속성을 부여.
- DOM 직접 조작(setAttribute)은 TinyMCE sanitizer를 우회하여 속성이 DOM 노드에 보존됨.
- textarea(`#editor-tistory`)에는 `editor.getContent()` 대신 `body.innerHTML`을 주입하여, DOM에 설정된 `represent` 속성이 최종 전송 데이터(폼 제출값)에 그대로 포함되도록 처리.

### 수정한 파일

- [publish.py](publish.py) (L311-342: JS evaluate 블록 내 DOM 직접 조작 로직 추가, textarea 값 소스 변경)

### 테스트 결과

- `python -m py_compile publish.py` 구문 검사 통과 확인.

## [2026-08-01]

### 수정 목적

- 글 자동 발행 시 비공개가 아닌 '공개'로 발행되도록 기본 설정 및 셀렉터 클릭 동작 수정.
- 포스팅 본문 내 첫 번째 이미지가 대표 이미지(썸네일)로 정상 인식/지정되도록 `represent="true"`, `data-represent="true"` 및 부모 컨테이너 태그/클래스 지정 강화.

### 주요 결정 사항

1. **글 발행 공개 설정 변경**:
   - `config.json`에 `"visibility": "public"` 항목을 명시하고, `publish.py`의 기본값을 `"public"`으로 변경.
   - 공개 설정 레이어에서 라벨, 버튼, 라디오 등 다중 셀렉터를 순차 시도하여 '공개' 선택이 확실하게 처리되도록 클릭 로직 강화.
2. **첫 번째 이미지 대표 이미지 지정 로직 강화**:
   - `publish.py`에서 파싱된 본문 HTML 내 첫 번째 이미지 태그(`<img>`)에 `represent="true"`와 `data-represent="true"`를 모두 추가.
   - 이미지가 `<figure>` 또는 `div` 등 컨테이너에 감싸진 경우 부모 태그에도 `represent="true"`, `data-represent="true"` 속성과 `represent` 클래스를 부여하여 티스토리 에디터 썸네일 인식 안정화.

### 수정한 파일

- [config.json](config.json)
- [publish.py](publish.py)
- [CHANGELOG.md](CHANGELOG.md)

### 테스트 결과

- `publish.py` 구문 검사(`py_compile`) 통과 확인 완료.

## [2026-07-15]

### 수정 목적

- 로컬 변경사항 중 일일 발행 제한 설명 수정본을 올바르게 반영하고 원격 저장소와 싱크 처리.
- 보안이 필요하고 로컬 환경 전용 설정이 포함된 `config.json` 파일을 Git 추적(Tracking) 목록에서 영구 제외하여 원격 저장소 노출을 방지.

### 주요 결정 사항

1. **동기화용 깃 스테이징 및 커밋 정리**:
   - 미스테이징 상태의 `how_to_run.md` (일일 발행 수 제한 가이드 15개 -> 5개 수정 반영본)를 병합 과정에 포함하여 커밋.
   - 로컬 저장소의 머지 상태를 완결하고 `git push`를 통해 원격 리포지토리(`origin/main`)와 완전히 동기화.
2. **`config.json` 추적 중단**:
   - `git rm --cached config.json`을 적용하여 로컬의 물리적 파일 및 설정값은 보존하면서 Git 인덱스와 GitHub 원격 저장소에서 제거.

### 수정한 파일

- [how_to_run.md](how_to_run.md)
- [CHANGELOG.md](CHANGELOG.md)
- [config.json](config.json) (추적 제거)

### 테스트 결과

- `git status`를 통한 파일 병합 충돌(conflict) 해결 확인 완료.
- 원격 브랜치(`origin/main`)로의 `git push` 완료 후 저장소가 최신 상태(up-to-date)로 유지됨을 확인.
- `git ls-files config.json`을 통해 해당 파일이 더 이상 깃에 의해 관리되지 않으며 로컬에 정상 보존되어 있음을 검증 완료.

## [2026-07-13]

### 수정 목적

- 최근 24시간 이내의 누적 발행 글 개수를 트래킹하여 50개 제한(기본값)을 초과한 경우 발행을 제어하고, 다음 글 발행이 가능한 대기 시간을 계산하여 안내해주는 예외 처리 로직 추가.
- 글 발행 시 본문에 첨부된 이미지가 있는 경우, 첫 번째 이미지를 대표 이미지(썸네일)로 자동 지정하는 기능 추가.

### 주요 결정 사항

1. **24시간 이내 발행 수 실시간 조회**:
   - `db_utils.py`에 `get_recent_24h_posts` 함수를 신설하여 SQLite 내 `published_at` 컬럼의 ISO 문자열을 기준으로 현재 시각 24시간 이내에 성공(`success`)한 포스트의 발행 시각 목록을 수집.
2. **다음 발행 가능 시각 연산 알고리즘 도입**:
   - `db_utils.py`에 `get_next_available_time` 함수를 신설.
   - 최근 24시간 동안 발행된 글의 개수 `N`이 제한 `limit`(기본 50)에 도달하거나 초과했을 때, 오래된 순으로 정렬된 시간 목록 중 `N - limit`번째 글(초과를 해소하기 위해 24시간 범위 밖으로 빠져나가야 할 타겟 글)의 발행일시에서 24시간을 더해 다음 추가 발행이 가능해지는 기준 시각을 도출.
3. **메인 엔진(publish.py)의 가상 한도 검사 및 자동 종료**:
   - `main()` 구동 초입 단계에서 위 함수들을 활용하여 24시간 제한 여부를 점검.
   - 제한에 도달한 경우 경고 출력과 동시에 "다음 발행 가능 시각 및 남은 대기 시간"을 시간/분 단위로 표시하고 안전하게 브라우저 기동 전에 프로세스를 종료(`return`)하도록 함.
4. **첫 번째 이미지 대표 설정**:
   - `publish.py`의 본문 HTML 가공 단계에서 BeautifulSoup을 로드하여 본문 내 첫 번째 이미지(`<img>` 태그)를 찾아 티스토리 전용 대표 이미지 식별 속성인 `represent="true"`를 동적으로 부여.
   - 본문에 이미지가 없는 포스트인 경우 오류 없이 건너뛰도록 처리.

### 수정한 파일

- [db_utils.py](file:///e:/개인_백업/www/tistory_auto_posting/db_utils.py)
- [publish.py](file:///e:/개인_백업/www/tistory_auto_posting/publish.py)

### 테스트 결과

- `test_limit.py` 가상 데이터(52개 글)를 통한 다음 발행 가능 시각 추산 알고리즘이 100% 예상 시간과 정합함을 검증 완료.
- 실제 데이터베이스 기준(최근 24시간 내 53개 글 기록) 실행 시, 50개 제한 경고를 띄우고 약 47분 뒤(가장 오래된 초과분이 등록된 24시간 후) 재시작할 수 있음을 확인하고 정상 종료됨을 검증 완료.
- `test_represent.py` 유닛 테스트를 통해 복수 이미지 인입 시 첫 번째 이미지에만 `represent="true"`가 반영되고, 이미지 미존재 케이스에서는 오설정이나 오류 없이 안전하게 통과됨을 입증 완료.

## [2026-07-12]

### 수정 목적

- 포스팅 등록 시마다 브라우저가 종료되고 새로 열리는 과정을 개선하여, 브라우저 창을 계속 열어둔 상태로 연속 글 작성이 가능하도록 아키텍처 개선.
- 로컬 백업 HTML의 작성 일자(Date) 중 연월일 값을 파싱해 글 발행 시 제목의 맨 뒤에 `[YYYY-MM-DD]` 형태로 자동으로 붙여주는 기능 추가.

### 주요 결정 사항

1. **브라우저 컨텍스트 재사용**:
   - `publish_one` 내부에 있던 `sync_playwright` 브라우저 기동 코드를 제거하고, `main` 함수에서 브라우저 컨텍스트를 1회만 열어두도록 리팩터링.
   - 포스팅 간 대기 시간(딜레이) 동안에도 브라우저 창을 닫지 않고 유지하여 프로그램 실행 연속성 확보.
2. **리스너 관리**:
   - `page.on("response", handle_response)` 등록 이후 각 포스팅 단계가 완료되는 `finally` 블록에서 `remove_listener`를 통해 감시자를 해제함으로써 메모리 누수 방지.
3. **작성 일자 파싱 및 제목 결합**:
   - `parser_utils.py`에서 기존 `p.date`로 한정하여 가져오던 로직을, 클래스명이 `date`인 임의의 태그 요소에서도 텍스트를 추출할 수 있게 유연성을 향상시킴 (`soup.find(class_="date")`).
   - `publish.py`에서 파싱된 날짜가 있는 경우 정규식을 사용하여 `YYYY-MM-DD` 연월일 부분만 발췌한 뒤, 제목 우측에 접미사(suffix) `[YYYY-MM-DD]`로 덧붙여 포스팅하도록 구현.

### 수정한 파일

- [publish.py](file:///e:/개인_백업/www/tistory_auto_posting/publish.py)
- [parser_utils.py](file:///e:/개인_백업/www/tistory_auto_posting/parser_utils.py)

### 테스트 결과

- HTML 파싱 결과 `2009-12-23 01:57:45` 형식의 날짜 텍스트에서 `2009-12-23`만 안전하게 분리 추출.
- 발행 시 글 제목이 `오사카에서 먹은 치킨, 삼겹살 [2009-12-23]` 형태로 가공되어 에디터에 정상 주입됨을 검증 완료.

## [2026-07-11]

### 수정 목적

- 티스토리 신에디터 구조 분석을 바탕으로 자동 발행(posting) 실패 이슈(오버레이 간섭, 버튼 비활성화, 카카오 봇 방지 문자 처리 지연) 최종 교정 및 연동 성공

### 주요 결정 사항

1. **헤드풀(headful) 브라우저 모드 전환**:
   - 봇 우회 및 발행 차단 레이어로 생성되는 카카오 지리 캡차(DKAPTCHA) 수동 해제 대응을 위해 `config.json`의 `"headless"` 설정을 `false`로 변경.
2. **이미지 업로드 매핑 자동화**:
   - 기존의 불안정한 "HTML 모드 전환 및 textarea 정규식 분석"에서 탈피하여 Playwright 네트워크 리스너(`page.on("response")`)로 이미지 업로드 REST API(`/manage/post/attach.json`) 반환 주소를 감지해 파일명-CDN 매핑 맵을 100% 신뢰성 있게 구축.
3. **UI 선후관계 재배치**:
   - 카테고리 설정(header 드롭다운) 및 태그 입력을 완료 버튼 누르기 전인 메인 에디터 상태에서 먼저 완수하도록 코드 위치 변경. (완료 모달 오픈 후 overlay 차단으로 인한 요소 클릭 실패 차단)
4. **발행/저장 대기 및 예외 루프 처리**:
   - 완료 레이어 클릭 후 티스토리 백그라운드 자동 저장(auto-save)과 캡차(DKAPTCHA) 해제를 최대 2분간 모니터링하여 버튼 비활성 상태(`disabled=""` 및 `저장중`)가 해제되는 시점을 동적으로 포착 및 자동 제출 처리.

### 수정한 파일

- [config.json](file:///c:/Users/ethan/Downloads/tistory_backup/config.json)
- [publish.py](file:///c:/Users/ethan/Downloads/tistory_backup/publish.py)

### 테스트 결과

- 100% 실제 동작 검증 결과, 캡차 해결 시 최종 발행 완료 후 티스토리 포스팅 글 목록 화면 리다이렉션 및 SQLite DB 카운트 업 정상 작동 완료.
