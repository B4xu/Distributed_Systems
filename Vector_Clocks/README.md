# Vector Clock Simulation in Distributed Systems (Class Assignment)

This C++ project is designed as a hands-on class assignment with a clear 3-section structure: Concept, Implementation, and Evaluation. Each section includes objectives and concrete tasks that students can complete in one session.

---

## Section 1: Concept (Understanding Vector Clocks)

### Objective
Explain vector clocks and causality in distributed systems.

### Tasks
- Define:
  - **Node**: independent process in a distributed system
  - **Vector Clock**: N-element array that tracks logical time across N nodes
  - **Happened-before relation**: partial ordering of events
- State the rules in your own words:
  - Local event: `VC[i] += 1`
  - Send event: increment own clock and attach vector clock to message
  - Receive event: merge incoming vector clock with local, then increment local clock
- Write a short example (2-3 steps) that shows concurrent vs causal events.

---

## Section 2: Implementation (Run & Inspect the Code)

### Objective
Compile and run the vector clock simulation and observe behavior.

### Tasks
1. Compile the code:
   - `g++ -std=c++14 -pthread vector_clock.cpp -o vector_clock`
2. Run the simulation:
   - `./vector_clock`
3. Identify phases in output:
   - `MAP PHASE`, `SHUFFLE PHASE`, `REDUCE PHASE`
4. For one map-reduce message, verify:
   - Sender clock before send
   - Receiver merges and updates correctly
5. Record final vector clock values for nodes 0, 3, 6.

---

## Section 3: Evaluation (Assignment Questions)

### Objective
Demonstrate understanding through analysis and extension.

### Tasks
- Question 1: How does vector clock compare to Lamport clock when determining concurrency?
- Question 2: In this simulation, how does shuffle randomness (map node -> random reduce node) affect event ordering?
- Question 3: Propose one extension:
  - Add failure detection or retry for lost messages
  - Add another phase (e.g., “Finalize”) with additional local events
- Bonus coding exercise:
  - Change number of map nodes from 6 to 4 and reduce nodes from 3 to 2, then rerun and compare final VC outputs.

---

## Quick Reference
- Build: `g++ -std=c++14 -pthread vector_clock.cpp -o vector_clock`
- Run: `./vector_clock`

> This structured README is now a class-friendly, 3-section assignment: Concept, Implementation, Evaluation.</content>
<parameter name="filePath">/home/irakli/Desktop/Distributed_Systems/Vector_Clocks/README.md