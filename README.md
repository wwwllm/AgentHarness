# AgentHarness

<div align="center">

**面向车载座舱场景的轻量级、确定性、高安全性智能体架构（Agent Harness）**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C%2B%2B-17%20(No--Exception)-00599C?logo=c%2B%2B&logoColor=white)](https://en.cppreference.com/w/cpp/17)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 📌 项目概述

**项目进行中：当前仅 P1 最小 Loop 跑通 1 条真实任务，`src/agent/loop.py` 为 136 行；B MVP 的其余模块尚未完成，完整评测未运行。** 当前处于 P2a 观测层，消息归一化进行中，统一 wrapper、trace、模拟器、四工具与权限、评测闭环均待实现。

**AgentHarness** 是一个专为**车载智能座舱控制与智能驾驶仿真评测**打造的 Agent Harness 工程体系。

不同于传统仅停留在自然语言对话的 Chatbot，AgentHarness 直面智能座舱物理控制中的**硬安全边界（Safety Constraints）**、**状态强一致性（State Invariants）**与**不可逆物理操作风险**。B MVP 计划采用 **Python 调度核心 + C++17 车况状态机** 的架构，摒弃黑盒臃肿的通用 Agent 框架，完全手写确定性的调度控制流与权限拦截机制，并计划通过 C++ 模拟器的**终态断言 + 过程断言**实现闭环量化评测。

当前 B MVP 范围为 **4 个工具（状态查询 / 空调 / 车窗 / 导航）、单模型、20 条评测（8 普通 + 8 安全边界 + 4 强任务），每条跑 3 次**。Go 网关、并发、SSE、FTS5 记忆和三模型对比均不在 MVP 内；上下文只留硬上限，不做截断/摘要。完整工程细则见 [PROGRESS.md「B MVP 范围与工程细则」](PROGRESS.md#b-mvp-范围与工程细则)。

---

## 💡 为什么做 AgentHarness？

### 1. 座舱车控的硬物理安全边界
在车载座舱环境中，Agent 的动作会直接映射到物理执行机构（车窗升降、空调开闭、行车中车门锁止、辅助驾驶开关）。
* **不能仅靠 Prompt 防御**：大模型本质存在不可预测的幻觉与结构化漏参，绝不能让模型直连执行机构。
* **分级安全治理**：必须建立确定性的拦截管道，将指令严格划分为 L0（只读）至 L3（绝对禁止），并在关键操作（如高速行驶中开窗）触发确定性的二次确认机制。

### 2. 为什么不用 LangChain / AutoGen 等通用框架？
根据对业界 11 个生产级 Agent 系统的架构调研（参考 [*arXiv:2609.00006: Harness Engineering*](https://arxiv.org/abs/2609.00006)）：**生产级系统几乎无一依赖通用 Agent 框架，全部采用手写 Async Loop**。
* **过度封装**：通用框架隐藏了状态推进、上下文裁剪、重试机制和结构化回灌的关键时序，一旦出现死循环或上下文击穿，排查极其困难。
* **状态黑盒**：车控需要毫秒级可控的 Token 预算管理与结构化 Trace 落盘，手写轻量 Harness 才能实现极致的确定性与工程可解释性。

### 3. 为什么真对象必须是 C++ 状态机？
如果 Agent 执行工具只是修改 Python 内存中的一个 `dict`，评测断言本质只是“自欺欺人”的局部变量检查。
* AgentHarness 将所有车辆硬件状态收敛至独立的 **C++ 车况模拟器（`vehicle_sim`）**，模拟车速、风阻、内外温度、门窗开度与物理能耗。
* 评测的判据不依赖大模型的自述或文本匹配，而是**读取模拟器终态数据与模拟器侧过程证据**，分别执行终态断言与过程断言；未授权写入 0 不能仅由终态推出。

---

## 🏛️ 系统架构

以下为 B MVP 目标架构（待实现；当前仅最小 Loop 跑通）：

```text
                      ┌──────────────────────────────────────┐
                      │          用户指令 / 座舱语音输入          │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Core Agent Loop (Python 3.12)                          │
│                                                                                 │
│   ┌─────────────────────┐   Prompt + Context   ┌────────────────────────────┐   │
│   │   Context Manager   │ ───────────────────> │         LLM Client         │   │
│   │ (Hard Limits Only)  │ <─────────────────── │ (Single Model Wrapper)     │   │
│   └─────────────────────┘    Tool Calls JSON   └────────────────────────────┘   │
│              │                                                │                 │
│              ▼                                                ▼                 │
│   ┌─────────────────────┐                       ┌───────────────────────────┐   │
│   │ JSONL Trace System  │                       │ Safety & Permission Guard │   │
│   │ (Latency/Cost/Step) │                       │  (L0 ~ L3 权限分级拦截器)   │   │
│   └─────────────────────┘                       └─────────────┬─────────────┘   │
└───────────────────────────────────────────────────────────────┼─────────────────┘
                                                                │ Safe Actions
                                                                ▼
                                                  ┌───────────────────────────┐
                                                  │    Python Sim Bridge      │
                                                  │   (stdin/stdout 行协议)     │
                                                  └─────────────┬─────────────┘
                                                                │ IPC / Line Protocol
                                                                ▼
                                                  ┌───────────────────────────┐
                                                  │    C++17 车况模拟器        │
                                                  │ (AUTOSAR 导向 / 离散步长推进) │
                                                  └───────────────────────────┘
```

模拟器按每次评测运行新建进程，结束后终止并回收；当前目标只验收串行隔离。

### 核心子系统对应实现

下表为目标职责与模块路径：仅 Loop 已跑通，其余均待实现。

| 子系统 (Subsystem) | 职责与技术选型 | 对应工程模块 |
|---|---|---|
| **Agent Loop** | 显式 `while` 状态机推进，管理执行轮次、预算阻断与结构化解析 | `src/agent/loop.py` |
| **LLM Integration** | 统一 API Client，封装计价、结构化返回校验与指数退避重试 | `src/llm/client.py` |
| **Tools & Actions** | 统一强契约工具对象（Schema + Handler 强绑定），结构化错误提示 | `src/tools/` |
| **Context Limits** | 只保留上下文硬上限；MVP 不做记忆、截断/摘要 | `src/context/` |
| **Safety & Permissions** | 声明式 L0–L3 权限控制矩阵，阻断越权与高危物理指令 | `src/safety/` |
| **Simulator Bridge** | stdin/stdout 行协议通信，每次运行新建模拟器进程并在结束后回收 | `src/sim_bridge.py` |
| **Environment Sim** | 车辆状态机，提供终态与过程断言证据；具体约束来源待补 | `sim/` (C++17) |

---

## 🛡️ 车载权限分级体系 (L0 ~ L3)

以下为 B MVP 待实现的项目自定 L0–L3 权限策略，不代表车规原文；仅注册状态查询、空调、车窗、导航四个工具。L3 示例为应拒绝的请求，不新增可执行工具：

| 权限等级 | 风险定义 | 典型工具示例 | 执行策略 | 异常/防御机制 |
|:---:|---|---|---|---|
| **L0** | **只读查询**（无物理副作用） | `get_vehicle_status`（状态查询） | 直接执行 | 参数类型校验失败返回结构化修复提示 (`hint`) |
| **L1** | **低危可逆**（轻微影响舒适度） | `control_ac`（调温） | 参数白名单校验后直接执行 | 越界参数即时拦截并回灌纠错；具体温度范围来源待补 |
| **L2** | **高危影响**（影响行车安全或不可逆） | `control_window`（行驶中车窗操作）<br>`navigate`（改变行车路线） | **阻断执行，触发二次确认** | 需用户显式确认；车速与车窗开度的具体数值限制待提供依据 |
| **L3** | **绝对禁止**（危及人身物理安全） | 行驶中解锁车门 / 关闭安全系统 / 未知目的地请求（均拒绝，不注册为额外工具） | **物理拦截，强制拒绝** | 记录安全审计告警日志，模型无权越权请求 |

---

## ⚖️ 关键工程决策与取舍 (Trade-offs)

> 💡 **“优秀的工程不是使用了多少最前沿的库，而是在明确的约束下做出了最合理的取舍。”**
>
> 范围提示：下表保留我原有的技术判断，尚未同步当前范围。其中 FTS5 属于 MVP 之后；MVP 不做上下文截断，评测采用终态断言 + 过程断言。表内相关论证待我自行修订，不代表当前已实现能力。

| 架构选择 | 对比弃选 | 核心理由 (Why) | 付出代价 (Trade-off) |
|---|---|---|---|
| **手写 Async Loop** | LangChain / AutoGen | 保证控制流、重试边界和上下文截断绝对透明，避免黑盒抽象泄漏与死循环失控 | 需自行编写报文解析、生命周期事件管理与状态调度逻辑 |
| **C++17 + `std::optional` / 错误码** | C++23 / 抛出 C++ 异常 | 遵循 AUTOSAR C++14 与 MISRA 车规规范，车端编译环境普遍落后且严控异常安全开销 (`-fno-exceptions`) | 无法使用最新的 C++23 语法糖（如 `std::expected` / `<ranges>`），错误码需层层显式传递 |
| **SQLite FTS5 全文检索** | 专用向量数据库 (Milvus/Chroma) | 智能座舱本地算力宝贵，FTS5 零外部依赖、极低资源开销、匹配逻辑 100% 具备确定性与可解释性 | 缺乏对泛化长尾语义的模糊向量相似度召回能力 |
| **真实 C++ 模拟器终态断言** | 字符串/正则匹配判断 | 杜绝模型“自述已完成、实际状态未改变”的静默评测穿透，以物理环境真实状态作为唯一判据 | 需额外实现跨进程 IPC 行协议通信机制，测试夹具搭建成本较高 |
| **单文件约束 ≤ 150 行** | 宽泛的单文件规模 | 强制模块解耦与职责隔离，杜绝巨石文件；代码天然契合单元测试与代码评审 | 文件数量增多，需严格约定命名规范与包组织层级 |

---

## 📊 评测基准与五维量化指标

评测模块（`eval/`）待实现，目标任务集（`eval/tasks.jsonl`）为 **20 条：8 普通 + 8 安全边界 + 4 强任务**，使用**单模型**，每条运行 3 次，共 60 次。强任务覆盖多意图、3 步以上、失败重试与 L2 确认。

判定采用**终态断言 + 过程断言**：读取模拟器终态，并核查模拟器侧每次写入的来源、授权状态、实际执行与状态变化，关联上游权限决策及写后读回证据。即使先违规再恢复终态也必须检出；证据缺失须标为未知，不能宣称未授权写入为 0。

报告同时给出总成功数 **x/60** 和三组结果：**普通 x/24、安全边界 x/24、强任务 x/12**，以及逐任务结果、未授权写入数和失败分类。**8+8 全过就是 48/60，强任务仍可能全挂**，因此总成功数不能代替三组报告。48/60 是项目自拟门槛，另外还要求确定性测试全过、未授权写入 0、失败都有 trace 并完成归类。

五维指标为**成功率、平均步数、平均 token、单任务成本、端到端 p95 延迟**，当前完整评测数据均待采集。固定 60 次中的失败也计入成功率分母和指标汇总；缺失值单独报告缺失数与有效样本数，不填 0。步数按模型请求计，重试计步；token/成本累计所有请求，p95 按最近秩法计算。每次运行计时包含模拟器启动、模型等待、工具与重试、双断言及进程回收。

仅修改工具描述、固定其余条件的前后对比也待实现，前后各 60 次，保留原始结果与 trace；模型输出只报告重复次数与波动，不保证复跑成功数相同。完整口径见 [PROGRESS.md](PROGRESS.md#阶段唯一的学习单位)。

---

## 📂 仓库目录规范

以下为 B MVP 目标目录示意，包含待实现路径，不表示文件已齐备；当前进度以 [PROGRESS.md](PROGRESS.md#模块进度) 为准。

```text
AgentHarness/
├── AGENTS.md                  # 工程行为契约、编码规范与开发约束（不可违反）
├── PROGRESS.md                # 唯一工程范围、验收与进度事实来源
├── README.md                  # 本文件（对外技术展示与架构总览）
├── src/                       # Python Agent 核心实现
│   ├── agent/                 # 核心调度循环 (loop.py)
│   ├── llm/                   # 统一 LLM Client Wrapper (client.py)
│   ├── tools/                 # 结构化工具注册与 Handler 实现
│   ├── context/               # 上下文硬上限（不做截断/摘要）
│   ├── safety/                # L0~L3 权限拦截器与规则过滤
│   ├── sim_bridge.py          # 模拟器通信与进程回收
│   └── trace.py               # 结构化 JSONL 追踪埋点落盘
├── sim/                       # C++17 车况模拟器
│   ├── include/               # 车辆状态机头文件
│   ├── src/                   # 物理状态演化与行协议解析实现
│   └── CMakeLists.txt         # 严格编译配置 (-Wall -Wextra -O2 -std=c++17)
├── eval/                      # 自动化评测体系
│   ├── tasks.jsonl            # 20 条评测用例与终态/过程断言规则
│   └── run.py                 # 评测执行入口与指标聚合脚本
├── traces/                    # 运行时执行轨迹（.gitignore 忽略）
└── notes/                     # 架构演化实验笔记与参考实现
```

---

## 🚀 快速开始

**以下保留拟定复现命令，尚未完成干净环境实跑，不能据此直接运行完整 B MVP。** 依赖声明、模拟器构建、评测入口与报告产物均待实现；最小 Loop 已有 P1 真 API 运行记录，但不代表以下整套流程已验证。

### 1. 环境准备
* **Python**: 3.12+ (推荐使用 `uv` 或 `venv`)
* **C++ Compiler**: GCC 9+ / Clang 11+ (支持 C++17)
* **CMake**: 3.20+
* **Go**: MVP 不需要；工具网关为 MVP 之后的规划

### 2. 克隆与依赖安装
```bash
git clone https://github.com/wwwllm/AgentHarness.git
cd AgentHarness

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows 用户: .venv\Scripts\activate

# 待实现：requirements.txt 依赖声明及干净环境安装验证
pip install -r requirements.txt
```

### 3. 配置 API Key
当前 Loop 读取进程环境变量，未实现自动加载 `.env`；请配置环境变量（密钥不入库）：
```bash
export DEEPSEEK_API_KEY=your_deepseek_api_key_here
export DEEPSEEK_API_URL=https://api.deepseek.com
```

### 4. 编译 C++ 模拟器
待实现：模拟器源码、CMake 配置与构建验证；以下为预留命令。
```bash
cd sim
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
cd ..
```

### 5. 运行最小 Agent Loop
现有入口仅为 P1 演示，含历史内联工具与 Python 内存状态；B MVP 四工具、C++ 桥接、权限与双断言接入待实现。
```bash
# 运行现有 P1 演示（不代表 B MVP 四工具已实现）
python src/agent/loop.py
```

### 6. 执行端到端评测
待实现：任务集、评测 CLI 与报告产物；以下旧入口仅作预留，最终参数以实现并验证后的入口为准。拟定产物包括 `manifest.json`、`runs.jsonl`、`trace.jsonl`、`sim_audit.jsonl`、`report.json` 和前后对比的 `comparison.json`，当前均未生成；完整约定见 [PROGRESS.md「复现交付」](PROGRESS.md#复现交付)。
```bash
# 待实现：运行 20 条 × 3 次评测，输出三组结果与五维指标
python eval/run.py --tasks eval/tasks.jsonl
```

---

## 🗺️ 里程碑路线图 (Roadmap)

- [x] **M1: 最小 Loop 端到端验证** — 跑通 Python 同步 Loop 与 DeepSeek 真实工具调用链路
- [ ] **M2: 工具集体系建设** — 完成状态查询 / 空调 / 车窗 / 导航 4 工具注册；MVP 使用单模型，扩充工具与三模型对比留到 MVP 之后
- [ ] **M3: 上下文硬上限** — MVP 只保留硬上限；截断/摘要、滑动窗口与 FTS5 记忆留到 MVP 之后
- [ ] **M4: 车规级安全防御层** — 落地 L0~L3 权限过滤矩阵与 Prompt 越权注入拦截
- [ ] **M5: 高可用 Go 网关（MVP 之后）** — 上线 Go 工具代理，完成 `go test -race` 高并发安全验证
- [ ] **M6: 终态与过程断言评测闭环** — 接入 20 条任务，每条跑 3 次，输出总分、三组报告、五指标、失败分类与 JSONL 轨迹
- [ ] **M7: 生产化工程交付** — 全链路文档、基准评测报告与技术选型总结定稿

---

## 📚 参考文献与理论依据

1. **Harness Engineering (arXiv:2609.00006)**: *The Emerging Paradigm of Autonomous Agent Runtimes*
2. **Anthropic Engineering Guides**:
   - [Writing Tools for Agents: Principles and Best Practices](https://www.anthropic.com/engineering/writing-tools-for-agents)
   - [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
3. **AUTOSAR / MISRA C++**:
   - *Guidelines for the use of the C++14 language in critical and safety-related systems*

---

<div align="center">
<sub>Progress tracked in <a href="PROGRESS.md">PROGRESS.md</a> · Agent contract defined in <a href="AGENTS.md">AGENTS.md</a></sub>
</div>
