# 'Chat Room Connection - Client-To-Client'
import threading
import socket
from connect import connect

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, port))
server.listen()


(db_conn, db_cur) = connect()

def connect_servers():
    db_cur.execute("""
        SELECT COUNT("ID") FROM "Server Info"
    """)
    c = db_cur.fetchone()
    print(c[0])

    db_cur.execute("""
        SELECT * FROM "Server Info" WHERE "Status"='true'
    """)
    t = db_cur.fetchall()



    print(t)

connect_servers()

def connect_server(IP, port):
    


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


# if __name__ == "__main__":
#     serve(socket.gethostbyname(socket.gethostname()), 59000)
#     receive()