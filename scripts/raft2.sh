redis-server --port 5002 --dbfilename raft.rdb --loadmodule /tmp/redisraft/redisraft.so raft-log-filename raftlog.db addr 0.0.0.0:5002
redis-cli -p 5002 RAFT.CLUSTER JOIN raft1:5001