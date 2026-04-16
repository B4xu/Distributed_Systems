import random

replicas = {
    "A": 0,
    "B": 0,
    "C": 0
}

latest_written_value = None

def show_replicas():
    print("Current replica state:")
    for name, value in replicas.items():
        print(f"  {name}: {value}")
    print()

def write(value, W):
    global latest_written_value
    latest_written_value = value

    chosen = random.sample(list(replicas.keys()), W)

    for replica in chosen:
        replicas[replica] = value

    print(f"Write {value} to replicas {chosen}")
    return chosen

def read(R):
    chosen = random.sample(list(replicas.keys()), R)
    values = [replicas[replica] for replica in chosen]

    print(f"Read from replicas {chosen} -> {values}")

    result = max(set(values), key=values.count)
    return result

def reset():
    for key in replicas:
        replicas[key] = 0

def run_case(name, value, W, R):
    print("=" * 40)
    print(name)
    print("=" * 40)

    reset()
    show_replicas()

    write(value, W)
    result = read(R)

    print(f"Read result: {result}")

    if result == value:
        print("Result: up-to-date read")
    else:
        print("Result: stale read")

    N = len(replicas)
    print(f"N={N}, W={W}, R={R}, R+W={R+W}")

    if R + W > N:
        print("Quorum satisfied")
    else:
        print("Quorum NOT satisfied")

    print()
    show_replicas()

def main():
    run_case("Case 1: W=1, R=1", 10, 1, 1)
    run_case("Case 2: W=2, R=2", 20, 2, 2)

if __name__ == "__main__":
    main()