import re
from typing import Tuple, List, Optional, NamedTuple


class ParsedSig(NamedTuple):
    return_type: str
    class_name: str          # 없으면 ""
    func_name: str
    args: List[Tuple[str, str]]   # [(타입, 값), ...]  – 정적 정보가 없으면 []
    return_value: Optional[str]   # => 값이 없으면 None

def _split_signature_parts(sig: str) -> Tuple[str, str]:
    """Return (class_name, func_name) from a string like 'Class::Func'.
    If no class qualifier exists, class_name is "".
    """
    parts = sig.split("::")
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return "", parts[-1]


def _extract_args(arg_str: str) -> List[Tuple[str, str]]:
    """Extract list of (type, value) from '(argN=[type: T] value)' blocks."""
    pattern = re.compile(r"\w+=\[type: (.*?)\] ([^\)]+)")
    return pattern.findall(arg_str)


def extract_callee(sig: str) -> ParsedSig:
    """Parse a callee signature string.
    """

    # Normalize & strip leading markers
    sig = sig.replace("(anonymous namespace)", "##").removeprefix("virtual ").strip()

    # Extract explicit return value (after '=>') if present
    return_value: Optional[str] = None
    if " => " in sig:
        sig, return_value = sig.split(" => ", 1)
        return_value = return_value.strip()

    # Pull out inline argument value list  e.g.  '(arg0=[type: int] -5)'
    arg_values: List[Tuple[str, str]] = []
    if ") (" in sig:
        sig, arg_part = sig.rsplit(") (", 1)
        sig += ")"  # restore closing parenthesis removed by rsplit
        arg_values = _extract_args(arg_part)

    # Separate return type from the remainder (might be missing)
    sig_parts = sig.split(None, 1)
    if len(sig_parts) == 2:
        return_type, func_part = sig_parts
    else:
        return_type, func_part = "", sig_parts[0]

    # Split class and function
    class_name, func_name = _split_signature_parts(func_part)
    return ParsedSig(
        return_type=return_type,
        class_name=class_name,
        func_name=func_name,
        args=arg_values,
        return_value=return_value
    )
