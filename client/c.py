import os
import socket
import threading
import json
import sys
from connect import connect
from packets import send_msg
from packets import recv_msg
import base64
import sqlite3
import rsa
from Crypto.Cipher import AES
from secrets import token_bytes
from cryptography.fernet import Fernet

buffer = 1024
format = 'utf-8'

balancerIP = "127.0.0.1"
balancerPort = 9091

# my_name = "Kevin"
# my_pass = "hello"
my_ID = -1
curr_server_ID = 0
private_key = 0
public_key = 0

(db_conn, db_cur) = connect()

servers = {}


def get_server(balancer):
    balancer.send("gib server".encode(format))
    server_id = balancer.recv(buffer).decode(format)
    print(server_id)
    return int(server_id)

def register(server,pub_str):
    IP = server[1]
    Port = int(server[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((IP, Port))
    credentials = {"type":"client_reg", "Name":my_name, "Pass":my_pass, "Public Key":pub_str}
    sock.send(json.dumps(credentials).encode(format))
    received_info = json.loads(sock.recv(buffer).decode(format))
    id = received_info["ID"]
    # personal_curr.execute("""
    #     INSERT INTO 
    # """)
    
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

        credentials = {"type":"client_auth", "Pass":my_pass, "ID": my_ID}
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
    print(online_servers)

    global my_ID
    global personal_conn
    global personal_curr
    global public_key
    if my_ID <= 0:
        (pubkey, privkey) = rsa.newkeys(512)
        public_key = pubkey
        priv_str = privkey.save_pkcs1(format='PEM').decode()
        pub_str = pubkey.save_pkcs1(format='PEM').decode()

        my_ID = register(online_servers[0], pub_str)
        personal_curr.close()
        personal_conn.close()
        os.rename("tmp.db", f"{my_ID}.db")
        personal_conn = sqlite3.connect(f"{my_ID}.db")
        personal_curr= personal_conn.cursor() 
        personal_curr.execute(f"""
            INSERT INTO "Single_keys" ("ID", "Name", "Public Key") VALUES ({my_ID},"You", "{priv_str}")
        """)
        personal_conn.commit()

    for server in online_servers:
        connect_server_thread = threading.Thread(target=connect_server, args=(server,))
        connect_server_thread.start()


def handle_server(server):
    while True:
        try:
            # message = server.recv(buffer).decode(format)
            message = recv_msg(server).decode(format)
            # print("hello")
            # print("msg=", message)
            message = json.loads(message)

            # if message["type"] == "single_message":
            #     print(message["ID"], message["message"])
            if message["type"] == "single_message":
                local_conn = sqlite3.connect(f"{my_ID}.db")
                local_curr = local_conn.cursor() 
                local_curr.execute(f"""
                    SELECT "Symmetric Key" FROM "Single_keys" WHERE "ID" = {message["ID"]}
                """)
                key = local_curr.fetchone()[0]
                key_obj = Fernet(key.encode())

                msg = key_obj.decrypt(message["message"].encode()).decode()

                print(msg)
                local_curr.close()
                local_conn.close()
                # print(message["ID"], message["message"])
                # print("msg", message)
            elif message["type"] == "single_image":
                # print(message["ID"], message["message"])
                local_conn = sqlite3.connect(f"{my_ID}.db")
                local_curr = local_conn.cursor() 
                local_curr.execute(f"""
                    SELECT "Symmetric Key" FROM "Single_keys" WHERE "ID" = {message["ID"]}
                """)
                key = local_curr.fetchone()[0]
                key_obj = Fernet(key.encode())

                msg = key_obj.decrypt(message["message"].encode()).decode()

                print("image")
                with open("received_"+message["title"], mode='wb') as file:
                    file.write(base64.decodebytes(msg.encode(format)))

                local_curr.close()
                local_conn.close()

                
            elif message["type"] == "add_friend":
                accept_friend(message)
            elif message["type"] == "friend_key":
                friend_key(message)
            else:
                print(message)

        except Exception as error:
            print(error)
            server.close()
            print("An error occured!")
            break



def add_friend():
    
    recipient = int(input("Receiver ID? "))
    # enc_msg = rsa.encrypt(message.encode(),)
    # msg = {"type":"single_message", "Recipient":recipient, "message":message, "ID":my_ID}
    # send_msg(servers[curr_server_ID], json.dumps(msg).encode(format))
    # servers[curr_server_ID].send(json.dumps(msg).encode(format))
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "ID","Public Key" FROM "Single_keys" WHERE "ID" = {recipient}
    """)

    a = local_curr.fetchone()
    if not a:
        db_cur.execute(f"""
        SELECT "ID", "Public Key" FROM "Clients" WHERE "ID" = {recipient}
        """)
        g = db_cur.fetchone()
        local_curr.execute(f"""
            INSERT INTO "Single_Keys" ("ID","Public Key") VALUES ({g[0]},"{g[1]}")
        """)
        local_conn.commit()
        a=g
        # msg = {"type":"single_message", "Recipient":recipient, "message":rsa.encrypt(message,g[1]), "ID":my_ID}

        # servers[curr_server_ID].send(json.dumps(msg).encode(format))
    
    # receiver_pubk = rsa.key.PublicKey.load_pkcs1(a[1].encode(), format='PEM')
    msg = {"type":"add_friend", "Recipient":recipient}
    send_msg(servers[curr_server_ID],json.dumps(msg).encode(format))

    local_curr.close()
    local_conn.close()


def accept_friend(message):
    recipient = message["ID"]
    print(f"Friend req from {recipient}")

    key = Fernet.generate_key()

    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "ID","Public Key" FROM "Single_keys" WHERE "ID" = {recipient}
    """)

    a = local_curr.fetchone()
    if not a:
        db_cur.execute(f"""
            SELECT "ID", "Public Key" FROM "Clients" WHERE "ID" = {recipient}
        """)
        g = db_cur.fetchone()
        local_curr.execute(f"""
            INSERT INTO "Single_Keys" ("ID","Public Key", "Symmetric Key") VALUES ({g[0]},"{g[1]}","{key.decode()}")
        """)
        local_conn.commit()
        a=g
        # msg = {"type":"single_message", "Recipient":recipient, "message":rsa.encrypt(message,g[1]), "ID":my_ID}

        # servers[curr_server_ID].send(json.dumps(msg).encode(format))
    else:
        local_curr.execute(f"""
            UPDATE "Single_Keys" 
            SET "Symmetric Key" = "{key.decode()}"
            WHERE "ID" = {recipient}
        """)
    
    receiver_pubk = rsa.key.PublicKey.load_pkcs1(a[1].encode(), format='PEM')
    msg = {"type":"friend_key", "Recipient":recipient, "message":base64.encodebytes(rsa.encrypt(key, receiver_pubk)).decode(format), "ID":my_ID}
    send_msg(servers[curr_server_ID],json.dumps(msg).encode(format))

    local_curr.close()
    local_conn.close()


def friend_key(message):
    friend = message["ID"]
    print(f"request accepted from {friend}")
    key = rsa.decrypt(base64.decodebytes(message["message"].encode(format)),private_key)
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    print(key.decode())
    local_curr.execute(f"""
        UPDATE "Single_Keys" 
        SET "Symmetric Key" = "{key.decode()}"
        WHERE "ID" = {friend}
    """)
    local_curr.close()
    local_conn.commit()
    local_conn.close()





def single_message():
    recipient = int(input("Reciever"))
    message = input("Message Text")
    # enc_msg = rsa.encrypt(message.encode(),)
    # msg = {"type":"single_message", "Recipient":recipient, "message":message, "ID":my_ID}
    # send_msg(servers[curr_server_ID], json.dumps(msg).encode(format))
    # servers[curr_server_ID].send(json.dumps(msg).encode(format))
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "ID","Public Key","Symmetric Key" FROM "Single_keys" WHERE "ID" = {recipient}
    """)

    a = local_curr.fetchone()
    if not a:
        db_cur.execute(f"""
        SELECT "ID", "Public Key" FROM "Clients" WHERE "ID" = {recipient}
        """)
        g = db_cur.fetchone()
        local_curr.execute(f"""
            INSERT INTO "Single_Keys" ("ID","Public Key") VALUES ({g[0]},"{g[1]}")
        """)
        local_conn.commit()
        a=g
        # msg = {"type":"single_message", "Recipient":recipient, "message":rsa.encrypt(message,g[1]), "ID":my_ID}

        # servers[curr_server_ID].send(json.dumps(msg).encode(format))
    
    # receiver_pubk = rsa.key.PublicKey.load_pkcs1(a[1].encode(), format='PEM')
    # msg = {"type":"single_message", "Recipient":recipient, "message":base64.encodebytes(rsa.encrypt(message.encode(), receiver_pubk)).decode(format), "ID":my_ID}

    key = a[2].encode()
    key_obj=Fernet(key)
    encrypted_message = key_obj.encrypt(message.encode())

    msg = {"type":"single_message", "Recipient":recipient, "message":encrypted_message.decode(format), "ID":my_ID}

    send_msg(servers[curr_server_ID],json.dumps(msg).encode(format))

    local_curr.close()
    local_conn.close()


def single_image():
    recipient = int(input("Reciever"))
    path = input("Image path? ")
    title = os.path.basename(path)
    img = None
    with open(path, mode='rb') as file:
        img = file.read()
    
    message = base64.encodebytes(img).decode(format)
    
    # msg = {"type":"single_image","title": title, "Recipient":recipient, "message":base64.encodebytes(img).decode(format), "ID":my_ID}
    # # msg["message"] = 
    # send_msg(servers[curr_server_ID], json.dumps(msg).encode(format))


    # recipient = int(input("Reciever"))
    # message = input("Message Text")
    # enc_msg = rsa.encrypt(message.encode(),)
    # msg = {"type":"single_message", "Recipient":recipient, "message":message, "ID":my_ID}
    # send_msg(servers[curr_server_ID], json.dumps(msg).encode(format))
    # servers[curr_server_ID].send(json.dumps(msg).encode(format))
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "ID","Public Key","Symmetric Key" FROM "Single_keys" WHERE "ID" = {recipient}
    """)

    a = local_curr.fetchone()
    if not a:
        db_cur.execute(f"""
        SELECT "ID", "Public Key" FROM "Clients" WHERE "ID" = {recipient}
        """)
        g = db_cur.fetchone()
        local_curr.execute(f"""
            INSERT INTO "Single_Keys" ("ID","Public Key") VALUES ({g[0]},"{g[1]}")
        """)
        local_conn.commit()
        a=g
        # msg = {"type":"single_message", "Recipient":recipient, "message":rsa.encrypt(message,g[1]), "ID":my_ID}

        # servers[curr_server_ID].send(json.dumps(msg).encode(format))
    
    # receiver_pubk = rsa.key.PublicKey.load_pkcs1(a[1].encode(), format='PEM')
    # msg = {"type":"single_message", "Recipient":recipient, "message":base64.encodebytes(rsa.encrypt(message.encode(), receiver_pubk)).decode(format), "ID":my_ID}

    key = a[2].encode()
    key_obj=Fernet(key)
    
    encrypted_message = key_obj.encrypt(message.encode())

    # msg = {"type":"single_message", "Recipient":recipient, "message":encrypted_message.decode(format), "ID":my_ID}
    msg = {"type":"single_image","title": title, "Recipient":recipient, "message":encrypted_message.decode(format), "ID":my_ID}

    send_msg(servers[curr_server_ID],json.dumps(msg).encode(format))

    local_curr.close()
    local_conn.close()

def group_message():
    Group=int(input("group_id "))
    message=input("Message Text ")
    mess={"type":"group_message","group_id":Group,"message":message}
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    # servers[curr_server_ID].send(json.dumps(mess).encode(format))

def create_group():
    g_encryption_key = token_bytes(16)
    # personal_curr.execute("""
    #     INSERT INTO "Group_keys" ("ID")
    # """)
    g_ID=input("Group_Name")
    mem=input("Members")
    Members=[my_ID]
    for member in mem.split():
        Members.append(int(member))
    mess={"type":"create_group","Group_Name":g_ID,"Members":Members}
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    # servers[curr_server_ID].send(json.dumps(mess).encode(format))

def kick():
    g_ID=int(input("group_id"))
    ban_ID=int(input("ban ID"))
    mess={"type":"kick","g_ID":g_ID, "ban_ID":ban_ID}
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    # servers[curr_server_ID].send(json.dumps(mess).encode(format))

def add():
    g_ID=int(input("group_id"))
    add_ID=int(input("add ID"))
    mess={"type":"add","g_ID":g_ID, "add_ID":add_ID}
    # print("hello")
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    # servers[curr_server_ID].send(json.dumps(mess).encode(format))

def del_group():
    g_ID=int(input("group_id"))
    mess={"type":"del_group","g_ID":g_ID}
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    # servers[curr_server_ID].send(json.dumps(mess).encode(format))
    
def Command(Command_type):
    if Command_type=="create_group":
        create_group()
    elif Command_type == "add_friend":
        add_friend()
    elif Command_type=="single_message":
        single_message()
    elif Command_type == "single_image":
        single_image()
    elif Command_type=="group_message":
        group_message()
    elif Command_type=="kick":
        kick()
    elif Command_type=="add":
        add()
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

personal_conn = None
personal_curr = None

if my_ID <=0 :
    personal_conn = sqlite3.connect(f"tmp.db")
    personal_curr=personal_conn.cursor()

else:
    personal_conn = sqlite3.connect(f"{my_ID}.db")
    personal_curr=personal_conn.cursor() 

personal_curr.execute("""CREATE TABLE IF NOT EXISTS "Single_keys" 
(
    "ID" integer NOT NULL,
    "Name" text,
    "Public Key" text NOT NULL,
    "Symmetric Key" text,
    CONSTRAINT "Single_keys_pkey" PRIMARY KEY ("ID")
)""")

personal_curr.execute("""CREATE TABLE IF NOT EXISTS "Group_keys" 
(
    "ID" integer NOT NULL,
    "Name" text,
    "Symmetric Key" text NOT NULL,
    CONSTRAINT "Groups_keys_pkey" PRIMARY KEY ("ID")
)
""")
personal_conn.commit()

connect_servers()
# connect_balancer()
balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
balancer.connect((balancerIP, balancerPort))
    
personal_curr.execute(f"""
    SELECT "Public Key" FROM "Single_keys" WHERE "ID" = {my_ID}
""")


private_str =  personal_curr.fetchone()[0]
private_key = rsa.key.PrivateKey.load_pkcs1(private_str.encode(), format='PEM')
print(private_key)

print("""
    To message-type "single_message" then the message then the message text
    To Group_message-type "group_message" then the message then the message text
    To Create Group-type "create_group" then group id then members(space separated)
    To ban from group-type "ban" then group id and then ban id
    To add in a group-type "add" then group id and then add id
    To delete Group- type "del_group" then group id
""")
# Starting Threads For Listening And Writing
write_thread = threading.Thread(target=write, args=(balancer,))
write_thread.start()

    