import socket
import threading
import json

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
                print(client_ID)
                ID_socket[client_ID].send(message.encode("ascii"))
            return True
    return False
        
def single_message(message,ID):
    print(message)
def group_message(message,ID):
    print(message)
def create_group(message,ID):
    print(message)
def ban(message,ID):
    print(message)
def del_group(message,ID):
    print(message)
# Handling Messages From Clients
def handle(client, clientID):
    while True:
        try:
            print("FUCK")
            mess = json.loads(client.recv(1024).decode('ascii'))
            print(mess['type'])
            print(type(mess))
            if mess['type']=="single_message":
                print("HI")
                single_message(mess,clientID)
            elif mess['type']=="group_message":
                group_message(mess,clientID)
            elif mess['type']=="create_group":
                create_group(mess,clientID)
            elif mess['type']=="ban":
                ban(mess,clientID)
            elif mess['type']=="del_group":
                del_group(mess,clientID)
            else:
                print("H2I")
                print("Invalid request")
            print("H3I")
            # if message
            # ID=int(message.split(":")[0].strip())
            # msg = message.split(":")[1]
            # if msg[0]=="/":
            #     command(msg)
            #     continue
            # msg=str(clientID)+ ":" + msg
            # print(msg,ID)
            # if send_to(msg,ID):
            #     client.send(f"Received by {ID}".encode("ascii"))
            # else:
            #     client.send(f"No such user".encode("ascii"))
                
        except:
            client.close()
            print(f"{client} went offline")
            break

def Verify(credentials):
    return credentials["password"]==ID_password[credentials["ID"]]
def Add(credentials,client):
    ID_password[credentials["ID"]]=credentials["password"]
    ID_socket[credentials["ID"]]=client
    
# Receiving / Listening Function
def receive():
    while True:
        client, address = server.accept()
        credentials=client.recv(64).decode('ascii')
        credentials=json.loads(credentials)
        if credentials["ID"] in ID_password.keys():
            if not Verify(credentials):
                client.send("""ID already Present
                                Wrong Password""")
                client.close()
                continue
            else:
                client.send("""ID already Present
                                Verified""")
        else:
            Add(credentials,client)
            client.send("""New ID created""".encode("ascii"))
        print("Connected with {}".format(str(address)))
        thread = threading.Thread(target=handle, args=(client,credentials["ID"]))
        thread.start()
        
receive()