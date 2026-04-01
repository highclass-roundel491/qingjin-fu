import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .poem_tools import (
    SEARCH_POEMS_TOOL,
    GET_POEM_DETAIL_TOOL,
    VERIFY_POEM_LINE_TOOL,
    GET_RELATED_POEMS_TOOL,
    tool_search_poems,
    tool_get_poem_detail,
    tool_verify_poem_line,
    tool_get_related_poems,
)
from .author_tools import (
    GET_AUTHOR_INFO_TOOL,
    tool_get_author_info,
)
from .stats_tools import (
    COUNT_POEMS_STATS_TOOL,
    tool_count_poems_stats,
)
from .compare_tools import (
    COMPARE_POETS_TOOL,
    tool_compare_poets,
)
from .discovery_tools import (
    RANDOM_POEM_TOOL,
    GET_DYNASTY_CONTEXT_TOOL,
    tool_random_poem,
    tool_get_dynasty_context,
)
from .search_tools import (
    SEARCH_POEMS_ADVANCED_TOOL,
    tool_search_poems_advanced,
)
from .user_tools import (
    GET_USER_PROFILE_TOOL,
    GET_USER_LEARNING_HISTORY_TOOL,
    tool_get_user_profile,
    tool_get_user_learning_history,
)

logger = logging.getLogger("uvicorn.error")

TOOL_DEFINITIONS = [
    SEARCH_POEMS_TOOL,
    GET_POEM_DETAIL_TOOL,
    GET_AUTHOR_INFO_TOOL,
    VERIFY_POEM_LINE_TOOL,
    GET_RELATED_POEMS_TOOL,
    COUNT_POEMS_STATS_TOOL,
    COMPARE_POETS_TOOL,
    RANDOM_POEM_TOOL,
    GET_DYNASTY_CONTEXT_TOOL,
    SEARCH_POEMS_ADVANCED_TOOL,
    GET_USER_PROFILE_TOOL,
    GET_USER_LEARNING_HISTORY_TOOL,
]

_TOOL_DISPATCH = {
    "search_poems": tool_search_poems,
    "get_poem_detail": tool_get_poem_detail,
    "get_author_info": tool_get_author_info,
    "verify_poem_line": tool_verify_poem_line,
    "get_related_poems": tool_get_related_poems,
    "count_poems_stats": tool_count_poems_stats,
    "compare_poets": tool_compare_poets,
    "random_poem": tool_random_poem,
    "get_dynasty_context": tool_get_dynasty_context,
    "search_poems_advanced": tool_search_poems_advanced,
    "get_user_profile": tool_get_user_profile,
    "get_user_learning_history": tool_get_user_learning_history,
}


async def execute_tool(
    tool_name: str,
    arguments: dict,
    db: AsyncSession,
) -> str:
    handler = _TOOL_DISPATCH.get(tool_name)
    if not handler:
        return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)
    try:
        return await handler(db, **arguments)
    except Exception as e:
        logger.error(f"工具 {tool_name} 执行失败: {e}")
        return json.dumps({"error": f"工具执行失败: {str(e)}"}, ensure_ascii=False)


def register_tool(definition: dict, handler):
    TOOL_DEFINITIONS.append(definition)
    name = definition["function"]["name"]
    _TOOL_DISPATCH[name] = handler


__all__ = [
    "TOOL_DEFINITIONS",
    "execute_tool",
    "register_tool",
]
