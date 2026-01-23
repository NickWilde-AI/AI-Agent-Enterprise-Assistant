from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

import docx2txt
import zipfile
from docx import Document

ROOT = Path(__file__).resolve().parents[2]
# 自动读取 .env，避免每次手动设置环境变量。
load_dotenv(ROOT / ".env")
PRICING_DOC = "XX智能基于大模型应用开发需求分析和报价方案6-8.docx"
PRICING_KEYWORDS = ("报价", "价格", "单价", "人天", "成本", "预算", "金额")
DATA_DIR = ROOT / "data"


def _clean_snippet(text: str, limit: int = 200) -> str:
    """清理并截断文本片段，便于展示。"""
    cleaned = " ".join(text.strip().replace("\n", " ").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "..."


def format_sources(source_nodes) -> str:
    """格式化来源引用，仅列出文件名。"""
    lines = []
    for idx, node in enumerate(source_nodes, start=1):
        file_name = node.node.metadata.get("file_name", "unknown")
        lines.append(f"[{idx}] {file_name}")
    return "\n".join(lines)


def _get_env(name: str, default: str | None = None) -> str | None:
    """读取环境变量，若未设置则返回默认值。"""
    value = os.getenv(name)
    return value if value else default


def _extract_rag_pricing_from_table() -> tuple[str | None, str | None]:
    """从报价文档表格中提取 RAG 引擎开发的人天与单价。"""
    doc_path = DATA_DIR / PRICING_DOC
    if not doc_path.exists():
        return None, None

    doc = Document(str(doc_path))
    for table in doc.tables:
        if not table.rows:
            continue
        headers = [cell.text.strip() for cell in table.rows[0].cells]
        day_idx = None
        price_idx = None
        for idx, header in enumerate(headers):
            if "人天" in header:
                day_idx = idx
            if "单价" in header:
                price_idx = idx
        if day_idx is None and price_idx is None:
            continue

        for row in table.rows[1:]:
            cells = [cell.text.strip() for cell in row.cells]
            row_text = " ".join(cells)
            if "RAG" in row_text and ("引擎" in row_text or "开发" in row_text):
                person_days = None
                unit_price = None
                if day_idx is not None and day_idx < len(cells):
                    person_days = re.sub(r"[^0-9]", "", cells[day_idx]) or None
                if price_idx is not None and price_idx < len(cells):
                    unit_price = re.sub(r"[^0-9]", "", cells[price_idx]) or None
                return person_days, unit_price

    return None, None


def _sentences_from_text(text: str) -> list[str]:
    """将文本切分为句子，便于做精准匹配。"""
    normalized = " ".join(text.replace("\n", " ").split())
    if not normalized:
        return []
    parts = re.split(r"[。！？!?.；;]", normalized)
    return [part.strip() for part in parts if part.strip()]


def _load_doc_sentences() -> list[dict[str, list[str]]]:
    """读取 data/ 下的文档，返回 [{name, sentences}]。"""
    docs = []
    for path in DATA_DIR.rglob("*"):
        if path.suffix.lower() not in {".md", ".txt", ".docx"}:
            continue
        if path.name.startswith("~$"):
            continue
        if path.suffix.lower() == ".docx":
            try:
                text = docx2txt.process(str(path))
            except zipfile.BadZipFile:
                # 跳过损坏或伪装成 docx 的文件，避免中断检索流程。
                continue
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
        sentences = _sentences_from_text(text)
        if sentences:
            docs.append({"name": path.name, "sentences": sentences})
    return docs


def _best_match_sentences(
    question: str, docs: list[dict[str, list[str]]]
) -> tuple[str | None, list[str]]:
    """根据关键词匹配选择最相关的句子列表。"""
    raw_tokens = re.findall(r"[\u4e00-\u9fff]+|[A-Za-z0-9_]+", question)
    tokens: list[str] = []
    for token in raw_tokens:
        if len(token) <= 2:
            tokens.append(token)
            continue
        tokens.extend(token[i : i + 2] for i in range(len(token) - 1))

    def score(text: str) -> int:
        return sum(text.count(token) for token in tokens)

    best_name = None
    best_sentences: list[str] = []
    best_score = 0
    for doc in docs:
        ranked = sorted(
            doc["sentences"],
            key=score,
            reverse=True,
        )
        if not ranked:
            continue
        top_score = score(ranked[0])
        if top_score > best_score:
            best_score = top_score
            best_name = doc["name"]
            best_sentences = ranked[:2]

    if best_score < 2:
        return None, []
    return best_name, best_sentences


def query(question: str) -> None:
    """执行检索问答：优先结构化提取，其次走句子级关键词匹配。"""
    # 报价类问题优先从报价文档表格中提取结构化答案。
    if any(keyword in question for keyword in PRICING_KEYWORDS):
        if "RAG" in question:
            person_days, unit_price = _extract_rag_pricing_from_table()
            if person_days or unit_price:
                answer_parts = []
                if person_days:
                    answer_parts.append(f"人天：{person_days}")
                if unit_price:
                    answer_parts.append(f"单价：{unit_price}")
                print("Answer:\n", "，".join(answer_parts))
                print("\nSource:\n", PRICING_DOC)
                return
            print("Answer:\n", "不好意思，报价文档中未找到明确的 RAG 引擎开发单价/人天字段")
            print("\nSource:\n", PRICING_DOC)
            return

    docs = _load_doc_sentences()
    name, sentences = _best_match_sentences(question, docs)
    if not name or not sentences:
        print("Answer:\n", "不好意思，知识库里检索不到")
        return

    answer = "；".join(_clean_snippet(sentence, limit=120) for sentence in sentences)
    print("Answer:\n", answer)
    print("\nSource:\n", name)


if __name__ == "__main__":
    import sys

    # 支持命令行参数自定义查询问题。
    question = "差旅报销的住宿标准是多少？"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    query(question)
