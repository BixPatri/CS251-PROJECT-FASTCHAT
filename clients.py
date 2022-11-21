import socket
import threading
import json


# Listening to Server and Sending Nickname
def receive():
    while True:
        try:
            message = json.loads(client.recv(1024).decode('ascii'))
            print(message["type"]+":"+message["text"])
            # if message == '/AUTH':
            #     # client.send((ID+":"+passwd).encode('ascii'))
            #     authenticate()
            
        except:
            print("An error occured!")
            client.close()
            break

def single_message():
    reciepient=int(input("Reciever"))
    message=input("Message Text")
    mess={"type":"single_message","Reciepient":reciepient,"message":message}
    client.send(json.dumps(mess).encode('ascii'))

def group_message():
    Group=int(input("Reciever"))
    message=input("Message Text")
    mess={"type":"group_message","Reciepient":Group,"message":message}
    client.send(json.dumps(mess).encode('ascii'))

def create_group():
    g_ID=int(input("group_id"))
    mem=input("members")
    Members=[Credentials["ID"]]
    for member in mem.split():
        Members.append(int(member))
    mess={"type":"create_group","g_ID":g_ID,"Members":Members}
    client.send(json.dumps(mess).encode('ascii'))


def ban():
    g_ID=int(input("group_id"))
    ban_ID=int(input("ban ID"))
    mess={"type":"ban","g_ID":g_ID,"ban_ID":ban_ID}
    client.send(json.dumps(mess).encode('ascii'))

def del_group():
    g_ID=int(input("group_id"))
    mess={"type":"del_group","g_ID":g_ID}
    client.send(json.dumps(mess).encode('ascii'))
    
def Command(Command_type):
    if Command_type=="create_group":
        create_group()
    elif Command_type=="single_message":
        single_message()
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
def write():
    while True:
        Command_type=input()
        if Command(Command_type):
            print("Done")
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
        # client.send(message.encode('ascii'))
        
        


#Take the input ID of the port you want to connect to
port = int(input())

# Choosing Nickname
ID = int(input("Enter Your ID: "))
passwd = input("Enter Your Password: ")

Credentials={"ID":ID,"password":passwd}

# Connecting To the main load balancer server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', port))
        
        
def authenticate():
    client.send(json.dumps(Credentials).encode('ascii'))

authenticate()
welcome_message=client.recv(1024).decode('ascii')
print(welcome_message)
print("""
To message-type "single_message" then the message then the message text
To Group_message-type "group_message" then the message then the message text
To Create Group-type "create_group" then group id then members(space separated)
To ban from group-type "ban" then group id and then ban id
To delete Group- type "del_group" then group id
""")


# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()