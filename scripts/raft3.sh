redis-server --port 5003 --dbfilename raft.rdb --loadmodule /tmp/redisraft/redisraft.so raft-log-filename raftlog.db addr 0.0.0.0:5003
redis-cli -p 5003 RAFT.CLUSTER JOIN raft1:5001