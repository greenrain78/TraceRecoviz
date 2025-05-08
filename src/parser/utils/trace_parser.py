import re
from logging import getLogger
from pathlib import Path

log = getLogger(__name__)

from src.parser.utils.extract import extract_callee


class TraceParser:
    """
    로그 파일을 파싱하여 시퀀스 다이어그램을 생성하는 클래스입니다.
    """

    _LOG_PATTERN = re.compile(r"\[(.*?)] \[(CALL|RETURN)] caller: \(ptr=(.*?)\) (.*?) => callee: \(ptr=(.*?)\) (.*)")
    def __init__(self, file_path):
        self.file_path = file_path
        self.nodes = {}
        self.links = []
        self.time_count = 0

    def run(self):
        for raw in Path(self.file_path).read_text(encoding="utf-8").splitlines():
            if raw.startswith("[TRACE]"):
                continue
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

    def _process_line(self, line: str) -> None:
        # log.info(f"Processing line: {line}")
        match = self._LOG_PATTERN.match(line)
        if not match:
            raise ValueError(f"Invalid log line: {line}")
        test_name, action, caller_ptr, caller_sig, callee_ptr, callee_sig = match.groups()

        # 노드 추가
        caller = extract_callee(caller_sig)
        callee = extract_callee(callee_sig)
        print(f"caller: {caller.class_name}, callee: {callee.class_name}")
        self._ensure_node(caller_ptr, caller.class_name)
        self._ensure_node(callee_ptr, callee.class_name)

        if action == "CALL":
            self.links.append({
                "source": caller_ptr,
                "target": callee_ptr,
                "text": f"{callee.return_type} {callee.func_name}({', '.join([f'{arg[0]} {arg[1]}' for arg in callee.args])})",
                "time": self.time_count,
            })
        elif action == "RETURN":
            self.links.append({
                "source": callee_ptr,
                "target": caller_ptr,
                "text": f"{callee.return_type} {callee.return_value}",
                "time": self.time_count,
            })
        else:
            raise ValueError(f"Invalid action: {action}")
        self.time_count += 1

    def _ensure_node(self, ptr: str, name: str):
        """ 노드가 존재하지 않으면 생성합니다. """
        if ptr not in self.nodes:
            if ptr == '0':
                text = f"전역함수"
            else:
                text = f"{name} : {ptr}"

            self.nodes[ptr] = {
                "key": ptr,
                "text": text,
                "loc": f"{len(self.nodes) * len(name) * 6 + 20} 0",
                "size": f"{max(100, len(name) * 6)} 60",
                "isGroup": True,
                "duration": 0
            }

