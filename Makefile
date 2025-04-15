ACXX = ag++
CXXFLAGS = -std=c++17 -I./src -I. -I./builder -I./gtest -I./gtest/googletest/googletest/include
LDFLAGS = -lpthread
GTEST_LIBS = ./gtest/libgtest.a ./gtest/libgtest_main.a

TARGET = test

# 소스 파일과 오브젝트 파일 정의
SRCS =  src/sample3_unittest.cc
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