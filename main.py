import sh
from rich.console import Console

console = Console()

console.log(sh.redis_cli("-p", "5001", "-h", "raft1", "raft.cluster", "init"))
console.log(sh.redis_cli("-p", "5002", "-h", "raft2", "RAFT.CLUSTER", "JOIN", "raft1:5001"))
console.log(sh.redis_cli("-p", "5003", "-h", "raft3", "RAFT.CLUSTER", "JOIN", "raft1:5001"))
# console.log(sh.redis_cli("-p", "5001", "-h", "raft1", "-h", "raft1", "RAFT.INFO", raw=True).stdout.decode())

ycsb = sh.Command("/YCSB/bin/ycsb")

console.log(ycsb("load", "redis", "-s", "-P", "/YCSB/workloads/workloada", "-p", "redis.host=raft1", "-p", "redis.port=5001", _out="/output/outputLoad.txt"))
console.log(ycsb("run", "redis", "-s", "-P", "/YCSB/workloads/workloada", "-p", "redis.host=raft1", "-p", "redis.port=5001", _out="/output/outputRun.txt"))
