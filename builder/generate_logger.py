from typing import List

# === 1. 추적할 함수 시그니처 정의 ===
# 필요한 함수 인자 타입 조합만 추가
signature_list: List[List[str]] = [
    ["int", "int"],
    ["float"],
    ["std::string", "double"]
]

# === 2. arg 로그 표현 생성 ===
def format_arg_log(args: List[str]) -> str:
    parts = [f'"arg{i}=" << *tjp->arg<{i}>()' for i in range(len(args))]
    return ' << ", " << '.join(parts)

# === 3. 어드바이스 코드 생성 ===
def generate_advice_block(arg_types: List[str]) -> str:
    sig_str = ', '.join(arg_types)
    arg_log = format_arg_log(arg_types)

    return f"""
    // --- Trace for: ({sig_str}) ---
    advice call("% %::%({sig_str})") : before() {{
        std::ostringstream oss;
        oss << "[CALL   ] " << tjp->signature() << "(" << {arg_log} << ")";
        TraceLogger::log(oss.str());
    }}

    advice call("% %::%({sig_str})") : after() {{
        std::ostringstream oss;
        oss << "[RETURN ] " << tjp->signature();
        if (tjp->result()) {{
            oss << " => " << *tjp->result();
        }} else {{
            oss << " => void";
        }}
        TraceLogger::log(oss.str());
    }}
    """

# === 4. 전체 Aspect 코드 생성 (파일 저장은 안 함) ===
def generate_aspect_code() -> str:
    blocks = [generate_advice_block(sig) for sig in signature_list]
    code_block = "\n".join(blocks)

    header = """
#include <iostream>
#include <fstream>
#include <mutex>
#include <sstream>

class TraceLogger {
public:
    static std::ofstream& stream() {
        static std::ofstream log("trace.log", std::ios::out | std::ios::app);
        return log;
    }

    static std::mutex& lock() {
        static std::mutex mtx;
        return mtx;
    }

    static void log(const std::string& msg) {
        std::lock_guard<std::mutex> guard(lock());
        stream() << msg << std::endl;
    }
};
aspect UniversalLogger {

    """
    footer = """
};
    """
    return f"""
{header}\n{code_block}\n{footer}
    """.strip()

# === 5. 파일 저장은 별도 함수에서 수행 ===
def write_aspect_file(filename="function_logger.ah"):
    aspect_code = generate_aspect_code()
    with open(filename, "w") as f:
        f.write(aspect_code)

if __name__ == "__main__":
    write_aspect_file()
