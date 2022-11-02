import socket
import threading

host = 'localhost'
port = int(input())

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
print("SERVER IS LISTENING")
server.listen()


# Lists For Clients and Their Nicknames
ID_password=dict()
ID_socket=dict()

#Keys is the ID of the group and value is the list of all the ID of clients in the group
groups = dict()

def send_to(message,ID):
    if(ID > 0): #Means it is a single person
        if ID in ID_socket.keys():
            ID_socket[ID].send(message.encode("ascii"))
            return True
    else:
        if ID in groups.keys():
            client_IDS = groups[ID]
            for client_ID in client_IDS: 
                ID_socket[client_ID].send(message.encode("ascii"))
            return True
    return False
    
# Handling Messages From Clients
def handle(client, clientID):
    while True:
        try:
            # Broadcasting Messages
            message = client.recv(1024).decode('ascii')
            # broadcast(message)
            ID=message.split(":")[0]
            msg = clientID+ ":" + message.split(":")[1]
            ID=ID.strip()
            if send_to(msg,ID):
                client.send(f"Received by {ID}".encode("ascii"))
            else:
                client.send(f"No such user".encode("ascii"))
        except:
            client.close()
            print(f"{client} went offline")
            break

# Receiving / Listening Function
def receive():
    while True:
        # Accept Connection
        client, address = server.accept()
        print("Connected with {}".format(str(address)))

        # Request And Store Nickname
        client.send('/AUTH'.encode('ascii'))
        ID=client.recv(1024).decode('ascii')
        pass_hash = client.recv(1024).decode('ascii')
        if ID in ID_password.keys():
            if not ID_password[ID]==pass_hash:
                client.send("Wrong password".encode("ascii"))  
        else:
            ID_password[ID]=pass_hash
            ID_socket[ID]=client
        client.send('You are connected to a server!'.encode('ascii'))

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,ID))
        thread.start()
        
receive()