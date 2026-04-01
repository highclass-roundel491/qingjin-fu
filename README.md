# 青衿赋

《青衿赋》是一个面向中国大学生计算机设计大赛的软件开发类 Web 项目，定位为沉浸式传统诗词学习与创作平台。项目围绕传统文化数字化表达与 AI 赋能诗词教育创新展开设计，融合诗词检索、智能助学、创作辅助、互动竞技、成长激励与可视化探索，希望让古典诗词以更生动、更具陪伴感和参与感的方式进入当代年轻用户的学习场景。

## 项目信息

- 项目名称：《青衿赋》
- 项目类型：中国大学生计算机设计大赛 Web 项目
- 项目定位：沉浸式传统诗词学习与创作平台
- 核心目标：在比赛中获奖

## 项目亮点

- 沉浸式学习闭环：从诗词浏览、注释翻译、深度赏析到学习记录、成长反馈，形成完整体验链路
- AI 深度嵌入：AI 不只是问答入口，而是贯穿助学、创作、评分、互动和多轮对话全流程
- 游戏化设计：填词挑战、飞花令、诗词接龙、限时挑战将传统诗词学习转化为可参与、可竞技、可复盘的玩法
- 成长激励体系：8 级科举式等级体系、41 个成就、卷宗导览与排行榜强化持续使用动力
- 文脉可视化表达：文脉星图以力导向图方式展示朝代、诗人、题材之间的关联，增强知识探索感

## AI 设计特色

### 多层 AI 能力编排

项目采用 DashScope / Qwen 模型体系，并通过 OpenAI 兼容接口统一接入。系统按照任务复杂度区分轻量问答、复杂赏析、创作建议与综合评分等场景，在生成质量、响应速度与调用成本之间做平衡。

### Agent 化诗词问答

后端内置诗词 Agent 引擎，支持 ReAct 推理、工具路由、结果压缩和多轮调用控制。问答过程中可以结合诗词检索、作者信息、统计信息与上下文信息完成更可靠的回答，避免单纯依赖模型裸生成。

### 记忆驱动的个性化陪伴

系统实现了用户偏好、学习目标、交互风格、上下文主题等多类记忆抽取机制。AI 可以根据用户近期问题、偏爱诗人题材和学习状态调整回答内容，增强连续对话中的陪伴感与个性化。

### 助学与创作双引擎

- AI 助学：诗人小传、深度赏析、典故意象、逐句精析、格律标注、自由问答、多轮诗词对话
- AI 创作：灵感生成、续写、主题创作、格律检查、综合评分、修改建议
- AI 竞技：填词挑战评分、飞花令应答、创作结果分析、排行榜反馈

### 可落地的工程实现

项目当前已实现 12 个 Agent 工具、7 个诗词 AI 能力点、5 个创作 AI 能力点，并与学习、创作、竞技、社交模块联动，体现的是一套可运行、可演示、可扩展的完整比赛作品，而不是静态概念原型。

## 功能概览

- 诗词学习：157876 首诗词库、分类检索、诗词详情、注释翻译赏析、收藏与学习记录
- 互动竞技：填词挑战、飞花令、诗词接龙、限时挑战、排行榜、连续奖励
- 创作中心：自由创作、AI 灵感、AI 续写、格律检查、作品发布、创作者排行
- 社区成长：作品展示墙、评论点赞、等级体系、成就殿堂、卷宗导览
- 数据可视化：学习趋势、热力图、成长曲线、挑战雷达图、文脉星图

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus、ECharts、PixiJS
- 后端：FastAPI、SQLAlchemy、Pydantic、Uvicorn、Redis
- 数据库：PostgreSQL 15
- AI：DashScope / Qwen，OpenAI 兼容接口
- 部署：Docker、Docker Compose、Nginx

## 项目结构

```text
backend/    FastAPI 服务、业务接口、Agent 引擎、AI 服务与数据模型
frontend/   Vue 3 前端应用、互动页面、可视化与创作体验
docs/       PRD、技术设计、接口文档、前端规范与比赛材料
data/       初始化和业务数据
```

## 本地开发

### 1. 启动基础服务

```bash
docker compose up -d postgres redis
```

### 2. 配置后端环境变量

```bash
copy backend\\.env.example backend\\.env
```

请在 `backend/.env` 中补充 `DASHSCOPE_API_KEY`、`SECRET_KEY` 等配置。

### 3. 启动后端

```bash
cd backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认开发地址：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- 接口文档：`http://localhost:8000/docs`

## Docker 部署

```bash
docker compose -f docker-compose.deploy.yml build backend
docker compose -f docker-compose.deploy.yml build frontend
docker compose -f docker-compose.deploy.yml up -d
docker compose -f docker-compose.deploy.yml ps
```

## 相关文档

- `docs/PRD.md`
- `docs/技术设计文档.md`
- `docs/API接口文档.md`
- `docs/前端设计规范.md`

## 当前进度

核心学习、创作、挑战、社交、成就与可视化模块已经完成，项目已具备完整演示能力，适合作为比赛展示版本继续打磨细节、优化表现和完善答辩材料。
