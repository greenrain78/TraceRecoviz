#ifndef TRACE_LISTENER_H
#define TRACE_LISTENER_H

#include <gtest/gtest.h>
#include "trace.h"
#include <algorithm>
#include <filesystem>

class TraceListener : public testing::EmptyTestEventListener {
public:
    void OnTestProgramStart(const testing::UnitTest& unit_test) override {
        const void* phase = reinterpret_cast<void*>(0x1001);
        trace_enter(phase, "GoogleTest::OnTestProgramStart");
        trace_ofs << "[TRACE] TestProgram START" << std::endl;
    }

    void OnTestIterationStart(const testing::UnitTest& unit_test, int iteration) override {
        const void* phase = reinterpret_cast<void*>(0x1002);
        trace_enter(phase, "GoogleTest::OnTestIterationStart");
        trace_ofs << "[TRACE] TestIteration START: #" << iteration << std::endl;
    }

    void OnEnvironmentsSetUpStart(const testing::UnitTest& unit_test) override {
        const void* phase = reinterpret_cast<void*>(0x1003);
        trace_enter(phase, "GoogleTest::OnEnvironmentsSetUpStart");
        trace_ofs << "[TRACE] GlobalEnvironment SetUp START" << std::endl;
    }

    void OnEnvironmentsSetUpEnd(const testing::UnitTest& unit_test) override {
        trace_ofs << "[TRACE] GlobalEnvironment SetUp END" << std::endl;
        const void* phase = reinterpret_cast<void*>(0x1003);
        trace_return(phase, "GoogleTest::OnEnvironmentsSetUpStart");
    }

    void OnTestSuiteStart(const testing::TestSuite& test_suite) override {
        const void* phase = reinterpret_cast<void*>(0x1004);
        trace_enter(phase, "GoogleTest::OnTestSuiteStart");
        trace_ofs << "[TRACE] TestSuite START: " << test_suite.name() << std::endl;
    }

    void OnTestStart(const testing::TestInfo& test_info) override {
        const void* phase = reinterpret_cast<void*>(0x1005);
        trace_enter(phase, "GoogleTest::OnTestStart");

        std::string suite = test_info.test_suite_name();
        std::string test = test_info.name();
        std::string param = test_info.value_param() ? test_info.value_param() : "";

        trace_ofs << "[TRACE] Test START: " << suite << "." << test;
        if (!param.empty()) {
            trace_ofs << " [Param: " << param << "]";
        }
        trace_ofs << std::endl;

        // 로그 파일 이름 생성
        std::string safe_suite = suite;
        std::replace(safe_suite.begin(), safe_suite.end(), '/', '_');
        std::string safe_test = test;
        std::replace(safe_test.begin(), safe_test.end(), '/', '_');

        std::filesystem::path filePath(test_info.file());
        std::string fileName = filePath.stem().string();

        std::string filename = fileName + "_" + safe_suite + "." + safe_test + ".log";
        trace_set_current_test(suite, test);
        trace_open_file(filename);

        if (!param.empty()) {
            trace_ofs << "[TRACE] Registered Parameter: " << param << std::endl;
        }
    }

    void OnTestPartResult(const testing::TestPartResult& result) override {
        const void* phase = reinterpret_cast<void*>(0x1006);
        trace_enter(phase, "GoogleTest::OnTestPartResult");

        trace_ofs << "[TRACE] Assertion "
                  << (result.failed() ? "FAILED" : "PASSED")
                  << ": " << result.summary() << std::endl;

        trace_return(phase, "GoogleTest::OnTestPartResult");
    }

    void OnTestEnd(const testing::TestInfo& test_info) override {
        trace_ofs << "[TRACE] Test END: " << test_info.test_suite_name()
                  << "." << test_info.name() << std::endl;
        trace_close_file();

        const void* phase = reinterpret_cast<void*>(0x1005);
        trace_return(phase, "GoogleTest::OnTestStart");
    }

    void OnTestSuiteEnd(const testing::TestSuite& test_suite) override {
        trace_ofs << "[TRACE] TestSuite END: " << test_suite.name() << std::endl;
        const void* phase = reinterpret_cast<void*>(0x1004);
        trace_return(phase, "GoogleTest::OnTestSuiteStart");
    }

    void OnEnvironmentsTearDownStart(const testing::UnitTest& unit_test) override {
        const void* phase = reinterpret_cast<void*>(0x1007);
        trace_enter(phase, "GoogleTest::OnEnvironmentsTearDownStart");
        trace_ofs << "[TRACE] GlobalEnvironment TearDown START" << std::endl;
    }

    void OnEnvironmentsTearDownEnd(const testing::UnitTest& unit_test) override {
        trace_ofs << "[TRACE] GlobalEnvironment TearDown END" << std::endl;
        const void* phase = reinterpret_cast<void*>(0x1007);
        trace_return(phase, "GoogleTest::OnEnvironmentsTearDownStart");
    }

    void OnTestIterationEnd(const testing::UnitTest& unit_test, int iteration) override {
        trace_ofs << "[TRACE] TestIteration END: #" << iteration << std::endl;
        const void* phase = reinterpret_cast<void*>(0x1002);
        trace_return(phase, "GoogleTest::OnTestIterationStart");
    }

    void OnTestProgramEnd(const testing::UnitTest& unit_test) override {
        trace_ofs << "[TRACE] TestProgram END" << std::endl;
        const void* phase = reinterpret_cast<void*>(0x1001);
        trace_return(phase, "GoogleTest::OnTestProgramStart");
    }
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
