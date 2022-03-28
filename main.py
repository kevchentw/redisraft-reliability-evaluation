import sh
from rich.console import Console
from time import sleep
from os import mkdir
from datetime import datetime

console = Console()

console.log(sh.docker_compose("exec", "-T", "client", "redis-cli",
            "-p", "5001", "-h", "raft1", "raft.cluster", "init"))
console.log(sh.docker_compose("exec",  "-T", "client", "redis-cli",
            "-p", "5002", "-h", "raft2", "RAFT.CLUSTER", "JOIN", "raft1:5001"))
console.log(sh.docker_compose("exec", "-T", "client", "redis-cli",
            "-p", "5003", "-h", "raft3", "RAFT.CLUSTER", "JOIN", "raft1:5001"))

# console.log(sh.docker_compose("exec",  "-T", "client", "redis-cli",
#             "-p", "5002", "-h", "raft2", "--raw", "RAFT.INFO"))
# console.log(sh.docker_compose("exec",  "-T", "client", "redis-cli",
#             "-p", "5003", "-h", "raft3", "--raw", "RAFT.INFO"))

# # ycsb = sh.Command("/YCSB/bin/ycsb")

# # console.log(ycsb("load", "redis", "-s", "-P", "/YCSB/workloads/workloada", "-P", "large.dat", "-p", "redis.host=raft1", "-p", "redis.port=5001", _out="/output/outputLoad.txt"))
# # console.log(ycsb("run", "redis", "-s", "-P", "/YCSB/workloads/workloada", "-P", "large.dat", "-p", "redis.host=raft1", "-p", "redis.port=5001", _out="/output/outputRun.txt"))
timestamp = datetime.utcnow()
console.log("start benchmark")

folder = f"./output/{timestamp}"
mkdir(folder)

for c in range(1, 300, 10):
    bm = sh.docker_compose("exec", "-T", "client", "redis-benchmark", "-p", "5001", "-h", "raft1", "-q", "-t",
                           "set,get", "-n", "10000000000", "-c", c, "-P", "16", "-d", "1024", "-l", _bg=True)
    sleep(3)
    latency = sh.docker_compose("exec", "-T", "client", "redis-cli", "-p", "5001", "-h", "raft1",
                                "--latency-history", _bg=True, _out=f"{folder}/latency-{c}.txt")
    f = open(f"{folder}/tp-{c}.txt", "w")

    for i in range(10):
        stats = sh.docker_compose(
            "exec",  "-T", "client", "redis-cli", "-p", "5002", "-h", "raft2", "info", "stats")
        data = stats.stdout.decode().split("\r\n")
        console.log("raft2", data[3])
        stats = sh.docker_compose(
            "exec",  "-T", "client", "redis-cli", "-p", "5003", "-h", "raft3", "info", "stats")
        data = stats.stdout.decode().split("\r\n")
        console.log("raft3", data[3])
        stats = sh.docker_compose(
            "exec",  "-T", "client", "redis-cli", "-p", "5001", "-h", "raft1", "info", "stats")
        data = stats.stdout.decode().split("\r\n")
        console.log(data[3])
        f.write(data[3].split(":")[1]+"\n")
        sleep(1)

    f.close()
    try:
        latency.kill()
    except Exception:
        pass
    try:
        bm.kill()
    except Exception:
        pass
    sleep(3)

console.log("end benchmark")
