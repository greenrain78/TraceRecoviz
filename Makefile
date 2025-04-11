ACXX = ag++
CXXFLAGS = -std=c++17
LDFLAGS = -lgtest -lgtest_main -pthread

TARGET = test

SRCS = src/sample1.cc src/sample1_unittest.cc
OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(ACXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.cpp
	$(ACXX) $(CXXFLAGS) -c $<

clean:
	rm -f *.o *.acd $(TARGET) trace.log auto_generated_aspect.ah
