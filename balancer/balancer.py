import socket
import threading
from connect import connect
import random 
import sys
random.seed(0)

format = 'utf-8'
buffer = 1024

#BALANCER ACCEPTING SOCKET
balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
balancer.bind(("localhost", 9091))
balancer.listen()

#Connection with the database
(db_conn, db_cur) = connect()

#Round robin counter
counter = -1

# strategy 
strategy = sys.argv[1]

def handle_client(sock):
    """
    Handles a client and give it a server it should send its next message to.

    :param sock: The socket of the client.
    :type sock: socket
    """
    while(True):
        try:
            request = sock.recv(buffer).decode(format)
            print("balancer received")      
            server_id = str(return_server(strategy))
            sock.send(server_id.encode(format))
        except Exception as error:
            print(error)
            print("Client went offline")
            sock.close()
            break

def receive_client():
    """
    Receives clients and makes threads of handle function for each client.
    """
    while(True):
        sock, add = balancer.accept()
        thread = threading.Thread(target=handle_client, args=(sock,))
        thread.start()
        

def return_server(strategy):
    """
    Returns a server based on a strategy which is a command line argument to the program
    
    :param strategy: The strategy for load balancing namely random, round robin, minimun load.
    :type strategy: str
    """
    global counter
    if(strategy == "rand"):
        db_cur.execute("""
            SELECT "ID" FROM "Server Info" WHERE "Status" = true 
        """) 
        Ids = db_cur.fetchall()
        print("Assigned server is ", int(random.choice(Ids)[0]))
        return int(random.choice(Ids)[0])
    
    elif (strategy == "round_robin"):
        db_cur.execute("""
            SELECT "ID" FROM "Server Info" WHERE "Status" = true 
        """) 
        Ids = db_cur.fetchall()
        size = len(Ids)
        counter = counter+1
        print("Assigned server is ", Ids[counter%size][0])
        return Ids[counter%size][0]
    
    elif (strategy == "min_load"):
        db_cur.execute("""
            SELECT "ID","Load" FROM "Server Info" WHERE "Status" = true 
        """) 
        Ids = db_cur.fetchall()
        Ids.sort(key=lambda tup: tup[1])
        to_ret = Ids[0][0]
        print("Assigned server is ", to_ret)
        return to_ret
    return -1   

if __name__ == "__main__":
    receive_client()