# 'Chat Room Connection - Client-To-Client'
import sys
import threading
import socket
import json
from connect import connect

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


def handle_server(server):
    while True:
        try:
            message = server.recv(1024)
        except:
            # index = socks.index(sock)
            # socks.remove(sock)
            # sock.close()
            # alias = aliases[index]
            # broadcast(f'{alias} has left the chat room!'.encode('utf-8'))
            # aliases.remove(alias)
            break



def single_message(message, sender_ID):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    
    if not recipient:
        msg = {"type": "server", "message": "No such recipient"}
        clients[sender_ID].send(json.dumps(msg).encode(format)) 
    elif recipient[1] == 1:
        msg = {"type": message["type"], "message": message["message"], "ID": sender_ID}
        clients[int(recipient[0])].send(json.dumps(msg).encode(format))
    else:
        msg = {"type": message["type"], "message": message["message"], "ID": sender_ID}
        curr.execute("""
            SELECT "Pending Messages" FROM "Clients" WHERE "ID" = %s
        """, (message["Recipient"],))
        prev_msgs = curr.fetchone()[0]

        curr.execute("""
            UPDATE "Clients"
            SET "Pending Messages" = %s
            WHERE "ID" = %s
        """, (prev_msgs.append(json.dumps(msg)), message["Recipient"]))
        db_conn.commit()
    
    curr.close()




def handle_client(client, client_ID):
    while True:
        try:
            message = json.loads(client.recv(buffer).decode(format))
            msg_type = message["type"]

            if msg_type == "single_message":
                single_message(message, client_ID)
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
    ID = server[0]
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
    msg = {"verified":1, "msg": "Welcome!"}
    client.send(json.dumps(msg).encode(format))
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
    count = curr.fetchone()[0]

    curr.execute("""
        INSERT INTO "Clients" ("ID","Name", "Password", "Public Key", "Status")
        VALUES (%s, %s, %s, %s, %s)
    """, (count+1, credentials["Name"], credentials["Pass"], credentials["Public Key"], True))
    db_conn.commit()

    

    
    curr.close()

    return count

def client_verify(credentials):
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Password" FROM "Clients" WHERE "ID" = %s
    """, (credentials["ID"],))
    curr.close()

    if credentials["Pass"] == curr.fetchone()[0]:
        return True
    else:
        return False




#A function which runs in an infinite loop and main purpose of this is to listen to any new connection.
def accept_connections():
    print("Listening for new Connections...")
    while True:
        sock, addr = server.accept()

        credentials = sock.recv(1024).decode('ascii')
        credentials = json.loads(credentials)

        is_server = 0
        server_id = None

        if credentials["type"] == "server_auth":
            if credentials["password"] == "server_pass":
                is_server = 1
                server_id = credentials["ID"]
            else:
                sock.close()
                continue
        elif credentials["type"] == "client_auth":
            if not client_verify(credentials):
                msg = json.loads({"verified":0, "msg": "Invalid credentials, please try again"})
                sock.send(msg.encode(format))
                sock.close()
                continue
            else:
                msg = json.loads({"verified":1, "msg": "Successfully verified"})
                sock.send(msg.encode(format))
        elif credentials["type"] == "client_reg":
            client_id = client_reg(credentials)
            msg = {"type": "server", "ID": client_id}
            sock.send(json.dumps(msg).encode(format))
        

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