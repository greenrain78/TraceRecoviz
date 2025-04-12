# Makefile

# Compiler
ACPP = ag++    # AspectC++ 컴파일러
CXXFLAGS = -std=c++17 -Igoogletest/googletest/include -Igoogletest/googletest -Igoogletest/googletest/internal -I. 
LDFLAGS = -lpthread

# 대상 파일
GTEST_DIR = googletest/googletest
GTEST_SRCS = $(GTEST_DIR)/src/gtest-all.cc
GTEST_HDRS = $(GTEST_DIR)/include/gtest

# 결과물
OUT = test_exec
LIB = libgtest.a

# 기본 타겟
all: $(LIB) $(OUT)

# gtest 정적 라이브러리 빌드
$(LIB):
	$(ACPP) -c $(CXXFLAGS) $(GTEST_SRCS)
	ar rcs $(LIB) gtest-all.o

# 테스트 실행 파일
$(OUT): main.cpp logger.ah $(LIB)
	$(ACPP) main.cpp -o $(OUT) $(LIB) $(CXXFLAGS) $(LDFLAGS)

clean:
	rm -f *.o $(OUT) $(LIB)
