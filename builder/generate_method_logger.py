from typing import List

TEMPLATE_FILE = "builder/template_method.txt"
OUTPUT_FILE = "auto_method_logger.ah"

# === 1. 추적할 함수 시그니처 정의 ===
signature_list: List[List[str]] = [
    # ["int"],  # sample1
    ["const char*"],
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
    AspectLogger::log(oss.str());
}}

advice call("% %::%({sig_str})") : after() {{
    std::ostringstream oss;
    oss << "[RETURN ] " << tjp->signature();
    if (tjp->result()) {{
        oss << " => " << tjp->result();
        // oss << " => " << *tjp->result();  // void함수까지 인식해서 실제값을 출력 못함
    }} else {{
        oss << " => void";
    }}
    AspectLogger::log(oss.str());
}}
""".strip()

# === 4. 전체 어드바이스 블록 생성 ===
def generate_advice_blocks() -> str:
    return "\n\n".join(generate_advice_block(sig) for sig in signature_list)

# === 5. 템플릿 기반 전체 Aspect 파일 생성 ===
def generate_aspect_file(template_file: str, output_file: str):
    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()

    advice_code = generate_advice_blocks()
    final_code = template.replace("{{ADVICE_BLOCKS}}", advice_code)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_code)

    print(f"[✓] Generated {output_file} with {len(signature_list)} signature variants.")

# === 6. 실행 ===
if __name__ == "__main__":
    generate_aspect_file(TEMPLATE_FILE, OUTPUT_FILE)
