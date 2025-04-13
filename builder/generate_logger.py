from typing import List
from template import ADVICE_FUNCTION, SIGNATURE_FUNCTION


TEMPLATE_FILE = "builder/template_function.txt"
OUTPUT_FILE = "auto_test_logger.ah"

# === 1. 추적할 함수 시그니처 정의 ===
signature_list: List[List[str]] = [
    # ["int"], # sample1
]

# === 2. arg 로그 표현 생성 ===
def format_arg_log(num_args: int) -> str:
    parts = [f'"arg{i}=" << *tjp->arg<{i}>()' for i in range(num_args)]
    return ' << ", " << '.join(parts)

# === 3. 어드바이스 코드 생성 ===
def generate_advice_block(sign: str, arg_types: List[str]) -> str:
    sig_str = f"%{sign}%(', '.join(arg_types))"
    args_log = format_arg_log(len(arg_types))

    advice = ADVICE_FUNCTION.replace("{{SIGNATURE}}", sig_str)
    advice = advice.replace("{{ARGS_LOG}}", args_log)
    return advice

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
    # generate_aspect_file(TEMPLATE_FILE, OUTPUT_FILE)
    test_signature = [
        ("Factorial(int)", ["int"]),
    ]
    print(f"generate_advice_block")
    print(generate_advice_block(*test_signature[0]))  # Test the function with a sample signature
