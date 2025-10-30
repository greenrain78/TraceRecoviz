CXX = clang++-18
CXXFLAGS = -std=c++17 -I. -I$(GTEST_INCLUDE) -include limits -include climits
LDFLAGS = -lgtest -lgtest_main -lpthread -ldl
GTEST_INCLUDE = /usr/include/gtest
GTEST_LIB = /usr/lib/libgtest.a /usr/lib/libgtest_main.a

# 소스/헤더 파일
INJECT_TOOL_SRC = src/generator/inject_trace_tool.cpp
TRACE_SRC = src/generator/trace.cpp
TRACE_HDR = trace.h
LISTENER_HDR = trace_listener.h

# 계측 대상 디렉토리
TARGET_DIRS = target_new target_old
INSTR_DIR = build/instrumented

# 편의 변수
INSTR_NEW = $(INSTR_DIR)/target_new
INSTR_OLD = $(INSTR_DIR)/target_old

all: all_tests

# Clang LibTooling 도구 빌드
inject_trace_tool: $(INJECT_TOOL_SRC)
	clang++-18 -std=c++17 $(INJECT_TOOL_SRC) -o inject_trace_tool \
    `llvm-config-18 --cxxflags --ldflags --system-libs --libs all` \
    -lclang-cpp

# 테스트 코드 계측 (build/instrumented/<dir>/*.{cc,cpp,h,hpp} 생성)
instrument: inject_trace_tool
	mkdir -p $(INSTR_DIR)
	for d in $(TARGET_DIRS); do \
		for f in $$(find $$d -type f \( -name '*.cc' -o -name '*.cpp' -o -name '*.h' -o -name '*.hpp' \)); do \
			rel_path=$${f#$$d/}; \
			out_file=$(INSTR_DIR)/$$d/$$rel_path; \
			out_dir=$$(dirname $$out_file); \
			mkdir -p $$out_dir; \
			./inject_trace_tool $$f > $$out_file; \
		done; \
	done

# 디렉토리별로 별도 테스트 바이너리 생성
all_tests_new: instrument $(TRACE_SRC) $(TRACE_HDR) $(LISTENER_HDR)
	$(CXX) $(CXXFLAGS) -DTRACE_VARIANT=\"new\" -Itarget_new -I$(INSTR_NEW) -include $(LISTENER_HDR) \
	$$(find $(INSTR_NEW) -type f \( -name '*.cc' -o -name '*.cpp' \)) $(TRACE_SRC) -o $@ $(GTEST_LIB)

all_tests_old: instrument $(TRACE_SRC) $(TRACE_HDR) $(LISTENER_HDR)
	$(CXX) $(CXXFLAGS) -DTRACE_VARIANT=\"old\" -Itarget_old -I$(INSTR_OLD) -include $(LISTENER_HDR) \
	$$(find $(INSTR_OLD) -type f \( -name '*.cc' -o -name '*.cpp' \)) $(TRACE_SRC) -o $@ $(GTEST_LIB)

# 메타 타겟: 두 바이너리 모두 빌드
all_tests: all_tests_new all_tests_old

# 정리
clean:
	rm -f inject_trace_tool all_tests_new all_tests_old
	rm -rf $(INSTR_DIR)
	rm -f build/log/*.log
	rm -f trace_hooks_output.log trace_hooks_output.new.log trace_hooks_output.old.log

re: clean runAll