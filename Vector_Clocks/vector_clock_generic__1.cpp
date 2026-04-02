#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <thread>
#include <sstream>
#include <iomanip>

using namespace std;

string get_timestamp() {
    auto now = chrono::system_clock::now();
    auto time_t = chrono::system_clock::to_time_t(now);
    auto ms = chrono::duration_cast<chrono::milliseconds>(now.time_since_epoch()) % 1000;
    stringstream ss;
    ss << put_time(localtime(&time_t), "%H:%M:%S") << "." << setfill('0') << setw(3) << ms.count();
    return ss.str();
}

struct VectorNode {
    int id;
    vector<int> clock;

    VectorNode(int id, int total) : id(id), clock(total, 0) {}

    void local_event() {
        clock[id]++;
    }

    void send(VectorNode &other) {
        clock[id]++;
        other.receive(clock);
    }

    void receive(const vector<int> &sender_clock) {
        for (size_t i = 0; i < clock.size(); i++) {
            clock[i] = max(clock[i], sender_clock[i]);
        }
        clock[id]++;
    }

    void print() const {
        cout << "Node " << id << ": [";
        for (size_t i = 0; i < clock.size(); i++) {
            cout << clock[i] << (i + 1 < clock.size() ? ", " : "");
        }
        cout << "]\n";
    }
};

struct LamportNode {
    int id;
    int clock;

    LamportNode(int id) : id(id), clock(0) {}

    void local_event() {
        clock++;
    }

    int send() {
        clock++;
        return clock;
    }

    void receive(int other_clock) {
        clock = max(clock, other_clock) + 1;
    }

    void print() const {
        cout << "Node " << id << ": " << clock << "\n";
    }
};

int main(int argc, char *argv[]) {
    int num_nodes = 6;
    int steps = 30;
    int send_chance = 40; // percentage
    string mode = "vector";
    mt19937 rng((unsigned)chrono::high_resolution_clock::now().time_since_epoch().count());

    for (int i = 1; i < argc; i++) {
        string arg = argv[i];
        try {
            if (arg.rfind("--mode=", 0) == 0) {
                mode = arg.substr(7);
            } else if (arg.rfind("--nodes=", 0) == 0) {
                string value = arg.substr(8);
                if (value.empty()) throw invalid_argument("--nodes value missing");
                num_nodes = stoi(value);
            } else if (arg.rfind("--steps=", 0) == 0) {
                string value = arg.substr(8);
                if (value.empty()) throw invalid_argument("--steps value missing");
                steps = stoi(value);
            } else if (arg.rfind("--send-chance=", 0) == 0) {
                string value = arg.substr(14);
                if (value.empty()) throw invalid_argument("--send-chance value missing");
                send_chance = stoi(value);
            } else if (arg.rfind("--seed=", 0) == 0) {
                string value = arg.substr(7);
                if (value.empty()) throw invalid_argument("--seed value missing");
                unsigned seed = static_cast<unsigned>(stoul(value));
                rng.seed(seed);
            } else {
                cerr << "Warning: unknown argument ignored: " << arg << "\n";
            }
        } catch (const exception &e) {
            cerr << "Error parsing argument '" << arg << "': " << e.what() << "\n";
            return 1;
        }
    }

    if (num_nodes < 2) {
        cerr << "Need at least 2 nodes for messaging\n";
        return 1;
    }

    uniform_int_distribution<int> node_dist(0, num_nodes - 1);
    uniform_int_distribution<int> chance_dist(1, 100);

    cout << "--- Generic event workload (" << mode << ") with " << num_nodes << " nodes, " << steps << " steps, send chance " << send_chance << "% ---\n";

    if (mode == "lamport") {
        vector<LamportNode> nodes;
        nodes.reserve(num_nodes);
        for (int i = 0; i < num_nodes; i++) nodes.emplace_back(i);

        for (int step = 1; step <= steps; step++) {
            int sender = node_dist(rng);
            int roll = chance_dist(rng);
            if (roll <= send_chance) {
                int receiver;
                do {
                    receiver = node_dist(rng);
                } while (receiver == sender);

                int ts = nodes[sender].send();
                nodes[receiver].receive(ts);
            } else {
                nodes[sender].local_event();
            }

            this_thread::sleep_for(chrono::milliseconds(60));
        }

        cout << "--- final Lamport clocks ---\n";
        for (auto &n : nodes) n.print();

    } else {
        vector<VectorNode> nodes;
        nodes.reserve(num_nodes);
        for (int i = 0; i < num_nodes; i++) nodes.emplace_back(i, num_nodes);

        for (int step = 1; step <= steps; step++) {
            int sender = node_dist(rng);
            int roll = chance_dist(rng);
            if (roll <= send_chance) {
                int receiver;
                do {
                    receiver = node_dist(rng);
                } while (receiver == sender);

                nodes[sender].send(nodes[receiver]);
            } else {
                nodes[sender].local_event();
            }

            this_thread::sleep_for(chrono::milliseconds(60));
        }

        cout << "--- final vector clocks ---\n";
        for (auto &n : nodes) n.print();
    }

    return 0;
}
