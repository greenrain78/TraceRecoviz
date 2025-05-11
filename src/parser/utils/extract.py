from logging import getLogger
from typing import Tuple


log = getLogger(__name__)


def parse_caller_sig(sig: str) -> tuple[str, str, str]:
    sig = (
        sig.replace(" const", "")
        .replace("(anonymous namespace)", "익명")
        .replace("virtual ", "")
        .strip()
    )
    # 분리된 sig
    sig = sig.split(" ")
    if len(sig) == 0:
        return "", "", ""
    elif len(sig) == 1:
        return "", sig[0].split("::")[-2], sig[0].split("::")[-1]
    elif len(sig) == 2:
        return sig[0], sig[1].split("::")[-2], sig[1].split("::")[-1]
    else:
        log.error(f"❌ 잘못된 caller_sig 형식: {sig} - 길이: {len(sig)}")

def parse_callee_sig(sig: str) -> tuple[str, str, str, str]:
    if "|ARGS|" not in sig:
        return parse_caller_sig(sig) + ("",)
    sig, args = sig.split("|ARGS|")
    ret_type, class_name, func_name = parse_caller_sig(sig)
    return ret_type, class_name, func_name, args