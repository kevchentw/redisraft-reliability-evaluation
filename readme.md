sudo cgcreate -g memory:raft1
echo 524288000 > /sys/fs/cgroup/memory/raft1/memory.limit_in_bytes


docker update --memory=104857600 --memory-swap=104857601 --cpu-shares=2 redisraft-reliability-evaluation_raft2_1