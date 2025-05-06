#ifndef TRACE_H
#define TRACE_H

#include <string>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <type_traits>
#include <filesystem>
#include <stack>
#include <thread>
#include <cxxabi.h>  // 💡 추가

extern std::string current_test_name;
extern std::ofstream trace_ofs;

void trace_set_current_test(const std::string& suite, const std::string& name);
void trace_open_file(const std::string& filename);
void trace_close_file();
std::string replaceTemplateParams(const std::string& prettyFunc);

struct CallInfo {
    const void* ptr;
    std::string signature;
};

inline thread_local std::stack<CallInfo> call_stack;

// 💡 demangle 함수 추가
inline std::string demangle(const char* name) {
    int status = 0;
    char* demangled = abi::__cxa_demangle(name, nullptr, nullptr, &status);
    std::string result = (status == 0 && demangled) ? demangled : name;
    free(demangled);
    return result;
}

// 💡 생성자/소멸자 판별 공통 함수
inline void check_ctor_dtor(const std::string& signature, bool& is_ctor, bool& is_dtor) {
    is_ctor = false;
    is_dtor = false;
    if (signature.find('~') != std::string::npos) {
        is_dtor = true;
    } else {
        size_t space = signature.find(' ');
        size_t col = signature.rfind(':');
        if (space != std::string::npos && col != std::string::npos) {
            std::string retType = signature.substr(0, space);
            std::string func = signature.substr(space + 1);
            size_t paren = func.find('(');
            std::string funcName = func.substr(0, paren);
            size_t col2 = funcName.rfind("::");
            std::string className = (col2 != std::string::npos ? funcName.substr(0, col2) : "");
            std::string shortFunc = (col2 != std::string::npos ? funcName.substr(col2 + 2) : funcName);
            if (!className.empty() && retType == className && shortFunc == className) {
                is_ctor = true;
            }
        }
    }
}

template<typename... Args>
void trace_enter(const void* obj, const char* signature, Args&&... args) {
    if (!trace_ofs.is_open()) return;

    const void* caller_ptr = call_stack.empty() ? nullptr : call_stack.top().ptr;
    std::string caller_sig = call_stack.empty() ? "<ENTRY>" : replaceTemplateParams(call_stack.top().signature);

    trace_ofs << "[" << current_test_name << "] [CALL] ";
    trace_ofs << "caller: (ptr=" << caller_ptr << ") " << caller_sig << " => ";
    trace_ofs << "callee: (ptr=" << obj << ") " << replaceTemplateParams(signature);


    int idx = 0;
    (void)std::initializer_list<int>{(
        [&](){
            trace_ofs << (idx == 0 ? " (" : ", ");
            std::ostringstream oss;
            using T = std::decay_t<Args>;
            oss << "[type: " << demangle(typeid(T).name()) << "] ";  // 💡 demangled name 출력
            if constexpr(std::is_arithmetic_v<T> || std::is_pointer_v<T>) {
                oss << args;
            } else {
                oss << "<non-arithmetic addr=" << std::hex << (void*)&args << ">";
            }
            trace_ofs << "arg" << idx << "=" << oss.str();
            ++idx;
        }(), 0)...};
    if (idx > 0) trace_ofs << ")";
    trace_ofs << std::endl;

    call_stack.push(CallInfo{obj, signature});
}



template<typename Ret>
void trace_return(const void* obj, const char* signature, Ret retVal) {
    if (!trace_ofs.is_open()) return;

    call_stack.pop();
    bool is_ctor, is_dtor;
    check_ctor_dtor(signature, is_ctor, is_dtor);

    const void* caller_ptr = call_stack.empty() ? nullptr : call_stack.top().ptr;
    std::string caller_sig = call_stack.empty() ? "<UNKNOWN>" : replaceTemplateParams(call_stack.top().signature);

    trace_ofs << "[" << current_test_name << "] [RETURN] ";
    trace_ofs << "caller: (ptr=" << caller_ptr << ") " << caller_sig << " => ";
    trace_ofs << "callee: (ptr=" << obj << ") " << replaceTemplateParams(signature);


    if (is_ctor) {
        trace_ofs << " => <constructed>";
    } else if (is_dtor) {
        trace_ofs << " => <destroyed>";
    } else {
        std::ostringstream oss;
        using T = std::decay_t<Ret>;
        if constexpr(std::is_arithmetic_v<T> || std::is_pointer_v<T>) {
            oss << retVal;
        } else {
            oss << std::hex << (void*)&retVal;
        }
        trace_ofs << " => " << oss.str();
    }

    trace_ofs << std::endl;
}

inline void trace_return(const void* obj, const char* signature) {
    if (!trace_ofs.is_open()) return;

    call_stack.pop();
    bool is_ctor, is_dtor;
    check_ctor_dtor(signature, is_ctor, is_dtor);

    const void* caller_ptr = call_stack.empty() ? nullptr : call_stack.top().ptr;
    std::string caller_sig = call_stack.empty() ? "<UNKNOWN>" : replaceTemplateParams(call_stack.top().signature);

    trace_ofs << "[" << current_test_name << "] [RETURN] ";
    trace_ofs << "caller: (ptr=" << caller_ptr << ") " << caller_sig << " => ";
    trace_ofs << "callee: (ptr=" << obj << ") " << replaceTemplateParams(signature);


    if (is_ctor) {
        trace_ofs << " => <constructed>";
    } else if (is_dtor) {
        trace_ofs << " => <destroyed>";
    }

    trace_ofs << std::endl;
}

#endif // TRACE_H
