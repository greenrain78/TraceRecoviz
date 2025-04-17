from typing import List

TEMPLATE_PATH = "builder/template_aspect.txt"
OUTPUT_PATH = "auto_aspect_logger.ah"

# 추적할 함수 및 클래스 목록
TARGET_FUNCTIONS = [
    "Factorial", "IsPrime", "CloneCString", "Set", "c_string", "Length",
    "element", "next", "Clear", "Size", "Head", "Last", "Enqueue", "Dequeue", "Map",
    "Increment", "Decrement", "GetNextPrime",
    "CreatePrimeTable",
    "OnTestProgramStart", "OnTestProgramEnd", "OnTestStart", "OnTestPartResult", "OnTestEnd", "PrintsMessage","Succeeds", "Fails", "main"
    "new", "delete","allocated", "OnTestStart", "OnTestEnd", "DoesNotLeak", "LeaksWater",
]

TARGET_CLASSES = [
    "MyString", "Counter", 
    "QuickTest", "IntegerFunctionTest",
    "PrimeTableTest",
    "HybridPrimeTable", "OnTheFlyPrimeTable", "PreCalculatedPrimeTable",
    "TersePrinter",
    "Water", "LeakChecker", "ListenersTest",
]

def generate_pointcut_block(function_names: List[str], class_names: List[str]) -> str:
    def join_calls(prefix: str) -> str:
        return ' || '.join([f'call("{prefix} ...::{name}(...)")' for name in function_names])

    def join_constructors(classes: List[str]) -> str:
        return ' || '.join([f'construction("{cls}")' for cls in classes])

    def join_destructors(classes: List[str]) -> str:
        return ' || '.join([f'destruction("{cls}")' for cls in classes])

    all_calls = join_calls("%")
    void_calls = join_calls("void")
    constructors = join_constructors(class_names)
    destructors = join_destructors(class_names)

    return f"""\
    pointcut AllTargetFunctions() = {all_calls};
    pointcut VoidTargetFunctions() = {void_calls};
    pointcut NonVoidTargetFunctions() = AllTargetFunctions() && !VoidTargetFunctions();

    pointcut TrackedConstructors() = {constructors};
    pointcut TrackedDestructors() = {destructors};"""

def generate_aspect_file(template_path: str, output_path: str, pointcut_code: str) -> None:
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    output = template.replace("{{POINTCUTS}}", pointcut_code)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"✅ Generated {output_path} with {len(TARGET_FUNCTIONS)} target functions and {len(TARGET_CLASSES)} classes.")

if __name__ == "__main__":
    pointcut_code = generate_pointcut_block(TARGET_FUNCTIONS, TARGET_CLASSES)
    generate_aspect_file(TEMPLATE_PATH, OUTPUT_PATH, pointcut_code)
