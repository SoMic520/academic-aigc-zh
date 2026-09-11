#!/usr/bin/env python3
"""Compare verified report values. No detector calls, estimates or network use."""
import argparse
import json
import math
from pathlib import Path
import sys


def score(value, label):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(label + " 必须为数值或 null；区间和风险标签不能当作精确比例")
    if not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError(label + " 必须是0至100之间的有限数值")
    return value


def nonempty(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip() != "未识别"


def compare(data):
    if not isinstance(data, dict) or not isinstance(data.get("pairs"), list) or not data["pairs"]:
        raise ValueError("输入需要非空 pairs 数组")
    rows, platforms, before_versions, after_versions = [], set(), set(), set()
    versions_complete = True
    for pair in data["pairs"]:
        if not isinstance(pair, dict) or not nonempty(pair.get("platform")):
            raise ValueError("每项需要实际 platform")
        platform = pair["platform"].strip()
        if platform in platforms:
            raise ValueError("重复平台：" + platform + "；不同产品或配置应在平台标识中区分")
        platforms.add(platform)
        before, after = score(pair.get("before_pct"), platform + " before_pct"), score(pair.get("after_pct"), platform + " after_pct")
        before_version, after_version = pair.get("before_version"), pair.get("after_version")
        has_versions = nonempty(before_version) and nonempty(after_version)
        versions_complete = versions_complete and has_versions
        if has_versions:
            before_versions.add(before_version)
            after_versions.add(after_version)
        has_reports = nonempty(pair.get("before_report")) and nonempty(pair.get("after_report"))
        if before is None or after is None:
            state = "missing_exact_result"
        elif not has_versions or not has_reports:
            state = "missing_provenance"
        elif pair.get("comparable") is not True:
            state = "not_comparable"
        elif after > before:
            state = "increased"
        elif before == 0:
            state = "already_zero"
        elif after == before:
            state = "unchanged"
        else:
            state = "decreased"
        comparable_states = {"increased", "already_zero", "unchanged", "decreased"}
        delta = round(after - before, 8) if state in comparable_states else None
        rows.append({"platform": platform, "before_version": before_version, "after_version": after_version,
                     "before_pct": before, "after_pct": after, "change_percentage_points": delta,
                     "state": state, "before_report": pair.get("before_report"),
                     "after_report": pair.get("after_report"), "note": pair.get("note", "")})
    same_documents = versions_complete and len(before_versions) == 1 and len(after_versions) == 1
    all_decreased = same_documents and all(row["state"] == "decreased" for row in rows)
    if all_decreased:
        state, description = "all_tested_platforms_decreased", "本次已测试平台均下降"
    elif not same_documents:
        state, description = "mixed_or_missing_document_versions", "稿件版本混用或缺失，不能汇总为全部下降"
    elif any(row["state"] in {"missing_exact_result", "missing_provenance", "not_comparable"} for row in rows):
        state, description = "incomplete_comparison", "存在结果缺失或不可比项目，不能确认全部下降"
    else:
        state, description = "not_all_decreased", "本次已测试平台未全部严格下降"
    return {"state": state, "description": description, "all_tested_platforms_decreased": all_decreased,
            "same_document_versions": same_documents, "rows": rows,
            "limits": "结论仅基于用户核实的输入；脚本不验证报告真伪，也不代表未测试平台的效果。"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        if args.out and Path(args.input).resolve() == Path(args.out).resolve():
            raise ValueError("输出路径不能覆盖输入报告数据")
        result = compare(json.loads(Path(args.input).read_text(encoding="utf-8-sig")))
        output = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
