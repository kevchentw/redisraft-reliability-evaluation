FROM eisvogle/slooo

RUN apt-get update 
RUN apt-get install -y build-essential libssl-dev git cmake
WORKDIR /tmp
RUN git clone https://github.com/RedisLabs/redisraft.git
RUN cd /tmp/redisraft && mkdir build && cd build && cmake .. && make
RUN git clone https://github.com/redis/redis  
RUN cd redis && make && make install
RUN git clone http://github.com/brianfrankcooper/YCSB.git /YCSB
RUN cd /YCSB && mvn -pl site.ycsb:redis-binding -am clean package
WORKDIR /data
COPY scripts /data/scripts