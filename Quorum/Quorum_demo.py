import random
import time

class Replica:
    def __init__(self, name):
        self.name = name
        self.value = 0
        self.version = 0

    def write(self, value, version):
        self.value = value
        self.version = version

    def read(self):
        return {"name": self.name, "value": self.value, "version": self.version}

    def reset(self):
        self.value = 0
        self.version = 0


class DistributedSystem:
    def __init__(self):
        self.replicas = [Replica("A"), Replica("B"), Replica("C")]
        self.latest_version = 0
        self.latest_value = 0

    def show_state(self):
        print("\nState:")
        for r in self.replicas:
            print(f"{r.name}: value={r.value}, version={r.version}")
        print()

    def write(self, value, W):
        self.latest_version += 1
        self.latest_value = value

        selected = random.sample(self.replicas, W)

        for r in selected:
            r.write(value, self.latest_version)

        print(f"Write {value} -> {[r.name for r in selected]}")

        self.pending = [r for r in self.replicas if r not in selected]

    def delayed_replication(self, value, version):
        print("Replicating to remaining nodes...")
        for r in self.pending:
            time.sleep(0.5)
            r.write(value, version)
            print(f"Replicated to {r.name}")

    def read(self, R):
        selected = random.sample(self.replicas, R)
        responses = [r.read() for r in selected]

        print(f"Read from {[r.name for r in selected]}")
        print("Responses:", responses)

        latest = max(responses, key=lambda x: x["version"])
        print("Chosen:", latest)

        if latest["value"] == self.latest_value:
            print("Up-to-date")
        else:
            print("Stale")

        return latest


def run_case(system, name, value, W, R):
    print("=" * 50)
    print(name)
    print("=" * 50)

    for r in system.replicas:
        r.reset()

    system.show_state()

    system.write(value, W)

    print("\nImmediate read:")
    system.read(R)

    print("\nAfter delayed replication:")
    system.delayed_replication(value, system.latest_version)
    system.read(R)

    system.show_state()


def main():
    system = DistributedSystem()

    run_case(system, "Case 1: W=1, R=1", 10, 1, 1)
    run_case(system, "Case 2: W=2, R=2", 20, 2, 2)


if __name__ == "__main__":
    main()