import glob
import json
import os
from logging import getLogger

log = getLogger(__name__)


def delete_files(folder_path: str, extension: str = "*.json"):
    """
    """
    log_files = glob.glob(os.path.join(folder_path, extension))
    for file_path in log_files:
        try:
            os.remove(file_path)
            log.debug(f"삭제됨 {file_path}")
        except Exception as e:
            log.error(f"오류 발생: {file_path} → {e}")

def save_log_file(folder_path: str, filename: str, data: dict):
    """
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        log.info(f"✅ 디렉토리 생성됨: {folder_path}")

    filepath = os.path.join(folder_path, filename)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
        log.info(f"✅ 저장됨: {filepath}")