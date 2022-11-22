import os
import socket
import threading
import json
import sys
from connect import connect
from packets import send_msg
from packets import recv_msg
import base64


buffer = 1024
format = 'utf-8'

balancerIP = "localhost"
balancerPort = 9091

# my_name = "Kevin"
# my_pass = "hello"
my_ID = -1
curr_server_ID = 0

(db_conn, db_cur) = connect()

servers = {}


def get_server(balancer):
    balancer.send("gib server".encode(format))
    server_id = balancer.recv(buffer).decode(format)
    return int(server_id)

def register(server):
    IP = server[1]
    Port = int(server[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((IP, Port))
    credentials = {"type":"client_reg", "Name":my_name, "Pass":my_pass, "Public Key":"1234"}
    sock.send(json.dumps(credentials).encode(format))
    received_info = json.loads(sock.recv(buffer).decode(format))
    id = received_info["ID"]
    print(f"Successfully Registered with ID: {id}")
    sock.close()

    return id

def connect_server(server):
    ID = int(server[0])
    IP = server[1]
    Port = int(server[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while(True):
        sock.connect((IP, Port))
        global my_pass
        credentials = {"type":"client_auth", "Name":my_name, "Pass":my_pass, "Public Key":"1234", "ID": my_ID}
        sock.send(json.dumps(credentials).encode(format))

        allowed = sock.recv(buffer).decode(format)
        print(allowed)
        allowed = json.loads(allowed)
        if allowed["verified"]:
            print(f"Connected to server with ID:{ID}, IP:{IP}, Port:{Port}")
            servers[ID] = sock
            handle_server(sock)
            break
        else:
            my_pass = input("Re-Enter the Password: ")
            sock.close()

def connect_servers():
    db_cur.execute("""
        SELECT * FROM "Server Info" WHERE "Status"='true'
    """)
    online_servers = db_cur.fetchall()

    global my_ID
    if my_ID <= 0:
        my_ID = register(online_servers[0])

    for server in online_servers:
        connect_server_thread = threading.Thread(target=connect_server, args=(server,))
        connect_server_thread.start()


def handle_server(server):
    while True:
        try:
            # message = server.recv(buffer).decode(format)
            message = recv_msg(server).decode(format)
            # print("msg", message)
            message = json.loads(message)

            if message["type"] == "single_message":
                # print(message["ID"], message["message"])
                print("msg", message)
            elif message["type"] == "single_image":
                # print(message["ID"], message["message"])
                print("image")
                with open("received_"+message["title"], mode='wb') as file:
                    file.write(base64.decodebytes(message["message"].encode(format)))
            

        except Exception as error:
            print(error)
            server.close()
            print("An error occured!")
            break


# # Listening to Server and Sending Nickname
# def receive():
#     while True:
#         try:
#             message = json.loads(servers[curr_server_ID].recv(buffer).decode(format))
#             print(message["type"]+":"+message["text"])
#             # if message == '/AUTH':
#             #     # client.send((ID+":"+passwd).encode(format))
#             #     authenticate()
            
#         except:
#             print("An error occured!")
#             servers[curr_server_ID].close()
#             break

def single_message():
    recipient = int(input("Reciever"))
    message = input("Message Text")
    msg = {"type":"single_message", "Recipient":recipient, "message":message, "ID":my_ID}
    send_msg(servers[curr_server_ID], json.dumps(msg).encode(format))
    # servers[curr_server_ID].send(json.dumps(msg).encode(format))

def single_image():
    recipient = int(input("Reciever"))
    path = input("Image path? ")
    title = os.path.basename(path)
    img = None
    with open(path, mode='rb') as file:
        img = file.read()
    msg = {"type":"single_image","title": title, "Recipient":recipient, "message":base64.encodebytes(img).decode(format), "ID":my_ID}
    # msg["message"] = 
    send_msg(servers[curr_server_ID], json.dumps(msg).encode(format))
    # servers[curr_server_ID].send(json.dumps(msg).encode(format))

def group_message():
    Group=int(input("Reciever"))
    message=input("Message Text")
    mess={"type":"group_message","Reciepient":Group,"message":message}
    client.send(json.dumps(mess).encode(format))

def create_group():
    g_ID=int(input("group_id"))
    mem=input("members")
    Members=[Credentials["ID"]]
    for member in mem.split():
        Members.append(int(member))
    mess={"type":"create_group","g_ID":g_ID,"Members":Members}
    client.send(json.dumps(mess).encode(format))


def ban():
    g_ID=int(input("group_id"))
    ban_ID=int(input("ban ID"))
    mess={"type":"ban","g_ID":g_ID,"ban_ID":ban_ID}
    client.send(json.dumps(mess).encode(format))

def del_group():
    g_ID=int(input("group_id"))
    mess={"type":"del_group","g_ID":g_ID}
    client.send(json.dumps(mess).encode(format))
    
def Command(Command_type):
    if Command_type=="create_group":
        create_group()
    elif Command_type=="single_message":
        single_message()
    elif Command_type == "single_image":
        single_image()
    elif Command_type=="group_message":
        group_message()
    elif Command_type=="ban":
        ban()
    elif Command_type=="del_group":
        del_group()
    else:
        return False
    return True

# Sending Messages To Server from this client
def write(balancer_sock):
    count = 0
    while True:
        if count <= 0:
            global curr_server_ID
            curr_server_ID = get_server(balancer_sock)
            count = 5

        Command_type=input()
        if Command(Command_type):
            print("Done")
            count -= 1
        else:
            print("Invalid Query")
        # pID = input("kisko bhejna hai? ")
        # msg = input("Are bhai kehna kya chahte ho? ")
        # # if msg=="image":
        # #     i=input("Image Name")
        # #     file=open(i,'rb')
        # #     file.read(1024)
        # #     file
        # message =pID+":"+msg
        # print(message)
        # client.send(message.encode(format))
        
        


# #Take the input ID of the port you want to connect to
# port = int(input())

# # Choosing Nickname
# ID = int(input("Enter Your ID: "))
# passwd = input("Enter Your Password: ")

# Credentials={"ID":ID,"password":passwd}

# # Connecting To the main load balancer server
# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client.connect(('localhost', port))
        
        
# def authenticate():
#     client.send(json.dumps(Credentials).encode(format))

# authenticate()
# # welcome_message=client.recv(1024).decode(format)
# # print(welcome_message)
# print("""
# To message-type "single_message" then the message then the message text
# To Group_message-type "group_message" then the message then the message text
# To Create Group-type "create_group" then group id then members(space separated)
# To ban from group-type "ban" then group id and then ban id
# To delete Group- type "del_group" then group id
# """)





# if __name__ == "__main__":
#     global my_ID
#     global my_name
#     global my_pass
my_ID = int(sys.argv[1])
# Choosing Nickname
# ID = int(input("Enter Your ID: "))
my_name = input("Enter Your Name: ")
my_pass = input("Enter Your Password: ")

connect_servers()
# connect_balancer()
balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
balancer.connect((balancerIP, balancerPort))
    
    
print("""
    To message-type "single_message" then the message then the message text
    To Group_message-type "group_message" then the message then the message text
    To Create Group-type "create_group" then group id then members(space separated)
    To ban from group-type "ban" then group id and then ban id
    To delete Group- type "del_group" then group id
""")
# Starting Threads For Listening And Writing
write_thread = threading.Thread(target=write, args=(balancer,))
write_thread.start()

    