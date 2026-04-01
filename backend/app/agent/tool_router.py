from .tools import TOOL_DEFINITIONS

_TOOL_BY_NAME = {t["function"]["name"]: t for t in TOOL_DEFINITIONS}

SKILL_TOOL_MAP: dict[str, list[str]] = {
    "poem_context_author_bio": [
        "get_author_info", "search_poems", "get_poem_detail",
    ],
    "poem_context_deep_appreciation": [],
    "poem_context_allusions": [
        "search_poems", "get_poem_detail", "verify_poem_line",
    ],
    "poem_context_verse_analysis": [
        "get_poem_detail", "verify_poem_line",
    ],
    "poem_context_meter_analysis": [
        "get_poem_detail",
    ],
    "poem_context_free_qa": [
        "search_poems", "get_poem_detail", "get_author_info",
        "verify_poem_line", "get_related_poems", "compare_poets",
        "get_user_profile", "get_user_learning_history",
    ],
    "poem_chat": [
        "search_poems", "get_poem_detail", "get_author_info",
        "verify_poem_line", "get_related_poems", "compare_poets",
        "get_user_profile", "get_user_learning_history",
    ],
    "challenge_score": [
        "verify_poem_line", "get_poem_detail",
    ],
    "challenge_generate": [
        "search_poems", "get_poem_detail", "verify_poem_line",
    ],
    "challenge_hint": [
        "verify_poem_line", "search_poems",
    ],
    "challenge_review": [
        "verify_poem_line", "get_poem_detail",
    ],
    "challenge_explain": [
        "verify_poem_line", "get_poem_detail", "get_related_poems",
    ],
    "creation": [
        "search_poems", "get_poem_detail", "get_related_poems",
        "get_author_info", "verify_poem_line",
        "get_user_profile", "get_user_learning_history",
    ],
    "creation_imitate": [
        "search_poems", "get_poem_detail", "get_related_poems",
        "get_author_info",
    ],
    "analysis": [
        "search_poems", "get_poem_detail", "get_author_info",
        "get_related_poems", "compare_poets",
    ],
    "feihualing": [
        "search_poems", "verify_poem_line",
    ],
    "score_answer": [
        "verify_poem_line", "get_poem_detail",
    ],
    "check_poem": [
        "search_poems", "get_poem_detail", "verify_poem_line",
    ],
    "check_challenge": [
        "verify_poem_line", "search_poems", "get_poem_detail",
    ],
}


def get_tools_for_skill(skill_name: str) -> list[dict]:
    tool_names = SKILL_TOOL_MAP.get(skill_name)
    if tool_names is None:
        return TOOL_DEFINITIONS
    if not tool_names:
        return []
    return [_TOOL_BY_NAME[n] for n in tool_names if n in _TOOL_BY_NAME]


def estimate_tool_tokens(tools: list[dict]) -> int:
    total = 0
    for t in tools:
        fn = t.get("function", {})
        total += len(fn.get("name", "")) * 2
        total += len(fn.get("description", ""))
        params = fn.get("parameters", {})
        for prop_name, prop_def in params.get("properties", {}).items():
            total += len(prop_name) * 2
            total += len(prop_def.get("description", ""))
            if "enum" in prop_def:
                total += sum(len(str(e)) for e in prop_def["enum"])
    return total // 3
