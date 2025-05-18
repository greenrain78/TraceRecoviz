CXX = clang++-18
CXXFLAGS = -std=c++17 -I. -I$(GTEST_INCLUDE)
LDFLAGS = -lgtest -lgtest_main -lpthread -ldl
GTEST_INCLUDE = /usr/include/gtest
GTEST_LIB = /usr/lib/libgtest.a /usr/lib/libgtest_main.a
# GoogleTest 경로

# 소스/헤더 파일
INJECT_TOOL_SRC = src/generator/inject_trace_tool.cpp
TRACE_SRC = src/generator/trace.cpp
TRACE_HDR = trace.h
LISTENER_HDR = trace_listener.h

# 계측 대상 (테스트 디렉토리)
TEST_SRCS = $(wildcard target/*.cpp) $(wildcard target/*.cc)
INSTR_DIR = build/instrumented

all: all_tests

# Clang LibTooling 도구 빌드
inject_trace_tool: $(INJECT_TOOL_SRC)
	clang++-18 -std=c++17 $(INJECT_TOOL_SRC) -o inject_trace_tool \
    `llvm-config-18 --cxxflags --ldflags --system-libs --libs all` \
    -lclang-cpp



# 테스트 코드 계측 (instrumented/*.cpp 생성)
instrument: inject_trace_tool
	mkdir -p build/instrumented
	for f in $(wildcard target/*.cc) $(wildcard target/*.cpp) $(wildcard target/*.h) $(wildcard target/*.hpp); do \
		base=$$(basename $$f); \
		./inject_trace_tool $$f > build/instrumented/$$base; \
	done


# 모든 테스트 컴파일 (계측된 코드와 trace 라이브러리 링크)
# 테스트 바이너리 빌드 (계측 코드 + trace + GoogleTest)
all_tests: instrument $(TRACE_SRC) $(TRACE_HDR) $(LISTENER_HDR)
	$(CXX) $(CXXFLAGS) -Itarget -I$(INSTR_DIR) -include trace_listener.h \
	$(INSTR_DIR)/*.cc $(TRACE_SRC) -o $@ $(GTEST_LIB)

# 테스트 실행 (로그 파일 생성)
runAll: all_tests
	./all_tests > trace_hooks_output.log
	python3 src/parser/convertLogtoJson.py

# 이전 파일 삭제
clean:
	rm -f inject_trace_tool all_tests
	rm -f $(INSTR_DIR)/*.cc
	rm -f build/log/*.log
	rm -f trace_hooks_output.log

re: clean runAll