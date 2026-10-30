# AgentHarness

<div align="center">

**面向车载座舱场景的轻量级、确定性、高安全性智能体架构（Agent Harness）**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C%2B%2B-17%20(No--Exception)-00599C?logo=c%2B%2B&logoColor=white)](https://en.cppreference.com/w/cpp/17)
[![Go](https://img.shields.io/badge/Go-1.22+-00ADD8?logo=go&logoColor=white)](https://go.dev/)
[![SQLite](https://img.shields.io/badge/Memory-SQLite%20FTS5-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/fts5.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 📌 项目概述

**AgentHarness** 是一个专为**车载智能座舱控制与智能驾驶仿真评测**打造的 Agent Harness 工程体系。

不同于传统仅停留在自然语言对话的 Chatbot，AgentHarness 直面智能座舱物理控制中的**硬安全边界（Safety Constraints）**、**状态强一致性（State Invariants）**与**不可逆物理操作风险**。项目采用 **Python 调度核心 + Go 工具网关 + C++ 车况状态机** 的混合架构，摒弃黑盒臃肿的通用 Agent 框架，完全手写确定性的调度控制流与权限拦截机制，并通过真实 C++ 物理世界模拟器的**终态断言（End-State Assertion）**实现闭环量化评测。

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
* 评测的判据不依赖大模型的自述或文本匹配，而是**直接读取物理模拟器的终态环境数据**进行严格断言。

---

## 🏛️ 系统架构

整个系统对齐行业 Harness Engineering 七大子系统标准，架构分层清晰，职责单一：

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
│   │ (Budget / FTS5 Mem) │ <─────────────────── │ (DeepSeek / OpenAI Wrapper)│   │
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
                                                  │     Go Tool Gateway       │
                                                  │  (并发安全 / 速率限制 / 鉴权) │
                                                  └─────────────┬─────────────┘
                                                                │ IPC / Line Protocol
                                                                ▼
                                                  ┌───────────────────────────┐
                                                  │    C++17 车况模拟器        │
                                                  │ (AUTOSAR 导向 / 离散步长推进) │
                                                  └───────────────────────────┘
```

### 核心子系统对应实现

| 子系统 (Subsystem) | 职责与技术选型 | 对应工程模块 |
|---|---|---|
| **Agent Loop** | 显式 `while` 状态机推进，管理执行轮次、预算阻断与结构化解析 | `src/agent/loop.py` |
| **LLM Integration** | 统一 API Client，封装计价、结构化返回校验与指数退避重试 | `src/llm/client.py` |
| **Tools & Actions** | 统一强契约工具对象（Schema + Handler 强绑定），结构化错误提示 | `src/tools/` |
| **Memory & Context** | 基于 Token 预算的滑动窗口截断，基于 **SQLite FTS5** 的工作区召回 | `src/context/`, `src/memory/` |
| **Safety & Permissions** | 声明式 L0–L3 权限控制矩阵，阻断越权与高危物理指令 | `src/safety/` |
| **Tool Gateway** | 高并发工具代理，解耦模型决策与底软执行，隔离故障传播 | `gateway/` (Go) |
| **Environment Sim** | 符合车规级约束的确定性物理模拟器，提供真实可信的断言靶标 | `sim/` (C++17) |

---

## 🛡️ 车载权限分级体系 (L0 ~ L3)

为杜绝大模型在行驶状态下的灾难性误操作，所有已注册工具均绑定严格的权限标签：

| 权限等级 | 风险定义 | 典型工具示例 | 执行策略 | 异常/防御机制 |
|:---:|---|---|---|---|
| **L0** | **只读查询**（无物理副作用） | `get_vehicle_status`<br>`search_poi`<br>`get_weather` | 直接执行 | 参数类型校验失败返回结构化修复提示 (`hint`) |
| **L1** | **低危可逆**（轻微影响舒适度） | `control_ac` (调温)<br>`play_media`<br>`set_reminder` | 参数白名单校验后直接执行 | 越界参数（如空调设为 -20℃）即时拦截并回灌纠错 |
| **L2** | **高危影响**（影响行车安全或不可逆） | `control_window` (车窗)<br>`navigate` (改变行车路线) | **阻断执行，触发二次确认** | 行驶速度 > 60 km/h 时禁止全开天窗；需用户显式 Affirm |
| **L3** | **绝对禁止**（危及人身物理安全） | `unlock_doors` (行驶中解锁)<br>`disable_adas` (关闭主被动安全) | **物理拦截，强制拒绝** | 记录安全审计告警日志，模型无权越权请求 |

---

## ⚖️ 关键工程决策与取舍 (Trade-offs)

> 💡 **“优秀的工程不是使用了多少最前沿的库，而是在明确的约束下做出了最合理的取舍。”**

| 架构选择 | 对比弃选 | 核心理由 (Why) | 付出代价 (Trade-off) |
|---|---|---|---|
| **手写 Async Loop** | LangChain / AutoGen | 保证控制流、重试边界和上下文截断绝对透明，避免黑盒抽象泄漏与死循环失控 | 需自行编写报文解析、生命周期事件管理与状态调度逻辑 |
| **C++17 + `std::optional` / 错误码** | C++23 / 抛出 C++ 异常 | 遵循 AUTOSAR C++14 与 MISRA 车规规范，车端编译环境普遍落后且严控异常安全开销 (`-fno-exceptions`) | 无法使用最新的 C++23 语法糖（如 `std::expected` / `<ranges>`），错误码需层层显式传递 |
| **SQLite FTS5 全文检索** | 专用向量数据库 (Milvus/Chroma) | 智能座舱本地算力宝贵，FTS5 零外部依赖、极低资源开销、匹配逻辑 100% 具备确定性与可解释性 | 缺乏对泛化长尾语义的模糊向量相似度召回能力 |
| **真实 C++ 模拟器终态断言** | 字符串/正则匹配判断 | 杜绝模型“自述已完成、实际状态未改变”的静默评测穿透，以物理环境真实状态作为唯一判据 | 需额外实现跨进程 IPC 行协议通信机制，测试夹具搭建成本较高 |
| **单文件约束 ≤ 150 行** | 宽泛的单文件规模 | 强制模块解耦与职责隔离，杜绝巨石文件；代码天然契合单元测试与代码评审 | 文件数量增多，需严格约定命名规范与包组织层级 |

---

## 📊 评测基准与五维量化指标

评测模块（`eval/`）内建 50+ 条覆盖**正常控制、多意图复合、越界纠错、跨步重试及高危拦截**的复杂任务集（`eval/tasks.jsonl`）。

所有评测均在每次代码变更后自动化重跑，输出五维核心指标对比：

```text
======================= AgentHarness Evaluation Benchmark =======================
  [1] 任务成功率 (Task Success Rate)   :  100% (终态物理断言为准)
  [2] 平均交互步数 (Avg Steps/Task)     :  3.00 步
  [3] 单任务 Token 消耗 (Avg Tokens)   :  2,269 (Prompt: 2,152 | Completion: 117)
  [4] 单任务 API 成本 (Cost per Task)  :  ¥0.00524 (DeepSeek-V3 计价口径)
  [5] 端到端 p95 延迟 (p95 Latency)    :  3.63 s
=================================================================================
```

---

## 📂 仓库目录规范

```text
AgentHarness/
├── AGENTS.md                  # 工程行为契约、编码规范与开发约束（不可违反）
├── PROGRESS.md                # 唯一开发进度事实来源（记录每日推进与关键指标）
├── README.md                  # 本文件（对外技术展示与架构总览）
├── src/                       # Python Agent 核心实现
│   ├── agent/                 # 核心调度循环 (loop.py)
│   ├── llm/                   # 统一 LLM Client Wrapper (client.py)
│   ├── tools/                 # 结构化工具注册与 Handler 实现
│   ├── context/               # 上下文预算管理与截断策略
│   ├── memory/                # SQLite FTS5 本地持久化工作区
│   ├── safety/                # L0~L3 权限拦截器与规则过滤
│   └── trace.py               # 结构化 JSONL 追踪埋点落盘
├── sim/                       # C++17 车况模拟器
│   ├── include/               # 车辆状态机头文件
│   ├── src/                   # 物理状态演化与行协议解析实现
│   └── CMakeLists.txt         # 严格编译配置 (-Wall -Wextra -O2 -std=c++17)
├── gateway/                   # Go Tool Gateway
│   ├── cmd/                   # 网关启动入口
│   └── pkg/                   # 鉴权、速率控制与通信管道
├── eval/                      # 自动化评测体系
│   ├── tasks.jsonl            # 评测用例集（终态断言定义）
│   └── run.py                 # 评测执行入口与指标聚合脚本
├── traces/                    # 运行时执行轨迹（.gitignore 忽略）
└── notes/                     # 架构演化实验笔记与参考实现
```

---

## 🚀 快速开始

### 1. 环境准备
* **Python**: 3.12+ (推荐使用 `uv` 或 `venv`)
* **C++ Compiler**: GCC 9+ / Clang 11+ (支持 C++17)
* **CMake**: 3.20+
* **Go**: 1.22+ (可选，工具网关)

### 2. 克隆与依赖安装
```bash
git clone https://github.com/wwwllm/AgentHarness.git
cd AgentHarness

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows 用户: .venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
```

### 3. 配置 API Key
在项目根目录创建 `.env` 文件（或配置环境变量）：
```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 4. 编译 C++ 模拟器
```bash
cd sim
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
cd ..
```

### 5. 运行最小 Agent Loop
```bash
# 运行单次任务演示（例如：座舱温度调节与天气联动）
python src/agent/loop.py
```

### 6. 执行端到端评测
```bash
# 运行评测套件并输出五维量化指标
python eval/run.py --tasks eval/tasks.jsonl
```

---

## 🗺️ 里程碑路线图 (Roadmap)

- [x] **M1: 最小 Loop 端到端验证** — 跑通 Python 同步 Loop 与 DeepSeek 真实工具调用链路
- [ ] **M2: 工具集体系建设** — 完成 20+ 个座舱领域工具标准化注册与三模型错误率横评
- [ ] **M3: 长程上下文抗击穿** — 引入 Token 预算截断与滑动窗口，支撑 100 轮多轮对话不溢出
- [ ] **M4: 车规级安全防御层** — 落地 L0~L3 权限过滤矩阵与 Prompt 越权注入拦截
- [ ] **M5: 高可用 Go 网关** — 上线 Go 工具代理，完成 `go test -race` 高并发安全验证
- [ ] **M6: 终态断言评测闭环** — 接入 50 条复杂多意图评测集与 JSONL 轨迹全量回放
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
