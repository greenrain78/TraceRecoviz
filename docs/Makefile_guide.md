# Makefile 문서화

이 문서는 프로젝트의 최상위 Makefile의 주요 타겟과 동작을 설명합니다.

## 주요 변수
- **CXX**: C++ 컴파일러 (clang++-18)
- **CXXFLAGS**: C++ 컴파일 플래그 (C++17, GTest 포함 경로)
- **LDFLAGS**: 링크 플래그 (gtest, pthread, dl)
- **GTEST_INCLUDE**: GTest 헤더 경로
- **GTEST_LIB**: GTest 라이브러리 경로
- **INJECT_TOOL_SRC**: 계측 도구 소스 파일
- **TRACE_SRC, TRACE_HDR, LISTENER_HDR**: 트레이스 관련 소스/헤더
- **TARGET_DIRS**: 계측 대상 디렉토리 (target_new, target_old)
- **INSTR_DIR**: 계측 결과 디렉토리 (build/instrumented)
- **INSTR_NEW, INSTR_OLD**: 계측 결과 디렉토리별 경로

## 주요 타겟

### all (기본 타겟)
- `all_tests` 타겟을 빌드합니다.

### inject_trace_tool
- Clang LibTooling 기반 계측 도구(`inject_trace_tool`)를 빌드합니다.
- 빌드 명령에 llvm-config, clang-cpp 라이브러리 사용.

### instrument
- `inject_trace_tool`을 이용해 `target_new`, `target_old` 디렉토리 내의 소스/헤더 파일을 계측합니다.
- 계측 결과는 `build/instrumented/<dir>/`에 저장됩니다.

### all_tests_new, all_tests_old
- 계측된 소스와 트레이스 코드를 링크하여 각각의 테스트 바이너리(`all_tests_new`, `all_tests_old`)를 빌드합니다.
- GTest 라이브러리와 함께 빌드됩니다.
- `TRACE_VARIANT` 매크로로 new/old 구분.

### all_tests
- `all_tests_new`, `all_tests_old`를 모두 빌드하는 메타 타겟입니다.

### clean
- 빌드 산출물, 계측 결과, 로그 파일 등을 삭제합니다.

### re
- `clean` 후 `runAll` 실행 (단, runAll 타겟은 Makefile에 정의되어 있지 않음)

## 빌드/실행 예시
```sh
make            # 전체 테스트 바이너리 빌드
make clean      # 빌드 산출물 정리
make inject_trace_tool  # 계측 도구만 빌드
make instrument # 계측만 수행
```

## 참고
- GTest, Clang, LLVM 관련 라이브러리 및 헤더가 시스템에 설치되어 있어야 합니다.
- WSL/리눅스 환경 기준으로 작성되어 있습니다.
