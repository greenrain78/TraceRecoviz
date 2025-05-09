#ifndef TRACE_LISTENER_H
#define TRACE_LISTENER_H

#include <gtest/gtest.h>
#include "trace.h"
#include <algorithm>
#include <filesystem>

class TraceListener : public testing::EmptyTestEventListener {
public:
    // void OnTestProgramStart(const testing::UnitTest& unit_test) override {
    //     const void* runner_ptr = &unit_test;
    //     trace_set_current_test("Global", "TestProgram");
    //     //trace_open_file("trace_global.log");
    //     trace_flush_pending_logs();

    //     trace_enter(runner_ptr, "TestRunner");
    //     trace_listener_log("[TRACE] TestProgram START");
    // }

    // void OnTestIterationStart(const testing::UnitTest& unit_test, int iteration) override {
    //     const void* phase = reinterpret_cast<void*>(0x1002);
    //     trace_enter(phase, "GoogleTest::OnTestIterationStart");
    //     trace_listener_log("[TRACE] TestIteration START: #" + std::to_string(iteration));
    // }

    // void OnEnvironmentsSetUpStart(const testing::UnitTest& unit_test) override {
    //     const void* phase = reinterpret_cast<void*>(0x1003);
    //     trace_enter(phase, "GoogleTest::OnEnvironmentsSetUpStart");
    //     trace_listener_log("[TRACE] GlobalEnvironment SetUp START");
    
    // }

    // void OnEnvironmentsSetUpEnd(const testing::UnitTest& unit_test) override {
    //     trace_listener_log("[TRACE] GlobalEnvironment SetUp END");
    //     const void* phase = reinterpret_cast<const void*>(0x1003);
    //     trace_return(phase, "GoogleTest::OnEnvironmentsSetUpStart");
    // }

    // void OnTestSuiteStart(const testing::TestSuite& test_suite) override {
    //     const void* suite_ptr = &test_suite;
    //     trace_enter(suite_ptr, std::string("TestFixture#" + std::string(test_suite.name())).c_str());
    //     trace_listener_log("[TRACE] TestSuite START: " + std::string(test_suite.name()));
    // }

    void OnTestStart(const testing::TestInfo& test_info) override {
        const void* test_ptr = &test_info;
        trace_enter(test_ptr, std::string("TestInstance#" + std::string(test_info.name())).c_str());
        std::string suite = test_info.test_suite_name();
        std::string test = test_info.name();
        std::string param = test_info.value_param() ? test_info.value_param() : "";

        trace_listener_log("[TRACE] Test START: " + suite + "." + test + (param.empty() ? "" : " [Param: " + param + "]"));


        // 로그 파일 이름 생성
        std::string safe_suite = suite;
        std::replace(safe_suite.begin(), safe_suite.end(), '/', '_');
        std::string safe_test = test;
        std::replace(safe_test.begin(), safe_test.end(), '/', '_');

        std::filesystem::path filePath(test_info.file());
        std::string fileName = filePath.stem().string();

        std::string filename = "trace_" + fileName + "_" + safe_suite + "." + safe_test + ".log";
        trace_set_current_test(suite, test);
        trace_open_file(filename);
        trace_flush_all_logs();  // 💡 전체 listener 로그 복사 밀어넣기
        trace_flush_pending_logs();

        if (!param.empty()) {
            trace_ofs << "[TRACE] Registered Parameter: " << param << std::endl;
        }
    }

    // void OnTestPartResult(const testing::TestPartResult& result) override {
    //     const void* phase = reinterpret_cast<const void*>(0x1006);
    //     trace_enter(phase, "GoogleTest::OnTestPartResult");

    //     trace_listener_log("[TRACE] Assertion " + std::string(result.failed() ? "FAILED" : "PASSED") + ": " + result.summary());

    //     trace_return(phase, "GoogleTest::OnTestPartResult");
    // }

    // void OnTestEnd(const testing::TestInfo& test_info) override {
    //     trace_listener_log("[TRACE] Test END: " + std::string(test_info.test_suite_name()) + "." + test_info.name());
    //     trace_close_file();

    //     const void* phase = reinterpret_cast<const void*>(0x1005);
    //     trace_return(phase, "GoogleTest::OnTestStart");
    // }

    // void OnTestSuiteEnd(const testing::TestSuite& test_suite) override {
    //     trace_listener_log("[TRACE] TestSuite END: " + std::string(test_suite.name()));
    //     const void* phase = reinterpret_cast<const void*>(0x1004);
    //     trace_return(phase, "GoogleTest::OnTestSuiteStart");
    // }

    // void OnEnvironmentsTearDownStart(const testing::UnitTest& unit_test) override {
    //     const void* phase = reinterpret_cast<const void*>(0x1007);
    //     trace_enter(phase, "GoogleTest::OnEnvironmentsTearDownStart");
    //     trace_listener_log("[TRACE] GlobalEnvironment TearDown START");
    // }

    // void OnEnvironmentsTearDownEnd(const testing::UnitTest& unit_test) override {
    //     trace_listener_log("[TRACE] GlobalEnvironment TearDown END");
    //     const void* phase = reinterpret_cast<const void*>(0x1007);
    //     trace_return(phase, "GoogleTest::OnEnvironmentsTearDownStart");
    // }

    // void OnTestIterationEnd(const testing::UnitTest& unit_test, int iteration) override {
    //     trace_listener_log("[TRACE] TestIteration END: #" + std::to_string(iteration));
    //     const void* phase = reinterpret_cast<const void*>(0x1002);
    //     trace_return(phase, "GoogleTest::OnTestIterationStart");
    // }

    // void OnTestProgramEnd(const testing::UnitTest& unit_test) override {
    //     trace_listener_log("[TRACE] TestProgram END");
    //     trace_close_file();
    // }
};

// 리스너 자동 등록 (static 객체 초기화)
namespace {
struct TraceListenerRegister {
    TraceListenerRegister() {
        testing::TestEventListeners& listeners =
            testing::UnitTest::GetInstance()->listeners();
        listeners.Append(new TraceListener);
    }
};
static TraceListenerRegister _register_trace_listener;
}

#endif // TRACE_LISTENER_H
