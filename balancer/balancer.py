import socket
import threading
from connect import connect
import random 
random.seed(0)

format = 'utf-8'
buffer = 1024

#BALANCER ACCEPTING SOCKET
balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
balancer.bind(("localhost", 9090))
balancer.listen()

#Connection with the database
(db_conn, db_cur) = connect()

def handle_client(sock):
    while(True):
        try:
            request = sock.recv(buffer).decode(format)        
            a = return_server("rand")
            sock.send(a.encode(format))
        except:
            print("Client went offline")

def recieve_client():
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
        return random.choice(Ids)
    # pass
    return -1   

if __name__ == "__main__":
    recieve_client()