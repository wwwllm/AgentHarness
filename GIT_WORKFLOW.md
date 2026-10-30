# Git 开发常用命令与工程规范手册

> 适用于 `AgentHarness` 工程及后续团队开发。遵循工业界主流的 **Conventional Commits** 规范与分支工作流，兼顾 Mac & Windows 跨平台协作。

---

## 一、工业界 Git 规范

### 1.1 提交信息规范（Conventional Commits）

在大厂工程与开源项目中，Commit 记录是版本追踪、生成 Changelog 和 Code Review 的核心依据。禁止出现 `update`、`fix`、`改了一点代码` 这种无意义提交。

统一格式：
```text
<type>(<scope>): <subject>

[可选 body: 详细解释为什么改，解决了什么问题]
[可选 footer: 关联的 issue / PR 编号]
```

#### 常见 `type` 类型速查：
| 类型 | 说明 | 示例 |
| :--- | :--- | :--- |
| **`feat`** | 新增功能/特性 | `feat(loop): 实现基于 step_count 的最大步数熔断` |
| **`fix`** | 修复缺陷/Bug | `fix(gateway): 修复工具调用返回 JSON 解析失败问题` |
| **`docs`** | 仅修改文档/注释 | `docs: 更新 AGENTS.md 契约与学习记录` |
| **`refactor`** | 代码重构（不增加功能也不修复 bug） | `refactor(context): 将窗口滑动裁剪逻辑独立为函数` |
| **`test`** | 增加或修复测试用例 | `test(eval): 为车载空调温度控制工具补充边界测试` |
| **`perf`** | 性能优化 | `perf(retrieval): 优化 SQLite FTS5 查询前缀匹配性能` |
| **`chore`** | 构建过程或辅助工具变动（依赖/配置/CI） | `chore: 更新 .gitignore 补充 Mac 临时文件过滤` |

---

### 1.2 分支开发规范

* **`main`（主分支）**：保持随时可用、测试全过的稳定状态。禁止直接在 `main` 上开发未完成的功能。
* **`feature/<name>`（特性分支）**：开发新模块/新功能时从 `main` 切出，如 `feature/tool-gateway`、`feature/eval-dataset`。
* **`fix/<name>`（缺陷修复分支）**：修复已知 Bug，如 `fix/async-loop-leak`。

---

### 1.3 提交四项铁律

1. **原子化提交（Atomic Commits）**：一个 Commit 只做一件事。改动功能与格式化/排版不要混在同一个提交里。
2. **严禁提交编译与本地配置**：虚拟环境（`.venv/`）、二进制产物、IDE 个人配置、`.env` 严禁提交。
3. **提交前先过门禁**：在 `git commit` 前，本地必须先运行静态检查（如 `ruff`）和测试（`pytest`），保证不提交断裂代码。
4. **动工前必 `pull`，收工后必 `push`**：避免双端并行修改产生脏冲突。

---

## 二、双端必做配置（Mac & Windows）

防止因为换行符（CRLF / LF）不同导致跨平台时整篇文件被误判全改：

* **Windows 端执行一次：**
  ```bash
  git config --global core.autocrlf true
  ```
* **Mac 端执行一次：**
  ```bash
  git config --global core.autocrlf input
  ```

---

## 三、常用 Git 命令全集

### 3.1 日常开发循环

```bash
# 1. 查看当前改动状态（红字未暂存，绿字已暂存）
git status
git status -s                      # 紧凑单行输出

# 2. 差异查看（动了什么）
git diff                           # 查看工作区与暂存区的具体代码行差异
git diff --staged                  # 查看已暂存内容与上一次 commit 的差异

# 3. 暂存改动
git add <文件路径>                  # 推荐：按文件精确暂存
git add .                          # 暂存当前目录下所有改动

# 4. 提交
git commit -m "feat(scope): 描述"   # 标准单行提交
git commit                         # 调出编辑器撰写详细 commit message

# 5. 推送
git push origin <当前分支名>
```

---

### 3.2 分支与多任务管理

```bash
# 查看所有本地分支（* 代表当前所在分支）
git branch

# 基于当前分支新建并切换到新分支
git switch -c feature/eval-runner
# （老命令等价于：git checkout -b feature/eval-runner）

# 切换已有分支
git switch main
# （老命令等价于：git checkout main）

# 合并分支（先切回目标主分支）
git switch main
git merge feature/eval-runner

# 删除已合并完成的无用分支
git branch -d feature/eval-runner

# 强制删除未合并的分支（放弃开发）
git branch -D feature/eval-runner
```

---

### 3.3 紧急储藏（临时切去修 bug 或拉代码）

当手上正在写的代码还没写完、无法提交，但需要切分支或 `git pull` 时使用：

```bash
# 1. 储藏当前未提交的修改并清空工作区
git stash save "正在写提示词模板，未完"

# 2. 查看储藏列表
git stash list

# 3. 恢复最近一次储藏并从栈中删除
git stash pop

# 4. 仅恢复储藏但不删除
git stash apply stash@{0}

# 5. 清空全部储藏
git stash clear
```

---

### 3.4 撤销与救火指南

根据代码所处的生命周期，采取不同的撤回手段：

#### 场景 1：改乱了工作区文件，想彻底放弃本地未保存修改
```bash
git restore <文件名>                # 放弃单文件修改
git restore .                      # 放弃所有工作区修改（不可逆，慎用）
```

#### 场景 2：不小心 `git add .` 把不该加的文件暂存了
```bash
git restore --staged <文件名>       # 把文件从暂存区撤回工作区，文件内容不变
```

#### 场景 3：刚刚 commit 完，发现漏了一个文件或提交信息写错了
```bash
git add <漏掉的文件>
git commit --amend --no-edit       # 补入上一条提交，不修改提交信息
git commit --amend -m "新提交信息"   # 修改上一条提交信息
```

#### 场景 4：彻底撤销上一次已经 commit 的记录（回退版本）
```bash
git reset --soft HEAD~1            # 撤销提交，保留修改内容在【暂存区】（最推荐）
git reset --mixed HEAD~1           # 撤销提交，保留修改内容在【工作区】
git reset --hard HEAD~1            # 彻底抹去上一条提交及所有代码改动（危险操作）
```

---

### 3.5 远程同步与变基（Keep History Clean）

在将特性分支并入 `main` 前，保持线性整洁历史：

```bash
# 拉取远端更新并以变基方式合入本地（避免生成无意义的 Merge 节点）
git pull --rebase origin main

# 如果发生冲突：
# 1. 打开冲突文件，搜索并手动解决 <<<<<<< ======= >>>>>>>
# 2. 标记冲突已解决
git add <解决好的文件>
# 3. 继续推进变基
git rebase --continue
# （若中途想彻底放弃本次 rebase 回到原点）
git rebase --abort
```

---

### 3.6 历史溯源与排查

```bash
# 格式化单行查看最近提交记录
git log --oneline -n 10

# 绘制分支树形图（清晰直观）
git log --graph --oneline --decorate -n 15

# 追查某个文件某一行是谁写/改的（排查 bug 关键）
git blame <文件路径>

# 查看某次具体提交改了什么
git show <commit_id>
```
