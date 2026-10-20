# Dog-ADHD

研究如何让 AI 回答直接、作出独立判断、自然交流，并保留任务必需的论据和条件。[GitHub 仓库](https://github.com/ZhouYinLong-lab/Dog-ADHD)。

**从这里开始**

- [本地技能与试用说明](evals/local-trial.md)：加载技能、生成对照任务、导入回答、匿名评审与配对明细。
- [0.3 最小中文规则](prompts/minimal-core-v0.3.md)：仅修改 E，补充限定的必要性及连续任务中的重复检查。
- [真实反馈与问题修正](docs/qualification-feedback.md)：具体的限定句也可能不必要，评审需看整段任务体验。
- [调研与 12 条解决路线](docs/research-and-solutions.md)：已有项目、实验结果、规则冲突和四套组合。
- [候选规则审查](docs/candidate-review.md)：13 项规则审查，涵盖冗余、冲突、保留项及首试选择理由。
- [0.2 中文规则留档](prompts/minimal-core-v0.2.md)：保留作为新表达模块的对照。
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
├── docs/qualification-feedback.md
├── prompts/chinese-modules.md
├── prompts/minimal-core-v0.2.md
├── prompts/minimal-core-v0.3.md
├── prompts/skills/dog-adhd/SKILL.md
├── evals/chinese-smoke-tests.md
├── evals/first-round-plan.md
├── evals/attention-cases.json
├── evals/local-trial.md
├── research/source-manifest.json
├── research/source-snapshots/   # 本地保存的第三方原始资料
├── scripts/collect_sources.py
├── scripts/dog_adhd.py
├── scripts/test_dog_adhd.py
└── work/                      # 后续草稿和临时结果
```

**当前状态**

2026-10-20 已实现 0.3 候选、本地技能和人工对照记录工具。模型对照运行数仍为 0；工具测试使用合成数据。作者实验、设计推演、软件检查与模型效果分别记录。

建议先试 F+J+E，长文按需增加原材料对照。评测检查抵抗错误施压、接受正确纠正、保留关键内容和任务序列中的不必要打断，不以限定词数量或字数判断质量。原有 24+8 组和新增 8 个序列用例都是开发材料，最终验收需另留真实任务。收费模型评测先明确预算和授权。

在项目根目录生成可复制的规则文本，或重新生成技能：

```powershell
python scripts/dog_adhd.py prompt --version 0.3
python scripts/dog_adhd.py build-skill
```

生成的技能可明确要求助手读取使用，或复制到支持技能的宿主目录。默认不修改全局配置。完整试用和评审步骤见 [本地说明](evals/local-trial.md)。

**继续工作**

在 Codex 中打开这个文件夹，开始新对话并让代理读取 `HANDOFF.md`。项目内的 `AGENTS.md` 提供维护规则。后续成果直接写到相应目录，临时文件放入 `work/`。

`scripts/collect_sources.py` 可重新获取关键开源项目规则；它会访问网络并更新来源快照及清单。原始快照和临时结果已由 `.gitignore` 排除在默认提交之外。

用户已指定 GitHub 目标，查询到其现有可见性为公开；本项目保持该设置。已有内容按来源、研究、提示词、评测和项目说明拆分提交；初始整包提交 `45f1190` 保留在本地 `codex/archive-initial` 分支。同步状态见 `HANDOFF.md`。
