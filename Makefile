ACXX = ag++
CXXFLAGS = -std=c++17 -I./src -I.
LDFLAGS = -lgtest -lgtest_main -pthread

TARGET = test

# 소스 파일과 오브젝트 파일 정의
SRCS = src/sample1.cc src/sample1_unittest.cc
OBJS = $(patsubst %.cc, %.o, $(SRCS))

all: $(TARGET)

$(TARGET): $(OBJS)
	$(ACXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

# src/my_class.cc → src/my_class.o
src/%.o: src/%.cc
	$(ACXX) $(CXXFLAGS) -c $< -o $@

# 루트에 있는 my_class_test.cc → my_class_test.o
%.o: %.cc
	$(ACXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f src/*.o *.o *.acd $(TARGET) trace.log 