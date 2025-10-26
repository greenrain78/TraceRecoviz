# TraceRecoViz 소프트웨어 설계 명세서(SDS)

- 버전: 0.1 (초안)
- 날짜: 2025-10-18
- 저장소: greenrain78/TraceRecoviz
- 소유자: 작성자 미정(TBD), 검토자 미정(TBD)

## 개정 이력(Revision history)

- 0.1 (2025-10-18): 기본 스켈레톤과 작성 계획 초안 추가.

## 1. 소개(Introduction)

### 1.1 목적(Purpose)
TraceRecoViz는 데스크톱 GUI와 임베디드 웹 서비스를 통해 C++ 빌드를 계측하고, 실행 추적을 수집하여 OLD/NEW 대상 프로젝트 간의 동작을 시각적 시퀀스 다이어그램으로 비교하는 도구입니다. 본 SDS는 구현과 유지보수를 위한 아키텍처, 모듈, 데이터 흐름, API, 배포, 품질 속성을 기술합니다.

### 1.2 범위(Scope)
- 데스크톱 GUI 애플리케이션(PySide6)
- 임베디드 FastAPI 백엔드(Uvicorn) 및 단독 서버 옵션
- 빌드/추적 계측 파이프라인(Make/Bear, Clang/LLVM 18, 계측 도구)
- 시퀀스 다이어그램 생성 및 뷰어(`index.html`/`viewer.html`)
- 지원 OS: Windows(WSL), Linux; PyInstaller 및/또는 Docker 패키징

### 1.3 용어/약어(Definitions)
- SDS: Software Design Specification
- GUI: Graphical User Interface
- API: Application Programming Interface
- WSL: Windows Subsystem for Linux
- Uvicorn: FastAPI용 ASGI 서버

### 1.4 참조(References)
- 저장소 파일: `main.py`, `server.py`, `index.html`, `viewer.html`, `Dockerfile`, `Makefile`, `inject_trace_tool/`, `src/`
- Clang/LLVM 18 설치 노트: `ReadMe.md`
- 시퀀스 다이어그램 샘플: `build/sequence_diagram/*.json`

## 2. 시스템 개요(System overview)

### 2.1 컨텍스트와 목표
- 테스트를 계측하여 두 코드베이스(OLD/NEW)의 동작을 비교하고, 시퀀스 다이어그램으로 표현
- GUI에서 프로젝트 선택, 계측/빌드 실행, 결과 확인까지 일련의 흐름 제공
- 로컬 HTTP API로 JSON 다이어그램을 제공하여 웹 뷰어에서 열람

### 2.2 주요 시나리오
- 사용자가 OLD/NEW 소스 폴더를 선택하면, 앱이 작업 디렉터리 내 `target_old/`, `target_new/`로 복제
- 계측/빌드 실행 시 `build/sequence_diagram/`에 다이어그램 JSON 생성
- 임베디드 웹서버를 토글하고 뷰어에서 흐름 비교

### 2.3 이해관계자
- 동작 변경을 검증하는 개발자/테스터
- 추적 기반 diff를 CI/빌드에 통합하는 엔지니어

### 2.4 제약 및 가정
- Linux/WSL 환경에서 Clang/LLVM 18과 GoogleTest 사용 가능
- 앱 디렉터리 내에서 복제/빌드 가능한 파일 시스템 권한
- Linux에서는 한글 폰트(Noto/Nanum)가 필요할 수 있음

## 3. 아키텍처(Architecture)

### 3.1 상위 구조(High-level view)
- 데스크톱 GUI(PySide6, `main.py`): 프로젝트 선택, 빌드 명령, 결과 뷰 조율
- 임베디드 백엔드(FastAPI, `main.py` 내 `UvicornRunner`): 뷰어용 REST 엔드포인트 제공; `server.py` 단독 실행도 가능
- 빌드/계측 파이프라인: Make/Bear, Clang/LLVM 18, `src/`, `inject_trace_tool/`를 통해 `build/sequence_diagram/`에 JSON 생성
- 웹 뷰어(`index.html`, `viewer.html`): 백엔드에서 JSON을 받아 시퀀스 다이어그램 렌더링

### 3.2 컴포넌트 다이어그램(추가 예정)
- Mermaid/PlantUML로 GUI/백엔드/빌드 파이프라인/데이터 저장소 관계를 도식화 예정

### 3.3 프로세스/스레드
- GUI 메인 스레드(Qt 이벤트 루프)
- ASGI 서버 스레드(`UvicornRunner`): GUI에서 시작/중지
- 빌드 서브프로세스: `QProcess`로 make 단계 실행, 표준 입출력 통합 스트리밍

### 3.4 핵심 모듈(Key modules)
- `UvicornRunner`: 백그라운드 스레드에서 uvicorn 생명주기 관리
- `BuildLogDialog`: 빌드 로그 실시간 뷰, 중지/닫기 제어
- `ControlPanel`: 프로젝트 선택, 작업 버튼, 서버 토글, Makefile 편집기
- `FilesProxy`, `PreviewPanel`: 검색/필터, 텍스트/이미지/폴더 정보 미리보기
- `MainWindow`: UI 구성/테마/QSettings/시그널 연결
- `server.py`: 임베디드 엔드포인트를 반영한 단독 FastAPI 앱
- `src/*`, `inject_trace_tool/*`: 계측/파싱/다이어그램 생성(세부는 4장 참고)

## 4. 상세 설계(Detailed design)

### 4.1 C++ 코드 실행 추적 계측(Instrumentation)
- 계측기(Clang LibTooling): `src/generator/inject_trace_tool.cpp`
  - 함수 진입에 `trace_enter(...)`, 반환/함수 종료 시점에 `trace_return(...)` 삽입
  - GoogleTest 매크로를 로깅 버전으로 치환(`EXPECT_*`/`ASSERT_*` → `*_LOG`)
  - 시스템 헤더/`testing::` 내부 제외, 템플릿 canonical type 적용, 결과는 stdout으로 출력(빌드 전 변환 또는 파일로 리다이렉션)
- Trace 런타임(C++): `trace.h`, `src/generator/trace.cpp`
  - 스레드 로컬 호출 스택으로 caller/callee 추적, 인자/반환값 캡처, 타입 디매글, 생성/소멸 식별
  - `trace_listener.h`가 테스트 단위로 로그 파일을 열어 `build/<variant>/*.log`에 기록
- 로그 포맷 핵심(CALL/RETURN/ASSERTION_CALL)
  - CALL: `[Test] [CALL] |caller=...| <caller_sig> >> |callee=...| <callee_sig> |ARGS|(...)`
  - RETURN: `[Test] [RETURN] |caller=...| <caller_sig> >> |callee=...| <callee_sig> => <값/constructed/destroyed>`
  - ASSERTION_CALL: `[Test] [ASSERTION_CALL] EXPECT_EQ(a,b)` 등

### 4.2 테스트 실행 로그 수집(Runner)
- 테스트 프레임워크: GoogleTest + 커스텀 리스너(`trace_listener.h`)
  - 테스트 시작 시 안전한 파일명으로 로그 파일 오픈(예: `build/old/*.log`, `build/new/*.log`)
  - 수명 이벤트(프로그램/스위트/테스트 시작/종료)와 단언 결과를 기록
- 실행 방법
  - OLD/NEW 각각의 계측된 테스트 바이너리 실행(스위트 전체/개별 테스트 지원 가능)
  - GUI에서는 `QProcess`로 make/실행을 호출하고 통합 로그를 팝업에 스트리밍

### 4.3 로그 파싱 및 분석(Parser)
- Diff 정규화: `src/diff/main.py`
  - 입력: `build/old/*.log` vs `build/new/*.log` → 출력: `build/result/*.log`
  - 포인터 주소 등 가변 토큰을 `@ADDR`로 치환, 줄 단위 `+/-/  ` 주석 부여
- 로그 파싱: `src/parser/main.py`, `src/parser/utils/trace_parser.py`
  - 입력: `build/{result,new,old}/*.log`
  - ASSERTION_CALL은 루트(Self-link) 이벤트로, diff 마커(`+/-/=/!`)는 색상으로 반영
  - 엣지 케이스: 대용량 로그(라인 처리), CALL/RETURN 불일치 허용(비대칭 가능), 익명 네임스페이스/수식어 정규화

### 4.4 시각화(Diagram Generator)
- 출력 모델: GoJS GraphLinksModel JSON → `build/sequence_diagram/`
  - 파일명: `{name}.json`(base), `{name}_old.json`, `{name}_new.json`
  - 노드(lifeline): 클래스/객체(+포인터 키), 링크(message): 호출/반환/단언
- 뷰어 연계
  - 백엔드(API)에서 다이어그램 목록/파일 서빙 → `index.html`/`viewer.html`이 fetch하여 렌더링
  - 생성/소멸 이벤트, 파라미터/반환값은 라벨로 표시; diff 색상은 링크/주석에 반영
- 계약(입력/출력)
  - 입력: OLD/NEW C++ 소스, 계측 적용 테스트 바이너리, Python 및 도구체인
  - 출력: 로그(`build/old|new|result/*.log`), 다이어그램(`build/sequence_diagram/*.json`)
- Make/Tasks 통합(권장)
  - `instrument` → `test_old/new` → `diff` → `gen` → 뷰/서빙 순으로 체인
- 검증(Verification)
  - 예상 폴더에 로그 생성/JSON 로딩/색상 반영 등 기본 동작 확인

### 4.5 GUI 설계(PySide6)
- 레이아웃: 좌측 컨트롤 패널, 우측 상단(디렉터리 트리+파일 테이블)/하단(미리보기+로그)
- 테마: Fusion + 다크/라이트 QSS; QSettings로 사용자 선호 저장
- 사용성: 재귀 필터, 브레드크럼, 텍스트/이미지 미리보기, Makefile 편집기

### 4.6 백엔드 API 설계(FastAPI)
- 기본 경로: `http://127.0.0.1:8000`
- 엔드포인트:
  - GET `/` -> `index.html`
  - GET `/viewer.html` -> `viewer.html`
  - GET `/api/sequence-diagrams` -> `{ files: string[] }` (OLD/NEW 쌍이 존재하는 베이스 파일명 목록)
  - GET `/build/sequence_diagram/{file_path}` -> JSON 파일 원본 반환
- CORS: 개발 단계에서는 `*`, 운영 시 제한 권장

### 4.7 데이터 모델(Data model)
- 시퀀스 다이어그램 JSON:
  - 위치: `build/sequence_diagram/*.json`
  - 명명: `{test_name}.json`, `{test_name}_old.json`, `{test_name}_new.json`
  - 최소 스키마(확인 필요):
    - metadata: 테스트명, 타임스탬프, 소스(old/new)
    - lifelines: 구성요소/객체 목록
    - messages: 호출/응답(호출자, 피호출자, 라벨, 시간)
- 설정(QSettings):
  - `project_dir_old`, `project_dir_new`, `last_dir`, `theme`

### 4.8 오류 처리 및 로깅(Error handling and logging)
- 빌드 서브프로세스 출력은 `QProcess`로 수집해 `BuildLogDialog`에 표시
- API는 상태 코드와 함께 JSON 에러 반환(예: 404 파일 없음)
- UI는 `QMessageBox`로 사용자에 오류 전달(복사/빌드/서버)

### 4.9 보안 및 개인정보(Security and privacy)
- 임베디드 서버 기본 호스트는 로컬(127.0.0.1); 개발 단계 CORS 개방, 운영에서는 제한 권장
- 기본 인증 미구현; 공유 환경에서는 토큰/허용 오리진 도입 권장
- 파일 서빙은 `build/sequence_diagram/` 경로로 제한

## 5. 배포(Deployment)

### 5.1 데스크톱 패키징
- PyInstaller spec: `TraceRecoviz_linux.spec`, `SimpleMakeBuilder.spec`(검토 및 정합)
- 예시: onefile + windowed + 데이터 번들링

### 5.2 컨테이너화(Containerization)
- `Dockerfile`로 Clang/LLVM 18 및 빌드 도구 제공; 프로젝트 마운트 후 컨테이너 내 `make`/`bear` 실행

### 5.3 환경 요구사항
- Linux/WSL + Clang/LLVM 18 + GoogleTest
- Python 3 패키지: PySide6, FastAPI, Uvicorn, (선택) PyInstaller
- CJK 폰트: `fonts-noto-cjk`, `fonts-nanum` 등(한글 렌더링)

## 6. 품질 속성(비기능 요구, NFR)
- 성능: 빌드 로그 스트리밍, 미리보기에서 대용량 텍스트 로드 제한(~200KB), JSON 지연 로드
- 호환성: Windows(WSL) 및 Linux, 최신 브라우저 기반 웹 뷰어
- 사용성: 명확한 피드백, 다크 모드 토글, 견고한 파일 미리보기, 친절한 메시지
- 신뢰성: 서브프로세스 생명주기 제어, 안전한 디렉터리 조작(깨끗한 생성/복사)
- 보안: 파일 서빙 범위 제한, 운영 시 CORS 제한
- 국제화: 한국어 라벨/폰트 지원(Linux 폰트 설치 가이드)

## 7. 테스트 전략(Testing strategy)
- 단위 테스트: `target_*` 샘플의 C/C++ 타깃에 GoogleTest 적용
- 기능(API) 테스트: 목록/파일 서빙 엔드포인트 동작 검증
- UI 스모크 테스트: 폴더 선택→복사→빌드→미리보기→서버 토글 기본 흐름
- 테스트 데이터: `build/sequence_diagram/*` JSON 샘플

## 8. 운영 고려사항(Operational considerations)
- 구성: QSettings와 Makefile로 구성/경로 관리
- 모니터링: UI 내 빌드 로그 확인; 추후 백엔드 구조적 로깅 도입 검토
- 알려진 리스크/오픈 이슈:
  - 다이어그램 JSON 스키마의 공식화 미완료
  - Makefile/도구 레벨의 계측 단계 문서화 보강 필요
  - 공유 네트워크 환경에서 CORS/보안 강화 필요

## 9. 로드맵 및 향후 개선(Roadmap)
- JSON 스키마 정식화 및 검증 체계 추가
- 뷰어 개선: diff 오버레이, 객체 라이프라인 색상 표시, 파라미터 변화 강조
- CI 통합 및 산출물 게시
- 크로스플랫폼 패키징(Windows 네이티브 빌드)

---

## SDS 작성 계획(본 프로젝트)

### 목표(Objectives)
현 시스템과 향후 개선 계획을 정확히 문서화하여, 기여자가 TraceRecoViz를 안전하게 유지/확장할 수 있도록 합니다.

### 작업 범위(Scope of work)
- 아키텍처/모듈/데이터/API/배포/NFR/테스트/운영을 포괄하는 SDS v1.0 완성
- 다이어그램 2종 이상(컨텍스트+컴포넌트) 및 실제 JSON에 매핑되는 시퀀스 예제 1건 포함
- 시퀀스 다이어그램용 JSON 스키마 정의 및 저장소 반영

### 입력 자료(Inputs)
- 소스 코드: `main.py`, `server.py`, `src/*`, `inject_trace_tool/*`
- 빌드 산출물/샘플: `build/sequence_diagram/*.json`
- 환경/설치 노트: `ReadMe.md`, `Dockerfile`, `Makefile`

### 역할(Roles)
- 작성자: 미정(TBD)
- 검토자: 미정(TBD, 메인테이너/리드)

### 마일스톤 및 일정(권장)
- M1(1~2일): SDS 스켈레톤/목차 확정, 범위/가정 확인
- M2(3~4일): 아키텍처/컴포넌트/모듈 상세, 다이어그램 초안
- M3(5일차): API/데이터 모델, JSON 스키마/예제 추가
- M4(6일차): 배포/NFR/테스트/운영, 보안 검토
- M5(7일차): 리뷰 반영, SDS v1.0 공개

### 산출물(Deliverables)
- `docs/SDS.md`(본 문서) v1.0 업데이트
- `docs/diagrams/` 다이어그램 원본(Mermaid/PlantUML) 및 내보내기 이미지
- `docs/schema/sequence-diagram.schema.json`(초안 및 검증 예제)

### 검토/승인 기준(Review & acceptance)
- 완전성: 모든 섹션 충족, 저장소 상태와 일치
- 정확성: 앱 실행/출력 점검으로 API/경로 검증
- 명확성: 다이어그램/예제 포함, 비기능 요구 반영
- 보안: CORS/서빙 범위 명시, 리스크 기재

### 편집 체크리스트(Working prompts)
- [ ] `main.py`에서 GUI 클래스/책임 확인
- [ ] `server.py` 및 임베디드 FastAPI의 API 계약 확인
- [ ] 빌드 파이프라인/Makefile 타깃 정밀 추적 및 문서화
- [ ] 샘플 파일에서 JSON 구조 역공학 후 스키마/예제 작성
- [ ] 다이어그램 작성 및 본문 링크 추가
- [ ] WSL/Linux, Docker 안내 검증

---

> 주의: 조사/구현 진행에 따라 미정(TBD)과 플레이스홀더를 실제 내용으로 교체하세요. 코드 변화에 맞춰 SDS를 지속적으로 최신화하세요.
