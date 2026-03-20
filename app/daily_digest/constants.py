from __future__ import annotations

from datetime import date, datetime, timedelta

KEYWORDS: list[str] = [
    "llm",
    "large language model",
    "language model",
    "foundation model",
    "rag",
    "retrieval-augmented",
    "retrieval augmented",
    "vector database",
    "embedding",
    "agent",
    "multi-agent",
    "tool calling",
    "function calling",
    "mcp",
    "workflow",
    "orchestration",
    "inference",
    "serving",
    "latency",
    "throughput",
    "kv cache",
    "kv caching",
    "speculative decoding",
    "quantization",
    "distillation",
    "lora",
    "qlora",
    "fine-tuning",
    "finetuning",
    "alignment",
    "rlhf",
    "dpo",
    "sft",
    "evaluation",
    "benchmark",
    "hallucination",
    "safety",
    "guardrail",
    "multimodal",
    "vision-language",
    "vlm",
    "transformer",
    "attention",
    "moe",
    "mixture of experts",
    "prompting",
    "prompt",
    "context window",
    "context length",
    "大模型",
    "语言模型",
    "基座模型",
    "多模态",
    "视觉语言",
    "智能体",
    "多智能体",
    "工具调用",
    "函数调用",
    "检索增强",
    "向量数据库",
    "向量检索",
    "嵌入",
    "推理",
    "推理加速",
    "部署",
    "服务",
    "吞吐",
    "延迟",
    "量化",
    "蒸馏",
    "微调",
    "对齐",
    "安全",
    "评测",
    "基准",
    "幻觉",
    "提示词",
    "上下文窗口",
    "上下文长度",
    "Transformer",
    "MoE",
    "RAG",
    "LLM",
]

ARXIV_RSS_SOURCES: list[tuple[str, str]] = [
    ("cs.AI", "https://export.arxiv.org/rss/cs.AI"),
    ("cs.CL", "https://export.arxiv.org/rss/cs.CL"),
    ("cs.LG", "https://export.arxiv.org/rss/cs.LG"),
]

HF_PAPERS_URLS: list[str] = [
    "https://huggingface.co/papers",
    "https://huggingface.co/papers/trending",
]

HF_PAPERS_DATE_URL_TEMPLATE = "https://huggingface.co/papers/date/{date_str}"

DEFAULT_REPO_WATCHLIST: list[str] = [
    "langchain-ai/langgraph",
    "qdrant/qdrant",
    "vllm-project/vllm",
    "ollama/ollama",
    "run-llama/llama_index",
    "open-webui/open-webui",
]

INFO_RSS_SOURCES: list[tuple[str, str]] = [
    ("hacker_news", "https://news.ycombinator.com/rss"),
    ("google_ai_blog", "https://ai.googleblog.com/feeds/posts/default?alt=rss"),
    ("reddit_machinelearning", "https://www.reddit.com/r/MachineLearning/.rss"),
    ("reddit_localllama", "https://www.reddit.com/r/LocalLLaMA/.rss"),
    ("lobsters", "https://lobste.rs/rss"),
]

DEFAULT_SUMMARY_LIMIT = 200


def get_default_digest_date() -> date:
    return (datetime.now().date() - timedelta(days=1))
