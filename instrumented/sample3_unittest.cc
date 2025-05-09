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

// In this example, we use a more advanced feature of Google Test called
// test fixture.
//
// A test fixture is a place to hold objects and functions shared by
// all tests in a test case.  Using a test fixture avoids duplicating
// the test code necessary to initialize and cleanup those common
// objects for each test.  It is also useful for defining sub-routines
// that your tests need to invoke a lot.
//
// <TechnicalDetails>
//
// The tests share the test fixture in the sense of code sharing, not
// data sharing.  Each test is given its own fresh copy of the
// fixture.  You cannot expect the data modified by one test to be
// passed on to another test, which is a bad idea.
//
// The reason for this design is that tests should be independent and
// repeatable.  In particular, a test should not fail as the result of
// another test's failure.  If one test depends on info produced by
// another test, then the two tests should really be one big test.
//
// The macros for indicating the success/failure of a test
// (EXPECT_TRUE, FAIL, etc) need to know what the current test is
// (when Google Test prints the test result, it tells you which test
// each failure belongs to).  Technically, these macros invoke a
// member function of the Test class.  Therefore, you cannot use them
// in a global function.  That's why you should put test sub-routines
// in a test fixture.
//
// </TechnicalDetails>

#include "sample3-inl.h"
#include "gtest/gtest.h"
#include "../trace.h"
namespace {
// To use a test fixture, derive a class from testing::Test.
class QueueTestSmpl3 : public testing::Test {
 protected:  // You should make the members protected s.t. they can be
             // accessed from sub-classes.
  // virtual void SetUp() will be called before each test is run.  You
  // should define it if you need to initialize the variables.
  // Otherwise, this can be skipped.
  void SetUp() override {trace_enter((void*)this, __PRETTY_FUNCTION__ );
  
    q1_.Enqueue(1);
    q2_.Enqueue(2);
    q2_.Enqueue(3);
  
  trace_return((void*)this, __PRETTY_FUNCTION__);
  }

  // virtual void TearDown() will be called after each test is run.
  // You should define it if there is cleanup work to do.  Otherwise,
  // you don't have to provide it.
  //
  // virtual void TearDown() {
  // }

  // A helper function that some test uses.
  static int Double(int n) {trace_enter((void*)0, __PRETTY_FUNCTION__ , n);
   { auto __trace_ret = 2 * n; trace_return((void*)0, __PRETTY_FUNCTION__, __trace_ret); return __trace_ret; } }

  // A helper function for testing Queue::Map().
  void MapTester(const Queue<int>* q) {trace_enter((void*)this, __PRETTY_FUNCTION__ , q);
  
    // Creates a new queue, where each element is twice as big as the
    // corresponding one in q.
    const Queue<int>* const new_q = q->Map(Double);

    // Verifies that the new queue has the same size as q.
    ASSERT_EQ_LOG(q->Size(), new_q->Size());

    // Verifies the relationship between the elements of the two queues.
    for (const QueueNode<int>*n1 = q->Head(), *n2 = new_q->Head();
         n1 != nullptr; n1 = n1->next(), n2 = n2->next()) {
      EXPECT_EQ_LOG(2 * n1->element(), n2->element());
    }

    delete new_q;
  }

  // Declares the variables your tests want to use.
  Queue<int> q0_;
  Queue<int> q1_;
  Queue<int> q2_;
};

// When you have a test fixture, you define a test using TEST_F
// instead of TEST.

// Tests the default c'tor.
TEST_F(QueueTestSmpl3, DefaultConstructor) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  // You can access data in the test fixture here.
  EXPECT_EQ_LOG(0u, q0_.Size());

trace_return((void*)this, __PRETTY_FUNCTION__);
}

// Tests Dequeue().
TEST_F(QueueTestSmpl3, Dequeue) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  int* n = q0_.Dequeue();
  EXPECT_TRUE_LOG(n == nullptr);

  n = q1_.Dequeue();
  ASSERT_TRUE_LOG(n != nullptr);
  EXPECT_EQ_LOG(1, *n);
  EXPECT_EQ_LOG(0u, q1_.Size());
  delete n;

  n = q2_.Dequeue();
  ASSERT_TRUE_LOG(n != nullptr);
  EXPECT_EQ_LOG(2, *n);
  EXPECT_EQ_LOG(1u, q2_.Size());
  delete n;
}

// Tests the Queue::Map() function.
TEST_F(QueueTestSmpl3, Map) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  MapTester(&q0_);
  MapTester(&q1_);
  MapTester(&q2_);

trace_return((void*)this, __PRETTY_FUNCTION__);
}
}  // namespace

// int main(int argc, char** argv) {
//   ::testing::InitGoogleTest(&argc, argv);
//   int result = RUN_ALL_TESTS();
//   //flushTrace();  // 테스트 끝나고 바로 JSON 저장
//   return result;
// }

