// main.cpp
#include <gtest/gtest.h>
#include <iostream>

TEST(SampleTest, BasicAssertion) {
    std::cout << "[LOG] SampleTest 시작: " << std::endl;
    EXPECT_EQ(1 + 1, 2);
    std::cout << "[LOG] SampleTest 종료: " << std::endl;
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

