# PROGRESS.md — 唯一进度事实来源

> 这是本目录**唯一**的进度文件。不要新建 plan.md / todo.md / TODO 之类的东西。
> Codex 每次会话开始必须读这个文件，结束必须更新它。
> **最后更新：2026-10-30**

---

## d01（10/25 周日）—— 建词汇表 + 拿报文直觉，约 2.5 小时

> 笔记骨架已建好：`notes/d01-2026-10-25.ipynb`，直接往里填（V2 那个 cell 会报 TypeError，故意的）。

| 顺序 | 做什么 | 具体 | 时长 | 产出（落在 `notes/w1-reading.md`） |
|---|---|---|---|---|
| 0 | **先做门槛自测**（最重要） | 关掉 AI，30 分钟内写一个 40 行的「假 agent」：一个 dict 存 2 个函数、输入一条指令、for 循环最多 3 步、每步调用一个函数并打印、用 try/except 接住异常继续。写完把代码贴进 notes | 30 min | 判断结果：写得出 → 后天直接写 `loop.py`；卡住 → 先补 3 天 Python（见 `00_资料清单` 五节 W1-A） |
| 1 | **[A4 Harness Engineering](https://arxiv.org/abs/2609.00006)** | 只读：**七个子系统的名字 + 一句话职责** + 结论。**跳过最小/最大实现对比**（那部分要工程经验才看得懂，第 4 周再回来看） | 20 min | 七个子系统清单，每个标注「我的作品里对应哪个文件」 |
| 2 | **你手上模型厂商的 Tool Use 文档**（一手，不是博客）。参考写法：[Anthropic Tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) | 完整的一次往返：请求里 tools 怎么定义 → 响应里 tool_calls 长什么样 → 结果怎么回灌 → 多轮怎么串 | 60 min | 手抄一份真实的 request / response 报文样例（脱敏） |
| 3 | **[B2 Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)** —— 只读两节 | 「What is a tool」+「Prompt-engineering your tool descriptions」 | 30 min | 5 条工具描述的自查项（写成能打勾的句子） |

**明天不读**：ReAct 全文、MemGPT、Voyager、任何源码、任何 C 类材料（计价/模型对比/面经）。理由见 `00_资料清单与学习法.md` 一·B 节。

### 常用链接速查（这几个会反复点）

| 用途 | 链接 |
|---|---|
| 全部资料清单（41 条链接） | [00_资料清单与学习法.md](00_资料清单与学习法.md) |
| 坐标系（七个子系统） | [arXiv:2609.00006](https://arxiv.org/abs/2609.00006) |
| 工具设计（写工具前必读） | [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) |
| 上下文工程 | [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 失败分类学（踩坑时查） | [Pitfalls](https://ai.zenoagi.com/harness/practice/pitfalls) |
| 中文打底 + 八股 | [hello-agents](https://github.com/datawhalechina/hello-agents) |
| 参考实现（最小 harness） | [pi-mono](https://github.com/earendil-works/pi) |
| 研究进展（每周扫标题） | [arXiv cs.CL](https://arxiv.org/list/cs.CL/recent) · [simonwillison.net](https://simonwillison.net/) |

---

## 当前状态

| 项 | 值 |
|---|---|
| 当前周次 | **W1-A（10/26–10/28）补 Python ＋ 同步开写 C++ 模拟器 → W1-B（10/29–11/04）最小 loop** |
| 本周主题 | 先能写，再写 agent。**第一版 loop 用同步 + 字典 + 不用 pydantic/pytest** |
| 我的基线 | Python 基础语法；agent 只学过 LangChain + 调 API；async / pydantic / pytest 未掌握；**C++ 是最强语言** |
| 当前天数 | **d02（2026-10-30）**，d01 已于 10/25–26 完成（笔记 + 自测） |
| 项目阶段 | **最小 loop 能跑**：真 DeepSeek API 端到端 3 步跑通一个任务 |
| 截止倒计时 | 距 2027/3 暑期实习投递 ≈ **18 周** |

---

## 模块进度

状态定义：`未开始` → `进行中` → `能跑`（跑通一个真实任务）→ `已验证`（进入评测集且通过）

| 模块 | 文件 | 状态 | 备注 |
|---|---|---|---|
| LLM 统一封装 | `src/llm/client.py` | 未开始 | 参考实现在 `notes/d02-reference/client.py`（真调通 DeepSeek）；`src/` 我自己写 |
| Agent Loop | `src/agent/loop.py` | 未开始 | 文件里还是 18 行草稿；参考实现在 `notes/d02-reference/loop.py` |
| 工具定义与注册 | `src/tools/` | 未开始 | 参考实现在 `notes/d02-reference/builtin.py`；目标 20 个 |
| **C++ 车况模拟器** | `sim/vehicle_sim.cpp` | 未开始 | **W1-A 就开工**（我的最强语言，不依赖 Python），工具的真对象 |
| Python ↔ 模拟器通信 | `src/sim_bridge.py` | 未开始 | W5，stdin/stdout 行协议 |
| 上下文管理 | `src/context/` | 未开始 | W4–W5，预算 / 截断 / 摘要 |
| 记忆（FTS5） | `src/memory/` | 未开始 | W5，工作区 / 召回 / 归档 |
| 安全与权限 | `src/safety/` | 未开始 | W6，L0–L3 分级 |
| Go tool gateway | `gateway/` | 未开始 | W7 |
| trace 落盘 | `src/trace.py` | 未开始 | 参考实现在 `notes/d02-reference/trace.py` |
| 评测集 | `eval/tasks.jsonl` | 未开始 | W8，目标 50 条 |
| 评测脚本 | `eval/run.py` | 未开始 | 终态断言 + 五指标 |
| README | `README.md` | 进行中 | 开源门面结构/架构图/设计取舍/评测指标已完善；后续随实测数据持续微调 |

---

## 关键数字（每完成一轮评测就更新，没有数字就是没有进展）

| 指标 | 当前 | 上一轮 | 备注 |
|---|---|---|---|
| 任务成功率 | 1/1 | — | **参考实现测的，不是 `src/` 的数**；也不是评测集 |
| 平均步数 | 3 | — | 同上 |
| 平均 token / 任务 | 2269（in 2152 / out 117） | — | 同上 |
| 单任务成本（元） | 0.00524 | — | deepseek-chat 单价 in 2 / out 8（元每百万） |
| p95 延迟（秒） | 3.63 | — | 单次样本，p95 = 均值 |
| 上下文峰值占用 | ~2.1k / 64k ≈ 3.3% | — | deepseek-chat 窗口 |
| 工具调用错误率 | 0/2 | — | 单任务，模型分不出来 |

---

## 本周卡点

> 一句话写清「我卡在什么现象上」，不是「我在学什么」。

- （空。今天开始填）

---

## 下一步（只写 3 件，按顺序，每件都要有验收标准）

1. **关掉 `src/agent/loop.py`，默写那 5 处 `# CORE`**
   - 验收：不看参考实现，从空文件写出能真跑通同样任务的 loop；写不出的那处就是认知缺口
   - 写完之后 `git diff` 对照参考实现，把差异写进 d02 笔记
2. **故意让工具报错，记录模型的反应**
   - 验收：把 `control_ac` 的上下限临时改成 24~26，让模型去设 16 度；记 3 条真实观察（它重试了几次 / 有没有读 `hint` / 最后有没有说实话）
   - 落点：`notes/d02-2026-10-30.md` §2，不要另开文件
3. **读 B2《Writing tools for agents》，把自己的工具 description 重写一遍**
   - 验收：对比前后两版 description，写出差在哪；重点看 `get_weather` 那句「不要用它查车况」有没有用

---

## 变更日志（Codex 每轮追加一行）

| 日期 | 模块 | 一句话 |
|---|---|---|
| 2026-10-24 | 目录初始化 | 建立 AGENTS.md / PROGRESS.md / README 占位，代码未动 |
| 2026-10-25 | notes/d01 | 门槛自测 V1/V2（V1 有两处静默 bug：负号被吞、状态没写回）+ A4 七子系统，报文档节未做 |
| 2026-10-30 | notes/d01 | 补 V3 假 agent 正确结构对照，含「模型说成功、state 没动」的真实现场输出 |
| 2026-10-30 | notes/d02-reference | 完整参考实现（5 文件 / 481 行 / 全部 ≤150 行）落在**笔记目录**，**不进 `src/`**——`src/` 归用户自己写。已验证真跑：3 步 done、成本 0.00524 元 |
| 2026-10-30 | notes/*.ipynb | 笔记全部改为 Jupyter notebook；已在**真 kernel** 里逐 cell 跑通（d01 的 V2 报 TypeError 属预期）；本机装了 ipykernel 并注册 kernelspec `python3` |
| 2026-10-30 | src/agent/loop.py | 按用户要求回退到 18 行草稿版，未动 |
| 2026-10-30 | README.md | 重构对外开源门面：补齐架构图、L0-L3权限矩阵、工程取舍对比表、五维评测基准与快速开始 |

---

## 每周自检（周日晚上回答，诚实，不许糊弄）

1. 这周我**自己**写了多少行代码？（关掉 AI 写的）
2. 作品现在能跑通的最复杂的一件事是什么？
3. 我踩到的最有价值的一个坑是什么？（答不出来 = 这周白过）
4. 评测集有几条？成功率是多少？
5. 简历上这周多出了哪一句可以写的话？

### 本周回答（W1）
- （周日填）

---

## 里程碑

| 里程碑 | 目标日期 | 验收 | 状态 |
|---|---|---|---|
| M1 最小 loop 能跑 | 2026-11-04 | 一个任务端到端跑通 | ☐ |
| M2 工具层可用 | 2026-11-20 | 20 个工具 + 三模型错误率表 | ☐ |
| M3 长任务不爆 | 2026-12-04 | 100 轮不超窗口，token 有下降 | ☐ |
| M4 安全层完成 | 2026-12-11 | L0–L3 分级 + 注入防御演示 | ☐ |
| M5 Go 网关上线 | 2026-12-18 | `go test -race` 通过，Python 侧走 HTTP 调用 | ☐ |
| M6 评测闭环 | 2026-12-25 | 50 条评测集 + 成功率表 + trace 回放 | ☐ |
| M7 简历定稿 | 2027-01-15 | 一页，两个项目，全部有数字 | ☐ |
| M8 投递开始 | 2027-03-01 | 一周内投完四家 + 五家保底 | ☐ |