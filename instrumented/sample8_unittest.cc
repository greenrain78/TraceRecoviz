// Copyright 2008 Google Inc.
// All Rights Reserved.
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

// This sample shows how to test code relying on some global flag variables.
// Combine() helps with generating all possible combinations of such flags,
// and each test is given one combination as a parameter.

// Use class definitions to test from this header.
#include <tuple>

#include "prime_tables.h"
#include "gtest/gtest.h"
namespace {

// Suppose we want to introduce a new, improved implementation of PrimeTable
// which combines speed of PrecalcPrimeTable and versatility of
// OnTheFlyPrimeTable (see prime_tables.h). Inside it instantiates both
// PrecalcPrimeTable and OnTheFlyPrimeTable and uses the one that is more
// appropriate under the circumstances. But in low memory conditions, it can be
// told to instantiate without PrecalcPrimeTable instance at all and use only
// OnTheFlyPrimeTable.
class HybridPrimeTable : public PrimeTable {
 public:
  HybridPrimeTable(bool force_on_the_fly, int max_precalculated)
      : on_the_fly_impl_(new OnTheFlyPrimeTable),
        precalc_impl_(force_on_the_fly
                          ? nullptr
                          : new PreCalculatedPrimeTable(max_precalculated)),
        max_precalculated_(max_precalculated) {trace_enter((void*)this, __PRETTY_FUNCTION__ , force_on_the_fly, max_precalculated);
        
        trace_return((void*)this, __PRETTY_FUNCTION__);
        }
  ~HybridPrimeTable() override {trace_enter((void*)this, __PRETTY_FUNCTION__ );
  
    delete on_the_fly_impl_;
    delete precalc_impl_;
  
  trace_return((void*)this, __PRETTY_FUNCTION__);
  }

  bool IsPrime(int n) const override {trace_enter((void*)this, __PRETTY_FUNCTION__ , n);
  
    if (precalc_impl_ != nullptr && n < max_precalculated_)
      { auto __trace_ret = precalc_impl_->IsPrime(n); trace_return((void*)this, __PRETTY_FUNCTION__, __trace_ret); return __trace_ret; }
    else
      { auto __trace_ret = on_the_fly_impl_->IsPrime(n); trace_return((void*)this, __PRETTY_FUNCTION__, __trace_ret); return __trace_ret; }
  }

  int GetNextPrime(int p) const override {trace_enter((void*)this, __PRETTY_FUNCTION__ , p);
  
    int next_prime = -1;
    if (precalc_impl_ != nullptr && p < max_precalculated_)
      next_prime = precalc_impl_->GetNextPrime(p);
    { auto __trace_ret = next_prime != -1 ? next_prime : on_the_fly_impl_->GetNextPrime(p); trace_return((void*)this, __PRETTY_FUNCTION__, __trace_ret); return __trace_ret; }
  }

 private:
  OnTheFlyPrimeTable* on_the_fly_impl_;
  PreCalculatedPrimeTable* precalc_impl_;
  int max_precalculated_;
};

using ::testing::Bool;
using ::testing::Combine;
using ::testing::TestWithParam;
using ::testing::Values;

// To test all code paths for HybridPrimeTable we must test it with numbers
// both within and outside PreCalculatedPrimeTable's capacity and also with
// PreCalculatedPrimeTable disabled. We do this by defining fixture which will
// accept different combinations of parameters for instantiating a
// HybridPrimeTable instance.
class PrimeTableTest : public TestWithParam< ::std::tuple<bool, int> > {
 protected:
  void SetUp() override {trace_enter((void*)this, __PRETTY_FUNCTION__ );
  
    bool force_on_the_fly;
    int max_precalculated;
    std::tie(force_on_the_fly, max_precalculated) = GetParam();
    table_ = new HybridPrimeTable(force_on_the_fly, max_precalculated);
  
  trace_return((void*)this, __PRETTY_FUNCTION__);
  }
  void TearDown() override {trace_enter((void*)this, __PRETTY_FUNCTION__ );
  
    delete table_;
    table_ = nullptr;
  
  trace_return((void*)this, __PRETTY_FUNCTION__);
  }
  HybridPrimeTable* table_;
};

TEST_P(PrimeTableTest, ReturnsFalseForNonPrimes) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  // Inside the test body, you can refer to the test parameter by GetParam().
  // In this case, the test parameter is a PrimeTable interface pointer which
  // we can use directly.
  // Please note that you can also save it in the fixture's SetUp() method
  // or constructor and use saved copy in the tests.

  EXPECT_FALSE_LOG(table_->IsPrime(-5));
  EXPECT_FALSE_LOG(table_->IsPrime(0));
  EXPECT_FALSE_LOG(table_->IsPrime(1));
  EXPECT_FALSE_LOG(table_->IsPrime(4));
  EXPECT_FALSE_LOG(table_->IsPrime(6));
  EXPECT_FALSE_LOG(table_->IsPrime(100));

trace_return((void*)this, __PRETTY_FUNCTION__);
}

TEST_P(PrimeTableTest, ReturnsTrueForPrimes) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  EXPECT_TRUE_LOG(table_->IsPrime(2));
  EXPECT_TRUE_LOG(table_->IsPrime(3));
  EXPECT_TRUE_LOG(table_->IsPrime(5));
  EXPECT_TRUE_LOG(table_->IsPrime(7));
  EXPECT_TRUE_LOG(table_->IsPrime(11));
  EXPECT_TRUE_LOG(table_->IsPrime(131));

trace_return((void*)this, __PRETTY_FUNCTION__);
}

TEST_P(PrimeTableTest, CanGetNextPrime) {trace_enter((void*)this, __PRETTY_FUNCTION__ );

  EXPECT_EQ_LOG(2, table_->GetNextPrime(0));
  EXPECT_EQ_LOG(3, table_->GetNextPrime(2));
  EXPECT_EQ_LOG(5, table_->GetNextPrime(3));
  EXPECT_EQ_LOG(7, table_->GetNextPrime(5));
  EXPECT_EQ_LOG(11, table_->GetNextPrime(7));
  EXPECT_EQ_LOG(131, table_->GetNextPrime(128));

trace_return((void*)this, __PRETTY_FUNCTION__);
}

// In order to run value-parameterized tests, you need to instantiate them,
// or bind them to a list of values which will be used as test parameters.
// You can instantiate them in a different translation module, or even
// instantiate them several times.
//
// Here, we instantiate our tests with a list of parameters. We must combine
// all variations of the boolean flag suppressing PrecalcPrimeTable and some
// meaningful values for tests. We choose a small value (1), and a value that
// will put some of the tested numbers beyond the capability of the
// PrecalcPrimeTable instance and some inside it (10). Combine will produce all
// possible combinations.
INSTANTIATE_TEST_SUITE_P(MeaningfulTestParameters, PrimeTableTest,
                         Combine(Bool(), Values(1, 10)));

}  // namespace
