#!/usr/bin/env python3
"""Offline editorial hints. No AI score, automatic rewriting, or network calls.

Adapted from aigc-reduce/scripts/aigc_scan.py; see
third_party/aigc-reduce/LICENSE and third_party/manifest.json.
"""
import argparse
import json
from pathlib import Path
import re
import sys

RULES_PATH = Path(__file__).resolve().parents[1] / "assets" / "style-patterns.json"
# Protect complete quotations, code spans and common TeX notation. This is not a
# full document parser: extract body paragraphs and identify other protected
# objects before scanning. Offsets refer to the exact returned paragraph text.
PROTECTED_RE = re.compile(
    r"```[\s\S]*?```|`[^`\n]+`|“[^”]*”|‘[^’]*’|「[^」]*」|『[^』]*』|"
    r'"[^"\n]*"|\$\$[\s\S]*?\$\$|(?<!\\)\$[^$\n]+\$|'
    r"\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]"
)


def load_rules():
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("rules"), list):
        raise ValueError("本地规则库结构无效")
    seen = set()
    rules = []
    for entry in data["rules"]:
        if not all(isinstance(entry.get(k), str) and entry[k] for k in
                   ("id", "pattern", "category", "advice")):
            raise ValueError("规则缺少必要文本字段")
        if entry["id"] in seen:
            raise ValueError("规则 ID 重复")
        seen.add(entry["id"])
        rules.append((entry, re.compile(entry["pattern"])))
    return rules


def scan(text):
    if not text.strip():
        raise ValueError("正文为空，请提供已提取的 UTF-8 正文")
    rules = load_rules()
    # Mask before splitting so a multi-paragraph quotation remains protected.
    protected = [(m.start(), m.end()) for m in PROTECTED_RE.finditer(text)]
    parts = list(re.finditer(r"\S[\s\S]*?(?=\n[ \t]*\n|\Z)", text))
    paragraphs = []
    total = 0
    for number, part in enumerate(parts, 1):
        original = part.group().rstrip()
        offset = part.start()
        spans = [(max(0, a - offset), min(len(original), b - offset))
                 for a, b in protected if a < offset + len(original) and b > offset]
        masked = list(original)
        for a, b in spans:
            masked[a:b] = " " * (b - a)
        body = "".join(masked)
        hints = []
        for entry, pattern in rules:
            for match in pattern.finditer(body):
                hints.append({
                    "rule_id": entry["id"], "category": entry["category"],
                    "start": match.start(), "end": match.end(),
                    "text": original[match.start():match.end()],
                    "context": original[max(0, match.start()-25):match.end()+40],
                    "advice": entry["advice"], "manual_review_required": True,
                })
        hints.sort(key=lambda h: (h["start"], h["end"], h["rule_id"]))
        total += len(hints)
        paragraphs.append({
            "id": f"P{number:03d}", "text": original,
            "non_whitespace_chars": sum(not c.isspace() for c in original),
            "protected_spans": [{"start": a, "end": b} for a, b in spans],
            "hints": hints,
        })
    return {
        "schema_version": 1, "check_type": "editorial_hints_only",
        "summary": {"paragraphs": len(paragraphs), "hint_count": total,
                    "non_whitespace_chars": sum(p["non_whitespace_chars"] for p in paragraphs)},
        "paragraphs": paragraphs,
        "limits": "仅定位需要阅读的表达；不判断 AI 来源、不估计 AIGC 率，不自动改写。引文、格式和完整语义仍需人工核对。",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="已提取正文的 UTF-8 文本；空行分段")
    parser.add_argument("--out", help="独立 JSON 输出路径，省略时输出至终端")
    args = parser.parse_args()
    try:
        source = Path(args.input).resolve()
        target = Path(args.out).resolve() if args.out else None
        if target and (target == source or (target.exists() and target.samefile(source))):
            raise ValueError("输出路径不能覆盖原文")
        # The asset is local and deliberately not downloaded at runtime.
        if target and (target == RULES_PATH or (target.exists() and target.samefile(RULES_PATH))):
            raise ValueError("输出路径不能覆盖技能规则库")
        result = scan(source.read_text(encoding="utf-8-sig"))
        output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if target:
            target.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        # Hints are not failures or a grade. Only invalid input returns 2.
        return 0
    except (OSError, UnicodeError, ValueError, re.error) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
