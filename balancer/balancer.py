import socket
import threading
from connect import connect
import random 
random.seed(0)

format = 'utf-8'
buffer = 1024

#BALANCER ACCEPTING SOCKET
balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
balancer.bind(("localhost", 9091))
balancer.listen()

#Connection with the database
(db_conn, db_cur) = connect()

def handle_client(sock):
    while(True):
        try:
            request = sock.recv(buffer).decode(format)
            print("balancer received")      
            server_id = str(return_server("rand"))
            sock.send(server_id.encode(format))
        except Exception as error:
            print(error)
            print("Client went offline")
            sock.close()
            break

def receive_client():
    while(True):
        sock, add = balancer.accept()
        thread = threading.Thread(target=handle_client, args=(sock,))
        thread.start()
        
def chckload():
    pass

def return_server(strategy):
    if(strategy == "rand"):
        db_cur.execute("""
            SELECT "ID" FROM "Server Info" WHERE "Status" = true 
        """) 
        Ids = db_cur.fetchall()
        return int(random.choice(Ids)[0])
    # pass
    return -1   

if __name__ == "__main__":
    receive_client()