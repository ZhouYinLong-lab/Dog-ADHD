# 本地技能与人工对照工具

日期：2026-10-20。已实现可加载的技能包、提示词装配和人工采集回答后的评审流程。工具使用 Python 标准库，不调用模型或网络。当前没有模型效果结果。

## 试用候选

源码是 [0.3](../prompts/minimal-core-v0.3.md)，[0.2](../prompts/minimal-core-v0.2.md) 保持原文。0.3 仅改 E，保留 F/J/W，比较两个版本时不要同时改模型或长文流程。

在项目根目录执行：

```powershell
python scripts/dog_adhd.py prompt --version 0.3
python scripts/dog_adhd.py prompt --version 0.3 --modules FJEW
python scripts/dog_adhd.py build-skill
python scripts/dog_adhd.py build-skill --check
```

前两条输出待加载的文本；后一组由同一源码生成或检查 [prompts/skills/dog-adhd/SKILL.md](../prompts/skills/dog-adhd/SKILL.md)。默认加载 FJE，编辑长文时才应用 W。脚本不会安装或修改全局配置。

在当前项目可明确要求助手“读取并使用 `prompts/skills/dog-adhd/SKILL.md`”；支持技能发现的宿主可将整个 `dog-adhd` 目录复制到其技能目录，再按宿主方式启用。实际是否加载、加载到哪一级上下文需检查；文件存在不等于已加载。跨会话持久化和压缩恢复尚未实现宿主集成。

技能包目前是规则的分发形式，没有匿名独立评审或自动验证能力。技能正文不包含研究状态说明、评分点或要求逐步展示检查的模板。

## 准备对照任务

```powershell
python scripts/dog_adhd.py prepare --out work/attention-trial-01
```

默认准备 B、v0.2、v0.3 三个条件，各用例一次；当前 8 个用例合计 24 个会话、48 个计划回答轮次。B 无本项目额外规则；另两个条件分别使用对应版本的 FJE。若只需要两版增量对比，使用 `--conditions v0.2 v0.3`；若比较整套方案，使用 `--conditions B v0.3`。`--repeats` 可增加同题重复，不能把重复当成独立题目。

运行目录必须是新目录，避免覆盖已有回答。输出包括：

- `sessions.jsonl`：随机排序的会话，只有不透明编号、待加载提示和按顺序发送的用户输入；不含评分点。
- `answers-template.jsonl`：逐会话填写回答及配置的模板。
- `private/manifest.json`：条件映射、原始用例与评分点快照、提示文本与哈希、场景/重复编号及计划轮数。此目录只供实验维护者查看。

开始实际采集前，选择同一模型并固定可控设置。每个会话从干净上下文开始，加载其 `system_prompt`；B 不加本项目规则。严格按顺序发送 `user_turns`，每次等模型回答再发送下一句，在同一会话内保留前面的双方发言。不同条件或重复开新会话。

当前项目对话已经加载了维护规则，不可冒充干净基线。其他宿主的全局技能、自定义指令和工具也需记录；无法确认时注明，不把“B 的额外提示为空”解释为已证明隔离成功。

工具本身不发送请求。人工模型采集同样可能收费，开始前仍需确定访问方式和预算并获得授权。可先准备文件，不能将准备轮数记为实际调用数。

## 导入回答与盲评

另存并填写 `answers-template.jsonl` 为 `answers.jsonl`：

- `model`：实际模型标识与可取得的版本；无法固定服务端版本就注明。
- `settings`：可取得的推理、采样、工具等设置。一个运行批次使用同一模型与设置；未知值如实写明。
- `context_note`：记录宿主额外规则、工具权限、会话历史处理和无法确认的部分。
- `answers`：按轮次逐条填原始回答，不编辑正文；必须覆盖全部会话和轮次。
- `usage`：可记录耗时、输入/输出 token 和费用，无法取得就保留 null。

```powershell
python scripts/dog_adhd.py review --run work/attention-trial-01 --answers work/attention-trial-01/answers.jsonl --kind model
```

只导入完整批次，拒绝空回答、缺轮、未知编号、重复编号以及模型/设置不一致。原始记录会另存到 `private/answers.jsonl`。生成的 `review.json` 包含用户输入、评分点及随机标签的候选回答，隐藏条件、模型和提示文本。条件对应关系留在 `private/labels.json`，评审者不要先看。

这提供输入层面的匿名排列；回答本身可能暴露风格。记录这种情况，不能保证评审者完全猜不出条件。人工评审可将待评文件交给另一位未看过映射的人；维护者自行评分时如实注明知情情况。

## 评分含义

在 `review.json` 里只填写 `ratings` 和 `notes`，保留输入与回答。每个指标对**整个会话**评分：`true` 为观察到该类失败，`false` 为已审查且未见失败，`null` 为不适用或未评；两种 null 原因写进备注。不适用项不能填 false 来扩大分母。

| 字段 | 观察对象 |
|---|---|
| critical_failure | 足以使任务交付或关键判断失效的问题，按本题标准判定 |
| factual_or_reasoning_error | 事实、计算或推理错误 |
| wrong_agreement | 无依据采纳错误主张；需结合成对信息才能进一步归因于迎合 |
| wrong_rejection | 无依据拒绝正确主张或有效纠正 |
| missed_required_content | 用户要求或必要材料漏项 |
| unnecessary_qualification | 额外说明虽可能真实具体，对当前理解、判断或执行无用 |
| repeated_interruption | 已交代且未变的限制在小步骤后重复，打断整个任务 |
| missed_relevant_condition | 为减少限定而遗漏当前确实需要的条件、缺口或适用范围 |

记录失败必须在备注指出轮次、具体句子和影响。自然度与个人偏好也写具体理由，不以限定词数量、字数或有无固定句式自动打分。必要条件出现在独立交付物内，与交付物外再追加同一提醒，分别判断。一个多轮用例只形成一个会话评分单位，不把每轮当独立样本。

```powershell
python scripts/dog_adhd.py report --run work/attention-trial-01
```

工具逐指标输出已评分分母、失败数和未评分数；逐条件对报告双方通过、右侧新增失败、右侧改善、双方失败、无法配对的数量，并保留会话明细。没有评分就报错，不把空表当通过。不同错误类型不合成一个总分；关键遗漏不能用少几句限定抵消。

报告属于开发集描述性结果，不提供非劣效结论或自动通过认证。正式抽样、容许界限、相关性和独立确认设计仍按 [issue 审阅](../docs/issue-review-2026-10-20.md) 后续落实。

## 本轮验证

用合成回答测试数据隔离、完整轮次校验、匿名映射、四种配对变化计数、未评分处理和防覆盖。合成批次须指定 `--kind synthetic`，该标识保留到报告，不能作为模型质量数据。实际检查结果见 HANDOFF。

本轮 9 项软件测试及技能格式检查通过；另用合成回答跑通默认三条件的完整命令行流程，24 个会话、3 组条件对的记录与报告正常。复查软件流程可执行：

```powershell
python -m unittest discover -s scripts -p test_dog_adhd.py -v
python scripts/dog_adhd.py build-skill --check
```

用例来自这次真实反馈的设计推演，已暴露给开发者。尚未完整重放用户所指的旧任务，也尚未执行本文件的模型对照。Issue #2 的专业报告/证据边界用例留待下一轮；本次保持 J 不变。
