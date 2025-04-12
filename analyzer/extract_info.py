import clang.cindex
import sys
import os
import json
from pathlib import Path

# 시스템에 맞게 libclang 경로 설정 (필요시 수정)
clang.cindex.Config.set_library_file("/usr/lib/llvm-17/lib/libclang.so.1")

def extract_function_info(cursor, result, file_path):
    if cursor.kind == clang.cindex.CursorKind.CXX_METHOD:
        parent = cursor.semantic_parent
        if parent.kind == clang.cindex.CursorKind.CLASS_DECL or parent.kind == clang.cindex.CursorKind.CLASS_TEMPLATE:
            class_name = parent.spelling
            func_name = cursor.spelling
            return_type = cursor.result_type.spelling

            params = []
            for i, arg in enumerate(cursor.get_arguments()):
                arg_name = arg.spelling or f"arg{i}"
                arg_type = arg.type.spelling
                params.append({"name": arg_name, "type": arg_type})

            result.append({
                "file": str(file_path),
                "class": class_name,
                "function": func_name,
                "return_type": return_type,
                "params": params
            })

def parse_cpp_files_in_dir(directory, output_file):
    index = clang.cindex.Index.create()
    result = []

    cpp_extensions = ['.cpp', '.cc', '.cxx', '.h', '.hpp']
    source_files = list(Path(directory).rglob("*"))

    for file_path in source_files:
        if file_path.suffix.lower() in cpp_extensions:
            try:
                tu = index.parse(str(file_path), args=['-std=c++17'])
                for cursor in tu.cursor.walk_preorder():
                    extract_function_info(cursor, result, file_path)
            except Exception as e:
                print(f"[!] Failed to parse {file_path}: {e}")

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    source_dir = sys.argv[1] if len(sys.argv) >= 2 else "./src"
    output_file = "output.json"

    parse_cpp_files_in_dir(source_dir, output_file)
    print(f"[✓] 함수 정보가 {output_file}에 JSON 형식으로 저장되었습니다.")
