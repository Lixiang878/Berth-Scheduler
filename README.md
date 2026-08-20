# Berth-Scheduler

> **⚠️ 已归档（二合一）**：本仓库已并入 [SmartPort-MultiAgent](https://github.com/Lixiang878/smartport-multiagent)——
> HiGHS 精确解（`bap_milp_highs`）、文献基准算例（`utils/benchmarks`）与灵敏度分析（`utils/sensitivity`）
> 均在 SmartPort 中继续维护。本仓库仅作历史留档，不再更新。
>
> **⚠️ ARCHIVED — MERGED INTO [SmartPort-MultiAgent](https://github.com/Lixiang878/smartport-multiagent).**
> The HiGHS exact solver, literature benchmarks and sensitivity analysis now live there.
> Kept for history; no further updates.

[![CI](https://github.com/Lixiang878/Berth-Scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/Lixiang878/Berth-Scheduler/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

Berth allocation + quay-crane scheduling for container terminals:
MIP exact, adaptive genetic algorithm, FCFS baseline.

[English](#english) · [中文](#中文)

---

<a id="english"></a>
## English

I worked on berth scheduling as part of a port-logistics research project
at Dalian Maritime University. The problem: assign incoming vessels to
berths and quay cranes so that the total time ships spend in port is
minimised, respecting berth length, crane availability, and vessel
arrival times. This package reproduces that work as a self-contained bench
with three solvers that can be compared head-to-head on the same instance.

### Solvers

| method | approach | scale | use as |
|--------|----------|-------|--------|
| **MIP** | discrete-time binary program (scipy / HiGHS) | <= 8 vessels | ground truth |
| **GA** | adaptive permutation GA with crane assignment | 100+ vessels | production heuristic |
| **FCFS** | first-come-first-served greedy | any | baseline |

The GA adapts crossover and mutation rates from population diversity
(low diversity -> explore more; high diversity -> exploit). Crane counts
are optimised jointly with berth and start-time.

### Headline number

On a 20-vessel / 4-berth / 8-crane random instance (`seed=42`):

```
method     avg_wait   avg_port   makespan  feasible
FCFS           1.85      11.49      54.71      True
GA             0.17       5.43      49.96      True
```

GA cuts average in-port time by **53%** against the greedy baseline.

### Install & run

```bash
pip install -e .
berth-scheduler compare --vessels 20 --berths 4 --cranes 8 --seed 42
berth-scheduler gen --vessels 30 --berths 5 --cranes 10 --seed 0 --out inst.json
```

### Notes

* MIP uses a coarse discrete time grid (default 2 h) and fixes crane count
  at the vessel minimum -- it is an exact *formulation* but with these
  simplifications it is a lower-bound reference, not a full QCAP solve.
* GA runtime is O(pop * gen * n^2); a few seconds for n=20, under a minute
  for n=100.
* Vessel handling time scales inversely with assigned cranes
  (`base / n_crane`).

---

<a id="中文"></a>
## 中文

这部分工作来自大连海事大学的港航物流调度研究预研。问题：为到港船舶
分配泊位和岸桥，最小化总在港时间，同时满足泊位长度、岸桥总量和船舶
到达时间的约束。本包把该工作复现为一个自包含的基准，三种求解器可在
同一算例上逐方案对比。

### 求解器

| 方法 | 思路 | 规模 | 用途 |
|------|------|------|------|
| **MIP** | 离散时间 0-1 规划（scipy / HiGHS） | <= 8 船 | 对照基准 |
| **GA** | 自适应排列遗传算法 + 岸桥分配 | 100+ 船 | 工程启发式 |
| **FCFS** | 先到先服务贪心 | 任意 | 基线 |

GA 根据种群多样性自适应调整交叉/变异概率（多样性低时探索、高时利用），
岸桥数量与泊位、靠泊时间联合优化。

### 核心数据

20 船 / 4 泊位 / 8 岸桥随机算例（`seed=42`）：

```
method     avg_wait   avg_port   makespan  feasible
FCFS           1.85      11.49      54.71      True
GA             0.17       5.43      49.96      True
```

GA 较贪心基线降低平均在港时间 **53%**。

### 安装与运行

```bash
pip install -e .
berth-scheduler compare --vessels 20 --berths 4 --cranes 8 --seed 42
berth-scheduler gen --vessels 30 --berths 5 --cranes 10 --seed 0 --out inst.json
```

### 说明

* MIP 使用粗离散时间网格（默认 2 h）并固定岸桥数为船舶下限——是精确
  形式的简化，作为下界参考而非完整 QCAP 求解。
* GA 复杂度 O(pop * gen * n^2)：n=20 数秒，n=100 分钟级。
* 船舶装卸时间与分配岸桥数成反比（`base / n_crane`）。
