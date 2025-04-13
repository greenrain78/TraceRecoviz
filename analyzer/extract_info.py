import clang.cindex
import sys
import os
import json
from pathlib import Path

# libclang 위치 (자신의 LLVM 버전에 맞게)
clang.cindex.Config.set_library_file("/usr/lib/llvm-14/lib/libclang.so.1")

# 시스템 헤더 경로 포함
clang_args = [
    "-std=c++17",
    "-I./src",
    "-I/usr/include",
    "-I/usr/include/c++/11",
    "-I/usr/include/x86_64-linux-gnu/c++/11"
]

def is_user_defined(cursor):
    if cursor.location.file:
        f = str(cursor.location.file)
        return (
            not f.startswith("/usr/include")
            and "bits/" not in f
            and "libc++" not in f
            and "std/" not in f
        )
    return False

def get_namespace(cursor):
    namespaces = []
    parent = cursor.semantic_parent
    while parent:
        if parent.kind == clang.cindex.CursorKind.NAMESPACE:
            namespaces.append(parent.spelling)
        parent = parent.semantic_parent
    return "::".join(reversed(namespaces))

def extract_class_info(cursor, file_path, result):
    if cursor.kind not in (clang.cindex.CursorKind.CLASS_DECL, clang.cindex.CursorKind.CLASS_TEMPLATE):
        return
    if not cursor.is_definition():
        return

    ns = get_namespace(cursor)
    # 필터링: 특정 네임스페이스로 시작하는 경우 제외
    if ns.startswith("std") or ns.startswith("__gnu_cxx") or ns.startswith("testing") or ns.startswith("__cxxabiv1"):
        return

    class_info = {
        "file": str(file_path),
        "namespace": ns,
        "class": cursor.spelling,
        "members": []
    }

    for child in cursor.get_children():
        if child.kind == clang.cindex.CursorKind.CXX_METHOD:
            if not is_user_defined(child):
                continue
            return_type = child.result_type.spelling
            func_name = child.spelling
            is_static = child.is_static_method()

            params = []
            for i, arg in enumerate(child.get_arguments()):
                arg_type = arg.type.spelling
                arg_name = arg.spelling or f"arg{i}"
                params.append({
                    "name": arg_name,
                    "type": arg_type
                })

            class_info["members"].append({
                "type": "static_method" if is_static else "method",
                "name": func_name,
                "return_type": return_type,
                "params": params
            })

        elif child.kind == clang.cindex.CursorKind.FIELD_DECL:
            var_type = child.type.spelling
            var_name = child.spelling
            # libclang에 따라 is_static_var 속성은 없을 수 있음
            class_info["members"].append({
                "type": "field",
                "declaration": f"{var_type} {var_name}",
                "name": var_name,
                "var_type": var_type
            })

        elif child.kind == clang.cindex.CursorKind.VAR_DECL:
            var_type = child.type.spelling
            var_name = child.spelling
            class_info["members"].append({
                "type": "static_field",
                "declaration": f"{var_type} {var_name}",
                "name": var_name,
                "var_type": var_type
            })

    if class_info["members"]:
        result.append(class_info)

def parse_cc_files_only(directory, output_file):
    index = clang.cindex.Index.create()
    result = []

    source_files = list(Path(directory).rglob("*.cc")) + list(Path(directory).rglob("*.cpp"))

    for src in source_files:
        try:
            print(f"[+] Parsing source: {src}")
            tu = index.parse(str(src), args=clang_args)
            for cursor in tu.cursor.walk_preorder():
                extract_class_info(cursor, src, result)
        except Exception as e:
            print(f"[!] Failed to parse {src}: {e}")

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[✓] 결과 저장 완료: {output_file}")

if __name__ == "__main__":
    src_dir = sys.argv[1] if len(sys.argv) >= 2 else "./src"
    output_path = "output.json"
    parse_cc_files_only(src_dir, output_path)
