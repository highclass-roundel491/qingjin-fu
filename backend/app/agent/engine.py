import asyncio
import json
import logging
import re
import time
from typing import Optional, Callable

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from .tools import TOOL_DEFINITIONS, execute_tool
from .tool_router import get_tools_for_skill, estimate_tool_tokens
from .prompts.identity import AI_IDENTITY_GUARD, AI_IDENTITY_GUARD_LITE, TOOL_USE_GUIDE, TOOL_USE_GUIDE_CHAT, REACT_REASONING, LIGHT_PLANNER_PROMPT, LIGHT_REPLANNER_PROMPT, REWOO_PLANNER_PROMPT, REWOO_EVIDENCE_TEMPLATE
from ..services.ai_service import AIModelTier, get_default_model_tier, get_model_name

_SENSITIVE_PATTERN = re.compile(
    r"(dashscope|qwen|openai|anthropic|claude|deepseek|glm|zhipu|bailian|api[_-]?key)",
    re.IGNORECASE,
)


def _sanitize_error(e: Exception) -> str:
    msg = str(e)
    if _SENSITIVE_PATTERN.search(msg):
        return "AI服务暂时不可用，请稍后再试"
    return msg

logger = logging.getLogger("uvicorn.error")

MAX_TOOL_ROUNDS = 5
MAX_CONTEXT_CHARS = 24000
TOOL_RESULT_HARD_LIMIT = 1200
PLANNER_TRIGGER_PATTERN = re.compile(
    r"(比较|对比|异同|结合|综合|同时|并且|推荐|路线|多首|多位|多个|分别|联系|创作|赏析|根据.*学习)",
    re.IGNORECASE,
)


class AgentEngine:

    def __init__(self, client: AsyncOpenAI):
        self.client = client
        self._seen_calls: set[str] = set()

    @staticmethod
    def _estimate_context_chars(messages: list) -> int:
        total = 0
        for msg in messages:
            if isinstance(msg, dict):
                total += len(str(msg.get("content", "")))
            else:
                total += len(str(getattr(msg, "content", "") or ""))
        return total

    @staticmethod
    def _compress_tool_results(messages: list) -> list:
        compressed = []
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "tool":
                content = msg.get("content", "")
                if len(content) > TOOL_RESULT_HARD_LIMIT:
                    msg = {**msg, "content": content[:TOOL_RESULT_HARD_LIMIT] + "...(已截断)"}
            compressed.append(msg)
        return compressed

    def _make_call_key(self, fn_name: str, fn_args: dict) -> str:
        return f"{fn_name}:{json.dumps(fn_args, sort_keys=True, ensure_ascii=False)}"

    def _reset_dedup(self):
        self._seen_calls.clear()

    def _get_model(self, tier: AIModelTier) -> str:
        return get_model_name(tier)

    def _should_use_planner(self, prompt: str, model_tier: AIModelTier) -> bool:
        if model_tier == AIModelTier.FLASH:
            return False
        if len(prompt.strip()) >= 220:
            return True
        return bool(PLANNER_TRIGGER_PATTERN.search(prompt))

    def _load_json_content(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
                cleaned = "\n".join(lines)
            return json.loads(cleaned)

    def _normalize_plan(self, plan: dict) -> Optional[dict]:
        if not isinstance(plan, dict):
            return None
        raw_steps = plan.get("steps") or []
        normalized_steps = []
        for idx, item in enumerate(raw_steps[:4], start=1):
            if not isinstance(item, dict):
                continue
            task = str(item.get("task") or "").strip()
            if not task:
                continue
            preferred_tools = item.get("preferred_tools") or []
            if not isinstance(preferred_tools, list):
                preferred_tools = [preferred_tools]
            preferred_tools = [str(tool).strip() for tool in preferred_tools if str(tool).strip()]
            normalized_steps.append({
                "step": idx,
                "task": task,
                "preferred_tools": preferred_tools,
                "success_criteria": str(item.get("success_criteria") or "").strip(),
            })
        if not normalized_steps:
            return None
        return {
            "goal": str(plan.get("goal") or "完成用户请求").strip(),
            "complexity": str(plan.get("complexity") or "medium").strip(),
            "steps": normalized_steps,
            "answer_strategy": str(plan.get("answer_strategy") or "").strip(),
            "replanned": bool(plan.get("replanned")),
        }

    def _render_plan(self, plan: dict, title: str = "执行计划") -> str:
        lines = [f"【{title}】", f"目标：{plan.get('goal', '完成用户请求')}"]
        for step in plan.get("steps", []):
            tool_text = "、".join(step.get("preferred_tools", [])) or "按需要选择工具"
            success = step.get("success_criteria") or "获取当前步骤所需信息"
            lines.append(f"第{step['step']}步：{step['task']}；优先工具：{tool_text}；完成标准：{success}")
        if plan.get("answer_strategy"):
            lines.append(f"回答策略：{plan['answer_strategy']}")
        return "\n".join(lines)

    async def _execute_tool_timed(
        self,
        tool_name: str,
        arguments: dict,
        db: AsyncSession,
    ) -> tuple[str, float]:
        from ..core.database import AsyncSessionLocal
        started = time.perf_counter()
        async with AsyncSessionLocal() as tool_db:
            result = await execute_tool(tool_name, arguments, tool_db)
        elapsed_ms = (time.perf_counter() - started) * 1000
        return result, elapsed_ms

    async def _call_json_completion(
        self,
        prompt: str,
        system_prompt: str,
        model_tier: AIModelTier,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        use_identity_guard: bool = True,
        on_progress: Optional[Callable] = None,
    ) -> dict:
        sys_content = (AI_IDENTITY_GUARD + "\n" + system_prompt) if use_identity_guard else system_prompt
        messages = [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": prompt},
        ]
        if on_progress:
            await on_progress({"type": "thinking", "content": "正在构思灵感..."})
        try:
            response = await self.client.chat.completions.create(
                model=self._get_model(model_tier),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.error(f"Planner 调用失败: {e}")
            raise RuntimeError(_sanitize_error(e)) from None
        raw = response.choices[0].message.content or "{}"
        return self._load_json_content(raw)

    async def _plan_task(
        self,
        prompt: str,
        system_prompt: str,
        model_tier: AIModelTier,
    ) -> Optional[dict]:
        plan = await self._call_json_completion(
            prompt=f"【用户问题】\n{prompt}",
            system_prompt=LIGHT_PLANNER_PROMPT,
            model_tier=AIModelTier.FLASH,
            temperature=0.2,
            max_tokens=1024,
            use_identity_guard=False,
        )
        return self._normalize_plan(plan)

    async def _replan_task(
        self,
        prompt: str,
        system_prompt: str,
        current_plan: dict,
        tool_call_log: list[dict],
        observation_hints: list[str],
        model_tier: AIModelTier,
    ) -> Optional[dict]:
        tool_log_lines = []
        for item in tool_call_log[-6:]:
            args_text = json.dumps(item.get("args", {}), ensure_ascii=False)[:120]
            result_text = str(item.get("result_preview", ""))[:160]
            tool_log_lines.append(f"- 工具：{item.get('tool', '')} 参数：{args_text} 结果摘要：{result_text}")
        tool_log_text = "\n".join(tool_log_lines) if tool_log_lines else "（暂无）"
        try:
            replan = await asyncio.wait_for(
                self._call_json_completion(
                    prompt=(
                        f"【原始用户问题】\n{prompt}\n\n"
                        f"【当前计划】\n{self._render_plan(current_plan)}\n\n"
                        f"【工具执行记录】\n{tool_log_text}\n\n"
                        f"【观察提示】\n{' '.join(observation_hints)}"
                    ),
                    system_prompt=LIGHT_REPLANNER_PROMPT,
                    model_tier=AIModelTier.FLASH,
                    temperature=0.2,
                    max_tokens=512,
                    use_identity_guard=False,
                ),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            logger.warning("Replan 超时(15s)，跳过重规划")
            return None
        normalized = self._normalize_plan(replan)
        if normalized:
            normalized["replanned"] = True
        return normalized

    def _plan_to_rewoo_steps(self, plan: dict, tools: list[dict]) -> Optional[list[dict]]:
        valid_tool_names = {t["function"]["name"] for t in tools}
        steps = plan.get("steps") or []
        if len(steps) < 2:
            return None
        rewoo_steps = []
        has_parallel = False
        for s in steps:
            preferred = s.get("preferred_tools") or []
            usable = [t for t in preferred if t in valid_tool_names]
            if not usable:
                continue
            tool = usable[0]
            task_text = s.get("task", "")
            args = {"keyword": task_text[:20]} if tool == "search_poems" else {}
            step_id = f"E{s['step']}"
            deps = [f"E{s['step'] - 1}"] if s["step"] > 1 and rewoo_steps else []
            if not deps and len(rewoo_steps) > 0:
                has_parallel = True
            rewoo_steps.append({"id": step_id, "tool": tool, "args": args, "depends_on": deps})
        if not rewoo_steps or not has_parallel:
            return None
        return rewoo_steps

    async def run_agent(
        self,
        prompt: str,
        system_prompt: str,
        db: AsyncSession,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_tier: AIModelTier = get_default_model_tier(),
        tools: Optional[list] = None,
        response_format: Optional[dict] = None,
        enable_react: bool = True,
        enable_planner: bool = False,
        on_progress: Optional[Callable] = None,
    ) -> str:
        trace_id = f"agent-{int(time.perf_counter() * 1000) % 1000000}"
        started_at = time.perf_counter()
        self._reset_dedup()
        if tools is None:
            tools = TOOL_DEFINITIONS
        use_tools = len(tools) > 0

        full_system = AI_IDENTITY_GUARD + "\n" + system_prompt
        if use_tools:
            full_system += "\n\n" + TOOL_USE_GUIDE
        if enable_react:
            full_system += "\n\n" + REACT_REASONING

        planner_state = None
        working_prompt = prompt
        if enable_planner and self._should_use_planner(prompt, model_tier):
            if on_progress:
                await on_progress({"type": "thinking", "content": "正在规划任务..."})
            planner_started = time.perf_counter()
            planner_state = await self._plan_task(prompt, system_prompt, model_tier)
            planner_elapsed = (time.perf_counter() - planner_started) * 1000
            if planner_state:
                rewoo_steps = self._plan_to_rewoo_steps(planner_state, tools)
                if rewoo_steps:
                    logger.info(f"Agent Planner → ReWOO 并行执行: {len(rewoo_steps)} steps")
                    return await self.run_agent_rewoo(
                        prompt=prompt, system_prompt=system_prompt, db=db,
                        temperature=temperature, max_tokens=max_tokens,
                        model_tier=model_tier, tools=tools,
                        response_format=response_format, on_progress=on_progress,
                    )
                working_prompt = prompt + "\n\n" + self._render_plan(planner_state) + "\n请先完成计划中的信息收集，再输出最终答案。"
                logger.info(f"Agent Planner 已启用: {planner_state.get('complexity')} / {planner_state.get('goal')}")
            logger.info(f"Agent 时序[{trace_id}] planner_ms={planner_elapsed:.1f}")

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": working_prompt},
        ]

        tool_call_log = []
        consecutive_failures = 0

        for round_idx in range(MAX_TOOL_ROUNDS + 1):
            kwargs = {
                "model": self._get_model(model_tier),
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if use_tools and round_idx < MAX_TOOL_ROUNDS:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            if response_format and round_idx == MAX_TOOL_ROUNDS:
                kwargs["response_format"] = response_format

            llm_started = time.perf_counter()
            try:
                response = await self.client.chat.completions.create(**kwargs)
            except Exception as e:
                llm_elapsed = (time.perf_counter() - llm_started) * 1000
                logger.info(f"Agent 时序[{trace_id}] round={round_idx + 1} llm_fail_ms={llm_elapsed:.1f}")
                logger.error(f"Agent LLM 调用失败 (round {round_idx}): {e}")
                raise RuntimeError(_sanitize_error(e)) from None
            llm_elapsed = (time.perf_counter() - llm_started) * 1000
            logger.info(f"Agent 时序[{trace_id}] round={round_idx + 1} llm_ms={llm_elapsed:.1f}")

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" or (
                choice.message.tool_calls and len(choice.message.tool_calls) > 0
            ):
                messages.append(choice.message)

                parsed_calls = []
                dedup_skipped = []
                for tc in choice.message.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        fn_args = {}
                    call_key = self._make_call_key(fn_name, fn_args)
                    if call_key in self._seen_calls:
                        dedup_skipped.append((tc.id, fn_name))
                        logger.info(f"Agent 工具去重跳过: {fn_name}")
                        continue
                    self._seen_calls.add(call_key)
                    logger.info(f"Agent 工具调用: {fn_name}({json.dumps(fn_args, ensure_ascii=False)[:200]})")
                    parsed_calls.append((tc.id, fn_name, fn_args))

                for tc_id, fn_name in dedup_skipped:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": json.dumps({"info": f"{fn_name} 已调用过相同参数，跳过重复"}, ensure_ascii=False),
                    })

                if parsed_calls:
                    if on_progress:
                        tool_names = [fn for _, fn, _ in parsed_calls]
                        await on_progress({"type": "tool_call", "content": f"调用工具: {', '.join(tool_names)}", "tools": tool_names, "round": round_idx + 1})
                    tool_batch_started = time.perf_counter()
                    timed_results = await asyncio.gather(
                        *(self._execute_tool_timed(name, args, db) for _, name, args in parsed_calls)
                    )
                    tool_batch_elapsed = (time.perf_counter() - tool_batch_started) * 1000
                    results = [item[0] for item in timed_results]
                    tool_elapsed_list = [item[1] for item in timed_results]
                    logger.info(
                        f"Agent 时序[{trace_id}] round={round_idx + 1} tools_batch_ms={tool_batch_elapsed:.1f} count={len(parsed_calls)}"
                    )
                else:
                    results = []
                    tool_elapsed_list = []

                observation_hints = []
                for idx, ((tc_id, fn_name, fn_args), tool_result) in enumerate(zip(parsed_calls, results)):
                    tool_elapsed = tool_elapsed_list[idx] if idx < len(tool_elapsed_list) else 0.0
                    tool_call_log.append({
                        "tool": fn_name,
                        "args": fn_args,
                        "result_preview": tool_result[:200],
                    })
                    logger.info(
                        f"Agent 时序[{trace_id}] round={round_idx + 1} tool={fn_name} ms={tool_elapsed:.1f}"
                    )
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": tool_result,
                    })
                    try:
                        parsed = json.loads(tool_result)
                        if isinstance(parsed, dict) and parsed.get("error"):
                            observation_hints.append(
                                f"⚠ {fn_name} 返回错误：{parsed['error']}。"
                                f"建议换关键词或换工具重试。"
                            )
                        elif isinstance(parsed, dict) and parsed.get("count") == 0:
                            observation_hints.append(
                                f"⚠ {fn_name} 未找到结果，可尝试更宽泛的搜索条件。"
                            )
                    except (json.JSONDecodeError, TypeError):
                        pass

                if observation_hints and round_idx < MAX_TOOL_ROUNDS - 1:
                    consecutive_failures += 1
                    hint_text = "\n".join(observation_hints)
                    if planner_state and not planner_state.get("replanned") and consecutive_failures >= 2:
                        replan_started = time.perf_counter()
                        replanned = await self._replan_task(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            current_plan=planner_state,
                            tool_call_log=tool_call_log,
                            observation_hints=observation_hints,
                            model_tier=model_tier,
                        )
                        replan_elapsed = (time.perf_counter() - replan_started) * 1000
                        logger.info(
                            f"Agent 时序[{trace_id}] round={round_idx + 1} replan_ms={replan_elapsed:.1f}"
                        )
                        if replanned:
                            planner_state = replanned
                            hint_text += "\n\n" + self._render_plan(planner_state, title="更新计划")
                            logger.info(f"Agent Planner 已重规划: {planner_state.get('goal')}")
                            if on_progress:
                                await on_progress({"type": "thinking", "content": "已调整计划，继续执行..."})
                    messages.append({
                        "role": "user",
                        "content": f"【观察提示】\n{hint_text}\n请根据以上观察决定是否需要重试或调整策略。",
                    })
                    logger.info(f"Agent 观察提示: {hint_text[:200]}")
                else:
                    consecutive_failures = 0

                if self._estimate_context_chars(messages) > MAX_CONTEXT_CHARS:
                    messages = [messages[0]] + self._compress_tool_results(messages[1:])
                    logger.info("Agent 上下文压缩已执行")

                continue

            final_content = choice.message.content or ""
            if on_progress:
                await on_progress({"type": "thinking", "content": "正在生成最终结果..."})

            if tool_call_log:
                logger.info(
                    f"Agent 完成: {len(tool_call_log)} 次工具调用, "
                    f"工具链: {' → '.join(t['tool'] for t in tool_call_log)}"
                )

            if response_format:
                try:
                    self._load_json_content(final_content)
                except Exception:
                    messages.append(choice.message)
                    try:
                        json_closure_started = time.perf_counter()
                        response_json = await self.client.chat.completions.create(
                            model=self._get_model(model_tier),
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            response_format=response_format,
                        )
                        json_closure_elapsed = (time.perf_counter() - json_closure_started) * 1000
                        logger.info(
                            f"Agent 时序[{trace_id}] json_closure_ms={json_closure_elapsed:.1f}"
                        )
                    except Exception as e:
                        json_closure_elapsed = (time.perf_counter() - json_closure_started) * 1000
                        logger.info(
                            f"Agent 时序[{trace_id}] json_closure_fail_ms={json_closure_elapsed:.1f}"
                        )
                        logger.error(f"Agent JSON 收口失败: {e}")
                        raise RuntimeError(_sanitize_error(e)) from None
                    total_elapsed = (time.perf_counter() - started_at) * 1000
                    logger.info(f"Agent 时序[{trace_id}] total_ms={total_elapsed:.1f}")
                    return response_json.choices[0].message.content or ""

            total_elapsed = (time.perf_counter() - started_at) * 1000
            logger.info(f"Agent 时序[{trace_id}] total_ms={total_elapsed:.1f}")
            return final_content

        last_msg = messages[-1]
        if isinstance(last_msg, dict) and last_msg.get("role") == "tool":
            kwargs_final = {
                "model": self._get_model(model_tier),
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs_final["response_format"] = response_format
            final_started = time.perf_counter()
            response = await self.client.chat.completions.create(**kwargs_final)
            final_elapsed = (time.perf_counter() - final_started) * 1000
            total_elapsed = (time.perf_counter() - started_at) * 1000
            logger.info(f"Agent 时序[{trace_id}] final_llm_ms={final_elapsed:.1f} total_ms={total_elapsed:.1f}")
            return response.choices[0].message.content or ""

        total_elapsed = (time.perf_counter() - started_at) * 1000
        logger.info(f"Agent 时序[{trace_id}] total_ms={total_elapsed:.1f}")
        return ""

    async def run_agent_json(
        self,
        prompt: str,
        system_prompt: str,
        db: AsyncSession,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_tier: AIModelTier = get_default_model_tier(),
        tools: Optional[list] = None,
        enable_react: bool = True,
        enable_planner: bool = False,
        on_progress: Optional[Callable] = None,
    ) -> dict:
        raw = await self.run_agent(
            prompt=prompt,
            system_prompt=system_prompt,
            db=db,
            temperature=temperature,
            max_tokens=max_tokens,
            model_tier=model_tier,
            tools=tools,
            response_format={"type": "json_object"},
            enable_react=enable_react,
            enable_planner=enable_planner,
            on_progress=on_progress,
        )
        return self._load_json_content(raw)

    @staticmethod
    def _format_tool_descriptions(tools: list[dict]) -> str:
        lines = []
        for t in tools:
            fn = t.get("function", {})
            name = fn.get("name", "")
            desc = fn.get("description", "")
            params = fn.get("parameters", {})
            props = params.get("properties", {})
            required = params.get("required", [])
            parts = []
            for pname, pdef in props.items():
                ptype = pdef.get("type", "string")
                suffix = "" if pname in required else "?"
                parts.append(f"{pname}{suffix}: {ptype}")
            sig = ", ".join(parts)
            lines.append(f"- {name}({sig}): {desc[:80]}")
        return "\n".join(lines)

    @staticmethod
    def _resolve_ref(value, evidence: dict):
        if not isinstance(value, str) or not value.startswith("$E"):
            return value
        match = re.match(r"^\$E(\d+)(.*)", value)
        if not match:
            return value
        step_id = f"E{match.group(1)}"
        path_suffix = match.group(2)
        raw = evidence.get(step_id)
        if raw is None:
            return value
        if not path_suffix:
            return raw
        try:
            obj = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return raw
        for segment in re.findall(r'\.(\w+)|\[(\d+)\]', path_suffix):
            key, idx = segment
            try:
                if key:
                    obj = obj[key]
                else:
                    obj = obj[int(idx)]
            except (KeyError, IndexError, TypeError):
                return raw
        return str(obj) if not isinstance(obj, str) else obj

    @staticmethod
    def _format_evidence(evidence: dict) -> str:
        blocks = []
        for step_id, result in evidence.items():
            blocks.append(f"[{step_id}] {result[:600]}")
        return "\n\n".join(blocks)

    async def run_agent_rewoo(
        self,
        prompt: str,
        system_prompt: str,
        db: AsyncSession,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_tier: AIModelTier = get_default_model_tier(),
        tools: Optional[list] = None,
        response_format: Optional[dict] = None,
        on_progress: Optional[Callable] = None,
    ) -> str:
        trace_id = f"rewoo-{int(time.perf_counter() * 1000) % 1000000}"
        started_at = time.perf_counter()
        if tools is None:
            tools = TOOL_DEFINITIONS

        tool_desc = self._format_tool_descriptions(tools)
        planner_prompt = REWOO_PLANNER_PROMPT.format(tool_descriptions=tool_desc)

        if on_progress:
            await on_progress({"type": "thinking", "content": "正在规划任务..."})
        planner_started = time.perf_counter()
        try:
            plan = await self._call_json_completion(
                prompt=prompt,
                system_prompt=planner_prompt,
                model_tier=AIModelTier.FLASH,
                temperature=0.2,
                max_tokens=512,
                use_identity_guard=False,
            )
        except Exception as e:
            logger.warning(f"ReWoo Planner 失败, fallback ReAct: {e}")
            return await self.run_agent(
                prompt=prompt, system_prompt=system_prompt, db=db,
                temperature=temperature, max_tokens=max_tokens,
                model_tier=model_tier, tools=tools,
                response_format=response_format,
                enable_react=True, enable_planner=False,
            )
        planner_elapsed = (time.perf_counter() - planner_started) * 1000
        logger.info(f"ReWoo 时序[{trace_id}] planner_ms={planner_elapsed:.1f}")

        steps = plan.get("steps") or []
        if not isinstance(steps, list):
            steps = []
        valid_tool_names = {t["function"]["name"] for t in tools}
        validated = []
        for s in steps[:4]:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("id", ""))
            tool_name = str(s.get("tool", ""))
            if tool_name not in valid_tool_names:
                continue
            args = s.get("args") or {}
            if not isinstance(args, dict):
                args = {}
            deps = s.get("depends_on") or []
            if not isinstance(deps, list):
                deps = []
            validated.append({"id": sid, "tool": tool_name, "args": args, "depends_on": deps})

        if not validated:
            logger.info(f"ReWoo Planner 返回空 steps, 直接进 Solver")

        evidence: dict[str, str] = {}

        if validated:
            step_map = {s["id"]: s for s in validated}
            executed = set()
            max_layers = 5
            for layer_idx in range(max_layers):
                layer = [
                    s for s in validated
                    if s["id"] not in executed
                    and all(d in executed for d in s["depends_on"])
                ]
                if not layer:
                    break

                if on_progress:
                    tool_names = [s["tool"] for s in layer]
                    await on_progress({"type": "tool_call", "content": f"执行工具: {', '.join(tool_names)}", "tools": tool_names, "round": layer_idx + 1})

                async def _exec_step(step):
                    resolved_args = {}
                    for k, v in step["args"].items():
                        resolved_args[k] = self._resolve_ref(v, evidence)
                    try:
                        result, elapsed = await self._execute_tool_timed(
                            step["tool"], resolved_args, db,
                        )
                    except Exception as e:
                        result = json.dumps({"error": str(e)}, ensure_ascii=False)
                        elapsed = 0
                    logger.info(
                        f"ReWoo 时序[{trace_id}] step={step['id']} tool={step['tool']} ms={elapsed:.1f}"
                    )
                    return step["id"], result

                results = await asyncio.gather(*[_exec_step(s) for s in layer])
                for sid, result in results:
                    evidence[sid] = result
                    executed.add(sid)

        worker_elapsed = (time.perf_counter() - started_at) * 1000 - planner_elapsed
        logger.info(f"ReWoo 时序[{trace_id}] worker_ms={worker_elapsed:.1f} steps={len(evidence)}")

        evidence_text = self._format_evidence(evidence) if evidence else "（无工具证据）"
        if on_progress:
            await on_progress({"type": "thinking", "content": "正在整合结果..."})
        solver_user = prompt + "\n\n" + REWOO_EVIDENCE_TEMPLATE.format(evidence_blocks=evidence_text)

        full_system = AI_IDENTITY_GUARD_LITE + "\n" + system_prompt
        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": solver_user},
        ]
        solver_kwargs = {
            "model": self._get_model(model_tier),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            solver_kwargs["response_format"] = response_format

        solver_started = time.perf_counter()
        try:
            response = await self.client.chat.completions.create(**solver_kwargs)
        except Exception as e:
            logger.error(f"ReWoo Solver 调用失败: {e}")
            raise RuntimeError(_sanitize_error(e)) from None
        solver_elapsed = (time.perf_counter() - solver_started) * 1000
        total_elapsed = (time.perf_counter() - started_at) * 1000
        logger.info(f"ReWoo 时序[{trace_id}] solver_ms={solver_elapsed:.1f} total_ms={total_elapsed:.1f}")

        final_content = response.choices[0].message.content or ""

        if response_format:
            try:
                self._load_json_content(final_content)
            except Exception:
                try:
                    messages.append(response.choices[0].message)
                    fix_response = await self.client.chat.completions.create(
                        model=self._get_model(model_tier),
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=response_format,
                    )
                    final_content = fix_response.choices[0].message.content or ""
                except Exception as e:
                    logger.error(f"ReWoo JSON 修复失败: {e}")
                    raise RuntimeError(_sanitize_error(e)) from None

        return final_content

    async def run_agent_rewoo_json(
        self,
        prompt: str,
        system_prompt: str,
        db: AsyncSession,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_tier: AIModelTier = get_default_model_tier(),
        tools: Optional[list] = None,
        on_progress: Optional[Callable] = None,
    ) -> dict:
        raw = await self.run_agent_rewoo(
            prompt=prompt,
            system_prompt=system_prompt,
            db=db,
            temperature=temperature,
            max_tokens=max_tokens,
            model_tier=model_tier,
            tools=tools,
            response_format={"type": "json_object"},
            on_progress=on_progress,
        )
        return self._load_json_content(raw)

    async def run_agent_chat(
        self,
        messages_history: list[dict],
        system_prompt: str,
        db: AsyncSession,
        temperature: float = 0.6,
        max_tokens: int = 1024,
        model_tier: AIModelTier = get_default_model_tier(),
        tools: Optional[list] = None,
    ) -> str:
        trace_id = f"chat-{int(time.perf_counter() * 1000) % 1000000}"
        started_at = time.perf_counter()
        self._reset_dedup()
        if tools is None:
            tools = TOOL_DEFINITIONS

        full_system = AI_IDENTITY_GUARD + "\n" + system_prompt + "\n\n" + TOOL_USE_GUIDE_CHAT

        messages = [{"role": "system", "content": full_system}]
        messages.extend(messages_history)

        for round_idx in range(MAX_TOOL_ROUNDS + 1):
            kwargs = {
                "model": self._get_model(model_tier),
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if round_idx < MAX_TOOL_ROUNDS:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            llm_started = time.perf_counter()
            try:
                response = await self.client.chat.completions.create(**kwargs)
            except Exception as e:
                llm_elapsed = (time.perf_counter() - llm_started) * 1000
                logger.info(f"Agent Chat 时序[{trace_id}] round={round_idx + 1} llm_fail_ms={llm_elapsed:.1f}")
                logger.error(f"Agent Chat LLM 调用失败 (round {round_idx}): {e}")
                raise RuntimeError(_sanitize_error(e)) from None
            llm_elapsed = (time.perf_counter() - llm_started) * 1000
            logger.info(f"Agent Chat 时序[{trace_id}] round={round_idx + 1} llm_ms={llm_elapsed:.1f}")

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" or (
                choice.message.tool_calls and len(choice.message.tool_calls) > 0
            ):
                messages.append(choice.message)
                parsed_calls = []
                for tc in choice.message.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        fn_args = {}
                    call_key = self._make_call_key(fn_name, fn_args)
                    if call_key in self._seen_calls:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({"info": f"{fn_name} 已调用过相同参数，跳过重复"}, ensure_ascii=False),
                        })
                        continue
                    self._seen_calls.add(call_key)
                    logger.info(f"Agent Chat 工具调用: {fn_name}")
                    parsed_calls.append((tc.id, fn_name, fn_args))

                if parsed_calls:
                    tool_batch_started = time.perf_counter()
                    timed_results = await asyncio.gather(
                        *(self._execute_tool_timed(name, args, db) for _, name, args in parsed_calls)
                    )
                    tool_batch_elapsed = (time.perf_counter() - tool_batch_started) * 1000
                    results = [item[0] for item in timed_results]
                    tool_elapsed_list = [item[1] for item in timed_results]
                    logger.info(
                        f"Agent Chat 时序[{trace_id}] round={round_idx + 1} tools_batch_ms={tool_batch_elapsed:.1f} count={len(parsed_calls)}"
                    )
                else:
                    results = []
                    tool_elapsed_list = []

                observation_hints = []
                for idx, ((tc_id, fn_name, _), tool_result) in enumerate(zip(parsed_calls, results)):
                    tool_elapsed = tool_elapsed_list[idx] if idx < len(tool_elapsed_list) else 0.0
                    logger.info(
                        f"Agent Chat 时序[{trace_id}] round={round_idx + 1} tool={fn_name} ms={tool_elapsed:.1f}"
                    )
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": tool_result,
                    })
                    try:
                        parsed = json.loads(tool_result)
                        if isinstance(parsed, dict) and parsed.get("error"):
                            observation_hints.append(
                                f"⚠ {fn_name} 返回错误：{parsed['error']}。建议换关键词或换工具重试。"
                            )
                    except (json.JSONDecodeError, TypeError):
                        pass

                if observation_hints and round_idx < MAX_TOOL_ROUNDS - 1:
                    hint_text = "\n".join(observation_hints)
                    messages.append({
                        "role": "user",
                        "content": f"【观察提示】\n{hint_text}\n请根据以上观察决定是否需要重试或调整策略。",
                    })

                if self._estimate_context_chars(messages) > MAX_CONTEXT_CHARS:
                    messages = [messages[0]] + self._compress_tool_results(messages[1:])

                continue

            total_elapsed = (time.perf_counter() - started_at) * 1000
            logger.info(f"Agent Chat 时序[{trace_id}] total_ms={total_elapsed:.1f}")
            return choice.message.content or ""

        total_elapsed = (time.perf_counter() - started_at) * 1000
        logger.info(f"Agent Chat 时序[{trace_id}] total_ms={total_elapsed:.1f}")
        return ""

    async def run_agent_chat_stream(
        self,
        messages_history: list[dict],
        system_prompt: str,
        db: AsyncSession,
        temperature: float = 0.6,
        max_tokens: int = 1024,
        model_tier: AIModelTier = get_default_model_tier(),
        tools: Optional[list] = None,
        emit_events: bool = True,
    ):
        trace_id = f"stream-{int(time.perf_counter() * 1000) % 1000000}"
        started_at = time.perf_counter()
        self._reset_dedup()
        if tools is None:
            tools = TOOL_DEFINITIONS

        full_system = AI_IDENTITY_GUARD + "\n" + system_prompt + "\n\n" + TOOL_USE_GUIDE_CHAT

        messages = [{"role": "system", "content": full_system}]
        messages.extend(messages_history)

        if emit_events:
            yield json.dumps({"type": "thinking", "content": "正在思考..."}, ensure_ascii=False)

        for round_idx in range(MAX_TOOL_ROUNDS + 1):
            is_last_round = round_idx == MAX_TOOL_ROUNDS
            kwargs = {
                "model": self._get_model(model_tier),
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if not is_last_round:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
                llm_started = time.perf_counter()
                try:
                    response = await self.client.chat.completions.create(**kwargs)
                except Exception as e:
                    llm_elapsed = (time.perf_counter() - llm_started) * 1000
                    logger.info(f"Agent Stream 时序[{trace_id}] round={round_idx + 1} llm_fail_ms={llm_elapsed:.1f}")
                    logger.error(f"Agent Stream LLM 调用失败 (round {round_idx}): {e}")
                    raise RuntimeError(_sanitize_error(e)) from None
                llm_elapsed = (time.perf_counter() - llm_started) * 1000
                logger.info(f"Agent Stream 时序[{trace_id}] round={round_idx + 1} llm_ms={llm_elapsed:.1f}")

                choice = response.choices[0]

                if choice.finish_reason == "tool_calls" or (
                    choice.message.tool_calls and len(choice.message.tool_calls) > 0
                ):
                    messages.append(choice.message)
                    parsed_calls = []
                    for tc in choice.message.tool_calls:
                        fn_name = tc.function.name
                        try:
                            fn_args = json.loads(tc.function.arguments)
                        except json.JSONDecodeError:
                            fn_args = {}
                        call_key = self._make_call_key(fn_name, fn_args)
                        if call_key in self._seen_calls:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": json.dumps({"info": f"{fn_name} 已调用过相同参数，跳过重复"}, ensure_ascii=False),
                            })
                            continue
                        self._seen_calls.add(call_key)
                        logger.info(f"Agent Stream 工具调用: {fn_name}")
                        parsed_calls.append((tc.id, fn_name, fn_args))

                    if emit_events and parsed_calls:
                        tool_names = [fn for _, fn, _ in parsed_calls]
                        _TOOL_LABELS = {
                            "search_poems": "搜索诗词",
                            "get_poem_detail": "查阅诗词详情",
                            "get_author_info": "查询诗人档案",
                            "verify_poem_line": "验证诗句",
                            "get_related_poems": "查找相关诗词",
                            "count_poems_stats": "统计数据",
                            "compare_poets": "对比诗人",
                            "random_poem": "随机推荐",
                            "get_dynasty_context": "朝代背景",
                            "search_poems_advanced": "高级搜索",
                            "get_user_profile": "查看学习画像",
                            "get_user_learning_history": "查看学习记录",
                        }
                        labels = [_TOOL_LABELS.get(n, n) for n in tool_names]
                        yield json.dumps({
                            "type": "tool_call",
                            "tools": tool_names,
                            "labels": labels,
                            "round": round_idx + 1,
                        }, ensure_ascii=False)

                    if parsed_calls:
                        tool_batch_started = time.perf_counter()
                        timed_results = await asyncio.gather(
                            *(self._execute_tool_timed(name, args, db) for _, name, args in parsed_calls)
                        )
                        tool_batch_elapsed = (time.perf_counter() - tool_batch_started) * 1000
                        results = [item[0] for item in timed_results]
                        tool_elapsed_list = [item[1] for item in timed_results]
                        logger.info(
                            f"Agent Stream 时序[{trace_id}] round={round_idx + 1} tools_batch_ms={tool_batch_elapsed:.1f} count={len(parsed_calls)}"
                        )
                        for idx, ((tc_id, fn_name, _), tool_result) in enumerate(zip(parsed_calls, results)):
                            tool_elapsed = tool_elapsed_list[idx] if idx < len(tool_elapsed_list) else 0.0
                            logger.info(
                                f"Agent Stream 时序[{trace_id}] round={round_idx + 1} tool={fn_name} ms={tool_elapsed:.1f}"
                            )
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc_id,
                                "content": tool_result,
                            })

                    if self._estimate_context_chars(messages) > MAX_CONTEXT_CHARS:
                        messages = [messages[0]] + self._compress_tool_results(messages[1:])

                    continue

                if emit_events:
                    yield json.dumps({"type": "thinking", "content": "整理回答中..."}, ensure_ascii=False)

                if choice.message.content:
                    content = choice.message.content
                    chunk_size = 4
                    for i in range(0, len(content), chunk_size):
                        yield content[i:i + chunk_size]
                        await asyncio.sleep(0)
                    total_elapsed = (time.perf_counter() - started_at) * 1000
                    logger.info(f"Agent Stream 时序[{trace_id}] total_ms={total_elapsed:.1f}")
                    return

            kwargs["stream"] = True
            if "tools" in kwargs:
                del kwargs["tools"]
            if "tool_choice" in kwargs:
                del kwargs["tool_choice"]

            try:
                stream_started = time.perf_counter()
                stream = await self.client.chat.completions.create(**kwargs)
            except Exception as e:
                stream_elapsed = (time.perf_counter() - stream_started) * 1000
                logger.info(f"Agent Stream 时序[{trace_id}] stream_fail_ms={stream_elapsed:.1f}")
                logger.error(f"Agent Stream LLM 流式调用失败: {e}")
                raise RuntimeError(_sanitize_error(e)) from None

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

            stream_elapsed = (time.perf_counter() - stream_started) * 1000
            total_elapsed = (time.perf_counter() - started_at) * 1000
            logger.info(f"Agent Stream 时序[{trace_id}] stream_output_ms={stream_elapsed:.1f} total_ms={total_elapsed:.1f}")
            return
