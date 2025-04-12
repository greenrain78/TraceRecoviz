# gtest_build/Makefile

ACPP = ag++
CXXFLAGS = -std=c++17 -Igoogletest/googletest/include -Igoogletest/googletest -Igoogletest/googletest/internal

GTEST_SRCS = googletest/googletest/src/gtest-all.cc
GTEST_MAIN = googletest/googletest/src/gtest_main.cc

LIB_GTEST = libgtest.a
LIB_GTEST_MAIN = libgtest_main.a

all: $(LIB_GTEST) $(LIB_GTEST_MAIN)

$(LIB_GTEST):
	$(ACPP) -c $(CXXFLAGS) $(GTEST_SRCS)
	ar rcs $(LIB_GTEST) gtest-all.o

$(LIB_GTEST_MAIN):
	$(ACPP) -c $(CXXFLAGS) $(GTEST_MAIN)
	ar rcs $(LIB_GTEST_MAIN) gtest_main.o

clean:
	rm -f *.o *.t.* $(LIB_GTEST) $(LIB_GTEST_MAIN)
