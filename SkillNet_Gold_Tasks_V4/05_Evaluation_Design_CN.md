# SkillNet 评价设计说明

版本：V4  
日期：2026-07-28

## 1. 评价输入

### Codex Prediction

Codex输出是否调用Skill、部门、Skill顺序、最终状态、阻断来源、路线选择和简要理由。

### Gold Standard

`02_Gold_Standard_21_V4.json`是评价唯一标准文件，包含：

- 46个Skill及所属部门的简单目录；
- 每题必要、可选和禁止Skill；
- 任务级强制偏序；
- 初始Skill状态；
- 任务级冲突和互斥规则；
- 正确最终状态、阻断来源和路线选择。

本版本不使用relations.json。Configuration C的图结构实现与评价器分离；评价器不会读取或运行Configuration C的图代码。

## 2. 为什么不比较完整序列完全相等

完整合法顺序可能不唯一。`canonical_sequence`只是一个可行示例；Python只检查`hard_order_constraints`中真正强制的先后关系。

例如必须满足A→C和B→C，但A、B之间没有强制顺序，则`A,B,C`和`B,A,C`都正确。

## 3. Required Order Accuracy

满足的强制顺序对数量 ÷ 全部强制顺序对数量。

- 初始已完成的前置Skill视为在预测路线之前；
- 顺序颠倒、前置缺失或后置缺失均视为该顺序对未满足；
- 必要Skill缺失还会同时降低Skill Recall并产生`MISSING_REQUIRED_SKILL`。

## 4. 主要指标

### Functional Success Rate

任务是否实质完成或被正确阻断。要求必要Skill、强制顺序、部门、状态和任务级约束均正确。

### Clean Success Rate

在Functional Success基础上，没有多余Skill、额外部门或重复Skill。

### Skill Precision / Recall / F1

评价Skill选择的完整性和简洁性；optional_skills不会降低Precision。

### Required Order Accuracy

评价任务级强制偏序，而非完整序列完全相等。

### Gold Constraint Violation Rate

出现任一任务级硬约束违反的任务比例，包括：

- 强制偏序未满足；
- 调用禁止Skill；
- 违反任务级冲突规则；
- 违反互斥路线；
- 重复调用初始已完成Skill；
- 阻断来源或路线选择错误。

### Department F1

比较预测部门和Gold必要部门。

### No-Tool Accuracy / Blocked-Flow Accuracy

分别评价不应调用企业Skill的任务，以及应正确停止的任务。

## 5. 删除Graph Validity Rate的原因

Graph Validity Rate需要独立的全局关系数据作为验证依据。当前实验决定让评价只依赖任务级Gold，因此删除该指标，不用其他重叠指标替代。

## 6. 失败分类

包括格式错误、错误触发/拒绝Skill、未知Skill、必要Skill缺失、多余Skill、顺序错误、禁止项、冲突、互斥、重复初始步骤、错误状态、错误阻断原因、错误路线选择、继续执行被阻断步骤、部门遗漏或冗余。

## 7. 评价步骤

1. 运行`validate-package`检查Gold内部一致性；
2. 对A、B、C分别保存固定JSON输出；
3. Python逐任务与Gold比较并计算指标；
4. 按Configuration和任务类别汇总；
5. 生成失败分类与人工复核队列；
6. 使用同一任务进行A/B/C配对比较。
