#!/usr/bin/env python3
from typing import List

TEMPLATE_FILE = "builder/template_class.txt"
OUTPUT_FILE = "auto_class_logger.ah"
TARGET_CLASSES: List[str] = [
    "MyString"
]

# 생성자/소멸자 advice 블록 생성 함수
def generate_ctor_dtor_advice(cls: str) -> str:
    return f"""
// ===== {cls} =====
advice construction("{cls}") : after() {{
    std::ostringstream oss;
    oss << "[CTOR ] {cls}::" << tjp->signature();
    AspectLogger::log(oss.str());
}}

advice destruction("{cls}") : before() {{
    std::ostringstream oss;
    oss << "[DTOR ] {cls}::" << tjp->signature();
    AspectLogger::log(oss.str());
}}
""".strip()

# 전체 advice 코드 생성
def generate_advice_block(class_names: List[str]) -> str:
    return "\n\n".join(generate_ctor_dtor_advice(cls) for cls in sorted(class_names))

# 템플릿을 읽고 advice 블록을 삽입
def generate_aspect_file(template_file: str, output_file: str, class_names: List[str]):
    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()

    advice_block = generate_advice_block(class_names)
    final_code = template.replace("{{ADVICE_BLOCKS}}", advice_block)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_code)

    print(f"[✓] Generated {output_file} with {len(class_names)} classes.")

# 실행
if __name__ == "__main__":
    generate_aspect_file(TEMPLATE_FILE, OUTPUT_FILE, TARGET_CLASSES)
