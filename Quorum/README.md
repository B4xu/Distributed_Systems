# 🧪 Lab: Quorum & Eventual Consistency Simulation (3 Points)

## 🎯 Objective

In this lab, you will simulate a distributed system with:

- Replicated nodes
- Quorum-based reads and writes
- Version tracking
- Delayed replication (eventual consistency)

---

## 🧠 Concepts Covered

- Quorum systems (`N`, `R`, `W`)
- Stale reads
- Versioning
- Eventual consistency

---

# 🧩 Task Breakdown

---

## 🔹 Task 1 — Replica Model (1 Point)

Create a `Replica` class with:

- `name`
- `value`
- `version`

Methods:
- `write(value, version)`
- `read()`
- `reset()`

---

## 🔹 Task 2 — Quorum Operations (1 Point)

Create a `DistributedSystem` class that:

Implements:

- `write(value, W)`
- `read(R)`
- `show_state()`

Requirements:

- Use **3 replicas**
- Randomly select replicas
- Increment version on each write
- Read must return the **latest version**

---

## 🔹 Task 3 — Eventual Consistency Experiment (1 Point)

Modify your system:

- Write to **only 1 replica first**
- Delay updates to other replicas

Simulate:

### Case 1:

W = 1, R = 1


### Case 2:

W = 2, R = 2


---

### For EACH case:

Print:

- replicas written to
- replicas read from
- responses (value + version)
- final chosen result
- whether result is:
  - ✅ Up-to-date
  - ❌ Stale

---

## 📤 Submission

Submit:

1. Your Python file
2. Short answers:

- Why do stale reads happen?
- How does delayed replication affect consistency?
- Why is `W=2, R=2` safer than `W=1, R=1`?

---

## 💡 Key Idea
Eventual consistency = delayed updates
Quorum = overlap between reads and writes
Together they control correctness vs speed

