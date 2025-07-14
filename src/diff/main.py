import difflib
import re
from pathlib import Path
from typing import List

from config import OLD_DIR, NEW_DIR, RESULT_DIR

HEX_PTR = re.compile(r"0x[0-9a-fA-F]+")

def _normalize(line: str) -> str:
    """포인터 주소 등 런타임 변동 값을 고정 토큰으로 치환"""
    # 1) 포인터 주소 제거
    line = HEX_PTR.sub("@ADDR", line)
    # 2) 공백 정리
    return " ".join(line.split())

def diff_charline(old: str, new: str) -> List[str]:
    """정규화 후 줄 단위 diff 결과 반환 (+ / - /  )"""
    old_raw = old.splitlines()
    new_raw = new.splitlines()
    old_norm = [_normalize(l) for l in old_raw]
    new_norm = [_normalize(l) for l in new_raw]

    sm = difflib.SequenceMatcher(None, old_norm, new_norm)
    result: List[str] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            result.extend(f"  {old_raw[i]}" for i in range(i1, i2))
        elif tag == "delete":
            result.extend(f"- {old_raw[i]}" for i in range(i1, i2))
        elif tag == "insert":
            result.extend(f"+ {new_raw[j]}" for j in range(j1, j2))
        elif tag == "replace":
            # ‘삭제 + 추가’로 분해
            result.extend(f"- {old_raw[i]}" for i in range(i1, i2))
            result.extend(f"+ {new_raw[j]}" for j in range(j1, j2))
    return result


if __name__ == "__main__":
    # result 폴더내 로그 파일 비우기
    for f in Path(RESULT_DIR).glob("*.log"):
        f.unlink()
    print("result 폴더내 로그 파일 비우기 완료")

    for old_file in Path(OLD_DIR).glob("*.log"):
        new_file = Path(NEW_DIR) / old_file.name
        result_file = Path(RESULT_DIR)  / old_file.name

        if not new_file.exists():
            print(f"[경고] 새 로그 파일 없음: {new_file}")
            continue

        with old_file.open(encoding="utf-8") as f:
            old_text = f.read()
        with new_file.open(encoding="utf-8") as f:
            new_text = f.read()

        with result_file.open("w", encoding="utf-8") as f:
            for line in diff_charline(old_text, new_text):
                f.write(line + "\n")


