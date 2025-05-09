// Copyright 2005, Google Inc.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met:
//
//     * Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above
// copyright notice, this list of conditions and the following disclaimer
// in the documentation and/or other materials provided with the
// distribution.
//     * Neither the name of Google Inc. nor the names of its
// contributors may be used to endorse or promote products derived from
// this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

// A sample program demonstrating using Google C++ testing framework.

// This sample shows how to write a simple unit test for a function,
// using Google C++ testing framework.
//
// Writing a unit test using Google C++ testing framework is easy as 1-2-3:

// Step 1. Include necessary header files such that the stuff your
// test logic needs is declared.
//
// Don't forget gtest.h, which declares the testing framework.

#include "sample1.h"
#include "../trace.h"
#include <limits.h>

#include "gtest/gtest.h"
namespace {

// Step 2. Use the TEST macro to define your tests.
//
// TEST has two parameters: the test case name and the test name.
// After using the macro, you should define your test logic between a
// pair of braces.  You can use a bunch of macros to indicate the
// success or failure of a test.  EXPECT_TRUE and EXPECT_EQ are
// examples of such macros.  For a complete list, see gtest.h.
//
// <TechnicalDetails>
//
// In Google Test, tests are grouped into test cases.  This is how we
// keep test code organized.  You should put logically related tests
// into the same test case.
//
// The test case name and the test name should both be valid C++
// identifiers.  And you should not use underscore (_) in the names.
//
// Google Test guarantees that each test you define is run exactly
// once, but it makes no guarantee on the order the tests are
// executed.  Therefore, you should write your tests in such a way
// that their results don't depend on their order.
//
// </TechnicalDetails>

// Tests Factorial().

// Tests factorial of negative numbers.
TEST(FactorialTest, Negative) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  // This test is named "Negative", and belongs to the "FactorialTest"
  // test case.
  EXPECT_EQ_LOG(1, Factorial(-5));
  EXPECT_EQ_LOG(1, Factorial(-1));
  EXPECT_GT(Factorial(-10), 0);

  // <TechnicalDetails>
  //
  // EXPECT_EQ_LOG(expected, actual) is the same as
  //
  //   EXPECT_TRUE_LOG((expected) == (actual))
  //
  // except that it will print both the expected value and the actual
  // value when the assertion fails.  This is very helpful for
  // debugging.  Therefore in this case EXPECT_EQ is preferred.
  //
  // On the other hand, EXPECT_TRUE accepts any Boolean expression,
  // and is thus more general.
  //
  // </TechnicalDetails>

trace_return((void*)this, __PRETTY_FUNCTION__);
}

// Tests factorial of 0.
TEST(FactorialTest, Zero) {trace_enter((void*)this, __PRETTY_FUNCTION__ );
 EXPECT_EQ_LOG(1, Factorial(0)); 
trace_return((void*)this, __PRETTY_FUNCTION__);
}

// Tests factorial of positive numbers.
TEST(FactorialTest, Positive) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  EXPECT_EQ_LOG(1, Factorial(1));
  EXPECT_EQ_LOG(2, Factorial(2));
  EXPECT_EQ_LOG(6, Factorial(3));
  EXPECT_EQ_LOG(40320, Factorial(8));

trace_return((void*)this, __PRETTY_FUNCTION__);
}

// Tests IsPrime()

// Tests negative input.
TEST(IsPrimeTest, Negative) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  // This test belongs to the IsPrimeTest test case.

  EXPECT_FALSE_LOG(IsPrime(-1));
  EXPECT_FALSE_LOG(IsPrime(-2));
  EXPECT_FALSE_LOG(IsPrime(INT_MIN));

trace_return((void*)this, __PRETTY_FUNCTION__);
}

// Tests some trivial cases.
TEST(IsPrimeTest, Trivial) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  EXPECT_FALSE_LOG(IsPrime(0));
  EXPECT_FALSE_LOG(IsPrime(1));
  EXPECT_TRUE_LOG(IsPrime(2));
  EXPECT_TRUE_LOG(IsPrime(3));

trace_return((void*)this, __PRETTY_FUNCTION__);
}

// Tests positive input.
TEST(IsPrimeTest, Positive) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  EXPECT_FALSE_LOG(IsPrime(4));
  EXPECT_TRUE_LOG(IsPrime(5));
  EXPECT_FALSE_LOG(IsPrime(6));
  EXPECT_TRUE_LOG(IsPrime(23));

trace_return((void*)this, __PRETTY_FUNCTION__);
}
}  // namespace

// Step 3. Call RUN_ALL_TESTS() in main().
//
// We do this by linking in src/gtest_main.cc file, which consists of
// a main() function which calls RUN_ALL_TESTS() for us.
//
// This runs all the tests you've defined, prints the result, and
// returns 0 if successful, or 1 otherwise.
//
// Did you notice that we didn't register the tests?  The
// RUN_ALL_TESTS() macro magically knows about all the tests we
// defined.  Isn't this convenient?
// class TraceListener : public testing::TestEventListener {
//   public:
//       // 테스트 시작 전
//       void OnTestProgramStart(const testing::UnitTest& /*unit_test*/) override {}
  
//       // 테스트 종료 후
//       void OnTestProgramEnd(const testing::UnitTest& /*unit_test*/) override {}
  
//       // 테스트 반복 시작 (기본적으로 1회)
//       void OnTestIterationStart(const testing::UnitTest& unit_test, int iteration) override {}
  
//       // 테스트 반복 종료
//       void OnTestIterationEnd(const testing::UnitTest& unit_test, int iteration) override {}
  
//       // 전역 환경 설정 시작/종료
//       void OnEnvironmentsSetUpStart(const testing::UnitTest& unit_test) override {}
//       void OnEnvironmentsSetUpEnd(const testing::UnitTest& unit_test) override {}
  
//       void OnEnvironmentsTearDownStart(const testing::UnitTest& unit_test) override {}
//       void OnEnvironmentsTearDownEnd(const testing::UnitTest& unit_test) override {}
  
//       // 테스트 스위트(테스트 그룹) 시작/종료
//       void OnTestSuiteStart(const testing::TestSuite& suite) override {
//           std::cout << "=== START SUITE: " << suite.name() << " ===" << std::endl;
//       }
  
//       void OnTestSuiteEnd(const testing::TestSuite& suite) override {
//           std::cout << "=== END SUITE: " << suite.name() << " ===" << std::endl;
//       }
  
//       // 테스트 케이스 시작/종료
//       void OnTestStart(const testing::TestInfo& test_info) override {
//           std::cout << "[TRACE] Test Started: " << test_info.test_suite_name()
//                     << "." << test_info.name() << std::endl;
//       }
  
//       void OnTestEnd(const testing::TestInfo& test_info) override {
//           std::cout << "[TRACE] Test Ended: " << test_info.test_suite_name()
//                     << "." << test_info.name() << std::endl;
//       }
  
//       // 단일 assertion 결과
//       void OnTestPartResult(const testing::TestPartResult& result) override {
//           if (result.failed()) {
//               std::cout << "[FAIL] " << result.summary() << std::endl;
//           }
//       }
//   };
  

// int main(int argc, char** argv) {
//   set_allow_trace(true);  // 트레이스 허용
//   ::testing::InitGoogleTest(&argc, argv);

//   // 리스너 교체
//   testing::TestEventListeners& listeners = testing::UnitTest::GetInstance()->listeners();
//   delete listeners.Release(listeners.default_result_printer());
//   listeners.Append(new TraceListener());

//   return RUN_ALL_TESTS();
// }

