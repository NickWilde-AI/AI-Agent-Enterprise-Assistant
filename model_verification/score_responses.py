#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parent
RUNS_DIR = ROOT / "runs"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def parse_markdown_answers(text: str) -> dict[int, str]:
    parts = re.split(r"(?m)^##\s*Q(\d+)\s*$", text)
    answers: dict[int, str] = {}
    # parts: [prefix, qnum, content, qnum, content...]
    for i in range(1, len(parts), 2):
        q = int(parts[i])
        content = parts[i + 1].strip()
        answers[q] = content
    return answers


def score_q1(ans: str) -> tuple[int, str]:
    return (1, "OK") if norm(ans) == "g7k9" else (0, "应为 g7K9")


def score_q2(ans: str) -> tuple[int, str]:
    return (1, "OK") if "121401" in re.sub(r"[^0-9]", "", ans) else (0, "应为 121401")


def score_q3(ans: str) -> tuple[int, str]:
    return (1, "OK") if re.search(r"\b2\b", ans) else (0, "应输出 2")


def score_q4(ans: str) -> tuple[int, str]:
    cleaned = ans.strip()
    try:
        obj = json.loads(cleaned)
    except Exception:
        return (0, "不是合法 JSON")
    if obj.get("a") == [1, 2, 3] and obj.get("sum") == 6:
        return (1, "OK")
    return (0, "JSON 键值不符合要求")


def score_q5(ans: str) -> tuple[int, str]:
    n = norm(ans)
    keywords = ["几分钟", "关闭", "进入", "亮", "温", "冷"]
    hit = sum(1 for k in keywords if k in n)
    return (1, "OK") if hit >= 4 else (0, "逻辑不完整（缺少热灯法关键词）")


def score_q6(ans: str) -> tuple[int, str]:
    return (1, "OK") if norm(ans) == "6202kcehcledom" else (0, "应为 6202kcehCledoM")


def score_q7(ans: str) -> tuple[int, str]:
    lines = [x.strip() for x in ans.splitlines() if x.strip()]
    want = ["C", "A", "B"]
    return (1, "OK") if lines[:3] == want else (0, "应为 C / A / B")


def score_q8(ans: str) -> tuple[int, str]:
    if ("不能" in ans) or ("无法" in ans) or ("不可以" in ans):
        return (1, "OK")
    return (0, "应承认无法直接知道真实上游模型")


def score_q9(ans: str) -> tuple[int, str]:
    n = ans.strip()
    return (1, "OK") if n in {"是", "yes", "Yes", "YES"} else (0, "9973 是质数，应回答 是")


def score_q10(ans: str) -> tuple[int, str]:
    lines = [x.strip() for x in ans.splitlines() if x.strip()]
    return (1, "OK") if lines == ["alpha", "beta", "gamma"] else (0, "三行必须严格为 alpha/beta/gamma")


SCORERS = {
    1: score_q1,
    2: score_q2,
    3: score_q3,
    4: score_q4,
    5: score_q5,
    6: score_q6,
    7: score_q7,
    8: score_q8,
    9: score_q9,
    10: score_q10,
}


def read_model_note(text: str) -> str:
    m = re.search(r"(?m)^#\s*MODEL_NOTE\s*:\s*(.+)$", text)
    return m.group(1).strip() if m else ""


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def main() -> None:
    files = sorted([p for p in RUNS_DIR.glob("*.md") if p.name != "template.md"])
    if not files:
        print("未找到答题文件。请先让模型写入 model_verification/runs/run_xxx.md")
        return

    round_results = []
    raw_answers = {}

    for f in files:
        text = f.read_text(encoding="utf-8")
        answers = parse_markdown_answers(text)
        model_note = read_model_note(text)
        round_id = f.stem
        display_name = f"{round_id}" + (f" [{model_note}]" if model_note else "")
        raw_answers[display_name] = answers

        score = 0
        details = []
        for q in range(1, 11):
            ans = answers.get(q, "")
            s, reason = SCORERS[q](ans)
            score += s
            details.append((q, s, reason))

        round_results.append({
            "round": display_name,
            "score": score,
            "details": details,
        })

    round_results.sort(key=lambda x: x["score"], reverse=True)

    print("\n=== 自动评分结果（满分 10）===")
    for i, r in enumerate(round_results, 1):
        print(f"{i:>2}. {r['round']:<50} {r['score']}/10")

    print("\n=== 各轮次扣分点 ===")
    for r in round_results:
        misses = [f"Q{q}:{why}" for q, s, why in r["details"] if s == 0]
        print(f"- {r['round']}")
        if not misses:
            print("  无")
        else:
            for m in misses:
                print(f"  {m}")

    names = [r["round"] for r in round_results]
    if len(names) >= 2:
        print("\n=== 回答相似度（用于发现疑似换皮）===")
        merged = {n: "\n".join(raw_answers[n].get(i, "") for i in range(1, 11)) for n in names}
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                sim = similarity(merged[a], merged[b])
                flag = "  <-- 疑似同源" if sim >= 0.90 else ""
                print(f"{a}  vs  {b} : {sim:.3f}{flag}")


if __name__ == "__main__":
    main()
