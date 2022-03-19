redis-server --port 5001 --dbfilename raft.rdb --loadmodule /tmp/redisraft/redisraft.so raft-log-filename raftlog.db addr 0.0.0.0:5001
redis-cli -p 5001 raft.cluster init