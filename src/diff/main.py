import difflib
from pathlib import Path
from typing import List

from src.diff.config import OLD_DIR, NEW_DIR, RESULT_DIR


def _char_level_diff(old: str, new: str) -> List[str]:
    """a, b 한 줄의 내용을 비교하여 전체 줄 기준으로 교체 포맷 적용"""
    if old != new:
        return [f"= {new}"]
    else:
        return [f"! {old} -> {new}"]



def diff_charline(old: str, new: str) -> List[str]:
    """old, new ⇒ 줄+문자 단위 diff 결과(스트링 리스트)"""
    old_lines, new_lines = old.splitlines(), new.splitlines()
    sm = difflib.SequenceMatcher(None, old_lines, new_lines)
    out: List[str] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.extend(f"  {line}" for line in old_lines[i1:i2])
        elif tag == "delete":
            out.extend(f"- {line}" for line in old_lines[i1:i2])
        elif tag == "insert":
            out.extend(f"+ {line}" for line in old_lines[i1:i2])
        elif tag == "replace":
            # 같은 위치의 줄 쌍을 문자 단위로 다시 비교
            for a, b in zip(old_lines[i1:i2], new_lines[j1:j2]):
                out.extend(_char_level_diff(a, b))
            # 길이가 다르면 남은 줄도 처리
            for line in old_lines[i1 + (j2 - j1) : i2]:
                out.append("- " + line)
            for line in new_lines[j1 + (i2 - i1) : j2]:
                out.append("+ " + line)
    return out

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


