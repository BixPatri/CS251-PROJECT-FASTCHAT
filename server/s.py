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

def handle_client(client):
    while True:
        try:
            message = json.loads(client.recv(buffer).decode(format))

            if message["type"] == "client_reg":
                

        except:
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
def receive_client(client):
    # clients[ID] = client
    # # Request And Store Nickname
    # client.send('/AUTH'.encode('ascii'))
    # client_recv=client.recv(1024).decode('ascii')
    # ID=int(client_recv.split(":")[0].strip())
    # pass_hash = int(client_recv.split(":")[1].strip())
    # print(ID,pass_hash)
    # if ID in ID_password.keys():
    #     if not ID_password[ID]==pass_hash:
    #         client.send("Wrong password".encode("ascii"))
    #         print("password sahi nahi dala")
    #         client.close()
    #         continue
    #     else:
    #         print("OK")
    # else:
    #     ID_password[ID]=pass_hash
    #     ID_socket[ID]=client
    #     print("adding new")
    # print("Connected with {}".format(str(address)))
    # client.send('You are connected to a server!'.encode('ascii'))

    # Start Handling Thread For Client
    thread = threading.Thread(target=handle_client, args=(client,))
    thread.start()

#Recieving a server.
def receive_server(sock, ID):
    other_servers[ID] = sock
    handle_server(sock)

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
        elif credentials["type"] == "client_auth":
            if not client_verify():
                sock.close()
        elif credentials["type"] == "client_reg":
            if not client_reg():
                sock.close()
        

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
            receive_client_thread = threading.Thread(target=receive_client, args=(sock,))
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