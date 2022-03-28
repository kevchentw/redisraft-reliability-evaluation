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

timestamp = datetime.utcnow()
console.log("start benchmark")

folder = f"./output/{timestamp}"
mkdir(folder)

cluster = [
    ("raft1", "5001"),
    ("raft2", "5002"),
    ("raft3", "5003")
]

result = []
sh.docker_compose("up", "--force-recreate", "-d")

for c in range(1, 200, 5):
    for p in [1]:
        console.log("start cluser")
        console.log("join raft")

        console.log(sh.docker_compose("exec", "-T", "client", "redis-cli",
                    "-p", "5001", "-h", "raft1", "raft.cluster", "init"))
        console.log(sh.docker_compose("exec",  "-T", "client", "redis-cli",
                    "-p", "5002", "-h", "raft2", "RAFT.CLUSTER", "JOIN", "raft1:5001"))
        console.log(sh.docker_compose("exec", "-T", "client", "redis-cli",
                    "-p", "5003", "-h", "raft3", "RAFT.CLUSTER", "JOIN", "raft1:5001"))

        res = {"c" : c, "p": p, "latency" : [], "throughput" : []}
        bm_process = sh.docker_compose("exec", "-T", "client", "redis-benchmark", "-p", "5001", "-h", "raft1", "-q", "-t",
                            "set,get", "-n", "10000000000", "-c", str(c), "-P", str(p), "-d", "1024", "-l", _bg=True, _bg_exc=False)

        sleep(5)
        for (host, port) in cluster:
            stats_process = sh.docker_compose(
                "exec",  "-T", "client", "redis-cli", "-p", port, "-h", host, "info", "stats")
            throughput = stats_process.stdout.decode().split("\r\n")[3].split(":")[1]
            res["throughput"].append(throughput)
            latency_process = sh.docker_compose("exec", "-T", "client", "redis-cli", "-p", port, "-h", host,
                                        "--latency", _bg=True)
            latency = latency_process.stdout.decode("utf-8").strip().split(" ")[2]
            res["latency"].append(latency)

        with open(f"{folder}/result.json", "a+") as f:
            f.write(json.dumps(res)+"\n")
        sleep(1)
        print(res)
        try:
            latency_process.terminate()
        except Exception:
            pass
        bm_process.terminate()

        sleep(5)

console.log("end benchmark")
