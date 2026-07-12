# CHANGELOG

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
