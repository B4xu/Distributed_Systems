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

using namespace std;

#define SIZE 10

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

        node(int id) : id(id), running(true) {
            clock.resize(SIZE, 0);
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
                cout << "[RECV] Node " << id << " received from Node " << msg.sender_id << "\n";
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
                cout << "[SEND " << tag << "] Node " << id << " -> Node " << receiver.id << "\n";
            }
            // Simulate network delay
            this_thread::sleep_for(chrono::milliseconds(rand() % 50 + 10));
        }

        void receive(const vector<int> &sender_clock) {
            for (int i = 0; i < SIZE; i++) {
                clock[i] = max(clock[i], sender_clock[i]);
            }
            clock[id]++;
        }

        void print_clock() {
            cout << "Node " << id << ": ";
            for (int i = 0; i < SIZE; i++) {
                cout << clock[i] << " ";
            }
            cout << "\n";
        }
};

mutex node::send_mutex;

int main() {
    srand(time(NULL)); // Seed for random delays

    const int numMap = 6;
    const int numReduce = 3;
    const int numNodes = numMap + numReduce;

    vector<unique_ptr<node>> nodes;
    for (int i = 0; i < numNodes; i++) {
        nodes.emplace_back(make_unique<node>(i));
    }

    mt19937 rng((unsigned)chrono::high_resolution_clock::now().time_since_epoch().count());
    uniform_int_distribution<int> map_work(1, 4);
    uniform_int_distribution<int> reduce_work(2, 5);
    uniform_int_distribution<int> reduce_target(0, numReduce - 1);

    cout << "=== MAP PHASE ===\n";
    for (int i = 0; i < numMap; i++) {
        int events = map_work(rng);
        cout << "Map node " << i << " performs " << events << " local events\n";
        for (int k = 0; k < events; k++) {
            nodes[i]->local_event();
        }
    }

    cout << "=== SHUFFLE PHASE ===\n";
    for (int i = 0; i < numMap; i++) {
        int target = (i % numReduce) + numMap;
        nodes[i]->send(*nodes[target], "shuffle");
    }

    // Wait for all messages to be processed
    this_thread::sleep_for(chrono::seconds(2));

    cout << "=== REDUCE PHASE ===\n";
    for (int i = 0; i < numReduce; i++) {
        int idx = numMap + i;
        int events = reduce_work(rng);
        cout << "Reduce node " << idx << " performs " << events << " local events\n";
        for (int k = 0; k < events; k++) {
            nodes[idx]->local_event();
        }
    }

    // Stop all threads
    for (auto& n : nodes) {
        n->running = false;
        n->queue_cv.notify_one();
    }

    // Join threads
    for (auto& n : nodes) {
        n->node_thread.join();
    }

    cout << "=== FINAL VECTOR CLOCKS ===\n";
    for (int i = 0; i < numNodes; i++) {
        nodes[i]->print_clock();
    }

    return 0;
}