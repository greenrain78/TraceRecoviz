# TraceRecoViz 소프트웨어 설계서 (SDS)

본 문서는 TraceRecoViz 데스크톱 애플리케이션(메인 진입점: `main.py`)의 아키텍처, 주요 컴포넌트, 데이터/제어 흐름, API, UI, 에러 처리, 비기능 요구사항, 운영 및 테스트 계획을 기술합니다. 본 SDS는 제공된 코드 기준으로 작성되었습니다.

---

## 1. 개요

- 목적: 코드 변화 전/후(Old/New) 프로젝트를 비교·계측하고 시퀀스 다이어그램(JSON)을 생성·열람할 수 있는 GUI + 내장 웹서버 통합 도구 제공
- 형태: PySide6 기반 데스크톱 앱 + FastAPI(uvicorn) 내장 서버 동시 구동
- 대상 플랫폼: Windows 중심(WSL 포함). PyInstaller 기반 패키징 스펙 파일 동봉
- 주요 산출물: `build/sequence_diagram/*.json` 및 관련 결과물, `index.html`/`viewer.html`를 통한 웹 뷰어

---

## 2. 시스템 구성 개요 (Architecture)

- 프런트엔드(Desktop GUI)
  - PySide6로 구성된 메인 윈도우(`MainWindow`)와 좌측 컨트롤 패널(`ControlPanel`), 파일 탐색기(QTreeView/QTableView), 미리보기 패널(`PreviewPanel`), 빌드 로그 다이얼로그(`BuildLogDialog`)
  - 다크/라이트 테마 QSS 제공
  - `QSettings(APP_ORG=ExampleCo, APP_NAME=TraceRecoViz)`로 사용자 설정(경로/테마) 유지

- 백엔드(Web API)
  - FastAPI 앱(`backend_app`)을 uvicorn으로 백그라운드 스레드에서 구동(`UvicornRunner`)
  - CORS 허용(개발/웹뷰 용이성)
  - 정적 페이지: `/`→`index.html`, `/viewer.html`→`viewer.html`
  - 데이터 API: `/api/sequence-diagrams`, `/build/sequence_diagram/{file_path:path}`

- 파일·결과물 구조(런타임 생성)
  - `build/sequence_diagram/` 시퀀스 다이어그램 JSON 저장소
  - `build/log/`, `build/new/`, `build/old/`, `build/result/` 등 결과/작업 디렉터리

- 배포/패키징
  - PyInstaller 스펙 존재: `SimpleMakeBuilder.spec`, `TraceRecoviz_linux.spec`
  - 실행 중 `sys._MEIPASS` 고려하여 리소스/작업 경로 계산

---

## 3. 주요 모듈/클래스 설계

### 3.1 UvicornRunner
- 책임: FastAPI 앱을 별도 데몬 스레드에서 안전하게 시작/중지
- 핵심 메서드
  - `start()`: 이미 실행 중이면 무시, 스레드 생성 및 `uvicorn.Server.run()` 호출
  - `stop()`: 정상 종료 신호(`should_exit`, `force_exit`) 후 join
  - `is_running()`: 스레드 생존 여부로 실행 상태 판단
- 예외 처리: 시작/종료 시 예외 발생 시 GUI에서 사용자에게 노출

### 3.2 FastAPI 엔드포인트
- `GET /api/sequence-diagrams`
  - 소스: `SEQUENCE_DIAGRAM_DIR = build/sequence_diagram`
  - 모든 `.json` 중 `_new.json`/`_old.json` 페어가 존재하는 베이스 파일만 반환
  - 응답: `{ "files": ["<base>.json", ...] }`

- `GET /`
  - `index.html` 반환(루트)

- `GET /viewer.html`
  - `viewer.html` 반환

- `GET /build/sequence_diagram/{file_path:path}`
  - 지정 JSON 파일을 파일 응답으로 반환(존재하지 않으면 404 JSON)

### 3.3 ControlPanel (좌측 패널)
- 책임: 프로젝트 폴더 선택/복제, 빌드/계측 실행, 웹서버 토글, Makefile 편집
- 핵심 기능
  - 폴더 선택 `_browse(type, edit)`
    - 선택 폴더를 앱 기준 `target_{type}` (`type`은 `old`/`new`)에 통째로 복사
    - 대상 폴더는 기존 내용 삭제 후 복사(`_ensure_empty_dir`, `_copy_entire_folder_to`)
    - 선택 경로를 `QSettings`에 보존(`project_dir_old`, `project_dir_new`)
  - 빌드 실행 `_on_build_clicked()`
    - 작업 디렉터리: `_dest_dir()` (실행 경로/MEIPASS)
    - 순차 명령:
      1) `make clean`
      2) `make`
      3) `./all_tests_new`
      4) `./all_tests_old`
      5) `python src/diff/main.py`
      6) `python src/parser/main.py`
    - `QProcess`로 실행, 출력/오류 스트림 실시간 수집, 단계 실패 시 중단
  - 웹서버 토글 `_on_web_toggled()`
    - 시작 시 링크 다이얼로그 표시(`http://127.0.0.1:8000`)
  - Makefile 편집 `_on_edit_makefile_clicked()`
    - 현재 작업 디렉터리의 `Makefile`을 열어 편집/저장(인코딩 유지)

### 3.4 PreviewPanel (우측 하단)
- 책임: 선택한 파일/폴더 미리보기(텍스트/이미지/정보)
- 텍스트 판단: 확장자/파일명 규칙 + 내용 스니핑(64KB, `utf-8`→`cp949` 엄격 디코딩)
- 텍스트 미리보기: 최대 200KB, 디코딩 폴백(`utf-8`→`cp949`→`latin-1`) 후 `utf-8 replace`
- 이미지 미리보기: `QImageReader`로 로딩 후 라벨 크기에 맞춰 스케일

### 3.5 FilesProxy (검색 필터)
- 책임: 파일/폴더 이름 필터(정규식), 재귀 필터링으로 하위 일치 시 부모 디렉터리 표시

### 3.6 MainWindow
- 책임: 전체 레이아웃/훅 구성, 테마/검색/브레드크럼/탐색기/미리보기/로그 초기화 및 바인딩
- 설정 복원: `last_dir`, `theme`
- 테마: Fusion + 전역 QSS(`DARK_QSS`, `LIGHT_QSS`)
- 파일 탐색: 디렉터리 트리(QFileSystemModel) + 파일 테이블(QFileSystemModel + FilesProxy)

### 3.7 BuildLogDialog
- 책임: 빌드/계측 로그 실시간 표출, 중지/닫기 제어

### 3.8 MakefileEditorDialog
- 책임: `Makefile` 편집(열기/저장/다른 이름 저장), 인코딩 자동 판별/유지

---

## 4. 데이터 및 설정

- QSettings 키
  - `project_dir_old`, `project_dir_new`: 원본 프로젝트 선택 경로
  - `last_dir`: 탐색기 루트 마지막 위치
  - `theme`: `dark` 또는 `light`

- 런타임 디렉터리 생성(앱 시작 시)
  - `build/sequence_diagram/`
  - `build/log/`
  - `build/new/`
  - `build/old/`
  - `build/result/`

- 리소스 경로
  - `INDEX_HTML_PATH = ./index.html`
  - `VIEWER_HTML_PATH = ./viewer.html`
  - `SEQUENCE_DIAGRAM_DIR = ./build/sequence_diagram`

---

## 5. 동작 흐름 (Control/Data Flow)

1) 사용자 Old/New 프로젝트 폴더 선택
- 선택 후 내부 작업 디렉터리의 `target_old/`, `target_new/`로 전체 복사
- UI에 경로 표시, 설정 저장

2) 빌드/계측 실행
- `make clean` → `make` → 새/구 테스트 실행 → diff/parser 실행
- 표준 출력이 `BuildLogDialog`에 스트리밍
- 어느 단계 실패 시 즉시 중단 및 실패 코드/상태 표시

3) 시퀀스 다이어그램 열람
- FastAPI 서버 ON → 브라우저에서 `http://127.0.0.1:8000` 접속
- `/api/sequence-diagrams`로 베이스 JSON 리스트 획득
- 각 항목 클릭 시 `/build/sequence_diagram/<name>.json` 등으로 개별 JSON 로딩

4) 파일 탐색/미리보기
- 트리/테이블에서 선택한 항목에 따라 PreviewPanel이 이미지/텍스트/정보로 전환

---

## 6. 외부 인터페이스 사양 (API/UI)

### 6.1 REST API
- `GET /api/sequence-diagrams`
  - 200: `{ "files": ["dvm_test_...Payment_ValidPayment_ShouldSucceed.json", ...] }`
  - 500: `{ "error": "..." }`

- `GET /`
  - 200: `index.html` (text/html)

- `GET /viewer.html`
  - 200: `viewer.html` (text/html)

- `GET /build/sequence_diagram/{file_path:path}`
  - 200: JSON 파일 (application/json)
  - 404: `{ "error": "File not found" }`

### 6.2 데스크톱 UI
- 메뉴/툴바
  - 다크 모드 토글, 검색 입력, 브레드크럼 표시
- 좌 패널(ControlPanel)
  - Old/New 프로젝트 폴더 선택 및 내부 복사
  - 빌드/계측 실행 버튼(순차 파이프라인)
  - 웹서버 On/Off 및 접속 링크 안내
  - Makefile 편집기
- 우 패널
  - 상단: 디렉터리 트리 + 파일/폴더 테이블
  - 하단: PreviewPanel(이미지/텍스트/정보), 로그 콘솔

---

## 7. 에러 처리 및 로깅

- 빌드 파이프라인
  - 각 단계 `QProcess` 종료 코드 검사, 실패 시 즉시 종료/표시
  - 실시간 출력/오류 스트림 병합 표출
- 파일 복사/경로 처리
  - 유효하지 않은 폴더 선택 시 경고
  - 복사 실패 시 대상 폴더 정리 및 오류 메시지
- 웹 서버
  - 시작/종료 예외 시 사용자 알림 및 토글 상태 복원
- API
  - 요청 파일 미존재 시 404 JSON 응답

---

## 8. 비기능 요구사항 (NFR)

- 성능
  - 미리보기의 디렉터리 크기 계산은 큰 트리에서 시간이 소요될 수 있음(rglob 합산)
  - 텍스트 미리보기는 최대 200KB로 제한하여 UI 응답성 보장
- 보안
  - 개발 편의를 위한 CORS 전체 허용(배포 시 필요 범위로 제한 권장)
  - 파일 서비스 대상은 `build/sequence_diagram`으로 제한되어 있음
- 이식성/플랫폼
  - Windows/WSL 환경에서 동작 가정
  - 빌드 명령(예: `./all_tests_new`)은 POSIX 실행 형식이므로 Windows 네이티브 환경에선 실패 가능 → WSL/MinGW 등 사용 권장
- 가용성
  - 백그라운드 웹서버가 GUI와 분리되어 있어 GUI는 독립적 동작 가능

---

## 9. 가정 및 제약

- `src/diff/main.py`, `src/parser/main.py`는 시퀀스 다이어그램 생성 파이프라인에 필요한 스크립트로 가정 (본 SDS 범위 외 내부 로직)
- `all_tests_new`, `all_tests_old` 실행 파일이 작업 디렉터리에 존재하고 실행 가능하다고 가정
- `index.html`, `viewer.html`은 프론트엔드(뷰어) 구현을 포함한다고 가정
- 패키징 시 `sys._MEIPASS` 하 자원 접근 권한 및 쓰기 권한이 확보되어야 함(필요시 AppData 등 대체 경로 고려)

---

## 10. 품질 보증 및 테스트 전략

- 단위/통합 테스트(권장)
  - `UvicornRunner` 시작/중지 라이프사이클 테스트
  - API 핸들러 파일 존재/부재 케이스 테스트
  - `FilesProxy` 필터링 동작 테스트(폴더 자식 일치 시 부모 표시)
  - `PreviewPanel` 텍스트/이미지/바이너리 판정 경계 테스트

- 수동 테스트 시나리오
  1) Old/New 폴더 선택 → 내부 `target_old/target_new`에 복사 확인
  2) 빌드 버튼 → 단계별 로그 확인 및 결과 JSON 생성 확인
  3) 웹서버 ON → `http://127.0.0.1:8000` 접속 → 리스트/JSON 로딩 정상
  4) 탐색기에서 다양한 파일 유형 선택 → 미리보기 동작 확인
  5) Makefile 편집기에서 저장/다른 이름 저장 확인(인코딩 유지)

- 수용 기준(예시)
  - 빌드 파이프라인 6단계가 모두 성공적으로 완료되고 `build/sequence_diagram`에 결과가 생성될 것
  - API가 정상적으로 베이스 JSON 목록을 제공하고, 개별 JSON 요청이 성공할 것
  - GUI 주요 동작(폴더 선택/검색/미리보기/테마 전환/로그 출력)이 오류 없이 동작할 것

---

## 11. 운영/배포 가이드(요약)

- 의존성(파이썬)
  - PySide6, FastAPI, uvicorn, (내장) CORS 미들웨어
- 실행 순서(개발환경)
  - `main.py` 실행 시 필수 디렉터리 자동 생성
  - GUI에서 웹서버 ON 후 브라우저로 접근
- 배포
  - PyInstaller 스펙을 통해 단일 실행 파일 생성(리소스 포함 경로 검증 필요)

---

## 12. 향후 개선 항목 (Backlog)

- 빌드 파이프라인의 플랫폼 의존성 개선(WSL 자동 감지/선택, Windows 네이티브 호환)
- 대용량 디렉터리 크기 계산 비동기화 및 캐싱으로 UI 응답성 향상
- API 보안(필요시 CORS 제한, 인증/인가 도입)
- 로그 저장/내보내기 UI 재활성화 및 확장(현재 주석 처리된 툴바 액션)
- 실패 단계 재시도/스킵 기능 추가
- 시퀀스 다이어그램 뷰어와의 상호작용(하이퍼링크, 비교 모드) 강화

---

## 13. 부록: 주요 경로/키 요약

- 설정 키: `project_dir_old`, `project_dir_new`, `last_dir`, `theme`
- 경로:
  - `./build/sequence_diagram` (JSON)
  - `./build/{log,new,old,result}`
  - `./index.html`, `./viewer.html`
- 엔드포인트:
  - `GET /`, `GET /viewer.html`
  - `GET /api/sequence-diagrams`
  - `GET /build/sequence_diagram/{file_path:path}`
