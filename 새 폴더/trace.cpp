// trace.cpp
#include "trace.h"
#include <iostream>
#include <regex>
#include <unordered_map>
#include <vector>
#include <filesystem>
#include <string>

std::string current_test_name;
std::ofstream trace_ofs;
// trace.cpp에 추가
static std::vector<std::string> pending_listener_logs;
static std::vector<std::string> all_listener_logs;

// void trace_listener_log(const std::string& msg) {
//     all_listener_logs.push_back(msg);  // 전체 로그에도 추가

//     if (trace_ofs.is_open()) {
//         trace_ofs << msg << std::endl;
//     } else {
//         pending_listener_logs.push_back(msg);
//     }
// }

// void trace_flush_all_logs() {
//     for (const auto& line : all_listener_logs) {
//         trace_ofs << line << std::endl;
//     }
// }



// void trace_flush_pending_logs() {
//     for (const auto& line : pending_listener_logs) {
//         trace_ofs << line << std::endl;
//     }
//     pending_listener_logs.clear();
// }

std::string replaceTemplateParams(const std::string& prettyFunc) {
    std::string result = prettyFunc;
    std::unordered_map<std::string, std::string> replacements;

    // 1️⃣ [E = int, T = double] 같은 패턴 찾기
    std::regex bracketPattern(R"(\[(.+?)\])");
    std::smatch match;
    if (std::regex_search(result, match, bracketPattern)) {
        std::string mappings = match[1];  // E = int, T = double

        // 각 매핑 분리
        std::regex pairPattern(R"((\w+)\s*=\s*(\w+))");
        auto pairsBegin = std::sregex_iterator(mappings.begin(), mappings.end(), pairPattern);
        auto pairsEnd = std::sregex_iterator();

        for (auto it = pairsBegin; it != pairsEnd; ++it) {
            std::string key = (*it)[1];
            std::string val = (*it)[2];
            replacements[key] = val;
        }

        // 2️⃣ 시그니처 본문에서 치환
        for (const auto& [key, val] : replacements) {
            std::regex wordPattern("\\b" + key + "\\b");
            result = std::regex_replace(result, wordPattern, val);
        }

        // 3️⃣ [E = int, ...] 부분만 삭제 (앞부분 자르지 않음!)
        result = std::regex_replace(result, bracketPattern, "");
    }

    return result;
}


void trace_set_current_test(const std::string& suite, const std::string& name) {
    current_test_name = suite + "." + name;
}

void trace_open_file(const std::string& filename) {
    if (trace_ofs.is_open()) trace_ofs.close();
    
    // log/ 디렉토리 안에 넣도록 경로 추가
    std::string log_path = "log/" + filename;
    //std::cout << "[DEBUG] Opening log file: " << log_path << std::endl;

    trace_ofs.open(log_path);
}


void trace_close_file() {
    if (trace_ofs.is_open()) {
        trace_ofs.close();
    }
}

