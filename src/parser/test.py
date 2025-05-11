import logging
import re
from pathlib import Path
from typing import Optional, Dict, List

from src.parser.utils.trace_parser import TraceParser
# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(module)s::%(lineno)d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)
# 예시 사용
if __name__ == "__main__":
    path = "../../build/log/trace_sample6_unittest_PrimeTableTest_0.ReturnsTrueForPrimes.log"
    # for raw in Path(path).read_text(encoding="utf-8").splitlines():
    #     print(raw)
    TraceParser(path).run()

