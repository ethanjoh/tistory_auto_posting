# CHANGELOG

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
