#!/usr/bin/env python3
"""Flag protected text changes; this is NOT an AI detector or semantic verifier."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata

NUMBER = r"[+\-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+\-]?\d+)?"
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9.])" + NUMBER)
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s<>\]，。；,;]+", re.I)
CITATION_RE = re.compile(r"[\[［]\s*\d+(?:\s*[-–,，、]\s*\d+)*\s*[\]］]")
FORMULA_RE = re.compile(r"\$\$[\s\S]*?\$\$|(?<!\\)\$[^$\n]+\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]")
UNIT_BASE = r"(?:cmol|mmol|μmol|µmol|mol|μg|µg|ng|mg|kg|g|mm|cm|km|hm|mL|μL|µL|min|ms|ha|m|L|h|s|t|℃|°C|K|%|‰)"
# Recognize complete supported expressions, including g kg⁻¹, t·ha⁻¹ and
# cmol(+) kg⁻¹. A first-token-only match would silently lose the denominator.
UNIT_ATOM = UNIT_BASE + r"(?:\([+\-]\))?(?:\^?[+\-]?\d+|[⁺⁻]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)?"
UNIT_SEPARATOR = r"(?:[^\S\r\n]*[·⋅/][^\S\r\n]*|[^\S\r\n]+)"
UNIT = UNIT_ATOM + r"(?:" + UNIT_SEPARATOR + UNIT_ATOM + r")*"
QUANTITY_RE = re.compile(r"(?<![A-Za-z0-9.])(" + NUMBER + r")\s*(" + UNIT + r")(?![A-Za-z])")
BINDING_RE = re.compile(
    r"(?<![A-Za-z])(?P<label>pH|CEC|BD|SOC|MNC|MAOC|POC|DOC|TN|TP|TK|AP|AK|RMSE|MAE|R²|R2|[Pp])"
    r"\s*(?:值|含量|浓度|比例)?\s*(?P<op>为|是|=|<|>|≤|≥|＜|＞|:|：)\s*(?P<value>" + NUMBER + r")"
)


def normalize(text):
    # Preserve superscripts, decimal precision and case. Normalize only equivalent glyphs.
    return unicodedata.normalize("NFC", text).replace("−", "-").replace("％", "%")


def compact(text):
    return re.sub(r"\s+", "", text)


def protected(text, terms=()):
    text = normalize(text)
    dois = Counter(m.group(0).rstrip(".") for m in DOI_RE.finditer(text))
    citations = Counter(compact(m.group(0)) for m in CITATION_RE.finditer(text))
    formulas = Counter(m.group(0) for m in FORMULA_RE.finditer(text))
    # Do not double-count digits inside identifiers, references or TeX.
    body = text
    for pattern in (FORMULA_RE, DOI_RE, CITATION_RE):
        body = pattern.sub(lambda m: " " * len(m.group(0)), body)
    numbers = Counter(m.group(0) for m in NUMBER_RE.finditer(body))
    quantities = Counter(m.group(1) + " " + m.group(2) for m in QUANTITY_RE.finditer(body))
    bindings = Counter()
    for match in BINDING_RE.finditer(body):
        operator = match.group("op")
        operator = {"为": "=", "是": "=", ":": "=", "：": "=", "＜": "<", "＞": ">"}.get(operator, operator)
        bindings[match.group("label") + operator + match.group("value")] += 1
    term_counts = Counter()
    for term in terms:
        term = normalize(term.strip())
        if not term:
            continue
        # Exact terms, bounded at Latin-letter edges (SOC must not match SOCx).
        pattern = (r"(?<![A-Za-z])" if term[0].isascii() and term[0].isalpha() else "")
        pattern += re.escape(term)
        pattern += r"(?![A-Za-z])" if term[-1].isascii() and term[-1].isalpha() else ""
        term_counts[term] = len(re.findall(pattern, text))
    return {"numbers": numbers, "quantities": quantities, "citations": citations,
            "dois": dois, "formulas": formulas, "simple_metric_bindings": bindings,
            "specified_terms": term_counts}


def compare(before, after, terms=()):
    left, right = protected(before, terms), protected(after, terms)
    changes = {}
    for category in left:
        removed, added = left[category] - right[category], right[category] - left[category]
        if removed or added:
            changes[category] = {"removed": dict(removed), "added": dict(added)}
    return {
        "check_state": "needs_review" if changes else "no_changes_found_in_checked_items",
        "changes": changes,
        "manual_review_required": [
            "数值与处理、时间、地点、指标的关系；尤其是分别对应的多组数值",
            "引用与论断的关系、否定、因果、统计解释和结论范围",
            "作者—年份引文及未覆盖的单位写法；脚本主要识别数字引文和常见单位表达式",
            "Word/PDF 提取时的脚注、上标、公式、表格和格式是否完整",
        ],
        "limits": "局部文本核对，不检测 AI、不验证完整语义。计数变化可能来自合法合并或重组，需逐项复核。",
    }


def read_utf8(path):
    return Path(path).read_text(encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--terms")
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        inputs = {Path(p).resolve() for p in (args.before, args.after, args.terms) if p}
        if args.out and Path(args.out).resolve() in inputs:
            raise ValueError("输出路径不能覆盖输入文件")
        terms = read_utf8(args.terms).splitlines() if args.terms else []
        result = compare(read_utf8(args.before), read_utf8(args.after), terms)
        output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 1 if result["changes"] else 0
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
