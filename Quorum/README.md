# 🧪 Lab: Quorum-Based Consistency (3 Tasks)

## 🎯 Objective

In this lab, you will build a simple simulation of a distributed system with 3 replicas and explore how quorum-based reads and writes affect consistency.

---

# 🧩 Task Breakdown

---

## 🔹 Task 1 — Replica Setup (1 Point)

### Goal
Create a basic replicated system.

### Requirements

- Create **3 replicas**:
  - `A`, `B`, `C`
- Each replica must store an **integer value**
- Initialize all values to `0`
- Print the current state of replicas

### Example Output
A: 0
B: 0
C: 0

---

## 🔹 Task 2 — Implement Read & Write (1 Point)

### Goal
Implement quorum-based operations.

### Requirements

### 1. `write(value, W)`
- Randomly select `W` replicas
- Update selected replicas with the given value
- Print:
  - value written
  - replicas updated

### Example
Read from ['B'] -> [0]

---

## 🔹 Task 3 — Run Experiments & Analyze (1 Point)

  ### Goal
  Test different quorum configurations and observe behavior.

---

### Case 1: Weak Quorum

W = 1, R = 1



- Perform a write
- Perform a read

---

### Case 2: Stronger Quorum
W = 2, R = 2


- Perform a write
- Perform a read

---

### For EACH case, print:

- Read result
- Whether result is:
  - ✅ Up-to-date
  - ❌ Stale
- Final state of all replicas
- Values of:
  - `N` (number of replicas)
  - `W`, `R`
  - `R + W`

---

### Check quorum rule:
R + W > N


Print:

- `"Quorum satisfied"` if true
- `"Quorum NOT satisfied"` if false

---

## 🧠 Expected Understanding

After completing this lab, you should understand:

- Weak quorum (`W=1, R=1`) can produce stale reads
- Stronger quorum (`W=2, R=2`) improves consistency
- Why overlapping reads and writes matters
- How quorum systems reduce inconsistency

---

## 📤 Submission

Submit:

- Your Python file
- A short explanation answering:

1. What happened in Case 1?
2. What happened in Case 2?
3. When did a stale read occur?
4. Was `R + W > N` satisfied in each case?

---

## ⭐ Key Idea
Weak quorum → faster but inconsistent
Strong quorum → slower but more consistent