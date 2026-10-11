# Dog-ADHD

研究如何让 AI 回答直接、作出独立判断、自然交流，并保留任务必需的论据和条件。[GitHub 仓库](https://github.com/ZhouYinLong-lab/Dog-ADHD)。

**从这里开始**

- [调研与 12 条解决路线](docs/research-and-solutions.md)：已有项目、实验结果、规则冲突和四套组合。
- [候选规则审查](docs/candidate-review.md)：13 项冗余、冲突或遗漏风险，以及首试选择理由。
- [0.2 最小中文规则](prompts/minimal-core-v0.2.md)：F 任务内容 + J 证据判断 + E 自然表达，长文按需加 W。
- [0.1 中文模块留档](prompts/chinese-modules.md)：初版共同规则、判断、写作、匿名评审和反方审查。
- [24 组中文验收用例](evals/chinese-smoke-tests.md)：错误迎合、错误反驳、内容保留和多轮稳定性。
- [首轮对照方案](evals/first-round-plan.md)：实验条件、8 组审查回归输入、评审标准和费用边界。
- [工作交接](HANDOFF.md)：需求、当前结论、已完成工作和下一步。
- [来源记录](research/source-manifest.json)：原始规则文件的链接、获取日期和内容哈希。

**目录**

```text
Dog-ADHD/
├── README.md
├── AGENTS.md
├── HANDOFF.md
├── docs/research-and-solutions.md
├── docs/candidate-review.md
├── prompts/chinese-modules.md
├── prompts/minimal-core-v0.2.md
├── evals/chinese-smoke-tests.md
├── evals/first-round-plan.md
├── research/source-manifest.json
├── research/source-snapshots/   # 本地保存的第三方原始资料
├── scripts/collect_sources.py
└── work/                      # 后续草稿和临时结果
```

**当前状态**

2026-10-11 已有第一轮调研与候选静态审查，提出 0.2 最小组合，尚未运行模型对照评测。作者实验、规则风险推演和本项目实际检查分别记录。

建议先试 F+J+E，长文按需增加原材料对照。评测同时检查抵抗错误施压、接受正确纠正和保留关键内容，不以反驳次数或字数判断质量。现有 24+8 组都是开发材料，最终验收需另留真实任务。收费模型评测先明确预算和授权。

**继续工作**

在 Codex 中打开这个文件夹，开始新对话并让代理读取 `HANDOFF.md`。项目内的 `AGENTS.md` 提供维护规则。后续成果直接写到相应目录，临时文件放入 `work/`。

`scripts/collect_sources.py` 可重新获取关键开源项目规则；它会访问网络并更新来源快照及清单。原始快照和临时结果已由 `.gitignore` 排除在默认提交之外。

用户已指定 GitHub 目标，查询到其现有可见性为公开；本项目保持该设置。已有内容按来源、研究、提示词、评测和项目说明拆分提交；初始整包提交 `45f1190` 保留在本地 `codex/archive-initial` 分支。同步状态见 `HANDOFF.md`。
