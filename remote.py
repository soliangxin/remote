#!/usr/bin/env python3
# coding: utf-8
Version = "%prog 2.0.0"

import optparse
import sys
import re
import time
import getpass
import paramiko
import os
import configparser
import glob
import fnmatch
import datetime


class Parsefile(object):
    """
    解析配置文件
    """
    def __init__(self, configfile):
        self.ConfigFile = configfile
        self.Conf = configparser.RawConfigParser(allow_no_value=True)
        self.Conf.read(self.ConfigFile)
        self.HostList = self.Conf.options('LIST')
        self.HostName = ""
        self.Ip = ""
        self.User = ""
        self.Password = ""
        self.Port = "22"
        self.DirPrefix = ""

    def parse_conf(self, node):
        self.HostName = self.Conf.get(node, 'HostName')
        self.Ip = self.Conf.get(node, 'IP')
        self.User = self.Conf.get(node, 'User')
        self.Password = self.Conf.get(node, 'Password')
        self.Port = self.Conf.getint(node, 'Port')
        self.DirPrefix = self.Conf.get(node, 'DirPrefix')


class Remote(Parsefile):
    """
    远程执行命令
    """
    def __init__(self, configfile, command):
        super(Remote, self).__init__(configfile)
        self.Comm = ""
        self.Prompt = ""
        if not os.path.isfile(command):
            self.Comm = command
        else:
            with open(command) as file:
                for line in file:
                    if not line.startswith('#'):
                        self.Comm = self.Comm + line

    def romote_exec(self):
        for Node in self.HostList:
            self.parse_conf(Node)
            self.Prompt = self.User + "@" + self.Ip
            print('-' * 43 + self.HostName + '-' * 53)
            paramiko.util.log_to_file('paramiko.log')
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=self.Ip, username=self.User,
                            password=self.Password, port=self.Port, timeout=60)
            except:
                print('[%s]Login failed !!!' % (self.Prompt))
                continue
            print('[%s] run:\n%s' % (self.Prompt, self.Comm))
            stdin, stdout, stderr = ssh.exec_command(self.Comm)
            print('[%s] out:' % (self.Prompt))
            StdOut = stdout.read()
            StdErr = stderr.read()
            ssh.close()
            if StdOut: print(StdOut.decode('ascii', 'ignore'))
            if StdErr: print(StdErr.decode('ascii', 'ignore'))


class Transfer(Parsefile):
    """
    传输文件
    """
    def __init__(self, configfile):
        super(Transfer, self).__init__(configfile)
        self.FileSzieDict = {}
        self.Sftp = ""
        self.Prompt = ""

    def size_switch(self, sizeInBytes):
        """
        容量转换单位 like: 9.9bytes/KB/MB/GB
        """
        for (cutoff, label) in [(1024 * 1024 * 1024, "GB"), (1024 * 1024, "MB"),
                                (1024, "KB"), ]:
            if sizeInBytes >= cutoff:
                return "%.1f %s" % (sizeInBytes * 1.0 / cutoff, label)

        if sizeInBytes == 1:
            return "1 byte"

        else:
            bytes = "%.1f" % (sizeInBytes or 0,)

        return (bytes[:-2] if bytes.endswith('.0') else bytes) + ' bytes'

    def create_local_dir(self, dir):
        """
        创建本地目录
        :param dir:
        :return:
        """
        while True:
            IsCreate = input('[%s]Whether to create directory "%s" (yes/no):'
                      %(self.Prompt, dir))
            if IsCreate.lower() in ('y', 'ye', 'yes'):
                os.makedirs(dir)
                return 1
            else:
                return 0
        return 0

    def check_ftp_dir(self, dir, iscreate=False):
        """
        检查ftp目录
        :param dir:
        :param iscreate:
        :return:
        """
        try:
            self.Sftp.stat(dir)
            return True
        except:
            if not iscreate:
                return False

        # 创建目录
        while True:
            Value = input('[%s]Whether to create directory "%s" (yes/no):'
                          %(self.Prompt, dir))
            if Value.lower() in ('y', 'ye', 'yes'):
                try:
                    self.Sftp.mkdir(dir)
                    return True
                except:
                    return False
            elif Value.lower() in ('n', 'no'):
                return False

    def get_lfile_size(self, pathname):
        """
        获取本地文件
        :param pathname: 文件名
        :return: 返回文件大小
        """
        if pathname in self.FileSzieDict:
            return self.FileSzieDict.get(pathname)

        FileSize = os.stat(pathname).st_size
        self.FileSzieDict.setdefault(pathname, FileSize)
        return FileSize

    def upload(self, srcfile, destdir):
        """
        上传文件
        :param srcfile:
        :param destdir:
        :return:
        """
        self.Prompt = getpass.getuser() + "@localhost"
        SrcFiles = os.path.abspath(srcfile)
        SrcDir, Macth = os.path.split(SrcFiles)
        FileList = glob.glob(SrcFiles)

        # 文件是否存在
        if not FileList:
            print('No files found %s' %(srcfile))
            sys.exit(1)

        print('[%s]Matching file Directory: %s' % (self.Prompt, SrcDir))
        print('[%s]Matching file Pattern  : %s' % (self.Prompt, Macth))
        FileNum = 0
        for PathName in FileList:
            FileNum += 1
            FileName = os.path.basename(PathName)
            print('[%s]Matched file name %s: %s' % (self.Prompt, str(FileNum).ljust(5), FileName))
        print('\n')

        for Node in self.HostList:
            self.parse_conf(Node)
            print('-' * 43 + self.HostName + '-' * 53 + '\n')
            self.Prompt = self.User + "@" + self.Ip
            try:
                t = paramiko.Transport((self.Ip, self.Port))
                t.connect(username=self.User, password=self.Password)
                self.Sftp = paramiko.SFTPClient.from_transport(t)
            except:
                print('[%s]Login failed !!!\n' % (self.Prompt))
                continue

            NewDestDir = os.path.join(self.DirPrefix, destdir)
            CheckValue = self.check_ftp_dir(destdir, iscreate=True)
            if CheckValue:

                FileNumAll = len(FileList)           # 文件总数
                FileNum = 0                          # 文件数当前数

                for PathName in FileList:

                    FileNum = FileNum + 1

                    SrcFileName = PathName
                    FileName = os.path.basename(PathName)
                    SrcFileName = os.path.join(SrcDir, FileName)
                    DestPathName = os.path.join(NewDestDir, FileName)

                    # 获取文件信息
                    FileSize = self.get_lfile_size(SrcFileName)

                    # 开始传输文件
                    StartTime = datetime.datetime.now()
                    self.Sftp.put(PathName, DestPathName)
                    StopTime = datetime.datetime.now()

                    # 计算文件传输速度
                    DiffTime = (StopTime - StartTime).seconds
                    if DiffTime == 0:
                        DiffTime = 1
                    Speed = self.size_switch(FileSize / DiffTime) + "/s"

                    print("Upload file [%s/%s] %s to %s Success. FileSize: %s. speed: %s" %
                          (FileNum, FileNumAll, SrcFileName, DestPathName, FileSize, Speed))

            # 关闭连接
            self.Sftp.close()
            print('\n')

    def download(self, srcfile, destdir):
        """
        远程下载文件
        :param srcfile:
        :param destdir:
        :return:
        """
        self.Prompt = getpass.getuser() + "@localhost"
        destdir = os.path.abspath(destdir)
        if not os.path.isdir(destdir):
            if not self.create_local_dir(destdir):
                print('[%s]The local directory %s not exist!' %(self.Prompt, destdir))
                sys.exit(2)

        OldSftpSrcDir, SftpMatch = os.path.split(srcfile)
        for Node in self.HostList:
            self.parse_conf(Node)
            print('-' * 43 + self.HostName + '-' * 53 + '\n')
            self.Prompt = self.User + "@" + self.Ip

            # 连接主机
            try:
                t = paramiko.Transport((self.Ip, self.Port))
                t.connect(username=self.User, password=self.Password)
                self.Sftp = paramiko.SFTPClient.from_transport(t)
            except:
                print('[%s]Login failed !!!\n' % (self.Prompt))
                continue

            # 检查远程主机目录
            SftpSrcDir = os.path.join(self.DirPrefix, OldSftpSrcDir)
            if not self.check_ftp_dir(SftpSrcDir):
                self.Sftp.close()
                print('[%s]No directory "%s"\n' %(self.Prompt, SftpSrcDir))
                continue

            FileListAll = self.Sftp.listdir(SftpSrcDir)
            FileList = fnmatch.filter(FileListAll, SftpMatch)

            print("[%s]Matching file Directory: %s" % (self.Prompt, SftpSrcDir))
            print("[%s]Matching file Pattern  : %s" % (self.Prompt, SftpMatch))
            FileNum = 0
            for FileName in FileList:
                FileNum += 1
                print("[%s]Matched file name %s: %s" % (self.Prompt, str(FileNum).ljust(5), FileName))

            FileNumAll = len(FileList)  # 文件总数
            FileNum = 0  # 文件数当前数

            # 传输文件
            for FileName in FileList:

                FileNum = FileNum + 1

                SrcFileName = os.path.join(SftpSrcDir, FileName)
                DestFileName = os.path.join(destdir, FileName)

                # 获取文件信息
                FileSize = self.Sftp.stat(SrcFileName).st_size

                # 开始传输文件
                StartTime = datetime.datetime.now()
                self.Sftp.get(SrcFileName, DestFileName)
                StopTime = datetime.datetime.now()

                # 计算文件传输速度
                DiffTime = (StopTime - StartTime).seconds
                if DiffTime == 0:
                    DiffTime = 1
                Speed = self.size_switch(FileSize / DiffTime) + "/s"

                print("Download file [%s/%s] %s to %s Success. FileSize: %s. "
                      "speed: %s " % (FileNum, FileNumAll, SrcFileName, DestFileName, FileSize, Speed))

            # 关闭连接
            self.Sftp.close()
            print('\n')


# 获取命令行参数
def get_parameters():
    """
    获取命令行参数
    :return:
    """
    Usage = "usage: %prog [options] PERSON_NAME"
    parser = optparse.OptionParser(usage=Usage, version=Version)
    parser.add_option('-H', '--hosts',
                      dest='HOSTS', default='hostlist',
                      help='specify a host list file')
    parser.add_option('-m', '--mode',
                      dest='MODE', default='exec',
                      help='parameter options exec or put or get, the default is exec')
    parser.add_option('-c', '--command',
                      dest='COMMAND',
                      help='commands to be executed, you can file')
    parser.add_option('-s', '--file',
                      dest='SOURCEFILE',
                      help='specifies upload or download files, you can use regular match')
    parser.add_option('-d',
                      dest='DESTDIR',
                      help='upload or download files to the specified directory')
    (options, args) = parser.parse_args()
    Hostlist = options.HOSTS
    Mode = options.MODE.lower()
    Command = options.COMMAND
    SrcFiles = options.SOURCEFILE
    DestDir = options.DESTDIR

    if not Hostlist:
        parser.print_help()
        sys.exit(3)

    # 执行模式
    if Mode == "exec":
        if not Command:
            parser.print_help()
            sys.exit(4)
        mo = Remote(Hostlist, Command)
        mo.romote_exec()
    elif Mode == "put":
        if not SrcFiles or not DestDir:
            parser.print_help()
            sys.exit(5)
        mo = Transfer(Hostlist)
        mo.upload(SrcFiles, DestDir)
    elif Mode == "get":
        if not SrcFiles or not DestDir:
            parser.print_help()
            sys.exit(6)
        mo = Transfer(Hostlist)
        mo.download(SrcFiles, DestDir)


if __name__ == "__main__":
    get_parameters()
