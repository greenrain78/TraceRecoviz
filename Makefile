ACXX = ag++
CXXFLAGS = -std=c++17 -I./src -I. -I./builder -I./gtest -I./gtest/googletest/googletest/include
LDFLAGS = -lpthread
GTEST_LIBS = ./gtest/libgtest.a ./gtest/libgtest_main.a

TARGET = test

# 소스 파일과 오브젝트 파일 정의
SRCS = src/sample8_unittest.cc src/sample7_unittest.cc src/sample6_unittest.cc src/sample5_unittest.cc src/sample4_unittest.cc src/sample3_unittest.cc src/sample2_unittest.cc src/sample1_unittest.cc
SRCS += src/sample1.cc src/sample2.cc src/sample4.cc
OBJS = $(patsubst %.cc, %.o, $(SRCS))

all: prepare $(TARGET)

prepare:
	@echo "🔧 Running Python scripts..."
	python3 builder/generate_logger.py

$(TARGET): $(OBJS)
	$(ACXX) $(CXXFLAGS) -o $@ $^ $(GTEST_LIBS) $(LDFLAGS)

# src/my_class.cc → src/my_class.o
src/%.o: src/%.cc
	$(ACXX) $(CXXFLAGS) -c $< -o $@

# 루트에 있는 my_class_test.cc → my_class_test.o
%.o: %.cc
	$(ACXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f src/*.o *.o *.acd $(TARGET) trace.log auto_*_logger.ah