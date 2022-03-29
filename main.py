import sh
from rich.console import Console
from time import sleep
from os import mkdir
from datetime import datetime
import json

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


def benchmark(client_cnt, thread_cnt, fn, round=1, bg=False):
    return sh.docker_compose("exec", "-T", "benchmark", "memtier_benchmark", "-p", "5001", "-s", "raft1",
                             "-c", str(client_cnt), "-t", str(
                                 thread_cnt), "--out-file", fn,
                             "--test-time", 10, "--data-offset", "1048575", "--data-size", "1024", "-x", round, _bg=bg, _bg_exc=False)


def run_baseline():
    timestamp = datetime.utcnow()
    console.log("start benchmark")

    folder = f"./output/{timestamp}"
    mkdir(folder)
    start_cluster()
    for client_cnt in range(1, 70, 2):
        console.log(client_cnt)
        for thread_cnt in [4]:
            benchmark(client_cnt, thread_cnt,
                      f"{folder}/baseline-{client_cnt}-{thread_cnt}.txt")

        console.log("end benchmark")


def run_fail_injection(target: str, memory: bool = False, cpu: bool = False):
    console.log("run fail injection")
    console.log("target:", target, "memory:", memory, "cpu:", cpu)
    client_cnt = 25
    thread_cnt = 4
    start_cluster()
    fn = "non-fail"
    if memory:
        fn = "memory"
    if cpu:
        fn = "cpu"
    bm_process = benchmark(client_cnt, thread_cnt,
              f"/output/fail-injection/{target}-{fn}.txt", 1, bg=True)
    sleep(1)
    stress_process = None
    if memory:
        # sz = 200000000
        # stress_process = sh.docker_compose(
        #     "--compatibility", "exec", "-T", target, "stress", "--vm", "2", "--vm-bytes", sz, _bg=True, _bg_exc=False)
        m = 1024*1024*100
        console.log("limit memory", target, m)
        target = f"redisraft-reliability-evaluation_{target}_1"
        try:
            sh.docker("update", "--memory", m, "--memory-swap", 10*m, target)
        except Exception:
            pass
    if cpu:
        console.log("limit cpu", target, 1)
        stress_process = sh.docker_compose(
            "--compatibility", "exec", "-T", target, "stress", "--cpu", "1", _bg=True, _bg_exc=False)
    console.log("wait benchmark")
    bm_process.wait()
    console.log("wait benchmark done")


for target, port in cluster:
    run_fail_injection(target)
    # run_fail_injection(target, memory=True)
    # run_fail_injection(target, cpu=True)
