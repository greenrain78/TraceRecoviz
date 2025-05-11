import re
from typing import Optional, Dict, List

LOG_PATTERN = re.compile(
    r'^\[(?P<testname>.*?)\]\s+\[(?P<action>CALL|RETURN|ASSERTION_CALL)\]\s*'
    r'\|caller=(?P<caller_ptr>[^|]*)\|\s*(?P<caller_sig>.*?)\s*>>\s*'
    r'(?:\|callee=(?P<callee_ptr>[^|]*)\|\s*(?P<callee_sig>.*?))?'
    r'(?:\s*=>\s*(?P<return_val>.*))?$'
)

def parse_log_line(line: str) -> Optional[Dict[str, str]]:
    match = LOG_PATTERN.match(line)
    if not match:
        return None

    return {
        "testname": match.group("testname"),
        "action": match.group("action"),
        "caller_ptr": match.group("caller_ptr"),
        "caller_sig": match.group("caller_sig").strip(),
        "callee_ptr": match.group("callee_ptr") or "",
        "callee_sig": match.group("callee_sig").strip() if match.group("callee_sig") else "",
        "return_val": match.group("return_val").strip() if match.group("return_val") else "",
    }

def parse_log_file(filepath: str) -> List[Dict[str, str]]:
    results = []
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("[TRACE]") and "ASSERTION_CALL" in line:
                continue  # 불필요한 줄은 건너뜀
            parsed = parse_log_line(line)
            if parsed:
                results.append(parsed)
    return results

# 예시 사용
if __name__ == "__main__":
    parsed_logs = parse_log_file("../../build/log/trace_sample6_unittest_PrimeTableTest_0.ReturnsTrueForPrimes.log")
    for entry in parsed_logs:
        print(entry)
