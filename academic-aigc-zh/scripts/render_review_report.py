#!/usr/bin/env python3
"""Build an offline Chinese paragraph review report; no AI score prediction."""
import argparse
import difflib
import html
import json
import math
from pathlib import Path
import re


def count(text):
    return len(re.sub(r"\s", "", text))


def escape(value):
    return html.escape(str(value), quote=True)


def diff_parts(before, after):
    """Sentence/phrase granularity keeps Chinese revision spans readable."""
    def tokens(text):
        return re.findall(r"[^。！？；\n]+[。！？；\n]?|[。！？；\n]", text)
    left, right = tokens(before), tokens(after)
    parts = []
    for tag, a, b, c, d in difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        if tag == "equal":
            parts.append(("equal", "".join(left[a:b])))
        else:
            if a != b:
                parts.append(("del", "".join(left[a:b])))
            if c != d:
                parts.append(("ins", "".join(right[c:d])))
    return parts


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get("paragraphs"), list) or not data["paragraphs"]:
        raise ValueError("需要非空 paragraphs 数组")
    cap = data.get("max_reduction_pct", 3)
    if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not math.isfinite(cap) or not 0 <= cap <= 100:
        raise ValueError("max_reduction_pct 应为 0 至 100 的有限数值")
    seen, failed = set(), []
    for p in data["paragraphs"]:
        if not isinstance(p, dict):
            raise ValueError("段落必须为对象")
        for key in ("id", "sample", "section", "before", "after", "comment"):
            if not isinstance(p.get(key), str) or not p[key].strip():
                raise ValueError("段落需要非空字符串字段 " + key)
        if p["id"] in seen:
            raise ValueError("段落编号重复：" + p["id"])
        seen.add(p["id"])
        if not isinstance(p.get("checks", []), list) or not all(isinstance(t, str) for t in p.get("checks", [])):
            raise ValueError("checks 应为字符串数组")
        if not isinstance(p.get("needs_review", False), bool) or not isinstance(p.get("review_note", ""), str):
            raise ValueError("批注标记或内容类型不正确")
        a, b = count(p["before"]), count(p["after"])
        if a == 0 or b * 100 + 1e-9 < a * (100 - cap):
            failed.append(p["id"])
    if failed:
        raise ValueError("以下段落超过减字上限，须先调整正文：" + "、".join(failed))
    for key in ("test_summary", "test_rows"):
        if key in data and (not isinstance(data[key], list) or not all(isinstance(v, dict) for v in data[key])):
            raise ValueError(key + " 应为对象数组")
    return cap


CSS = r'''
:root{--ink:#202b33;--muted:#596973;--green:#126653;--paper:#fff;--line:#dce3e7;--bg:#f3f5f6;--red:#a22e3a;--amber:#865618}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--bg);font:16px/1.75 system-ui,-apple-system,"Microsoft YaHei","Noto Sans CJK SC",sans-serif}button,input,select{font:inherit}button,a,summary{touch-action:manipulation}button{cursor:pointer}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #387bba;outline-offset:3px}a{color:var(--green)}.wrap{max-width:1260px;margin:auto;padding:32px 28px 60px}.eyebrow{font-size:13px;color:var(--green);font-weight:700;letter-spacing:.07em}h1{font-size:32px;line-height:1.3;margin:10px 0 12px;color:#111}h2{font-size:23px;line-height:1.4;margin:0 0 18px;color:#111}h3{font-size:18px;margin:0;color:#111}p{margin:0 0 12px}.lead{font-size:18px;max-width:940px}.meta,.small{font-size:13px;color:var(--muted)}.scope{color:var(--muted);max-width:1040px}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0}.metric{background:var(--paper);border:1px solid var(--line);padding:16px 20px;border-radius:8px}.metric strong{display:block;font-size:24px;line-height:1.4;color:var(--ink)}.metric span{font-size:13px;color:var(--muted)}.tabs{display:flex;gap:8px;margin:26px 0 18px;flex-wrap:wrap}.tabs button,.modes button,.plain{border:1px solid var(--line);border-radius:6px;background:white;padding:8px 14px;color:var(--ink)}button[aria-pressed=true],.tabs button[aria-selected=true]{color:white;background:var(--green);border-color:var(--green)}.toolbar{background:rgba(243,245,246,.98);border-bottom:1px solid var(--line);padding:12px 0;position:sticky;top:0;z-index:10;display:flex;gap:12px;align-items:center;flex-wrap:wrap}.modes{display:flex;gap:5px;flex-wrap:wrap}.filters{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.filters input[type=search]{min-width:160px;width:210px}.filters input[type=search],select{border:1px solid #bcc9cf;border-radius:5px;background:#fff;padding:7px 10px;max-width:100%}.checkbox{font-size:14px;display:flex;gap:5px;align-items:center}.status{font-size:13px;color:var(--muted);padding:14px 0 4px}.toc{display:flex;gap:8px;flex-wrap:wrap;padding:8px 0 16px}.toc a{font-size:13px;text-decoration:none;background:white;border:1px solid var(--line);border-radius:4px;padding:3px 10px}.review-block{background:white;border:1px solid var(--line);border-radius:9px;margin:0 0 20px;scroll-margin-top:160px;overflow:hidden}.block-top{padding:18px 22px;display:flex;gap:14px;justify-content:space-between;border-bottom:1px solid var(--line);align-items:flex-start;flex-wrap:wrap}.block-id{font-size:13px;color:var(--green);font-weight:700;margin-bottom:3px}.badge{font-size:12px;white-space:nowrap;border:1px solid #d8c2a4;border-radius:4px;padding:2px 8px;background:#fff7e9;color:var(--amber)}.word-count{font-size:13px;color:var(--muted);margin-top:5px}.word-count strong{color:var(--green)}.comparison{display:grid;grid-template-columns:1fr 1fr}.text-pane{padding:20px 22px;min-width:0}.text-pane+.text-pane{border-left:1px solid var(--line);background:#fcfdfc}.pane-label{font-size:12px;font-weight:700;letter-spacing:.06em;color:var(--muted);margin-bottom:10px}.prose{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.95;text-align:justify;margin:0}.revision,.clean{padding:20px 22px;display:none}.revision del{background:#fff0f1;color:var(--red);text-decoration:line-through;text-decoration-thickness:1px}.revision ins{background:#e7f3ec;color:#145d37;text-decoration:underline;text-underline-offset:3px}.legend{font-size:13px;color:var(--muted);margin-bottom:13px}.legend .added{color:#145d37}.legend .deleted{color:var(--red)}.mode-redline .comparison,.mode-redline .clean{display:none}.mode-redline .revision{display:block}.mode-clean .comparison,.mode-clean .revision{display:none}.mode-clean .clean{display:block}.comments{border-top:1px solid var(--line);padding:13px 22px;background:#fafbfc}.comments summary{font-size:14px;font-weight:600;cursor:pointer;color:#354a55}.comments p,.comments li{font-size:14px;line-height:1.75}.comments p{margin-top:10px;margin-bottom:5px}.comments ul{margin:6px 0;padding-left:22px}.verify-note{color:#775019}.review-block.filtered{display:none}.section-card{padding:26px;background:white;border:1px solid var(--line);border-radius:9px;margin:20px 0}.audit-table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.6}.audit-table th,.audit-table td{border:1px solid #d9d9d9;padding:10px 12px;text-align:left;vertical-align:middle;overflow-wrap:anywhere}.audit-table th{background:#e9eff2;color:#111}.audit-table th:first-child{width:14%}.audit-table th:nth-child(2){width:28%}.audit-table th:nth-child(3){width:16%}.audit-table tr:nth-child(even) td{background:#fbfcfd}.test-disclosure{margin-top:22px}.test-disclosure summary{cursor:pointer;font-weight:600;margin-bottom:14px}.empty{background:white;padding:28px;border:1px solid var(--line);border-radius:8px}.footer{margin-top:30px;font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:15px}[hidden]{display:none!important}.js-only{display:none}.enhanced .js-only{display:flex}.no-js{padding:10px 0;font-size:14px}.table-scroll{overflow-x:auto}
@media(max-width:760px){.wrap{padding:22px 16px 40px}h1{font-size:26px}.lead{font-size:16px}.metrics{grid-template-columns:1fr 1fr}.metric{padding:12px}.metric strong{font-size:20px}.toolbar{position:static;gap:10px}.comparison{grid-template-columns:1fr}.text-pane+.text-pane{border-left:0;border-top:1px solid var(--line)}.block-top,.text-pane,.revision,.clean{padding:16px}.comments{padding:12px 16px}.section-card{padding:18px}.audit-table{font-size:12px}.audit-table th,.audit-table td{padding:8px}.filters input[type=search]{width:100%}.review-block{scroll-margin-top:20px}}
@media print{body{background:white;font-size:11pt}.wrap{max-width:none;padding:0}.toolbar,.tabs,.toc,.js-only,.status,.no-js{display:none!important}.metrics{margin:12px 0}.metric{padding:8px}.metric strong{font-size:16pt}.review-block{break-inside:auto;border-radius:0;margin-bottom:16px}.block-top{break-after:avoid}.comments{break-inside:avoid}.comments>*{display:block}.comments ul{display:block}.section-card{padding:0;border:0}.report-section{display:block!important}.review-block.filtered{display:block}.audit-table tr{break-inside:avoid}.audit-table thead{display:table-header-group}h1{font-size:22pt}.footer{font-size:9pt}}
'''

JS = r'''
(()=>{
document.body.classList.add('enhanced');
const blocks=[...document.querySelectorAll('.review-block')];
const section=document.getElementById('review');
document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b===button)));
  document.querySelectorAll('.report-section').forEach(s=>s.hidden=s.id!==button.dataset.tab);
}));
document.querySelectorAll('.report-section').forEach(s=>s.hidden=s.id!=='review');
document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{
  section.classList.remove('mode-redline','mode-clean');
  if(button.dataset.mode!=='compare')section.classList.add('mode-'+button.dataset.mode);
  document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
}));
function filter(){
  const sample=document.getElementById('sample-filter').value;
  const keyword=document.getElementById('search').value.trim().toLocaleLowerCase();
  const only=document.getElementById('only-review').checked;
  let visible=0;
  blocks.forEach(block=>{
    const show=(!sample||block.dataset.sample===sample)&&(!only||block.dataset.needsReview==='true')&&(!keyword||block.textContent.toLocaleLowerCase().includes(keyword));
    block.classList.toggle('filtered',!show);if(show)visible++;
    document.querySelector('[data-jump="'+block.id+'"]').hidden=!show;
  });
  document.getElementById('visible-count').textContent='显示 '+visible+' / '+blocks.length+' 段';
  document.getElementById('empty').hidden=visible!==0;
}
document.getElementById('sample-filter').addEventListener('change',filter);
document.getElementById('search').addEventListener('input',filter);
document.getElementById('only-review').addEventListener('change',filter);
document.getElementById('toggle-comments').addEventListener('click',event=>{
  const open=event.currentTarget.getAttribute('aria-expanded')!=='true';
  document.querySelectorAll('.comments').forEach(c=>c.open=open);
  event.currentTarget.setAttribute('aria-expanded',String(open));
  event.currentTarget.textContent=open?'收起全部批注':'展开全部批注';
});
document.getElementById('print').addEventListener('click',()=>window.print());
let printDetails=null;
window.addEventListener('beforeprint',()=>{
  if(printDetails!==null)return;
  printDetails=[...document.querySelectorAll('details')].map(el=>({el,open:el.open}));
  printDetails.forEach(({el})=>{el.open=true});
});
window.addEventListener('afterprint',()=>{
  if(printDetails===null)return;
  printDetails.forEach(({el,open})=>{el.open=open});
  printDetails=null;
});
filter();
})();
'''


def render(data):
    cap = validate(data)
    paragraphs = data["paragraphs"]
    before_total = sum(count(p["before"]) for p in paragraphs)
    after_total = sum(count(p["after"]) for p in paragraphs)
    change = (after_total / before_total - 1) * 100
    summary = data.get("test_summary") or [
        {"label": "逐段覆盖", "value": str(len(paragraphs)) + " 段"},
        {"label": "正文原文字数", "value": before_total},
        {"label": "正文改文字数", "value": after_total},
        {"label": "全文字数变化", "value": f"{change:+.2f}%"},
    ]
    metrics = "".join(f'<div class="metric"><strong>{escape(x.get("value", ""))}</strong><span>{escape(x.get("label", ""))}</span></div>' for x in summary)
    samples = list(dict.fromkeys(p["sample"] for p in paragraphs))
    options = '<option value="">全部样稿</option>' + "".join(f'<option value="{escape(s)}">{escape(s)}</option>' for s in samples)
    blocks, jumps = [], []
    for index, p in enumerate(paragraphs):
        anchor = "paragraph-" + str(index + 1)
        jumps.append(f'<a data-jump="{anchor}" href="#{anchor}">{escape(p["id"])}</a>')
        a, b = count(p["before"]), count(p["after"])
        delta = (b / a - 1) * 100
        revision = "".join(escape(text) if tag == "equal" else f'<{tag}>{escape(text)}</{tag}>' for tag, text in diff_parts(p["before"], p["after"]))
        checks = "".join("<li>" + escape(t) + "</li>" for t in p.get("checks", []))
        need = p.get("needs_review", False)
        note = f'<p class="verify-note"><strong>需作者核实</strong> {escape(p.get("review_note", ""))}</p>' if p.get("review_note") else ""
        badge = '<span class="badge">需作者核实</span>' if need else ''
        blocks.append(f'''<article class="review-block" id="{anchor}" data-sample="{escape(p['sample'])}" data-needs-review="{str(need).lower()}">
<div class="block-top"><div><div class="block-id">{escape(p['id'])} · {escape(p['sample'])}</div><h3>{escape(p['section'])}</h3><div class="word-count">原文 {a} → 改文 {b} 字 · <strong>{b-a:+d} 字 / {delta:+.2f}%</strong> · 符合减字上限</div></div>{badge}</div>
<div class="comparison"><div class="text-pane"><div class="pane-label">原文</div><p class="prose before">{escape(p['before'])}</p></div><div class="text-pane"><div class="pane-label">改文</div><p class="prose after">{escape(p['after'])}</p></div></div>
<div class="revision"><div class="legend"><span class="deleted">删除内容带删除线</span>　<span class="added">新增内容带下划线</span> · 按句或分句标记</div><p class="prose redline-text">{revision}</p></div>
<div class="clean"><div class="pane-label">改后净稿</div><p class="prose">{escape(p['after'])}</p></div>
<details class="comments" open><summary>修改批注与保真核对</summary><p>{escape(p['comment'])}</p><ul>{checks}</ul>{note}</details></article>''')
    rows = "".join('<tr>'+''.join('<td>'+escape(row.get(k,''))+'</td>' for k in ('group','name','result','note'))+'</tr>' for row in data.get('test_rows', []))
    test_content = '<div class="table-scroll"><table class="audit-table"><thead><tr><th>轮次或类别</th><th>检查项目</th><th>结果</th><th>证据与说明</th></tr></thead><tbody>'+rows+'</tbody></table></div>' if rows else '<p>本次未提供额外测试记录。</p>'
    test_detail = ''
    if data.get('test_detail_rows'):
        detail_rows = ''.join('<tr>'+''.join('<td>'+escape(row.get(k,''))+'</td>' for k in ('group','name','result','note'))+'</tr>' for row in data['test_detail_rows'])
        test_detail='<details class="test-disclosure"><summary>展开逐项测试记录</summary><div class="table-scroll"><table class="audit-table"><thead><tr><th>编号</th><th>检查项目</th><th>结果</th><th>说明</th></tr></thead><tbody>'+detail_rows+'</tbody></table></div></details>'
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(data.get('title','中文论文逐段对比报告'))}</title><style>{CSS}</style></head>
<body><main class="wrap"><header><div class="eyebrow">中文论文审阅</div><h1>{escape(data.get('title','中文论文逐段对比报告'))}</h1><p class="lead">{escape(data.get('conclusion','已完成改写，降分效果未验证。'))}</p><p class="scope">{escape(data.get('scope_note',''))}</p><div class="meta">{escape(data.get('date',''))}　技能版本 {escape(data.get('skill_version','未记录'))}</div></header>
<div class="metrics">{metrics}</div><p class="small">字数口径：正文非空白字符，含数字和标点；不计标题及批注。全文 {before_total} → {after_total} 字，变化 {change:+.2f}%。每段和全文最多减少 {cap:g}%。</p>
<nav class="tabs js-only" aria-label="报告章节"><button data-tab="review" aria-selected="true">逐段对比</button><button data-tab="tests" aria-selected="false">多轮测试记录</button><button data-tab="guide" aria-selected="false">报告说明</button></nav>
<noscript><p class="no-js">当前未启用脚本，完整逐段对照、批注和测试记录仍可直接阅读。</p></noscript>
<section class="report-section" id="review" aria-label="逐段对比"><div class="toolbar js-only"><div class="modes" aria-label="查看模式"><button data-mode="compare" aria-pressed="true">左右对照</button><button data-mode="redline" aria-pressed="false">修订标记</button><button data-mode="clean" aria-pressed="false">改后净稿</button></div><div class="filters"><label><span class="small">样稿 </span><select id="sample-filter" aria-label="筛选样稿">{options}</select></label><input id="search" type="search" placeholder="搜索正文或批注" aria-label="搜索正文或批注"><label class="checkbox"><input id="only-review" type="checkbox">只看待核实</label></div><button class="plain" id="toggle-comments" aria-expanded="true">收起全部批注</button><button class="plain" id="print">打印报告</button></div><div class="status" id="visible-count">共 {len(paragraphs)} 段</div><nav class="toc" aria-label="段落定位">{''.join(jumps)}</nav><div id="empty" class="empty" hidden>没有符合当前筛选条件的段落。</div>{''.join(blocks)}</section>
<section class="report-section" id="tests"><div class="section-card"><h2>多轮测试记录</h2><p>以下通过数量描述功能验证。AIGC 比例只有真实检测报告才能确认，功能通过数量不能代替降分效果。</p>{test_content}{test_detail}</div></section>
<section class="report-section" id="guide"><div class="section-card"><h2>如何审阅</h2><p>先按段比较原文和改文，再切换到修订标记查看删除与新增内容。每段的批注说明修改理由、保真核对和待核实事项。窄屏会自动改为上下对照。</p><p>本 HTML 中的修订标记用于审阅；Word 原生修订文件可在支持审阅功能的文字处理软件中逐项接受或拒绝。查看模式和筛选只改变当前页面显示，不修改原稿或改稿。</p><p>本页为独立文件，无外部资源请求，可离线打开。打印使用当前查看模式并包含完整段落及报告章节；浏览器的打印设置会影响分页。若预览窗口限制脚本，可下载后在浏览器打开。</p><p>本次功能测试如使用虚构分数，会在对应记录中明确说明；这些分数没有来自检测服务，也不属于本次改稿的实际检测结果。</p></div></section>
<footer class="footer">逐段审阅 · 修改留痕 · 事实保真 · 字数核对</footer></main><script>{JS}</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        if Path(args.input).resolve() == Path(args.out).resolve():
            raise ValueError("输出不能覆盖输入")
        data = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
        output = render(data)
        Path(args.out).write_text(output, encoding="utf-8")
        print(json.dumps({"paragraphs":len(data['paragraphs']), "length_gate":"passed", "output":args.out}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
