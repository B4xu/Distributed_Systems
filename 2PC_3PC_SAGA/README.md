# Distributed Transactions Lab
## 2PC, 3PC, and Saga (Python Simulation)

---

## Overview

In this lab, you will build and demonstrate three distributed transaction protocols:

- **Two-Phase Commit (2PC)** — strong consistency, blocking issue
- **Three-Phase Commit (3PC)** — improved version of 2PC
- **Saga Pattern** — eventual consistency using compensation

All simulations run on one machine, using multiple Python processes communicating over TCP.

---

## Prerequisites

- **OS:** Arch Linux (or any Linux)
- **Python 3** installed

```bash
sudo pacman -S python
```

---

## Project Structure

Make sure all files are in one directory:

```
common_net.py

# 2PC
participant_2pc.py
coordinator_2pc.py

# 3PC
participant_3pc.py
coordinator_3pc.py

# SAGA
service_saga.py
orchestrator_saga.py
```

---

## Part 1 — Two-Phase Commit (2PC)

### Objective

- Understand the `prepare → commit` flow
- Demonstrate: Success, Abort, and the Blocking problem

### Step 1 — Start Participants

Open 3 terminals:

```bash
# Terminal 1
python participant_2pc.py --name P1 --port 5001 --vote YES

# Terminal 2
python participant_2pc.py --name P2 --port 5002 --vote YES

# Terminal 3
python participant_2pc.py --name P3 --port 5003 --vote YES
```

### Step 2 — Run Coordinator (SUCCESS)

Open a 4th terminal:

```bash
python coordinator_2pc.py \
  --txid tx100 \
  --value transfer100 \
  --participant P1:127.0.0.1:5001 \
  --participant P2:127.0.0.1:5002 \
  --participant P3:127.0.0.1:5003
```

**Expected Result:**
- All participants vote `YES`
- Coordinator sends `COMMIT`
- Transaction succeeds globally

### Step 3 — Abort Scenario

Restart participants, but make one vote `NO`:

```bash
python participant_2pc.py --name P2 --port 5002 --vote NO
```

Run the coordinator again.

**Expected Result:**
- One participant votes `NO`
- Coordinator sends `ABORT` to all

### Step 4 — Blocking Problem ⚠️

Run all participants with `YES`, then:

```bash
python coordinator_2pc.py \
  --txid tx101 \
  --value blocking-demo \
  --participant P1:127.0.0.1:5001 \
  --participant P2:127.0.0.1:5002 \
  --participant P3:127.0.0.1:5003 \
  --crash-after-yes
```

**Expected Result:**
- All participants enter `PREPARED`
- Coordinator crashes before `COMMIT`
- Participants are **blocked indefinitely**

### Key Learnings (2PC)

- Guarantees atomicity
- Has a **blocking problem**
- Coordinator is a **single point of failure**

---

## Part 2 — Three-Phase Commit (3PC)

### Objective

- Add an extra phase to reduce blocking
- Understand the three phases: `CAN_COMMIT → PRE_COMMIT → DO_COMMIT`

### Step 1 — Start Participants

Open 3 terminals:

```bash
python participant_3pc.py --name P1 --port 7001 --vote YES
python participant_3pc.py --name P2 --port 7002 --vote YES
python participant_3pc.py --name P3 --port 7003 --vote YES
```

### Step 2 — Run Coordinator (SUCCESS)

```bash
python coordinator_3pc.py \
  --txid tx3pc100 \
  --value value123 \
  --participant P1:127.0.0.1:7001 \
  --participant P2:127.0.0.1:7002 \
  --participant P3:127.0.0.1:7003
```

**Expected Flow:** `CAN_COMMIT → PRE_COMMIT → DO_COMMIT`

**Result:** All participants commit successfully

### Step 3 — Abort Scenario

Run one participant with `NO`:

```bash
python participant_3pc.py --name P2 --port 7002 --vote NO
```

**Expected Result:**
- Abort happens in `CAN_COMMIT` phase
- No partial commit

### Step 4 — Crash After PRE-COMMIT

```bash
python coordinator_3pc.py \
  --txid tx3pc101 \
  --value test \
  --participant P1:127.0.0.1:7001 \
  --participant P2:127.0.0.1:7002 \
  --participant P3:127.0.0.1:7003 \
  --crash-after-precommit
```

**Expected Result:**
- Participants reach `PRECOMMIT`
- Coordinator crashes
- System is **less likely to block** compared to 2PC

### Key Learnings (3PC)

- Adds an extra coordination step
- **Reduces blocking probability**
- Still not perfect in real-world distributed failures

---

## Part 3 — Saga Pattern

### Objective

- Replace distributed transactions with local transactions
- Handle failure via **compensation**

### Step 1 — Start Services

Open 3 terminals:

```bash
python service_saga.py --name Inventory --port 6001
python service_saga.py --name Payment  --port 6002
python service_saga.py --name Shipping --port 6003
```

### Step 2 — Run Orchestrator (SUCCESS)

```bash
python orchestrator_saga.py \
  --saga-id order500 \
  --service Inventory:127.0.0.1:6001:reserve:release \
  --service Payment:127.0.0.1:6002:charge:refund \
  --service Shipping:127.0.0.1:6003:ship:cancel
```

**Expected Flow:** `reserve → charge → ship → SUCCESS`

### Step 3 — Failure + Compensation

Restart Shipping with failure:

```bash
python service_saga.py --name Shipping --port 6003 --fail-action ship
```

Run the orchestrator again.

**Expected Flow:**
1. `reserve → charge → FAIL`
2. `refund → release` (compensation)

### Key Learnings (Saga)

- No global lock
- No blocking
- Uses **compensating transactions**
- Provides **eventual consistency**

---

## Final Comparison

| Feature         | 2PC        | 3PC                          | Saga          |
|-----------------|------------|------------------------------|---------------|
| Consistency     | Strong     | Stronger than 2PC (theoretical) | Eventual   |
| Blocking        | Yes        | Reduced                      | No            |
| Performance     | Slow       | Slower                       | Fast          |
| Fault tolerance | Low        | Medium                       | High          |
| Use case        | Databases  | Rare                         | Microservices |

---

## Cleanup

Stop all running processes:

```bash
pkill -f participant_2pc.py
pkill -f participant_3pc.py
pkill -f service_saga.py
```

---

## Lab Outcome

After completing this lab, you should understand:

- How distributed commits work
- Why 2PC blocks
- How 3PC improves coordination
- Why modern systems prefer **Saga** over 2PC/3PC