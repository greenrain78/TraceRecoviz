from typing import List

TEMPLATE_PATH = "builder/template_aspect.txt"
OUTPUT_PATH = "auto_aspect_logger.ah"

# 추적할 함수 이름들
TARGET_FUNCTIONS = ["TestBody", "Enqueue", "Push", "Pop"]


def generate_pointcut_block(function_names: List[str]) -> str:
    def join_calls(prefix: str) -> str:
        return ' || '.join([f'call("{prefix} ...::{name}(...)")' for name in function_names])

    all_calls = join_calls("%")
    void_calls = join_calls("void")

    return f"""\
    pointcut AllTargetFunctions() = {all_calls};
    pointcut VoidTargetFunctions() = {void_calls};
    pointcut NonVoidTargetFunctions() = AllTargetFunctions() && !VoidTargetFunctions();"""


def generate_aspect_file(template_path: str, output_path: str, pointcut_code: str) -> None:
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    output = template.replace("{{POINTCUTS}}", pointcut_code)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"✅ Generated {output_path} with {len(TARGET_FUNCTIONS)} target functions.")


if __name__ == "__main__":
    pointcut_code = generate_pointcut_block(TARGET_FUNCTIONS)
    generate_aspect_file(TEMPLATE_PATH, OUTPUT_PATH, pointcut_code)
