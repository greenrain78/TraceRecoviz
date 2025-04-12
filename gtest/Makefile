# gtest_build/Makefile
ACPP = ag++
CXXFLAGS = -std=c++17 -Igoogletest/googletest/include -Igoogletest/googletest -Igoogletest/googletest/internal
GTEST_SRCS = googletest/googletest/src/gtest-all.cc
LIB = libgtest.a

all: $(LIB)

$(LIB):
	$(ACPP) -c $(CXXFLAGS) $(GTEST_SRCS)
	ar rcs $(LIB) gtest-all.o

clean:
	rm -f *.o *.t.* $(LIB)
