### 使用remote.py在远程Linux主机执行命令或者传输文件

---
##### 通常运维人员管理的主机几十上百台机器，使用SSH登录每台主机进行操作太消耗时间，基于此，写了一个远程执行命令的工具

---
### 命令行

```
$ ./remote.py
Usage: remote.py [options] PERSON_NAME

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -H HOSTS, --hosts=HOSTS
                        specify a host list file
  -m MODE, --mode=MODE  parameter options exec or put or get, the default is
                        exec
  -c COMMAND, --command=COMMAND
                        commands to be executed, you can file
  -s SOURCEFILE, --file=SOURCEFILE
                        specifies upload or download files, you can use
                        regular match
  -d DESTDIR            upload or download files to the specified directory

```

### 配置文件格式

###### 配置文件使用ini格式，通过LIST节点将主机列表写上，程序会通过读取LIST节点来查找所有可用的主机，每个主机的配置参数介绍
- HostName 主机名称
- Ip  主机IP地址
- User 登录主机的用户
- Password 登录主机用户的密码
- Port SSH协议的端口
- DirPrefix 用户家目录

```
[LIST]
server1
server2

[server1]
HostName=server1
Ip=192.168.1.1
User=test
Password=test
Port=22
DirPrefix=

[server2]
HostName=server2
Ip=192.168.1.2
User=test
Password=test
Port=22
DirPrefix=
```

---

### 命令使用示例
##### 连接远程主机执行命令, -H 参数指定主机列表，-c 指定需要执行的命令
```
$ ./remote.py -H host_list.ini -c 'free -h'
-------------------------------------------server1-----------------------------------------------------
[root@192.168.196.10] run:
free -h
[root@192.168.196.10] out:
              total        used        free      shared  buff/cache   available
Mem:           3.8G        1.8G        322M         91M        1.7G        1.5G
Swap:          3.9G         66M        3.8G

-------------------------------------------server2-----------------------------------------------------
[root@192.168.196.20] run:
free -h
[root@192.168.196.20] out:
              total        used        free      shared  buff/cache   available
Mem:           3.8G        1.8G        322M         91M        1.7G        1.5G
Swap:          3.9G         66M        3.8G

```
##### 连接远程主机执行命令, -H 参数指定主机列表，-c 也可以指定一个文件，命令从文件中进行读取，可以将多个命令写入到同一个文件，读取文件过程中，会过滤掉以"#"开头的行。注意：优先从文件中读取需要执行的命令
```
$ cat > command.txt <<EOF
# test command
free -h
df -h
EOF

$ ./remote.py -H host_list.ini -c command.txt 
-------------------------------------------server1-----------------------------------------------------
[root@192.168.196.10] run:
free -h
df -h

[root@192.168.196.10] out:
              total        used        free      shared  buff/cache   available
Mem:           3.8G        1.8G        308M         99M        1.7G        1.5G
Swap:          3.9G         66M        3.8G
                          % 
/dev/mapper/cl_server1-root   50G   13G   38G   25% /
devtmpfs                     2.0G     0  2.0G    0% /dev
tmpfs                        2.0G  100K  2.0G    1% /dev/shm
tmpfs                        2.0G  123M  1.9G    7% /run
tmpfs                        2.0G     0  2.0G    0% /sys/fs/cgroup
/dev/sda1                   1014M  155M  860M   16% /boot
/dev/mapper/cl_server1-home   46G  3.8G   42G    9% /home
tmpfs                        394M   24K  394M    1% /run/user/1000
tmpfs                        394M     0  394M    0% /run/user/0

-------------------------------------------server2-----------------------------------------------------
[root@192.168.196.20] run:
free -h
df -h

[root@192.168.196.20] out:
              total        used        free      shared  buff/cache   available
Mem:           3.8G        1.8G        307M         99M        1.7G        1.5G
Swap:          3.9G         66M        3.8G
                          % 
/dev/mapper/cl_server1-root   50G   13G   38G   25% /
devtmpfs                     2.0G     0  2.0G    0% /dev
tmpfs                        2.0G  100K  2.0G    1% /dev/shm
tmpfs                        2.0G  123M  1.9G    7% /run
tmpfs                        2.0G     0  2.0G    0% /sys/fs/cgroup
/dev/sda1                   1014M  155M  860M   16% /boot
/dev/mapper/cl_server1-home   46G  3.8G   42G    9% /home
tmpfs                        394M   24K  394M    1% /run/user/1000
tmpfs                        394M     0  394M    0% /run/user/0

```
##### 从远程主机下载文件到本地，-H 指定主机列表, -m 指定模式，-s 指定源文件，支持shell的通配符，-d 指定本地目录
```
$ ./remote.py -H host_list.ini -m get -s '/root/*.cfg' -d /root/test/
-------------------------------------------server1-----------------------------------------------------

[root@192.168.196.10]Matching file Directory: /root
[root@192.168.196.10]Matching file Pattern  : *.cfg
[root@192.168.196.10]Matched file name 1    : anaconda-ks.cfg
[root@192.168.196.10]Matched file name 2    : initial-setup-ks.cfg
Download file [1/2] /root/anaconda-ks.cfg to /root/test/anaconda-ks.cfg Success. FileSize: 1538. speed: 1.5 KB/s 
Download file [2/2] /root/initial-setup-ks.cfg to /root/test/initial-setup-ks.cfg Success. FileSize: 1569. speed: 1.5 KB/s 


-------------------------------------------server2-----------------------------------------------------

[root@192.168.196.20]Matching file Directory: /root
[root@192.168.196.20]Matching file Pattern  : *.cfg
[root@192.168.196.20]Matched file name 1    : anaconda-ks.cfg
[root@192.168.196.20]Matched file name 2    : initial-setup-ks.cfg
Download file [1/2] /root/anaconda-ks.cfg to /root/test/anaconda-ks.cfg Success. FileSize: 1538. speed: 1.5 KB/s 
Download file [2/2] /root/initial-setup-ks.cfg to /root/test/initial-setup-ks.cfg Success. FileSize: 1569. speed: 1.5 KB/s 
```

##### 从本地主机上传文件到远程主机，-H 指定主机列表, -m 指定模式，-s 指定源文件，支持shell的通配符，-d 指定远程目录
```
$ ./remote.py -H host_list.ini -m put -s '/root/test/*.cfg' -d /root/
[root@localhost]Matching file Directory: /root/test
[root@localhost]Matching file Pattern  : *.cfg
[root@localhost]Matched file name 1    : anaconda-ks.cfg
[root@localhost]Matched file name 2    : initial-setup-ks.cfg


-------------------------------------------server1-----------------------------------------------------

Upload file [1/2] /root/test/anaconda-ks.cfg to /root/anaconda-ks.cfg Success. FileSize: 1538. speed: 1.5 KB/s
Upload file [2/2] /root/test/initial-setup-ks.cfg to /root/initial-setup-ks.cfg Success. FileSize: 1569. speed: 1.5 KB/s


-------------------------------------------server2-----------------------------------------------------

Upload file [1/2] /root/test/anaconda-ks.cfg to /root/anaconda-ks.cfg Success. FileSize: 1538. speed: 1.5 KB/s
Upload file [2/2] /root/test/initial-setup-ks.cfg to /root/initial-setup-ks.cfg Success. FileSize: 1569. speed: 1.5 KB/s

```
---
