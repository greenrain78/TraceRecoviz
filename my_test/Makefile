# my_test/Makefile

ACPP = ag++
CXXFLAGS = -std=c++17 -I../gtest/googletest/googletest/include
LDFLAGS = -lpthread
GTEST_LIB = ../gtest/libgtest.a

OUT = test_exec

all: $(OUT)

$(OUT): main.cpp
	$(ACPP) main.cpp -o $(OUT) $(GTEST_LIB) $(CXXFLAGS) $(LDFLAGS)

clean:
	rm -f $(OUT)
