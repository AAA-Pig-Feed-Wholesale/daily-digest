# 前沿日报（Daily Digest）

**前沿日报**是一个独立运行的每日简报系统，聚焦**大模型应用开发**与**大模型算法**，自动聚合信息源、评分排序并生成可读的日报页面（含原文链接）。

## 功能特性
- 单页面 Dashboard：生成日报 + 浏览历史
- RSS 优先抓取，**列表页 fallback**（无 RSS 时兜底）
- LLM 相关性评分（可选）+ 关键词兜底
- 可配置**相关性最低阈值**（MIN_RELEVANCE_SCORE）
- 本地 SQLite 存储

## 本地拉取后需要自行配置的内容
拉取代码后，你需要按实际情况补全以下配置：
1. `.env`（从 `.env.example.safe` 复制并填写）
   - `GITHUB_TOKEN`：避免 GitHub API 限流
   - `HF_TOKEN`：访问 Hugging Face（如网络可达）
   - `MIN_RELEVANCE_SCORE`：低于该分数不展示
2. `configs/providers.yaml`
   - 从 `configs/providers.example.yaml` 复制并填写真实 API Key/模型信息
3. `configs/sources.yaml`
   - 根据需求启用/禁用数据源或调整 RSS/列表页链接



## 系统功能概览
1. 多源抓取：支持 RSS 与列表页两种方式，RSS 优先，列表页兜底
2. 正文补全：对候选条目抓取正文，提升摘要与评分质量
3. 相关性评分：优先使用 LLM 评分，失败时回退到关键词策略
4. 排序与过滤：按相关性降序，并应用最低阈值过滤
5. 日报展示：单页面查看、切换日期、手动触发生成

## 目录结构
`
app/                      FastAPI 应用入口
app/daily_digest/         日报核心逻辑（抓取 / 评分 / 存储 / UI）
app/static/               前端资源
configs/                  数据源与 provider 配置
data/                     本地数据库
`

## 快速开始

### 1）安装依赖
```bash
pip install -r requirements.txt
```

### 2）配置环境变量
复制 .env.example.safe 为 .env，并填写必要配置：
```bash
copy .env.example.safe .env
```

关键字段说明：
- OPENAI_API_KEY / OPENAI_BASE_URL：用于相关性评分（可选）
- GITHUB_TOKEN：避免 GitHub API 限流
- HF_TOKEN：访问 Hugging Face（如网络可达）
- MIN_RELEVANCE_SCORE：低于该分数不展示（默认 15）

Provider 示例：
- configs/providers.example.yaml

### 3）启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

访问页面：
- http://localhost:8001/daily-digest

## 使用方式
- 点击 **生成日报** 可按当前日期生成
- 默认生成“前一天”的日报

### API 接口
- GET /api/daily-digest?date=YYYY-MM-DD
- POST /api/daily-digest/run（JSON：{ "date": "YYYY-MM-DD", "force": true }）
- GET /api/daily-digest/status?date=YYYY-MM-DD

## 数据源配置
编辑 configs/sources.yaml：
- rss_url：RSS 地址（优先使用）
- list_url：列表页地址（无 RSS 或 RSS 为空时使用）

行为规则：
- 有 rss_url：先用 RSS 拉候选，再用文章页补正文
- 无 rss_url：直接使用 list_url 做列表解析

## 数据源可用性测试脚本
运行脚本检查各数据源是否可访问：
```bash
python scripts/check_sources.py
```
输出会分别标注 RSS/列表页/结构化页面的可用性状态。

## 当前支持的数据源（以 configs/sources.yaml 为准）
说明：可用性受网络环境、反爬策略、地区限制影响，建议以本地验证脚本结果为准。

| 数据源 | 获取方式 | 可用性标注 |
| --- | --- | --- |
| arXiv（cs.AI / cs.CL / cs.LG） | RSS | 一般可用 |
| GitHub Watchlist（Releases） | API | 需 Token，易限流 |
| Hugging Face Papers / Trending / Blog | 结构化页面 | 可能受限，易限流 |
| Hacker News | RSS | 一般可用 |
| Google Blog（Innovation & AI） | RSS / 列表页 | 可能变更 |
| Reddit r/MachineLearning | RSS | 可能受限 |
| Reddit r/LocalLLaMA | RSS | 可能受限 |
| Lobsters | RSS | 一般可用 |
| 机器之心 | RSS / 列表页 | 可能受限 |
| 量子位 | RSS / 列表页 | 可能受限 |
| 36 氪 AI 专栏 | 列表页 | 可能受限 |
| InfoQ AI | RSS / 列表页 | 一般可用 |
| 雷峰网 AI | RSS / 列表页 | 可能受限 |
| 极客公园 AI | 列表页 | 可能受限 |
| 爱范儿 AI | RSS / 列表页 | 一般可用 |
| AIGC 开放社区 | 列表页 | 可能受限 |
| 大模型之家 | 列表页 | 可能受限 |
| AI 前线 | 列表页 | 可能受限 |
| 智源社区 | 列表页 | 一般可用 |
| 掘金 AI | 列表页 | 一般可用 |
| CSDN AI | 列表页 | 一般可用 |
| PaperWeekly | 列表页 | 可能受限 |
| 集智俱乐部 | 列表页 | 一般可用 |

## 常见问题
- 某些站点 404/403：建议禁用或换列表页
- HF 无法访问：可能需要 Token 或代理
- 状态接口日志刷屏：前端轮询正常现象

## 更新日志
### 2026-03-20
- 拆分为独立项目，保留单页面日报流程
- 新增 RSS 优先 + 列表页兜底抓取策略
- 新增相关性最低阈值 `MIN_RELEVANCE_SCORE`
- 完成前端样式与交互优化
