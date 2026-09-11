<p align="center">
  <img src="./assets/readme/cover.png" width="1200" alt="中文论文降 AIGC：逐段改写、事实保真、原格式交付。" />
</p>

<p align="center">
  <a href="https://github.com/SoMic520/academic-aigc-zh/archive/refs/heads/main.zip"><img src="./assets/readme/download.svg" width="150" alt="下载 ZIP" /></a>
  &nbsp;
  <a href="./SKILL.md"><img src="./assets/readme/guide.svg" width="150" alt="使用指南" /></a>
</p>

<p align="center">
  <strong>期刊论文 · 学位论文 · 研究报告</strong><br />
  <sub>以原文为依据，逐段调整表达，核对数据、引文与论证关系。</sub>
</p>

<br />

<p align="center">
  <a href="./references/sources.md">
    <picture>
      <source media="(max-width: 640px)" srcset="./assets/readme/modules-mobile.svg" />
      <img src="./assets/readme/modules.svg" width="1200" alt="五个功能模块：学术表达、段落改写、报告定位、中文语体、保真复核。点击查看模块规则。" />
    </picture>
  </a>
</p>

## 视频教程

**WorkBuddy 智能体实操** · 04:31<br />
技能名称：**中文论文降 AIGC（academic-aigc-zh）**。从技能导入、Word 文稿处理，到逐段对比与修订核对。

https://github.com/user-attachments/assets/d0e4543b-c502-4dec-a7f3-3f90d99650d6

[在 B 站观看](https://www.bilibili.com/video/BV1dBYU6jEsH/) &nbsp; · &nbsp; [下载 WorkBuddy](https://www.workbuddy.cn/) &nbsp; · &nbsp; [下载技能 ZIP](https://github.com/SoMic520/academic-aigc-zh/archive/refs/heads/main.zip)

## 开始使用

**01　下载并解压**<br />
点击上方 **下载 ZIP**，获取当前仓库的完整文件；也可以使用下方的命令行方式。

**02　导入完整目录**<br />
在支持 `SKILL.md` 的助手中导入解压后的文件夹，以根目录的 [SKILL.md](./SKILL.md) 为入口，保留包内目录结构。

**03　提供论文材料**<br />
附上正文，说明格式、篇幅和交付要求。已有 AIGC 检测报告时，一并提供以定位标记段落。

<details>
<summary><strong>复制开始指令</strong></summary>

```text
请用 academic-aigc-zh 处理这篇中文论文，降低 AIGC 检测比例。
逐段调整表达，保留原有格式、数据、术语、引文和论证关系，不新增事实。
交付修订批注稿、净稿与逐段对比报告。
如果附有检测报告，请将标记对应到原文后处理。
```

</details>

<details>
<summary><strong>使用 Git 克隆</strong></summary>

```bash
git clone https://github.com/SoMic520/academic-aigc-zh.git
```

</details>

## 交付清楚，便于审阅

**修订批注稿**　查看每一处修改及对应说明，在原文档中逐项审阅。<br />
**Word 净稿**　保留原有格式，提供接受修改后的正文。<br />
**HTML 对比报告**　并排查看原文、改文与修改说明，支持离线阅读。

文档编辑使用所用助手的文档处理能力。已有检测报告时，以同一稿件、同一平台的实际复测结果核对效果。

<details>
<summary><strong>查看改写示例</strong></summary>

合成示例：保留比较对象与研究范围。

**原文**

> 本研究主要比较处理A与对照的土壤有机碳（SOC）含量。结果显示，处理A的SOC为18.6 g·kg⁻¹，对照为15.2 g·kg⁻¹，差异具有统计学意义（P＜0.05）。这一比较仅涉及本次采集的表层土壤。

**改写后**

> 本研究以本次采集的表层土壤为对象，比较处理A与对照的土壤有机碳（SOC）含量。处理A的SOC为18.6 g·kg⁻¹；对照的含量为15.2 g·kg⁻¹。两者含量的差异具有统计学意义（P＜0.05）。

调整信息顺序，保留比较对象、研究范围、数值、单位与统计限定。

[更多示例](./assets/rewrite-examples.json) · [修订交付说明](./references/review-delivery.md)

</details>

<details>
<summary><strong>查看模块规则与项目文件</strong></summary>

- **学术表达**：[受保护片段](./references/local/academic-style/protected-spans.md) · [书面表达](./references/local/academic-style/positive-style-academic.md)
- **段落改写**：[逐段重组](./references/local/paragraph-rewrite/paragraph-rewrite.md)
- **报告定位**：[报告定位](./references/local/report-editing/report-editing.md)
- **中文语体**：[中文表达](./references/local/chinese-style/chinese-style.md)
- **保真复核**：[反向审读](./references/local/fidelity-review/reverse-audit.md)

```text
academic-aigc-zh/
├── SKILL.md                 技能入口
├── README.md                项目首页
├── agents/                  助手显示配置
├── assets/                  视觉素材、词库与示例
├── references/              改写规则与资源记录
│   └── local/               五个功能模块
└── scripts/                 本地辅助脚本
```

辅助脚本使用 Python 3 标准库，无需额外安装 Python 依赖。

- [scan_style.py](./scripts/scan_style.py)：定位需要人工审阅的表达。
- [check_revision.py](./scripts/check_revision.py)：核对篇幅与部分受保护内容。
- [compare_reports.py](./scripts/compare_reports.py)：比较前后检测报告。
- [render_review_report.py](./scripts/render_review_report.py)：生成离线 HTML 对比报告。

</details>

<br />

<p align="center">
  <a href="./SKILL.md">完整指南</a> &nbsp; · &nbsp;
  <a href="./references/sources.md">资源索引</a> &nbsp; · &nbsp;
  <a href="./references/report-workflow.md">复测说明</a>
</p>

<p align="center">
  <picture>
    <source media="(max-width: 640px)" srcset="./assets/readme/signature-mobile.svg" />
    <img src="./assets/readme/signature.svg" width="1200" alt="academic-aigc-zh · 中文学术写作与审阅" />
  </picture>
</p>
