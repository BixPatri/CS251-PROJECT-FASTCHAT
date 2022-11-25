# import sys
# sys.path.append("/opt/homebrew/bin/pwn")
# from "/opt/homebrew/bin/pwn" import *
from pwn import *
import time
import threading
import os
from os.path import exists
import csv
if not exists("log"): os.makedirs("log")

res=open("results1.csv","w")
writer=csv.writer(res)
writer.writerow(["type","time"])
class Client:
    users = []
    user_IDs = []
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.ps = process(argv=['./client.py'],stdin=process.PTY,stdout=process.PTY)
        self.ps.clean().decode()
        self.ps.sendline(b'1')
        self.ps.clean().decode()
        self.ps.sendline(self.username.encode())
        self.ps.clean().decode()
        self.ps.sendline(self.password.encode())
        self.ps.recvuntil(b"Successfully Registered with ID: ").decode()
        ID = self.ps.recvuntil(b"\n").decode()
        self.ID = int(ID[:len(ID)-1])
        self.ID
        self.ps.recvuntil(b'Menu\n')
        Client.users.append(self.ID)
        self.log_file = open("log/" + str(self.ID)+ "_log.txt", "w")

    def add_friend(self, friend_ID):
        self.ps.sendline(b"add_friend")
        self.ps.clean().decode()
        self.ps.sendline(str(friend_ID).encode())
        self.ps.clean().decode()
    def clean(self):
        time.sleep(.02)
        self.log_file.write("Received & "+str(time.perf_counter())+" & "+self.ps.recv().decode())
        writer.writerow(["Received",time.perf_counter()])
    def single_message(self,friend_ID):
        self.ps.sendline(b"single_message")
        "sent"+str(time.perf_counter())+self.ps.clean().decode()
        self.ps.sendline(str(friend_ID).encode())
        self.ps.clean()
        self.log_file.write("sent & "+str(time.perf_counter())+"\n")
        writer.writerow(["Sent",time.perf_counter()])
        self.ps.sendline(b"Hello")
        time.sleep(.02)
    def create_group(self):
        self.ps.clean()
        self.ps.sendline(b"create_group")
        self.ps.clean()
        self.ps.sendline(b"boys")
        self.ps.clean()
    def add(self,add_ID):
        self.ps.clean()
        self.ps.sendline(b"add_member")
        self.ps.clean()
        self.ps.send(line(b'1'))
        self.ps.clean()
        self.ps.sendline(str(add_ID).encode())
        self.ps.clean()

clients = [Client(f"{i}",f"{i}") for i in range(5)]

for i in range(5):
    for j in range(i+1,5):
        clients[i].add_friend(clients[j].ID)
        clients[j].ps.clean()

for i in range(5):
    for j in range(5):
        if(i!=j):
            clients[i].single_message(clients[j].ID)
            clients[j].clean()