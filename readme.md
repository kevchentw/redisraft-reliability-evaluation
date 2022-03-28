sudo cgcreate -g memory:raft1
echo 524288000 > /sys/fs/cgroup/memory/raft1/memory.limit_in_bytes


docker update --memory=6291456 --memory-swap=6291456 --cpu-shares=2 redisraft-reliability-evaluation_raft1_1