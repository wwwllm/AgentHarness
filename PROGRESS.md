# PROGRESS.md — 唯一进度事实来源

> 这是本目录**唯一**的进度文件。不要新建 plan.md / todo.md / TODO 之类的东西。
> Codex 每次会话开始必须读这个文件，结束必须更新它。
> **最后更新：2026-10-24**

---

## 明日（10/25 周日）读什么 —— 只读三样，共约 2.5 小时

| 顺序 | 读什么 | 读哪部分 | 时长 | 产出（必须落在 `notes/w1-reading.md`） |
|---|---|---|---|---|
| 1 | **[A4 Harness Engineering](https://arxiv.org/abs/2609.00006)** | §定义 + **七个子系统（每个的最小实现/最大实现）** + 结论与 13 条观察。**跳过 11 个系统的逐个剖析** | 60 min | 七个子系统清单，每个标注「我的作品里对应哪个文件」 |
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
| 当前周次 | **W1（10/26–11/01）** |
| 本周主题 | L0 语言 + L1 模型接口 |
| 项目阶段 | 冷启动，代码零行 |
| 截止倒计时 | 距 2027/3 暑期实习投递 ≈ **18 周** |

---

## 模块进度

状态定义：`未开始` → `进行中` → `能跑`（跑通一个真实任务）→ `已验证`（进入评测集且通过）

| 模块 | 文件 | 状态 | 备注 |
|---|---|---|---|
| LLM 统一封装 | `src/llm/client.py` | 未开始 | 要支持换模型 + 记账 + 重试 |
| Agent Loop | `src/agent/loop.py` | 未开始 | W1 的唯一目标 |
| 工具定义与注册 | `src/tools/` | 未开始 | W2–W3，20 个工具 |
| 上下文管理 | `src/context/` | 未开始 | W4–W5，预算 / 截断 / 摘要 |
| 记忆（FTS5） | `src/memory/` | 未开始 | W5，工作区 / 召回 / 归档 |
| 安全与权限 | `src/safety/` | 未开始 | W6，L0–L3 分级 |
| Go tool gateway | `gateway/` | 未开始 | W7 |
| trace 落盘 | `src/trace.py` | 未开始 | 每次工具调用写 JSONL |
| 评测集 | `eval/tasks.jsonl` | 未开始 | W8，目标 50 条 |
| 评测脚本 | `eval/run.py` | 未开始 | 终态断言 + 五指标 |
| README | `README.md` | 占位 | 结论由我自己写 |

---

## 关键数字（每完成一轮评测就更新，没有数字就是没有进展）

| 指标 | 当前 | 上一轮 | 备注 |
|---|---|---|---|
| 任务成功率 | — | — | |
| 平均步数 | — | — | |
| 平均 token / 任务 | — | — | |
| 单任务成本（元） | — | — | |
| p95 延迟（秒） | — | — | |
| 上下文峰值占用 | — | — | 占窗口百分比 |
| 工具调用错误率 | — | — | 分模型记录 |

---

## 本周卡点

> 一句话写清「我卡在什么现象上」，不是「我在学什么」。

- （空。今天开始填）

---

## 下一步（只写 3 件，按顺序，每件都要有验收标准）

1. **写 `src/llm/client.py` + `src/agent/loop.py`，让 agent 跑通一个任务**
   - 验收：终端打印出每一步的 `tool_calls` 和工具返回，最终输出一句话结论
   - 工具先写 2 个假的：`get_weather`、`control_ac`
   - 自己写，不叫 Codex 代写
2. **故意让工具报错，记录模型的反应**
   - 验收：`notes/w1-tool-error.md` 里有一条真实观察
3. **读 B2《Writing tools for agents》，把自己的工具 description 重写一遍**
   - 验收：对比前后两版 description，写出差在哪

---

## 变更日志（Codex 每轮追加一行）

| 日期 | 模块 | 一句话 |
|---|---|---|
| 2026-10-24 | 目录初始化 | 建立 AGENTS.md / PROGRESS.md / README 占位，代码未动 |

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
| M1 最小 loop 能跑 | 2026-11-01 | 一个任务端到端跑通 | ☐ |
| M2 工具层可用 | 2026-11-15 | 20 个工具 + 三模型错误率表 | ☐ |
| M3 长任务不爆 | 2026-11-29 | 100 轮不超窗口，token 有下降 | ☐ |
| M4 安全层完成 | 2026-12-06 | L0–L3 分级 + 注入防御演示 | ☐ |
| M5 Go 网关上线 | 2026-12-13 | `go test -race` 通过，Python 侧走 HTTP 调用 | ☐ |
| M6 评测闭环 | 2026-12-20 | 50 条评测集 + 成功率表 + trace 回放 | ☐ |
| M7 简历定稿 | 2027-01-15 | 一页，两个项目，全部有数字 | ☐ |
| M8 投递开始 | 2027-03-01 | 一周内投完四家 + 五家保底 | ☐ |