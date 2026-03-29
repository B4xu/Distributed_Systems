# Vector Clock Simulation in Distributed Systems

This C++ program simulates a distributed system using vector clocks to track causality and ordering of events across multiple nodes. It models a simplified MapReduce-like workflow where map nodes process data, shuffle results to reduce nodes, and reduce nodes perform final aggregation.

## Overview

In distributed systems, ensuring the correct ordering of events across different processes is crucial. Vector clocks provide a way to determine causality without relying on physical clocks, which may be unsynchronized.

### Key Concepts

- **Nodes**: Represent independent processes in a distributed system
- **Vector Clocks**: Arrays that track the logical time of events across all nodes
- **Events**: Local computations or message exchanges between nodes

## How It Works

The simulation consists of three phases:

1. **Map Phase**: Map nodes (0-5) perform local events, simulating data processing
2. **Shuffle Phase**: Map nodes send their results to randomly selected reduce nodes (6-8) via asynchronous message passing
3. **Reduce Phase**: Reduce nodes process received data and perform additional local events

Each node runs in its own thread, communicating through thread-safe message queues to simulate real distributed communication with network delays.

## Mathematical Explanation

### Vector Clock Rules

A vector clock VC is an array of size N (number of nodes), where VC[i] represents the logical clock value for node i.

**Local Event Rule:**
```
VC[i] = VC[i] + 1
```

**Send Message Rule:**
```
VC[i] = VC[i] + 1
Send (VC, message) to receiver j
```

**Receive Message Rule:**
```
For each k: VC[k] = max(VC[k], received_VC[k])
VC[i] = VC[i] + 1
```

### Causality

If VC1 ≤ VC2 (component-wise), then all events represented by VC1 happened before those by VC2. If neither VC1 ≤ VC2 nor VC2 ≤ VC1, the events are concurrent.

## Building and Running

### Prerequisites
- C++ compiler with C++14 support (e.g., g++ 5+)
- POSIX threads support

### Compilation
```bash
g++ -std=c++14 -pthread vector_clock.cpp -o vector_clock
```

### Execution
```bash
./vector_clock
```

The program will output the phases of execution, message sends/receives, and final vector clock states for all nodes.

## Sample Output Explanation

```
=== MAP PHASE ===
Map node 0 performs 2 local events
...
=== SHUFFLE PHASE ===
[SEND shuffle] Node 0 -> Node 6
[RECV] Node 6 received from Node 0
...
=== REDUCE PHASE ===
Reduce node 6 performs 3 local events
...
=== FINAL VECTOR CLOCKS ===
Node 0: 3 0 0 0 0 0 0 0 0 0
Node 6: 1 0 0 0 0 0 4 0 0 0
```

- Node 0 incremented its clock to 3 (initial + 2 events + 1 send)
- Node 6 received Node 0's clock (1), merged it, and incremented to 4 (1 + 3 events)

## Extensions

This simulation can be extended with:
- Fault tolerance (node failures)
- More complex communication patterns
- Real network protocols (TCP/UDP)
- Performance metrics and benchmarking

## References

- Lamport, L. (1978). Time, clocks, and the ordering of events in a distributed system.
- Fidge, C. J. (1988). Timestamps in message-passing systems that preserve the partial ordering.</content>
<parameter name="filePath">/home/irakli/Desktop/Distributed_Systems/Vector_Clocks/README.md