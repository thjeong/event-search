import json, re, ast
from typing import Any

def parse_lenient_json(s: str) -> Any:
    """
    LLM이 만든 비표준 JSON 문자열을 최대한 보정해 파싱합니다.
    반환값은 dict/list 등 파이썬 객체입니다.
    """
    if not isinstance(s, str):
        return s

    # 0) 코드펜스/여분 공백 제거
    s = s.strip()
    if s.startswith("```"):
        # ```json ... ``` 또는 ``` ... ```
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.IGNORECASE | re.DOTALL).strip()

    # 1) 먼저 표준 JSON 시도
    try:
        return json.loads(s)
    except Exception:
        pass

    # 2) 흔한 오류 보정: 배열/객체의 끝에 붙은 트레일링 콤마 제거
    s2 = re.sub(r",\s*([}\]])", r"\1", s)
    try:
        return json.loads(s2)
    except Exception:
        pass

    # 3) 마지막 시도: 파이썬 리터럴 파서 (홑따옴표, True/False/None 등 허용)
    #    literal_eval은 안전한 리터럴만 허용합니다(함수 호출/코드 실행 X)
    try:
        return ast.literal_eval(s)
    except Exception as e:
        raise ValueError(f"Could not parse as JSON-like: {e}") from e


def to_strict_json_string(obj: Any) -> str:
    """파싱된 객체를 표준 JSON 문자열로 직렬화(이모지/한글 유지)."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
