"""
AI 后端接口端到端耗时基准测试
直接调用项目 HTTP 接口，测量完整请求链路各阶段耗时
"""
import asyncio
import time
import sys
import io
import json
import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000/api/v1"
# 测试账号 - 如果登录失败请修改
TEST_USER = "test"
TEST_PASS = "test123456"

TOKEN = ""
RESULTS = []


def fmt(ms: float) -> str:
    return f"{ms/1000:.2f}s" if ms >= 1000 else f"{ms:.0f}ms"


def bar(label: str, ms: float, max_ms: float = 60000):
    n = int(min(ms / max_ms, 1.0) * 40)
    print(f"  {label:<20} |{'#'*n}{'-'*(40-n)}| {fmt(ms)}")


def header(title: str):
    print(f"\n{'='*64}")
    print(f"  {title}")
    print(f"{'='*64}")


async def login(client: httpx.AsyncClient):
    global TOKEN
    r = await client.post(f"{BASE}/users/login", json={
        "username": TEST_USER, "password": TEST_PASS,
    })
    if r.status_code != 200:
        print(f"  登录失败 ({r.status_code}): {r.text[:200]}")
        print(f"  请修改脚本中的 TEST_USER / TEST_PASS")
        sys.exit(1)
    data = r.json().get("data", r.json())
    TOKEN = data["access_token"]
    print(f"  登录成功, token: {TOKEN[:20]}...")


def auth_headers():
    return {"Authorization": f"Bearer {TOKEN}"}


async def bench_post(client: httpx.AsyncClient, name: str, path: str, body: dict):
    """测试普通 POST 接口，返回分段耗时"""
    header(name)

    t0 = time.perf_counter()
    r = await client.post(f"{BASE}{path}", json=body, headers=auth_headers(), timeout=90)
    t_total = (time.perf_counter() - t0) * 1000

    server_time = r.headers.get("X-Response-Time", "?")
    server_ms = float(server_time.replace("ms", "")) if "ms" in server_time else 0

    network_ms = t_total - server_ms if server_ms else 0

    print(f"  HTTP状态:        {r.status_code}")
    print(f"  客户端总耗时:    {fmt(t_total)}")
    print(f"  服务端耗时:      {server_time}  (X-Response-Time)")
    print(f"  网络开销:        {fmt(network_ms)}" if server_ms else "")

    if r.status_code == 200:
        text = r.text
        print(f"  响应大小:        {len(text)} bytes")
        # 尝试提取关键字段
        try:
            j = r.json()
            preview = json.dumps(j, ensure_ascii=False)[:120]
            print(f"  响应预览:        {preview}...")
        except Exception:
            print(f"  响应预览:        {text[:120]}...")
    else:
        print(f"  错误:            {r.text[:200]}")

    bar("network", network_ms)
    bar("server", server_ms)
    bar("total", t_total)

    RESULTS.append({
        "name": name, "total_ms": t_total,
        "server_ms": server_ms, "network_ms": network_ms,
        "status": r.status_code,
    })


async def bench_stream(client: httpx.AsyncClient, name: str, path: str, body: dict):
    """测试 SSE 流式接口，返回分段耗时"""
    header(name)

    events = []
    t0 = time.perf_counter()
    t_connected = None
    t_first_content = None
    content_parts = []

    async with client.stream("POST", f"{BASE}{path}", json=body,
                             headers=auth_headers(), timeout=90) as r:
        t_connected = (time.perf_counter() - t0) * 1000
        print(f"  HTTP状态:        {r.status_code}")

        async for line in r.aiter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            try:
                evt = json.loads(payload)
                evt_type = evt.get("type", "content")
                events.append({
                    "type": evt_type,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                })
                if evt_type == "content" or "content" in evt:
                    if t_first_content is None:
                        t_first_content = (time.perf_counter() - t0) * 1000
                    content_parts.append(evt.get("content", ""))
            except json.JSONDecodeError:
                pass

    t_total = (time.perf_counter() - t0) * 1000
    t_first_content = t_first_content or t_total
    t_streaming = t_total - t_first_content

    print(f"  连接建立:        {fmt(t_connected)}")
    print(f"  首内容到达:      {fmt(t_first_content)}  (TTFB)")
    print(f"  流式传输:        {fmt(t_streaming)}")
    print(f"  总耗时:          {fmt(t_total)}")
    print(f"  事件数:          {len(events)}")

    # 打印事件时间线
    if events:
        print(f"\n  -- 事件时间线 --")
        for e in events:
            print(f"     {fmt(e['time_ms']):>10}  {e['type']}")

    content = "".join(content_parts)
    if content:
        print(f"\n  回复长度:        {len(content)} 字符")
        print(f"  回复预览:        {content[:100]}...")

    print()
    bar("connect", t_connected)
    bar("TTFB", t_first_content)
    bar("streaming", t_streaming)
    bar("total", t_total)

    RESULTS.append({
        "name": name, "total_ms": t_total,
        "connect_ms": t_connected, "ttfb_ms": t_first_content,
        "stream_ms": t_streaming, "status": r.status_code,
    })


async def main():
    print("\n" + "=" * 64)
    print("  Backend AI API Benchmark")
    print("  Target: " + BASE)
    print("=" * 64)

    async with httpx.AsyncClient() as client:
        # 0. 健康检查
        try:
            r = await client.get("http://localhost:8000/health", timeout=5)
            print(f"\n  健康检查: {r.status_code}")
        except Exception as e:
            print(f"\n  后端未启动: {e}")
            print("  请先运行: uvicorn app.main:app --port 8000")
            sys.exit(1)

        # 1. 登录
        header("Step 0: 登录获取Token")
        await login(client)

        # ===== /ai/* 接口 =====

        # /ai/chat - 简单对话 (非Agent, 直接LLM, Plus)
        await bench_post(client, "ai/chat", "/ai/chat", {
            "prompt": "用一句话赏析李白的静夜思",
            "temperature": 0.7,
            "max_tokens": 256,
        })

        # /ai/score - 答题评分 (Agent + Flash)
        await bench_post(client, "ai/score", "/ai/score", {
            "question": "《静夜思》的作者是谁？",
            "correct_answers": ["李白"],
            "user_answer": "李白",
        })

        # /ai/creation - 创作辅助 (Agent + Plus)
        await bench_post(client, "ai/creation", "/ai/creation", {
            "context": "秋天的月亮",
            "mode": "inspire",
        })

        # /ai/check-poem - 格律检查 (Agent + Plus)
        await bench_post(client, "ai/check-poem", "/ai/check-poem", {
            "poem_text": "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。",
        })

        # /ai/analyze-poem - 赏析 (Agent + Plus)
        await bench_post(client, "ai/analyze-poem", "/ai/analyze-poem", {
            "poem_text": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
        })

        # /ai/feihua-respond - 飞花令 (Agent + Flash)
        await bench_post(client, "ai/feihua-respond", "/ai/feihua-respond", {
            "keyword": "月",
            "used_poems": ["床前明月光"],
        })

        # /ai/poem-context - 诗词助学 (Agent + Plus, 深度赏析)
        await bench_post(client, "ai/poem-context(deep)", "/ai/poem-context", {
            "title": "静夜思", "author": "李白", "dynasty": "唐",
            "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
            "query_type": "deep_appreciation",
        })

        # /ai/poem-context - 诗人小传 (Agent + Flash)
        await bench_post(client, "ai/poem-context(bio)", "/ai/poem-context", {
            "title": "静夜思", "author": "李白", "dynasty": "唐",
            "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
            "query_type": "author_bio",
        })

        # /ai/poem-chat - 非流式对话 (Agent + Plus)
        await bench_post(client, "ai/poem-chat", "/ai/poem-chat", {
            "title": "静夜思", "author": "李白", "dynasty": "唐",
            "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
            "history": [],
            "message": "这首诗表达了什么情感？",
        })

        # /ai/poem-chat-stream - 流式对话 (Agent + Stream)
        await bench_stream(client, "ai/poem-chat-stream", "/ai/poem-chat-stream", {
            "title": "静夜思", "author": "李白", "dynasty": "唐",
            "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
            "history": [],
            "message": "帮我逐句分析这首诗",
        })

        # ===== /challenges/* 接口 =====

        # /challenges/ai-generate - AI出题 (Agent + Flash)
        await bench_post(client, "challenges/ai-generate", "/challenges/ai-generate", {
            "difficulty": "medium",
        })

        # /challenges/ai-check - AI检查题目 (Agent + Plus)
        await bench_post(client, "challenges/ai-check", "/challenges/ai-check", {
            "sentence_template": "春眠不觉__",
            "user_answer": "晓",
        })

        # ===== /graph/* 接口 =====

        # /graph/ai-relation - 诗人关系分析 (LLM + Plus)
        await bench_post(client, "graph/ai-relation", "/graph/ai-relation", {
            "poet_a": "李白",
            "poet_b": "杜甫",
        })

    # ========== 汇总 ==========
    print(f"\n\n{'='*64}")
    print("  SUMMARY")
    print(f"{'='*64}")
    print(f"  {'Endpoint':<32} {'Status':<8} {'Server':<12} {'Network':<10} {'Total':<10}")
    print(f"  {'-'*32} {'-'*8} {'-'*12} {'-'*10} {'-'*10}")
    for r in RESULTS:
        srv = fmt(r.get("server_ms", 0)) if r.get("server_ms") else "-"
        net = fmt(r.get("network_ms", 0)) if r.get("network_ms") else "-"
        ttfb = fmt(r.get("ttfb_ms", 0)) if r.get("ttfb_ms") else ""
        total = fmt(r["total_ms"])
        extra = f"  TTFB={ttfb}" if ttfb else ""
        print(f"  {r['name']:<32} {r['status']:<8} {srv:<12} {net:<10} {total:<10}{extra}")

    print(f"\n  (Server = X-Response-Time, Network = Total - Server)")
    print(f"  (TTFB = 首个内容chunk到达时间, 仅流式接口)")
    print(f"{'='*64}\n")


if __name__ == "__main__":
    asyncio.run(main())
