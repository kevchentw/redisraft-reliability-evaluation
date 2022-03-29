FROM ubuntu

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Chicago
WORKDIR /tmp
COPY requirements.txt /tmp
RUN apt-get update && apt-get install -y build-essential libssl-dev git cmake default-jdk maven python3-pip python stress
RUN pip install -r /tmp/requirements.txt
RUN git clone https://github.com/RedisLabs/redisraft.git
RUN cd /tmp/redisraft && mkdir build && cd build && cmake .. && make
RUN git clone https://github.com/redis/redis  
RUN cd redis && make && make install
RUN mkdir /data/
RUN mv /tmp/redisraft/redisraft.so /data/redisraft.so
# RUN git clone http://github.com/brianfrankcooper/YCSB.git /YCSB
# WORKDIR /YCSB
# RUN cd /YCSB && mvn -pl site.ycsb:redis-binding -am clean package
# COPY main.py /YCSB
# COPY large.dat /YCSB