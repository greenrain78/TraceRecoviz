cmake_minimum_required(VERSION 3.15)
project(TraceRecoviz LANGUAGES C CXX)

# C++ 표준 설정
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 플랫폼 감지
if(WIN32)
    message(STATUS "Configuring for Windows")
    set(PLATFORM_WINDOWS TRUE)
elseif(UNIX AND NOT APPLE)
    message(STATUS "Configuring for Linux")
    set(PLATFORM_LINUX TRUE)
elseif(APPLE)
    message(STATUS "Configuring for macOS")
    set(PLATFORM_MACOS TRUE)
endif()

# LLVM/Clang 찾기 (inject_trace_tool 빌드용)
# - Windows(MSYS2 UCRT64/MINGW64) 기본 경로 힌트 추가
set(_LLVM_HINTS
    "$ENV{LLVM_DIR}"
    "C:/msys64/ucrt64/lib/cmake/llvm"
    "C:/msys64/mingw64/lib/cmake/llvm"
)
set(_CLANG_HINTS
    "$ENV{Clang_DIR}"
    "C:/msys64/ucrt64/lib/cmake/clang"
    "C:/msys64/mingw64/lib/cmake/clang"
)
find_package(LLVM REQUIRED CONFIG HINTS ${_LLVM_HINTS})
find_package(Clang REQUIRED CONFIG HINTS ${_CLANG_HINTS})

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")
message(STATUS "Using ClangConfig.cmake in: ${Clang_DIR}")

# LLVM include 디렉토리 추가
include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})

# GoogleTest 찾기
set(_GTEST_HINTS
    "$ENV{GTest_DIR}"
    "C:/msys64/ucrt64/lib/cmake/GTest"
    "C:/msys64/mingw64/lib/cmake/GTest"
)
find_package(GTest REQUIRED HINTS ${_GTEST_HINTS})
include_directories(${GTEST_INCLUDE_DIRS})

# Threads
find_package(Threads REQUIRED)

# 프로젝트 디렉토리
set(SRC_DIR ${CMAKE_SOURCE_DIR}/src)
set(TARGET_NEW_DIR ${CMAKE_SOURCE_DIR}/target_new)
set(TARGET_OLD_DIR ${CMAKE_SOURCE_DIR}/target_old)
set(BUILD_DIR ${CMAKE_BINARY_DIR})
set(INSTR_DIR ${BUILD_DIR}/instrumented)
set(INSTR_NEW_DIR ${INSTR_DIR}/target_new)
set(INSTR_OLD_DIR ${INSTR_DIR}/target_old)

# 1. inject_trace_tool 빌드
add_executable(inject_trace_tool
    ${SRC_DIR}/generator/inject_trace_tool.cpp
)

# LLVM/Clang 라이브러리 링크
# 최신 LLVM/Clang 패키지에서는 개별 컴포넌트 대신 단일 라이브러리(clang-cpp) 사용이 가장 호환성이 높습니다.
# MinGW/MSCV 환경 모두에서 심볼 해석 문제를 줄이기 위해 clang-cpp로 링크합니다.
target_link_libraries(inject_trace_tool
    PRIVATE
    clang-cpp
    LLVM
)

# Windows에서 추가 링크 옵션
if(WIN32)
    target_link_libraries(inject_trace_tool PRIVATE version)
endif()

# 2. 계측된 파일 생성을 위한 커스텀 타겟

# target_new 계측
file(GLOB TARGET_NEW_SOURCES 
    "${TARGET_NEW_DIR}/*.cc" 
    "${TARGET_NEW_DIR}/*.cpp"
)
file(GLOB TARGET_NEW_HEADERS 
    "${TARGET_NEW_DIR}/*.h" 
    "${TARGET_NEW_DIR}/*.hpp"
)

# target_old 계측
file(GLOB TARGET_OLD_SOURCES 
    "${TARGET_OLD_DIR}/*.cc" 
    "${TARGET_OLD_DIR}/*.cpp"
)
file(GLOB TARGET_OLD_HEADERS 
    "${TARGET_OLD_DIR}/*.h" 
    "${TARGET_OLD_DIR}/*.hpp"
)

# 계측 디렉토리 생성
file(MAKE_DIRECTORY ${INSTR_NEW_DIR})
file(MAKE_DIRECTORY ${INSTR_OLD_DIR})

# 계측 커맨드 생성 함수
function(add_instrumentation_commands TARGET_DIR INSTR_DIR SOURCE_FILES HEADER_FILES)
    set(INSTRUMENTED_FILES "")
    
    # 소스 파일 계측
    foreach(SOURCE_FILE ${SOURCE_FILES})
        get_filename_component(FILENAME ${SOURCE_FILE} NAME)
        set(OUTPUT_FILE ${INSTR_DIR}/${FILENAME})
        add_custom_command(
            OUTPUT ${OUTPUT_FILE}
            COMMAND inject_trace_tool ${SOURCE_FILE} > ${OUTPUT_FILE}
            DEPENDS inject_trace_tool ${SOURCE_FILE}
            COMMENT "Instrumenting ${FILENAME}"
        )
        list(APPEND INSTRUMENTED_FILES ${OUTPUT_FILE})
    endforeach()
    
    # 헤더 파일 계측
    foreach(HEADER_FILE ${HEADER_FILES})
        get_filename_component(FILENAME ${HEADER_FILE} NAME)
        set(OUTPUT_FILE ${INSTR_DIR}/${FILENAME})
        add_custom_command(
            OUTPUT ${OUTPUT_FILE}
            COMMAND inject_trace_tool ${HEADER_FILE} > ${OUTPUT_FILE}
            DEPENDS inject_trace_tool ${HEADER_FILE}
            COMMENT "Instrumenting ${FILENAME}"
        )
        list(APPEND INSTRUMENTED_FILES ${OUTPUT_FILE})
    endforeach()
    
    set(INSTRUMENTED_FILES ${INSTRUMENTED_FILES} PARENT_SCOPE)
endfunction()

# target_new 계측
add_instrumentation_commands(
    ${TARGET_NEW_DIR} 
    ${INSTR_NEW_DIR}
    "${TARGET_NEW_SOURCES}"
    "${TARGET_NEW_HEADERS}"
)
set(INSTRUMENTED_NEW_FILES ${INSTRUMENTED_FILES})

# 계측된 헤더(포함 파일) 생성 보장
set(INSTRUMENTED_NEW_HEADERS "")
foreach(FILE ${INSTRUMENTED_NEW_FILES})
    if(FILE MATCHES "\\.(h|hpp)$")
        list(APPEND INSTRUMENTED_NEW_HEADERS ${FILE})
    endif()
endforeach()
add_custom_target(instrument_headers_new DEPENDS ${INSTRUMENTED_NEW_HEADERS})

# target_old 계측
add_instrumentation_commands(
    ${TARGET_OLD_DIR}
    ${INSTR_OLD_DIR}
    "${TARGET_OLD_SOURCES}"
    "${TARGET_OLD_HEADERS}"
)
set(INSTRUMENTED_OLD_FILES ${INSTRUMENTED_FILES})

# 계측된 헤더(포함 파일) 생성 보장
set(INSTRUMENTED_OLD_HEADERS "")
foreach(FILE ${INSTRUMENTED_OLD_FILES})
    if(FILE MATCHES "\\.(h|hpp)$")
        list(APPEND INSTRUMENTED_OLD_HEADERS ${FILE})
    endif()
endforeach()
add_custom_target(instrument_headers_old DEPENDS ${INSTRUMENTED_OLD_HEADERS})

# 계측된 소스 파일만 필터링
set(INSTRUMENTED_NEW_SOURCES "")
foreach(FILE ${INSTRUMENTED_NEW_FILES})
    if(FILE MATCHES "\\.(cc|cpp)$")
        list(APPEND INSTRUMENTED_NEW_SOURCES ${FILE})
    endif()
endforeach()

set(INSTRUMENTED_OLD_SOURCES "")
foreach(FILE ${INSTRUMENTED_OLD_FILES})
    if(FILE MATCHES "\\.(cc|cpp)$")
        list(APPEND INSTRUMENTED_OLD_SOURCES ${FILE})
    endif()
endforeach()

# 3. all_tests_new 빌드
add_executable(all_tests_new
    ${INSTRUMENTED_NEW_SOURCES}
    ${SRC_DIR}/generator/trace.cpp
)

add_dependencies(all_tests_new instrument_headers_new)

target_include_directories(all_tests_new PRIVATE
    ${CMAKE_SOURCE_DIR}
    ${TARGET_NEW_DIR}
    ${INSTR_NEW_DIR}
    ${GTEST_INCLUDE_DIRS}
)

target_compile_definitions(all_tests_new PRIVATE
    TRACE_VARIANT="new"
)

# 사전 포함 헤더: MSVC(/FI) vs GCC/Clang(-include)
if(MSVC)
    target_compile_options(all_tests_new PRIVATE /FI"${CMAKE_SOURCE_DIR}/trace_listener.h")
else()
    target_compile_options(all_tests_new PRIVATE -include ${CMAKE_SOURCE_DIR}/trace_listener.h)
endif()

target_link_libraries(all_tests_new PRIVATE
    GTest::gtest
    GTest::gtest_main
    Threads::Threads
)

if(UNIX)
    target_link_libraries(all_tests_new PRIVATE dl)
endif()

# 4. all_tests_old 빌드
add_executable(all_tests_old
    ${INSTRUMENTED_OLD_SOURCES}
    ${SRC_DIR}/generator/trace.cpp
)

add_dependencies(all_tests_old instrument_headers_old)

target_include_directories(all_tests_old PRIVATE
    ${CMAKE_SOURCE_DIR}
    ${TARGET_OLD_DIR}
    ${INSTR_OLD_DIR}
    ${GTEST_INCLUDE_DIRS}
)

target_compile_definitions(all_tests_old PRIVATE
    TRACE_VARIANT="old"
)

if(MSVC)
    target_compile_options(all_tests_old PRIVATE /FI"${CMAKE_SOURCE_DIR}/trace_listener.h")
else()
    target_compile_options(all_tests_old PRIVATE -include ${CMAKE_SOURCE_DIR}/trace_listener.h)
endif()

target_link_libraries(all_tests_old PRIVATE
    GTest::gtest
    GTest::gtest_main
    Threads::Threads
)

if(UNIX)
    target_link_libraries(all_tests_old PRIVATE dl)
endif()

# 5. 정리 타겟
add_custom_target(clean-all
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${INSTR_DIR}
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${BUILD_DIR}/log
    COMMAND ${CMAKE_COMMAND} -E remove -f trace_hooks_output.log trace_hooks_output.new.log trace_hooks_output.old.log
    COMMENT "Cleaning all generated files"
)

# 6. 편의 타겟
add_custom_target(all_tests
    DEPENDS all_tests_new all_tests_old
    COMMENT "Building both test executables"
)

# 출력 메시지
message(STATUS "Build configuration complete")
message(STATUS "  - inject_trace_tool: Code instrumentation tool")
message(STATUS "  - all_tests_new: Test executable for new version")
message(STATUS "  - all_tests_old: Test executable for old version")
message(STATUS "")
message(STATUS "To build: cmake --build . --target all_tests")
message(STATUS "To clean: cmake --build . --target clean-all")
