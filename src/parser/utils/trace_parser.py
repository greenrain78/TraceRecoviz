import re
from logging import getLogger
from pathlib import Path
from typing import Tuple

from utils.extract import parse_caller_sig, parse_callee_sig

log = getLogger(__name__)


class TraceParser:
    """
    로그 파일을 파싱하여 시퀀스 다이어그램을 생성하는 클래스입니다.
    """

    _LOG_PATTERN = re.compile(
        r'^\[(?P<testname>.+?)\]\s+\[(?P<action>CALL|RETURN|ASSERTION_CALL)\]\s*'
        r'\|caller=(?P<caller_ptr>[^|]+)\|\s*(?P<caller_sig>.+?)\s*>>\s*'
        r'(?:\|callee=(?P<callee_ptr>[^|]+)\|\s*(?P<callee_sig>.+?))?'
        r'(?:\s*=>\s*(?P<return_val>.+))?$'
    )

    def __init__(self, file_path):
        self.file_path = file_path
        self.nodes = {}
        self.links = []
        self.time_count = 0
        self.test_name = ""
        self.root_node = ""

    def run(self):
        for raw in Path(self.file_path).read_text(encoding="utf-8").splitlines():
            if raw.startswith("[TRACE]") or raw.startswith("  [TRACE]"):
                continue
            if "[ASSERTION_CALL]" in raw:
                self._process_assertion(raw.strip())
            else:
                self._process_line(raw.strip())

        # 노드 가공
        for i, node in enumerate(self.nodes.values()):
            node["duration"] = self.time_count
            node["loc"] = f"{i * 60} 0"

        return {
            "class": "go.GraphLinksModel",
            "nodeDataArray": list(self.nodes.values()),
            "linkDataArray": self.links
        }

    @staticmethod
    def _is_changed(line: str):
        # 맨 앞 2글자와 나머지 분리
        first_two = line[:2]
        rest = line[2:]
        if first_two == "+ ":
            change_color = "green"
        elif first_two == "- ":
            change_color = "red"
        elif first_two == "= ":
            change_color = "yellow"
        elif first_two == "! ":
            change_color = "orange"
        elif first_two == "  ":
            change_color = "white"
        else:
            change_color = None
            rest = line
        return change_color, rest

    def _process_assertion(self, line: str) -> None:
        change_color, text = self._is_changed(line)
        text = line.split("[ASSERTION_CALL]")[1]
        if self.test_name == "":
            raise ValueError("테스트 시작전 ASSERT 문이 먼저 실행되어 있습니다.")
        self.links.append({
            "from": self.root_node,
            "to": self.root_node,
            "text": text,
            "time": self.time_count,
            **({"color": change_color} if change_color is not None else {}),
        })
        self.time_count += 2

    def _parse_line(self, line: str):
        match = self._LOG_PATTERN.match(line)
        if not match:
            return None
        if self.test_name == "":
            self.test_name = match.group("testname")

        caller_sig = match.group("caller_sig").strip()
        caller_ret_type, caller_class, caller_func = parse_caller_sig(caller_sig)

        callee_sig = match.group("callee_sig").strip()
        callee_ret_type, callee_class, callee_func, callee_args = parse_callee_sig(callee_sig)
        return {
            "action": match.group("action"),
            "caller_ptr": match.group("caller_ptr"),
            "caller_ret_type": caller_ret_type,
            "caller_class": caller_class,
            "caller_func": caller_func,
            "callee_ptr": match.group("callee_ptr") or "",
            "callee_ret_type": callee_ret_type,
            "callee_class": callee_class,
            "callee_func": callee_func,
            "callee_args": callee_args,
            "return_val": match.group("return_val").strip() if match.group("return_val") else "",
        }

    def _process_line(self, line: str) -> None:
        change_color, text = self._is_changed(line)
        log.info(f"변경된 줄: {change_color} {text}")
        data = self._parse_line(text)
        self._ensure_node(data.get("caller_ptr", "없음"), data.get("caller_class", ""))
        self._ensure_node(data.get("callee_ptr", "없음"), data.get("callee_class", ""))
        #
        if data['action'] == "CALL":
            self.links.append({
                "from": data['caller_ptr'],
                "to": data['callee_ptr'],
                "text": f"{data['callee_ret_type']} {data['callee_func']}{data['callee_args']}",
                "time": self.time_count,
                **({"color": change_color} if change_color is not None else {}),
            })
        elif data['action'] == "RETURN":
            self.links.append({
                "from": data['callee_ptr'],
                "to": data['caller_ptr'],
                "text": f"{data['callee_ret_type']} {data['return_val']}",
                "time": self.time_count,
                **({"color": change_color} if change_color is not None else {}),
            })
        else:
            raise ValueError(f"Invalid action: {data['action']}")
        self.time_count += 2
    #
    def _ensure_node(self, ptr: str, name: str):
        """ 노드가 존재하지 않으면 생성합니다. """
        if ptr not in self.nodes:
            if self.root_node == "" and name == "GoogleTest":
                self.root_node = ptr
            if ptr == '0':
                text = f"전역함수"
            else:
                text = f"{name} : {ptr}"

            self.nodes[ptr] = {
                "key": ptr,
                "text": text,
                "loc": f"{len(self.nodes) * len(name) * 6 + 20} 0",
                "size": f"{max(100, len(name) * 60)} 0",
                "isGroup": True,
                "duration": 0
            }

