import socket
import threading
import json

host = 'localhost'
port = int(input())

def mess_json(t,text):
    d={"type":t,"text":text}
    return json.dumps(d)


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

# def send_to(message,ID):
#     if(ID > 0): #Means it is a single person
#         if ID in ID_socket.keys():
#             ID_socket[ID].send(message.encode("ascii"))
#             return True
#     else:
#         if ID in groups.keys():
#             client_IDS = groups[ID]
#             for client_ID in client_IDS: 
#                 print(client_ID)
#                 ID_socket[client_ID].send(message.encode("ascii"))
#             return True
#     return False
        
def single_message(message,ID):
    if message["Reciepient"]in ID_socket.keys():
        ID_socket[message["Reciepient"]].send(mess_json("private "+str(ID),message[["message"]]).encode("ascii"))
        return True
    return False
def group_message(message,ID):
    if message["Reciepient"] in groups.keys():
        for i in groups["Reciepient"]:
            ID_socket[i].send(mess_json("Group "+str(message["Reciepient"])+str(ID),message[["message"]]).encode("ascii"))
        return True
    return False
def create_group(message,ID):
    if message["g_ID"] in groups.keys():
        return False
    else:
        for member_ID in message["Members"]:
            if member_ID not in ID_password.keys():
                return False
        for member_ID in message["Members"]:
            ID_socket[member_ID].send(mess_json("Group "+str(message["g_ID"])+str(ID),"Added to Group with"+str(message["Members"])))
        groups[message["g_ID"]]=message["Members"]
        return True
def ban(message,ID):
    if message["g_ID"] in groups.keys():
        if ID==groups[message["g_ID"]][0]:#admin check
            if message["ban_ID"] in groups[message["g_ID"]]:
                groups[message["g_ID"]].remove(message["ban_ID"])
                return True
    return False
def del_group(message,ID):
    if message["g_ID"] in groups.keys():
        if ID==groups[message["g_ID"]][0]:#admin check
            del groups[message["g_ID"]]
            return True
    return False
    # print(message)
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
                client.send(mess_json("server","""ID already Present Wrong Password""").encode('ascii'))
                client.close()
                continue
            else:
                client.send(mess_json("server","""ID already Present Verified""").encode('ascii'))
        else:
            Add(credentials,client)
            client.send(mess_json("server","""New ID created""").encode("ascii"))
        print("Connected with {}".format(str(address)))
        thread = threading.Thread(target=handle, args=(client,credentials["ID"]))
        thread.start()
        
receive()