# 'Chat Room Connection - Client-To-Client'
import sys
import threading
import socket
import json
import sqlite3
from connect import connect
from packets import send_msg
from packets import recv_msg

buffer = 1024
format = 'utf-8'

# hostIP = socket.gethostbyname(socket.gethostname())
hostIP = "127.0.0.1"
hostPort = int(sys.argv[1])
my_ID = int(sys.argv[2])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((hostIP, hostPort))
server.listen()


other_servers = {}
clients = {}

(db_conn, db_cur) = connect()

def send_client(status, ID, msg):
    # todo: add acknowledgement
    curr = db_conn.cursor()
    if status:
        send_msg(clients[ID], json.dumps(msg).encode(format))
        # clients[ID].send(json.dumps(msg).encode(format))
    else:
        curr.execute("""
            SELECT "Pending Messages" FROM "Clients" WHERE "ID" = %s
        """, (ID,))
        prev_msgs = curr.fetchone()[0]
        if prev_msgs==None:
            prev_msgs=[]
        curr.execute("""
            UPDATE "Clients"
            SET "Pending Messages" = %s
            WHERE "ID" = %s
        """, (prev_msgs.append(json.dumps(msg)), ID))
        db_conn.commit()
    curr.close()

def handle_server(server):
    while True:
        try:
            message = server.recv(1024)
        except:
            print("A server-server error occured!")
            server.close()
            # index = socks.index(sock)
            # socks.remove(sock)
            # sock.close()
            # alias = aliases[index]
            # broadcast(f'{alias} has left the chat room!'.encode('utf-8'))
            # aliases.remove(alias)
            break

def create_group(message, client_ID):

    curr = db_conn.cursor()
    participants = message["Members"]
    for p in participants:
        if p not in clients.keys():
            curr.close()
            return False

    curr.execute("""
        SELECT COUNT("ID") FROM "Groups";
    """)

    gid = (int(curr.fetchone()[0])+1)

    msg = "You are added to group"+ message["Group_Name"]
    msg = {"type":"New_group","message":msg,"admin":client_ID,"Group_ID":gid}

    # print("hm")
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" IN %s
    """, (tuple(participants),))
    participants_all = curr.fetchall()
    # print(msg)
    print(participants_all)
    for p in participants_all:
        # print(p)
        send_client(p[1],p[0],msg)

    curr.execute("""
            INSERT INTO "Groups" ("ID", "Name", "Admin ID", "Participants") VALUES (%s,%s,%s,%s)
        """, (gid, message["Group_Name"],client_ID,participants))
    db_conn.commit()

    curr.close()
    return True
    
def group_message(message,client_ID):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Participants" FROM "Groups" WHERE "ID" = %s
    """,(message["group_id"],))
    participants = curr.fetchone()[0]
    print(participants)
    participants.remove(client_ID)
    message["Sender"] = client_ID

    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" IN %s
    """, (tuple(participants),))

    participants_all = curr.fetchall()
    print(participants_all)

    for p in participants_all:
        send_client(p[1],p[0],message)

def kick(message, client_ID):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Participants","Admin ID" FROM "Groups" WHERE "ID" = %s
    """, (message["g_ID"],))
    
    old_party = curr.fetchone()
    if old_party[1]!=client_ID:
        return False
    old_party=old_party[0]
    print(old_party)
    old_party.remove(message["ban_ID"])
    print("remove")
    print(old_party)
    print("removed")
    curr.execute("""
            UPDATE "Groups"
            SET "Participants" = %s
            WHERE "ID" = %s
        """, (old_party, message["g_ID"]))
    db_conn.commit()


    message["message"] = str(message["ban_ID"]) + " was KICKED to the group " + str(message["g_ID"]) + "by " + str(client_ID)
    
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" IN %s
    """,(tuple(old_party),))
    old_stat = curr.fetchall()
    print(old_stat)
    print(message)
    
    for a in old_stat:
        send_client(a[1],a[0],message)
    

    curr.execute("""
        SELECT "Status" FROM "Clients" WHERE "ID" = %s
    """,(message["ban_ID"],))
    statustokick = curr.fetchone()[0]
    message["message"] = "You were kicked from group" + str(message["g_ID"]) + "by " + str(client_ID)
    send_client(statustokick,message["ban_ID"],message)
    curr.close()
    
def add(message , client_ID):
    print(message)
    curr = db_conn.cursor()
    if message["add_ID"] not in clients.keys():
        return False
    print("HI")
    curr.execute("""
        SELECT "Participants","Admin ID" FROM "Groups" WHERE "ID" = %s
    """, (message["g_ID"],))
    print("hm")
    old_party = curr.fetchone()
    if old_party[1]!=client_ID:
        return False
    print("hm")

    old_party=old_party[0]
    new_party=old_party+[]
    new_party.append(message["add_ID"])
    
    print(old_party,new_party)
    curr.execute("""
            UPDATE "Groups"
            SET "Participants" = %s
            WHERE "ID" = %s
        """, (new_party, message["g_ID"]))
    db_conn.commit()
    print("hm")

    curr.execute("""
        SELECT "Status" FROM "Clients" WHERE "ID" = %s
    """,(message["add_ID"],))
    statustoadd = curr.fetchone()[0]
    print("hm")

    message["message"] = str(message["add_ID"]) + " was added to the group " + str(message["g_ID"]) + "by " + str(client_ID)
    
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" IN %s
    """,(tuple(old_party),))
    old_stat = curr.fetchall()
    print("hm")

    for a in old_stat:
        send_client(a[1],a[0],message)

    message["message"] = "You were Added to group " + str(message["g_ID"]) + "by " + str(client_ID)
    
    send_client(statustoadd,message["add_ID"],message)
    db_conn.commit()
    print("hm")

    curr.close()

def del_group(message,client_ID):
    pass


def add_friend(message, sender_ID):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    
    msg = {"type": message["type"], "ID": sender_ID}
    send_client(recipient[1],recipient[0],msg)
    curr.close()

def friend_key(message, sender_ID):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    
    msg = {"type": message["type"], "message": message["message"], "ID": sender_ID}
    send_client(recipient[1],recipient[0],msg)
    curr.close()


def single_message(message, sender_ID):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    
    # if not recipient:
    #     msg = {"type": "server", "message": "No such recipient"}
    #     send_msg(clients[sender_ID], json.dumps(msg).encode(format))
        # clients[sender_ID].send(json.dumps(msg).encode(format)) 
    # elif recipient[1] == 1:
    #     msg = {"type": message["type"], "message": message["message"], "ID": sender_ID}
    #     clients[int(recipient[0])].send(json.dumps(msg).encode(format))
    # else:
    #     msg = {"type": message["type"], "message": message["message"], "ID": sender_ID}
    #     curr.execute("""
    #         SELECT "Pending Messages" FROM "Clients" WHERE "ID" = %s
    #     """, (message["Recipient"],))
    #     prev_msgs = curr.fetchone()[0]

    #     curr.execute("""
    #         UPDATE "Clients"
    #         SET "Pending Messages" = %s
    #         WHERE "ID" = %s
    #     """, (prev_msgs.append(json.dumps(msg)), message["Recipient"]))
    #     db_conn.commit()
    msg = {"type": message["type"], "message": message["message"], "ID": sender_ID}
    send_client(recipient[1],recipient[0],msg)
    curr.close()


def single_image(message, sender_ID):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    
    # if not recipient:
    #     msg = {"type": "server", "message": "No such recipient"}
    #     send_msg(clients[sender_ID], json.dumps(msg).encode(format))
        # clients[sender_ID].send(json.dumps(msg).encode(format)) 
    # elif recipient[1] == 1:
    #     msg = {"type": message["type"],"title": message["title"], "message": message["message"], "ID": sender_ID}
    #     # clients[int(recipient[0])].send(json.dumps(msg).encode(format))
    #     send_msg(clients[int(recipient[0])], json.dumps(msg).encode(format))
    # else:
    #     msg = {"type": message["type"], "message": message["message"], "ID": sender_ID}
    #     curr.execute("""
    #         SELECT "Pending Messages" FROM "Clients" WHERE "ID" = %s
    #     """, (message["Recipient"],))
    #     prev_msgs = curr.fetchone()[0]

    #     curr.execute("""
    #         UPDATE "Clients"
    #         SET "Pending Messages" = %s
    #         WHERE "ID" = %s
    #     """, (prev_msgs.append(json.dumps(msg)), message["Recipient"]))
    #     db_conn.commit()
    msg = {"type": message["type"],"title": message["title"], "message": message["message"], "ID": sender_ID}
    send_client(recipient[1],recipient[0],msg)
    curr.close()

def group_add(message, sender_ID):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    # msg = {"type": message["type"], "message": message["message"], "ID": sender_ID,"Group_ID":}
    send_client(recipient[1],recipient[0],message)
    curr.close()


def handle_client(client, client_ID):
    while True:
        try:
            message = json.loads(recv_msg(client).decode(format))
            # message = json.loads(client.recv(buffer).decode(format))
            msg_type = message["type"]

            if msg_type == "single_message":
                single_message(message, client_ID)
            elif msg_type == "add_friend":
                add_friend(message, client_ID)
            elif msg_type == "friend_key":
                friend_key(message, client_ID)
            elif msg_type == "single_image":
                single_image(message, client_ID)
            elif msg_type == "create_group":
                create_group(message, client_ID)
            elif msg_type == "group_message":
                group_message(message, client_ID)
            elif msg_type == "kick":
                kick(message, client_ID)    
            elif msg_type == "add":
                add(message, client_ID) 
            elif msg_type == "Group_add":
                group_add(message,client_ID)   
            else:
                print("invalid query")

        except:
            client.close()
            del clients[client_ID]
            
            curr = db_conn.cursor()
            curr.execute("""
                UPDATE "Clients"
                SET "Status" = false
                WHERE "ID" = %s
            """,(client_ID,))
            curr.close()
            db_conn.commit()
            # index = clients.index(client)
            # clients.remove(client)
            # client.close()
            # alias = aliases[index]
            # broadcast(f'{alias} has left the chat room!'.encode('utf-8'))
            # aliases.remove(alias)
            break



def connect_server(server):
    ID = int(server[0])
    IP = server[1]
    Port = int(server[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((IP, Port))
    credentials = {"type":"server_auth","ID":my_ID,"password":"server_pass"}
    sock.send(json.dumps(credentials).encode('ascii'))

    print(f"Connected to server with ID:{ID}, IP:{IP}, Port:{Port}")
    other_servers[ID] = sock

    handle_server(sock)


def connect_servers():
    db_cur.execute("""
        SELECT * FROM "Server Info" WHERE "Status"='true'
    """)
    online_servers = db_cur.fetchall()

    db_cur.execute(f"""
        UPDATE "Server Info"
        SET "Status" = true
        WHERE "IP" = %s AND "Port" = %s
    """, (hostIP, hostPort))
    db_conn.commit()


    print("Connecting to previously online servers...")

    for server in online_servers:
        connect_server_thread = threading.Thread(target=connect_server, args=(server,))
        connect_server_thread.start()




# Receiving / Listening Function
def receive_client(client, ID):
    clients[ID] = client
    handle_client(client, ID)

#Recieving a server.
def receive_server(sock, ID):
    other_servers[ID] = sock
    handle_server(sock)


# TODO Hashing password
def client_reg(credentials):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT COUNT("ID") FROM "Clients"
    """)
    count = int(curr.fetchone()[0])

    curr.execute("""
        INSERT INTO "Clients" ("ID","Name", "Password", "Public Key", "Status")
        VALUES (%s, %s, %s, %s, %s)
    """, (count+1, credentials["Name"], credentials["Pass"], credentials["Public Key"], True))
    db_conn.commit()    
    curr.close()

    return (count+1)

def client_verify(credentials):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Password" FROM "Clients" WHERE "ID" = %s
    """, (credentials["ID"],))
    
    if credentials["Pass"] == curr.fetchone()[0]:
        curr.close()
        return int(credentials["ID"])
    else:
        curr.close()
        return 0




#A function which runs in an infinite loop and main purpose of this is to listen to any new connection.
def accept_connections():
    print("Listening for new Connections...")
    while True:
        sock, addr = server.accept()

        credentials = sock.recv(1024).decode('ascii')
        credentials = json.loads(credentials)

        is_server = 0
        server_id = None
        client_id = None
        if credentials["type"] == "server_auth":
            if credentials["password"] == "server_pass":
                is_server = 1
                server_id = credentials["ID"]
            else:
                sock.close()
                continue
        elif credentials["type"] == "client_auth":
            client_id = client_verify(credentials)
            if not client_id:
                msg = json.dumps({"verified":0, "msg": "Invalid credentials, please try again"})
                sock.send(msg.encode(format))
                sock.close()
                continue
            else:
                msg = json.dumps({"verified":1, "msg": "Successfully verified"})
                sock.send(msg.encode(format))
        elif credentials["type"] == "client_reg":
            client_id = client_reg(credentials)
            msg = {"type": "server", "ID": client_id}
            sock.send(json.dumps(msg).encode(format))
            sock.close()
            continue


        # curse = db_conn.cursor()
        # curse.execute("""
        #     SELECT "ID" FROM "Server Info"
        #     WHERE "IP" = %s AND "Port" = %s
        # """, (addr[0],addr[1]))

        # server_id = curse.fetchone()
        # curse.close()

        if is_server:
            print(f"Connected to server with ID:{server_id}, IP:{addr[0]}, Port:{addr[1]}")
            receive_server_thread = threading.Thread(target=receive_server, args=(sock,server_id))
            receive_server_thread.start()
        else:
            print(f"Connected to client with IP:{addr[0]}, Port:{addr[1]}")
            receive_client_thread = threading.Thread(target=receive_client, args=(sock,client_id))
            receive_client_thread.start()











# def connect_server(IP, port):
    


# server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server.bind((IP, port))
# server.listen()
# clients = []
# aliases = []


# def broadcast(message):
#     for client in clients:
#         client.send(message)

# # Function to handle clients'connections


# def handle_client(client):
#     while True:
#         try:
#             message = client.recv(1024)
#             broadcast(message)
#         except:
#             index = clients.index(client)
#             clients.remove(client)
#             client.close()
#             alias = aliases[index]
#             broadcast(f'{alias} has left the chat room!'.encode('utf-8'))
#             aliases.remove(alias)
#             break
# # Main function to receive the clients connection


# def receive():
#     while True:
#         print('Server is running and listening ...')
#         client, address = server.accept()
#         print(f'connection is established with {str(address)}')
#         client.send('alias?'.encode('utf-8'))
#         alias = client.recv(1024)
#         aliases.append(alias)
#         clients.append(client)
#         print(f'The alias of this client is {alias}'.encode('utf-8'))
#         broadcast(f'{alias} has connected to the chat room'.encode('utf-8'))
#         client.send('you are now connected!'.encode('utf-8'))
#         thread = threading.Thread(target=handle_client, args=(client,))
#         thread.start()


if __name__ == "__main__":
    connect_servers()
    accept_connections()