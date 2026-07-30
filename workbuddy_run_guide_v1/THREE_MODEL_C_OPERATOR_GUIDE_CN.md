# WorkBuddy 三模型 E0/E1 C组（图结构）操作说明

本轮只运行 C 组：`E0-C-size46`、`E1-C-size10`、`E1-C-size30`，以及从
`E0-C-size46` 固定五题派生的 `E1-C-size46`。不运行 A/B 组。

这套实验可以在同一个 project 下开三个 WorkBuddy 窗口，但不能直接复用当前
`experiments/skillnet/run_condition.py`。那个 runner 固定调用 Codex CLI；即使
WorkBuddy 窗口选了 DeepSeek、GLM 或 Kimi，执行它得到的仍然是 Codex 结果。

正确结构是：WorkBuddy 窗口只负责编排，WorkBuddy/CodeBuddy CLI 每一道题启动一个
全新的非交互进程。每题还要有新的 UUID session 和新的空临时目录。

## 文件

- [Setup Prompt](./WorkBuddy_Setup_Prompt_E0_E1_C_v1_CN.txt)
- [Standard RUN Commands](./WorkBuddy_Standard_RUN_Commands_E0_E1_C_v1_CN.txt)

## 推荐流程

1. 先开一个非正式控制窗口，粘贴 Setup Prompt，使用
   `SETUP_MODE=COMMON_ADAPTER`。只创建一次 WorkBuddy adapter。
2. 审查 adapter，运行测试，把它提交并同步。三个正式窗口必须使用同一个 commit。
3. 在同一个 project 下新建三个独立 WorkBuddy 任务/窗口。
4. 每个窗口关闭 Auto Mode，关闭并清除 Memory，禁用 fallback、Skills、Expert、
   Connectors、Automations 和 MCP。
5. 每个窗口明确选择一个模型，并用 `SETUP_MODE=MODEL_PREFLIGHT` 完成本模型
   preflight 和 synthetic smoke。
6. 收到 READY 后，粘贴 Standard RUN Commands 中的正式 RUN 块。
7. 一个模型内部始终串行。三个窗口可以同时打开，但正式实验最好依次开始，以减少
   限流和共享负载造成的偏差。

| 窗口 | 显示名 | MODEL_ID | MODEL_SLUG | RUN_ID |
|---|---|---|---|---|
| 1 | DeepSeekV4-Pro | `deepseek-v4-pro` 仅为候选，需实测 | `deepseek_v4_pro` | `wb_deepseek_v4_pro_c_r01` |
| 2 | GLM5.2 | 从本机配置读取并实测，不猜 | `glm_5_2` | `wb_glm_5_2_c_r01` |
| 3 | Kimi-K3 | 从本机配置读取并实测，不猜 | `kimi_k3` | `wb_kimi_k3_c_r01` |

## 为什么必须先做公共 Setup

如果三个窗口同时修改同一个 adapter，会产生竞态：一个窗口可能在另一个窗口运行时
改代码或配置，三个模型就不再处于同一实验框架。公共 Setup 只做一次、提交后冻结；
三个模型窗口只运行各自 preflight 和正式实验。

建议输出根目录：

```text
experiments/skillnet_workbuddy/
  runs/
    deepseek_v4_pro/
    glm_5_2/
    kimi_k3/
  results/
    deepseek_v4_pro/
    glm_5_2/
    kimi_k3/
```

不要把 WorkBuddy 结果写入现有 Codex 的 `experiments/skillnet/runs/`，也不要让某个
模型读取另外两个模型或 Codex `run_01` / `run_02` 的结果。

## 界面和 CLI 要点

- WorkBuddy 的每个 task 有独立对话上下文，但“继续旧 task”会复用上下文；正式 child
  不能继续旧 task。
- Auto Mode 会自动选模型，正式实验必须关闭。
- Memory 可能把旧信息注入新 task，正式实验必须关闭并清理。
- 精确参数以组员机器上的 `codebuddy --help` 为准。若 CLI 不支持精确模型、新 session、
  非交互执行或可靠禁用 tools/MCP/fallback，Setup 必须停止，不能假装满足隔离要求。
- API key 只能保存在本机安全配置中，不能写入仓库、命令证据或结果。

如果组员坚持只用 WorkBuddy GUI、完全不用 CodeBuddy CLI，那么每一道题都要人工新建
一个全新 task，并给它只包含当前题和当前 Catalogue 的隔离工作区。一个 GUI 对话连续
回答多道正式题不符合实验隔离要求；无法证明隔离时应停止，而不是降低标准。

## 三个窗口是否同时跑

目录隔离能避免文件互相覆盖，但不能消除 API 限流、服务器负载和时间段差异。为了做
模型间公平比较，建议三个窗口都准备好后，按固定顺序分别跑完；如果必须并行，要记录
开始/结束时间、限流和 transport failure，并在展示中声明这一限制。

## 官方参考

- [WorkBuddy Quick Start](https://www.workbuddy.ai/docs/workbuddy/Quickstart)
- [Create Task](https://www.workbuddy.ai/docs/workbuddy/Create-Task)
- [Model Configuration](https://www.workbuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Model)
- [Permission Modes](https://www.workbuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes)
- [CodeBuddy CLI Reference](https://www.workbuddy.ai/docs/cli/reference)
- [WorkBuddy Memory（中文）](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Memory)
- [DeepSeek WorkBuddy Integration](https://api-docs.deepseek.com/quick_start/agent_integrations/workbuddy/)
