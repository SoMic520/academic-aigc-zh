# 本地资源索引与优化说明

资源版次：local-2026-09-11。五类功能模块已根据选用的上游内容修改适配；执行时直接读取下列包内文件，无需打开网站，也不需要安装其他技能。

## 内置文件

| 功能模块 | 实际采用的文件 | 执行用途 |
|---|---|---|
| 学术表达 | [受保护片段](local/academic-style/protected-spans.md)、[书面表达](local/academic-style/positive-style-academic.md) | 固定事实、对应关系与格式，约束学术语体 |
| 段落改写 | [逐段重组](local/paragraph-rewrite/paragraph-rewrite.md) | 按段落功能重组句法，控制每段和全文篇幅 |
| 报告定位 | [报告定位](local/report-editing/report-editing.md) | 从本地报告映射到原段，衔接复测与审阅交付 |
| 中文语体 | [中文局部检查](local/chinese-style/chinese-style.md) | 处理冗余、泛化评价、模糊归因与聊天残留 |
| 保真复核 | [反向审读](local/fidelity-review/reverse-audit.md) | 对照主张、术语、数值、引文与限定，检查改写副作用 |
| 本地适配程序 | [表达提示脚本](../scripts/scan_style.py)、[本地词库](../assets/style-patterns.json) | 输出可定位的人工审阅提示，不计算 AI 分数 |
| 本技能配套文件 | [完整段落示例](../assets/rewrite-examples.json)、[正文核对](../scripts/check_revision.py)、[报告比较](../scripts/compare_reports.py)、[HTML 生成器](../scripts/render_review_report.py) | 核对篇幅与部分受保护内容，比较真实报告，生成离线对比 HTML |

## 已处理的冲突

- 删除来源规则中的固定修改率、词汇配额、噪声预算和检测效果自评分，不采纳未经验证的平台算法或降分承诺。
- 不采用凭空加入作者感受、研究经历、数值、引文、实验机制的示例；本地示例只基于同段已有内容改写。
- 将“大幅压缩”改为每段和正文默认最多减少 3%，允许不变或增加；不能用额外标题、批注或空话补数。
- 真实三项列举、必要限定、统计学“显著”及规范被动句均可保留，不按词表机械删除。
- 不随风格修改标题、字体、加粗、页眉页脚、公式或表格。修订稿与净稿均使用原文档副本，HTML 单独生成。
- 已有正文就直接完成；本地材料足够时不要求先取得 HTML 报告、不反复请求开始确认。

## 本地许可与溯源

各模块对应的 MIT 许可证原文随包保留；原项目名称、作者信息和来源版本保留在许可证及来源清单中：

- [学术表达模块许可证](../third_party/academic-style/LICENSE)
- [段落改写模块许可证](../third_party/paragraph-rewrite/LICENSE)
- [报告定位模块许可证](../third_party/report-editing/LICENSE.txt)
- [中文语体模块许可证](../third_party/chinese-style/LICENSE)
- [保真复核模块许可证](../third_party/fidelity-review/LICENSE)

[本地来源清单](../third_party/manifest.json) 记录仓库标识、固定版本、下载文件 SHA-256、实际内置文件及适配内容。仓库标识仅用于保留许可溯源，不是任务中的访问步骤。

未打包上游完整技能入口、安装器、宣传文档及无关文件。核心规则在本地即可读取，四个辅助脚本无需第三方 Python 包或联网下载；复杂文档读取、编辑与渲染使用当前环境已有能力。实际 AIGC 下降仍以真实复测报告为准。
