import logging
import os
import re

from src.parser.utils.trace_parser import TraceParser

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(module)s::%(lineno)d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

from config import LOG_DIR, OUTPUT_DIR
from utils.files import delete_files, save_log_file


if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        log.error(f"❌ 해당 디렉토리가 존재하지 않습니다: {LOG_DIR}")
        exit(1)

    # 이전 데이터 삭제
    delete_files(OUTPUT_DIR, "*.json")
    log.info("🗑️ 이전 데이터 삭제")

    # 로그 파일 처리
    for filename in os.listdir(LOG_DIR):
        # if filename.endswith(".log") and "_sample6_unittest_OnTheFlyAndPreCalculated_PrimeTableTest2_0.CanGetNextPrime" in filename:
        if filename.endswith(".log"):
            log.info(f"📜 변환중: {filename}")
            result = TraceParser(os.path.join(LOG_DIR, filename)).run()
            save_log_file(OUTPUT_DIR, filename.replace(".log", ".json"), result)
    log.info("💡 모든 로그 파일이 변환되었습니다.")
