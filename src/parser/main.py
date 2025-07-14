import logging
import os
import re


# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(module)s::%(lineno)d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

from config import LOG_DIR, OUTPUT_DIR
from utils.files import delete_files, save_log_file

from utils.trace_parser import TraceParser

if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        log.error(f"❌ 해당 디렉토리가 존재하지 않습니다: {LOG_DIR}")
        exit(1)

    # 이전 데이터 삭제
    delete_files(OUTPUT_DIR, "*.json")
    log.info("🗑️ 이전 데이터 삭제")

    INPUT_DIRS = ["result", "new", "old"]
    # 로그 파일 처리
    for input_subdir in INPUT_DIRS:
        input_dir = os.path.join("./build/", input_subdir)
        suffix = "" if input_subdir == "result" else f"_{input_subdir}"

        for filename in os.listdir(input_dir):
            if filename.endswith(".log"):
                try:
                    log.info(f"📜 변환중: {filename} ({input_subdir})")
                    result = TraceParser(os.path.join(input_dir, filename)).run()
                    output_filename = filename.replace(".log", f"{suffix}.json")
                    save_log_file(OUTPUT_DIR, output_filename, result)
                except Exception as e:
                    log.error(f"❌ 변환 실패: {filename} ({input_subdir})")
                    log.error(e)
                    continue

    log.info("💡 모든 로그 파일이 변환되었습니다.")
