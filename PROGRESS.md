# PROGRESS.md — 唯一进度事实来源

> 这是本目录**唯一**的进度文件。不要新建 plan.md / todo.md / TODO 之类的东西。
> Codex 每次会话开始必须读这个文件，结束必须更新它。
> **最后更新：2026-11-06**

---

> 下面这段 d01 写于「按天 / 按分钟」的旧计划时期，**仅作存档**，不再作为排期依据。

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
| 当前阶段 | **P2 工具层可用**（P1 已通过真 API 复核，2026-11-06） |
| 本阶段目标 | 20 个工具 + 三模型错误率表 |
| 已完成阶段 | P1 最小 loop 能跑（d01–d03） |
| 我的基线 | Python 基础语法；agent 只学过 LangChain + 调 API；async / pydantic / pytest 未掌握；**C++ 是最强语言** |
| 项目现状 | `invoke_tool` 兜底完成（未知工具 / 坏 JSON / 非对象参数 / 多余参数），`loop.py` 136 行；20 个工具待写 |
| 截止倒计时 | 距 2027/3 投递 ≈ **18 周**（**外部约束，不是学习预算**） |

---

## 模块进度

> **阶段表才是学习单位**（见文末「阶段」）。这张表只是文件级细分：不用它算进度，也不拿它排任务。

状态定义：`未开始` → `进行中` → `能跑`（跑通一个真实任务）→ `已验证`（进入评测集且通过）

| 模块 | 文件 | 阶段 | 状态 | 备注 |
|---|---|---|---|---|
| Agent Loop | `src/agent/loop.py` | P1 | **能跑** | 136 行；四条假路径 + 真 API 复核通过（2026-11-06） |
| 测试替身 | `tests/loop_test.py` | P1 | **能跑** | `FakeClient` + `CASES` 四条用例；`python -m tests.loop_test` |
| 工具定义与注册 | `src/tools/` | P2 | 进行中 | 2 个工具仍内联在 `loop.py`；目标 20 个，先拆 `builtin.py` |
| LLM 统一封装 | `src/llm/client.py` | P2 | 未开始 | client 现在在 `run()` 里懒加载，未抽 wrapper |
| trace 落盘 | `src/trace.py` | P2 | 未开始 | 前置：`dump_messages` 归一化 |
| **C++ 车况模拟器** | `sim/vehicle_sim.cpp` | P2 | 未开始 | 工具的真对象；本机没装 cmake |
| Python ↔ 模拟器通信 | `src/sim_bridge.py` | P3 | 未开始 | stdin/stdout 行协议 |
| 上下文管理 | `src/context/` | P3 | 未开始 | 预算 / 截断 / 摘要 |
| 记忆（FTS5） | `src/memory/` | P3 | 未开始 | 工作区 / 召回 / 归档 |
| 安全与权限 | `src/safety/` | P4 | 未开始 | L0–L3 分级 |
| Go tool gateway | `gateway/` | P5 | 未开始 | `go test -race` |
| 评测集 | `eval/tasks.jsonl` | P6 | 未开始 | 目标 50 条 |
| 评测脚本 | `eval/run.py` | P6 | 未开始 | 终态断言 + 五指标 |
| README | `README.md` | — | 进行中 | 门面已成型；随实测数据微调 |

---

## 关键数字（只记 `src/` 的实测，不记参考实现）

> 旧的一组数（2269 token / 0.00524 元 / 3.63 秒）来自**已删除**的 `notes/d02-reference/`，
> 不代表 `src/` 的任何东西，已作废。

| 指标 | 当前 | 上一轮 | 备注 |
|---|---|---|---|
| 任务成功率 | 1/1 | — | **`src/` 实测**（2026-11-06 真 API 复核，单条）；不是评测集 |
| 平均步数 | 2 | — | 同上（1 次工具调用 + 1 次收尾） |
| 平均 token / 任务 | 待采集 | — | 那次复核没记 `usage` |
| 单任务成本（元） | 待采集 | — | 同上 |
| p95 延迟（秒） | 待采集 | — | 同上 |
| 上下文峰值占用 | 待采集 | — | 同上 |
| 工具调用错误率 | 0/1 | — | `src/` 单条，无错误 |

---

## 当前阶段卡点

> 一句话写清「我卡在什么现象上」，不是「我在学什么」。

- message混着dict和对象，message的归一化还没有落地
- 对部分python包理解不够，types包熟悉度不高（现在已经学习过了理解含义）


---

## 下一步（P2 阶段的前 3 个任务，按顺序，每件都要有验收标准）

1. **`dump_messages` 归一化落地**（`src/agent/message.py`）
   - 验收：`json.dumps(dump_messages(msgs), ensure_ascii=False)` 不崩；真 client 的 pydantic 消息和 FakeClient 的 `SimpleNamespace` 都能过；输出只含白名单字段（`role` / `content` / `tool_calls` / `name` / `tool_call_id`）
2. **`FakeClient` 记下 `kwargs["messages"]`**
   - 验收：能贴出用例 3 第 3 条 `role:"tool"` 的原文，`tool_call_id` 对得上 `call_1`
3. **拆 `src/tools/builtin.py`**
   - 验收：`loop.py` 降到 80 行以内，`python -m tests.loop_test` 四条输出与拆前逐字一致

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
| 2026-11-06 | src/agent/loop.py + notes/d03 | 工具兜底（未知工具 / 坏 JSON / 非对象参数 / 多余参数）+ `TOOL_LOG` 挪到统一出口（成功也记）+ 错误文案按错因分开（日志与回灌共用 `err`，不再分叉）；`arguments="null"` 的 UnboundLocalError 已修；FakeClient 剧本注入（返回 SimpleNamespace，`run()` 未改） |
| 2026-11-06 | src/agent/loop.py → tests/ | `FakeClient` + `CASES` 拆到 `tests/loop_test.py`，`loop.py` 173 → 136 行（回到 150 行以内）；四条假路径回归通过；真 API 复核通过 |
| 2026-11-06 | AGENTS.md + PROGRESS.md | 学习计划改**阶段制**（P1–P7 阶段表 + 外部时间约束单列）；AGENTS.md §4/§10 改为任务推送制；模块进度加阶段列并清掉 `d02-reference` 旧引用；关键数字只记 `src/` 实测；d01 段标存档 |

---

## 每阶段自检（阶段收尾时回答，诚实，不许糊弄）

1. 这周我**自己**写了多少行代码？（关掉 AI 写的）
2. 作品现在能跑通的最复杂的一件事是什么？
3. 我踩到的最有价值的一个坑是什么？（答不出来 = 这周白过）
4. 评测集有几条？成功率是多少？
5. 简历上这周多出了哪一句可以写的话？

### 阶段自检记录
- P1（2026-10-25 – 2026-11-06）：（阶段收尾时填）

---

## 阶段（唯一的学习单位）

状态：`未开始` → `进行中` → `已完成`（验收项全部达成）

| 阶段 | 目标 | 验收（可检查） | 状态 |
|---|---|---|---|
| P1 | 最小 loop 能跑 | 一个任务端到端跑通 | **已完成** |
| P2 | 工具层可用 | 20 个工具 + 三模型错误率表 | 进行中 |
| P3 | 长任务不爆 | 100 轮不超窗口，token 有下降 | 未开始 |
| P4 | 安全层完成 | L0–L3 分级 + 注入防御演示 | 未开始 |
| P5 | Go 网关上线 | `go test -race` 通过，Python 侧走 HTTP 调用 | 未开始 |
| P6 | 评测闭环 | 50 条评测集 + 成功率表 + trace 回放 | 未开始 |
| P7 | C++ 订单簿撮合与回测引擎（远期储备） | L2 订单簿重建 + 微秒级撮合 + 事件驱动回测 | 未开始 |

## 外部时间约束（不是学习计划，别当阶段排）

| 事项 | 日期 | 说明 |
|---|---|---|
| 简历定稿 | 2027-01-15 | 一页，两个项目，全部有数字 |
| 投递开始 | 2027-03-01 | 一周内投完四家 + 五家保底 |

> 这两项是外部窗口，不可移动；但它们不参与「阶段」排序，也不用来倒推每天学多少。
