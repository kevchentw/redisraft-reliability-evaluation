from typing import List
import sh
from rich.console import Console
from time import sleep
from os import mkdir
from datetime import datetime
from time import time
from tqdm import tqdm

console = Console()

# console.log(sh.docker_compose("exec",  "-T", "client", "redis-cli",
#             "-p", "5002", "-h", "raft2", "--raw", "RAFT.INFO"))
# console.log(sh.docker_compose("exec",  "-T", "client", "redis-cli",
#             "-p", "5003", "-h", "raft3", "--raw", "RAFT.INFO"))

cluster = [
    ("raft1", "5001"),
    ("raft2", "5002"),
    ("raft3", "5003")
]
CRASH_CLIENT_CNT = 20
CRSAH_THRED_CNT = 4

def get_throughput(host, port):
    stats_process = sh.docker_compose(
        "exec",  "-T", "client", "redis-cli", "-p", port, "-h", host, "info", "stats")
    return stats_process.stdout.decode().split("\r\n")[3].split(":")[1]


def start_cluster():
    console.log("start cluser")
    sh.docker_compose("down")
    sh.docker_compose("--compatibility", "up", "-d")
    console.log("join raft")

    console.log(sh.docker_compose("exec", "-T", "client", "redis-cli",
                "-p", "5001", "-h", "raft1", "raft.cluster", "init"))
    console.log(sh.docker_compose("exec",  "-T", "client", "redis-cli",
                "-p", "5002", "-h", "raft2", "RAFT.CLUSTER", "JOIN", "raft1:5001"))
    console.log(sh.docker_compose("exec", "-T", "client", "redis-cli",
                "-p", "5003", "-h", "raft3", "RAFT.CLUSTER", "JOIN", "raft1:5001"))


def benchmark(client_cnt, thread_cnt, fn, round=1, leader=("raft1", 5001,), bg=False):
    return sh.docker_compose("exec", "-T", "benchmark", "memtier_benchmark", "-p", leader[1], "-s", leader[0],
                             "-c", str(client_cnt), "-t", str(
                                 thread_cnt), "--out-file", fn,
                             "--data-offset", 1048576, "-x", round, 
                             "--random-data", "--key-minimum", "200", "--key-maximum", "400",
                             "--key-pattern", "S:S",
                             _bg=bg, _bg_exc=False)
def run_baseline():
    timestamp = datetime.utcnow()
    console.log("start benchmark")
    folder = f"./output/{timestamp}"
    mkdir(folder)
    start_cluster()
    for client_cnt in tqdm(range(1, 40, 2)):
        console.log(client_cnt)
        for thread_cnt in [4]:
            benchmark(client_cnt, thread_cnt,
                      f"{folder}/baseline-{client_cnt}-{thread_cnt}.txt", 3)

        console.log("end benchmark")


def run_fail_injection(targets: List[str], memory: bool = False, cpu: bool = False, level: int = 1):
    client_cnt = CRASH_CLIENT_CNT
    thread_cnt = CRSAH_THRED_CNT
    console.log("run fail injection")
    console.log("target:", targets, "memory:", memory, "cpu:", cpu)
    start_cluster()
    fn = "non-fail"
    if memory:
        fn = "memory"
    if cpu:
        fn = "cpu"
    bm_process = benchmark(client_cnt, thread_cnt,
              f"/output/fail-injection/{targets}-{fn}-{level}.txt", 3, bg=True)
    sleep(0.5)
    for target in targets:
        if memory:
            # sz = 200000000
            # stress_process = sh.docker_compose(
            #     "--compatibility", "exec", "-T", target, "stress", "--vm", "2", "--vm-bytes", sz, _bg=True, _bg_exc=False)
            if level == 1:
                m = 1024*1024*150
            elif level == 2:
                m = 1024*1024*100
            elif level ==3:
                m = 1024*1024*75
            elif level == 4:
                m = 1024*1024*50
            elif level == 5:
                m = 1024*1024*25
            console.log("limit memory", target, m)
            target = f"redisraft-reliability-evaluation_{target}_1"
            try:
                sh.docker("update", "--memory", m, "--memory-swap", 10*m, target)
            except Exception:
                pass
        if cpu:
            console.log("limit cpu", target, level)
            stress_process = sh.docker_compose(
                "--compatibility", "exec", "-T", target, "stress", "--cpu", level, _bg=True, _bg_exc=False)
    console.log("wait benchmark")
    bm_process.wait()
    console.log("wait benchmark done")


def get_leader():
    for (name, port) in cluster:
        try:
            info = sh.docker_compose("exec", "-T", "client", "redis-cli",
                    "-p", port, "-h", name, "RAFT.INFO")
            if "role:leader" in info:
                return (name, port,)
        except Exception:
            pass
    return ""
        


def run_crash_leader():
    client_cnt = CRASH_CLIENT_CNT
    thread_cnt = CRSAH_THRED_CNT
    target = "raft1"
    start_cluster()
    bm_process = benchmark(client_cnt, thread_cnt,
              f"/output/fail-injection/{target}-crash-leader-before.txt", 1, bg=True)
    sleep(0.5)
    sh.docker("stop", f"redisraft-reliability-evaluation_{target}_1")
    t = time()
    leader = None
    while not leader:
        leader = get_leader()
        console.log("new leader", leader)
    diff = time() - t
    t = time()
    bm_process = benchmark(client_cnt, thread_cnt,
            f"/output/fail-injection/{target}-crash-leader-after.txt", 1, leader, bg=True)
    console.log("wait benchmark")
    bm_process.wait()
    diff2 = time() - t
    console.log("diff", diff, diff2)
    console.log("wait benchmark done")


def run_crash_follower(target):
    client_cnt = CRASH_CLIENT_CNT
    thread_cnt = CRSAH_THRED_CNT
    start_cluster()
    bm_process = benchmark(client_cnt, thread_cnt,
              f"/output/fail-injection/{target}-crash-follower.txt", 3, bg=True)
    sleep(0.5)
    sh.docker("stop", f"redisraft-reliability-evaluation_{target}_1")
    console.log("wait benchmark")
    bm_process.wait()
    console.log("wait benchmark done")

# for target, port in cluster:
#     run_fail_injection(target)
#     run_fail_injection(target, memory=True)
#     run_fail_injection(target, cpu=True)

run_crash_leader()
# run_crash_follower("raft2")
# run_crash_follower("raft3")


# for level in [4, 5]:
# run_fail_injection([cluster[2][0], cluster[1][0]], memory=True, level=1)
# run_fail_injection([cluster[2][0], cluster[1][0]], cpu=True, level=1)

# run_baseline()