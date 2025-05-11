from logging import getLogger
from typing import Tuple


log = getLogger(__name__)


def paere_funct(sig: str) -> tuple[str, str]:
    splited_sig = sig.split("::")
    if len(splited_sig) == 1:
        return "", splited_sig[0]
    elif len(splited_sig) >= 2:
        return splited_sig[0], splited_sig[1]
    else:
        log.error(f"❌ 잘못된 함수 시그니처 형식: {sig} - 길이: {len(splited_sig)}")
        return "", ""

def parse_caller_sig(sig: str) -> tuple[str, str, str]:
    try:
        sig = (
            sig.replace("const", "")
            .replace("(anonymous namespace)", "익명")
            .replace("virtual ", "")
            .replace("static ", "")
            .split("(")[0]
            .strip()
        )
        # 분리된 sig
        sig = sig.split(" ")
        if len(sig) == 0:
            return "", "", ""
        elif len(sig) == 1:
            class_name, func_name = paere_funct(sig[0])
            return "", class_name, func_name
        elif len(sig) == 2:
            class_name, func_name = paere_funct(sig[1])
            return sig[0], class_name, func_name
        else:
            log.error(f"❌ 잘못된 caller_sig 형식: {sig} - 길이: {len(sig)}")
    except Exception as e:
        log.error(f"❌ caller_sig 파싱 중 오류 발생: {sig} - 오류: {e}")
        raise e

def parse_callee_sig(sig: str) -> tuple[str, str, str, str]:
    if "|ARGS|" not in sig:
        return parse_caller_sig(sig) + ("",)
    sig, args = sig.split("|ARGS|", maxsplit=1)
    ret_type, class_name, func_name = parse_caller_sig(sig)
    return ret_type, class_name, func_name, args