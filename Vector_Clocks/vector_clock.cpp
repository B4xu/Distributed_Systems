#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <thread>
#include <mutex>
#include <queue>
#include <condition_variable>
#include <atomic>
#include <memory>
#include <cstdlib>
#include <ctime>
#include <sstream>
#include <iomanip>

using namespace std;

static int NUM_MAP_NODES = 6;
static int NUM_REDUCE_NODES = 3;
static int NUM_NODES = NUM_MAP_NODES + NUM_REDUCE_NODES;
static bool USE_LAMPORT = false;

string get_timestamp() {
    auto now = chrono::system_clock::now();
    auto time_t = chrono::system_clock::to_time_t(now);
    auto ms = chrono::duration_cast<chrono::milliseconds>(now.time_since_epoch()) % 1000;
    stringstream ss;
    ss << put_time(localtime(&time_t), "%H:%M:%S") << "." << setfill('0') << setw(3) << ms.count();
    return ss.str();
}

struct Message {
    vector<int> clock;
    int sender_id;
};

class node {
    public:
        int id;
        vector<int> clock;
        queue<Message> message_queue;
        mutex queue_mutex;
        condition_variable queue_cv;
        atomic<bool> running;
        thread node_thread;
        static mutex send_mutex;

        node(int id, int total_nodes) : id(id), running(true) {
            clock.resize(total_nodes, 0);
            node_thread = thread(&node::run, this);
        }

        ~node() {
            running = false;
            queue_cv.notify_one();
            if (node_thread.joinable()) node_thread.join();
        }

        void run() {
            while (running) {
                unique_lock<mutex> lock(queue_mutex);
                queue_cv.wait(lock, [this]() { return !message_queue.empty() || !running; });
                if (!running) break;
                Message msg = message_queue.front();
                message_queue.pop();
                lock.unlock();

                // Process received message
                receive(msg.clock);
                cout << "[" << get_timestamp() << "] [RECV] Node " << id << " received from Node " << msg.sender_id << "\n";
            }
        }

        void local_event() {
            clock[id]++;
            // Simulate processing time
            this_thread::sleep_for(chrono::milliseconds(rand() % 100 + 50));
        }

        void send(node &receiver, const string &tag = "") {
            lock_guard<mutex> lock(send_mutex);
            clock[id]++;
            Message msg = {clock, id};
            {
                lock_guard<mutex> lock(receiver.queue_mutex);
                receiver.message_queue.push(msg);
            }
            receiver.queue_cv.notify_one();
            if (!tag.empty()) {
                cout << "[" << get_timestamp() << "] [SEND " << tag << "] Node " << id << " -> Node " << receiver.id << "\n";
            }
            // Simulate network delay
            this_thread::sleep_for(chrono::milliseconds(rand() % 50 + 10));
        }

        void receive(const vector<int> &sender_clock) {
            int n = static_cast<int>(clock.size());
            for (int i = 0; i < n; i++) {
                clock[i] = max(clock[i], sender_clock[i]);
            }
            clock[id]++;
        }

        void print_clock() {
            cout << "Node " << id << ": ";
            int n = static_cast<int>(clock.size());
            for (int i = 0; i < n; i++) {
                cout << clock[i] << " ";
            }
            cout << "\n";
        }
};

mutex node::send_mutex;

void run_map_phase(vector<unique_ptr<node>> &nodes, mt19937 &rng) {
    uniform_int_distribution<int> map_work(1, 4);
    cout << "[" << get_timestamp() << "] === MAP PHASE ===\n";
    for (int i = 0; i < NUM_MAP_NODES; i++) {
        int events = map_work(rng);
        cout << "[" << get_timestamp() << "] Map node " << i << " performs " << events << " local events\n";
        for (int k = 0; k < events; k++) {
            nodes[i]->local_event();
        }
    }
}

void run_shuffle_phase(vector<unique_ptr<node>> &nodes) {
    cout << "[" << get_timestamp() << "] === SHUFFLE PHASE ===\n";
    for (int i = 0; i < NUM_MAP_NODES; i++) {
        int target = (i % NUM_REDUCE_NODES) + NUM_MAP_NODES;
        nodes[i]->send(*nodes[target], "shuffle");
    }
    // Give time for asynchronous delivery to be processed
    this_thread::sleep_for(chrono::seconds(2));
}

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

    void receive(int incoming) {
        clock = max(clock, incoming) + 1;
    }
};

void run_lamport_phase(vector<LamportNode> &nodes, mt19937 &rng) {
    uniform_int_distribution<int> map_work(1, 4);
    uniform_int_distribution<int> reduce_work(2, 5);

    cout << "[" << get_timestamp() << "] === MAP PHASE (Lamport) ===\n";
    for (int i = 0; i < NUM_MAP_NODES; i++) {
        int events = map_work(rng);
        cout << "[" << get_timestamp() << "] Map node " << i << " performs " << events << " local events\n";
        for (int k = 0; k < events; k++) {
            nodes[i].local_event();
        }
    }

    cout << "[" << get_timestamp() << "] === SHUFFLE PHASE (Lamport) ===\n";
    for (int i = 0; i < NUM_MAP_NODES; i++) {
        int target = (i % NUM_REDUCE_NODES) + NUM_MAP_NODES;
        int timestamp = nodes[i].send();
        nodes[target].receive(timestamp);
        cout << "[" << get_timestamp() << "] [SEND shuffle] Node " << i << " -> Node " << target << " @" << timestamp << "\n";
        cout << "[" << get_timestamp() << "] [RECV] Node " << target << " received from Node " << i << "\n";
    }

    cout << "[" << get_timestamp() << "] === REDUCE PHASE (Lamport) ===\n";
    for (int i = 0; i < NUM_REDUCE_NODES; i++) {
        int idx = NUM_MAP_NODES + i;
        int events = reduce_work(rng);
        cout << "[" << get_timestamp() << "] Reduce node " << idx << " performs " << events << " local events\n";
        for (int k = 0; k < events; k++) {
            nodes[idx].local_event();
        }
    }

    cout << "[" << get_timestamp() << "] === FINAL LAMPORT CLOCKS ===\n";
    for (int i = 0; i < NUM_NODES; i++) {
        cout << "[" << get_timestamp() << "] Node " << i << ": " << nodes[i].clock << "\n";
    }
}

void run_reduce_phase(vector<unique_ptr<node>> &nodes, mt19937 &rng) {
    uniform_int_distribution<int> reduce_work(2, 5);
    cout << "[" << get_timestamp() << "] === REDUCE PHASE ===\n";
    for (int i = 0; i < NUM_REDUCE_NODES; i++) {
        int idx = NUM_MAP_NODES + i;
        int events = reduce_work(rng);
        cout << "[" << get_timestamp() << "] Reduce node " << idx << " performs " << events << " local events\n";
        for (int k = 0; k < events; k++) {
            nodes[idx]->local_event();
        }
    }
}

int main(int argc, char *argv[]) {
    auto start_time = chrono::high_resolution_clock::now();
    cout << "[" << get_timestamp() << "] Program started\n";

    // Command line: --mode=vector|lamport --map=N --reduce=M
    for (int i = 1; i < argc; i++) {
        string arg = argv[i];
        if (arg.rfind("--mode=", 0) == 0) {
            string mode = arg.substr(7);
            USE_LAMPORT = (mode == "lamport");
        } else if (arg.rfind("--map=", 0) == 0) {
            NUM_MAP_NODES = stoi(arg.substr(6));
        } else if (arg.rfind("--reduce=", 0) == 0) {
            NUM_REDUCE_NODES = stoi(arg.substr(9));
        }
    }
    NUM_NODES = NUM_MAP_NODES + NUM_REDUCE_NODES;

    srand((unsigned)time(NULL)); // Seed for random delays
    mt19937 rng((unsigned)chrono::high_resolution_clock::now().time_since_epoch().count());

    if (USE_LAMPORT) {
        vector<LamportNode> nodes;
        for (int i = 0; i < NUM_NODES; i++) {
            nodes.emplace_back(i);
        }
        run_lamport_phase(nodes, rng);
        auto end_time = chrono::high_resolution_clock::now();
        auto duration = chrono::duration_cast<chrono::milliseconds>(end_time - start_time);
        cout << "[" << get_timestamp() << "] Program ended. Total execution time: " << duration.count() << " ms\n";
        return 0;
    }

    vector<unique_ptr<node>> nodes;
    for (int i = 0; i < NUM_NODES; i++) {
        nodes.emplace_back(make_unique<node>(i, NUM_NODES));
    }

    run_map_phase(nodes, rng);
    run_shuffle_phase(nodes);
    run_reduce_phase(nodes, rng);

    // Stop and join all threads cleanly
    for (auto &n : nodes) {
        n->running = false;
        n->queue_cv.notify_one();
    }
    for (auto &n : nodes) {
        if (n->node_thread.joinable()) {
            n->node_thread.join();
        }
    }

    cout << "[" << get_timestamp() << "] === FINAL VECTOR CLOCKS ===\n";
    for (int i = 0; i < NUM_NODES; i++) {
        cout << "[" << get_timestamp() << "] ";
        nodes[i]->print_clock();
    }

    auto end_time = chrono::high_resolution_clock::now();
    auto duration = chrono::duration_cast<chrono::milliseconds>(end_time - start_time);
    cout << "[" << get_timestamp() << "] Program ended. Total execution time: " << duration.count() << " ms\n";

    return 0;
}