# Independent AI Collaborator Research

研究如何让 AI 回答直接、作出独立判断、自然交流，并保留任务必需的论据和条件。当前名称仅用于本地工作，后续可更名。

**从这里开始**

- [调研与 12 条解决路线](docs/research-and-solutions.md)：已有项目、实验结果、规则冲突和四套组合。
- [中文提示词模块](prompts/chinese-modules.md)：共同规则、判断、写作、匿名评审和反方审查。
- [24 组中文验收用例](evals/chinese-smoke-tests.md)：错误迎合、错误反驳、内容保留和多轮稳定性。
- [工作交接](HANDOFF.md)：需求、当前结论、已完成工作和下一步。
- [来源记录](research/source-manifest.json)：原始规则文件的链接、获取日期和内容哈希。

**目录**

```text
ai-collaborator-research/
├── README.md
├── AGENTS.md
├── HANDOFF.md
├── docs/research-and-solutions.md
├── prompts/chinese-modules.md
├── evals/chinese-smoke-tests.md
├── research/source-manifest.json
├── research/source-snapshots/   # 本地保存的第三方原始资料
├── scripts/collect_sources.py
└── work/                      # 后续草稿和临时结果
```

**当前状态**

2026-10-11 完成第一轮调研。已有方案与候选中文规则，尚未运行模型对照评测。文档中保留作者实验与本项目提案之间的区别。

建议从日常合作者和长文写作两套组合起步。评测同时检查能否抵抗错误施压、接受正确纠正，以及是否保留关键内容。用户要求展开时，篇幅按任务需要决定。

**继续工作**

在 Codex 中打开这个文件夹，开始新对话并让代理读取 `HANDOFF.md`。项目内的 `AGENTS.md` 提供维护规则。后续成果直接写到相应目录，临时文件放入 `work/`。

`scripts/collect_sources.py` 可重新获取关键开源项目规则；它会访问网络并更新来源快照及清单。原始快照和临时结果已由 `.gitignore` 排除在默认提交之外。

仓库名称、GitHub 目标及公开／私有设置尚未决定。本地 Git 使用 `main` 分支；确定目标后可以添加远程并推送。
