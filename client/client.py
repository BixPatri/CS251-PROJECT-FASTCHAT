#!/usr/bin/python3
import os
import socket
import threading
import json
from connect import connect
from packets import send_msg
from packets import recv_msg
import base64
import sqlite3
import rsa
from Crypto.Cipher import AES
from cryptography.fernet import Fernet
import time

# CONSTANTS
buffer = 1024
format = 'utf-8'
token_size = 5
server_count=0


####------------------CLIENT-BALANCER FUNCTIONS ------------------####

# Connect to balancer and return socket
def connect_balancer(balancerIP, balancerPort):
    """This function is used to connect the client to the load balancer

    :param balancerIP: IP of balancer
    :type balancerIP: str
    :param balancerPort: Port of balancer
    :type balancerPort: int
    :return: socket of balancer
    :rtype: socket
    """
    balancer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    balancer_sock.connect((balancerIP, balancerPort))
    return balancer_sock

# Gets server from balancer and returns server_ID
def get_server(balancer):
    """Asks the balancer for the server it should connect to

    :param balancer: balancer socket
    :type balancer: socket
    :return: Returns the server ID
    :rtype: int
    """
    balancer.send("req_server".encode(format))
    server_id = balancer.recv(buffer).decode(format)
    return int(server_id)


####------------------CLIENT-SERVER-CONNECTION FUNCTIONS ------------------####

# Connects to all online servers
def connect_servers():
    """Used to connect client with all the servers
    """
    global server_count
    # Get Online servers
    db_cur.execute("""
        SELECT * FROM "Server Info" WHERE "Status"='true'
    """)
    online_servers = db_cur.fetchall()
    server_count=len(online_servers)

    # global my_pass_hash
    global my_ID
    global private_key
    global public_key
    global my_info
    if my_ID <= 0:  # If new user then register
        personal_conn = sqlite3.connect(f"tmp.db")
        personal_curr = personal_conn.cursor()

        # Generate rsa keys
        (pubkey, privkey) = rsa.newkeys(512)
        priv_str = privkey.save_pkcs1(format='PEM').decode()
        pub_str = pubkey.save_pkcs1(format='PEM').decode()
        # my_pass_hash = base64.encodebytes(rsa.encrypt(my_pass.encode(), public_key)).decode(format)

        my_ID = register(online_servers[0], pub_str)

        personal_curr.execute(f"""
            INSERT INTO "My_Info" ("ID", "Name", "Private Key", "Public Key")
            VALUES ({my_ID}, "{my_name}", "{priv_str}", "{pub_str}")
        """)
        my_info = (my_ID, my_name, priv_str, pub_str)

        personal_conn.commit()
        personal_curr.close()
        personal_conn.close()

        # Rename temporary database to <id>.db
        os.rename("tmp.db", f"{my_ID}.db")
        

    private_key = rsa.key.PrivateKey.load_pkcs1(my_info[2].encode(), format='PEM')
    public_key = rsa.key.PublicKey.load_pkcs1(my_info[3].encode(), format='PEM')

    # Connect to each server in separate thread
    for server in online_servers:
        connect_server_thread = threading.Thread(target = connect_server, args=(server,))
        connect_server_thread.start()

# Registers user by sending credentials to server and returns assigned ID by server
def register(server_json, pub_str):
    """ This is called when the client joins for the first time. For storing his credentials

    :param server_json: Contains the information of the server
    :type server_json: list
    :param pub_str: The public key of the client in str format
    :type pub_str: str
    :return: ID assigned to the client by the server
    :rtype: int
    """
    IP = server_json[1]
    Port = int(server_json[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, Port))

    credentials = {
        "type": "client_reg",
        "Name": my_name,
        "Pass": my_pass,
        "Public Key": pub_str
        }


    sock.send(json.dumps(credentials).encode(format))
    received_info = json.loads(sock.recv(buffer).decode(format))
    # Receive ID assigned by the server
    id = received_info["ID"]
    print(f"\nSuccessfully Registered with ID: {id}")
    sock.close()

    return id

# Connect to a specific server
def connect_server(server_json):
    """ For connecting to a single server

    :param server_json: contains information about the server
    :type server_json: list
    """
    ID = int(server_json[0])
    IP = server_json[1]
    Port = int(server_json[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while(True):
        sock.connect((IP, Port))
        global my_pass
        # global my_pass_hash
        credentials = {
            "type": "client_auth",
            "Pass":my_pass,
            "ID": my_ID
            }
        
        sock.send(json.dumps(credentials).encode(format))

        result = sock.recv(buffer).decode(format)
        result_json = json.loads(result)

        if result_json["verified"] == 1:
            print(f"\n[Connected to server with server_ID:{ID}, IP:{IP}, Port:{Port}]")
            servers[ID] = sock
            handle_server(sock)
            break
        else:
            print("Invalid password!")
            my_pass = input("Re-Enter the Password: ")
            sock.close()


####------------------CLIENT-REQUEST FUNCTIONS ------------------####

# Sends Request for pending messages to server
def request_pending_msgs(): 
    """Used for requesting pending messages from the server
    """
    msg = {"type": "req_pending_msg"}
    server_ID = get_server(balancer_sock)   # request for server ID from balancer
    send_msg(servers[server_ID], json.dumps(msg).encode(format))

# Gets name from local database
def get_name_locally(ID):
    """Gets the name of a person who is already our friend
    
    :param ID: The ID of the person whose name we want
    :type ID: int
    :return: Returns the name of the person if he is our friend else returns empty string
    :rtype: str
    """
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "Name" FROM "Single_keys" WHERE "ID" = {ID}
    """)
    name = local_curr.fetchone()
    local_curr.close()
    local_conn.close()
    
    if name:
        return name[0]
    else:
        return ""

# Adds friend, establishes AES key using RSA and stores in local database
def add_friend():
    """When we want to make someone our friend. We can send messages to friends only.
    """
    recipient = int(input("Enter Friend ID: "))

    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 

    # Check if already a friend
    local_curr.execute(f"""
        SELECT * FROM "Single_keys" WHERE "ID" = {recipient}
    """)
    is_friend = local_curr.fetchone()
    if is_friend:
        print("Already a friend")
        return

    # Get name from main database and store into local database
    db_cur.execute(f"""
        SELECT "Name" FROM "Clients" WHERE "ID" = {recipient}
    """)
    recipient_info = db_cur.fetchone()

    local_curr.execute(f"""
        INSERT OR IGNORE INTO "Single_Keys" ("ID","Name")
        VALUES ({recipient},"{recipient_info[0]}")
    """)
    local_conn.commit()
    local_curr.close()
    local_conn.close()

    cmd = {"type": "add_friend", "Recipient": recipient}
    send_msg(servers[curr_server_ID], json.dumps(cmd).encode(format))

# Sends single message
def single_message():
    """When we want to send a text message to a friend.
    """
    recipient = int(input("Enter Recipient ID: "))
    message = input("Enter Message: ")

    # Get AES key from local database
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "Symmetric Key" FROM "Single_keys" WHERE "ID" = {recipient}
    """)
    sym_key = local_curr.fetchone()
    local_curr.close()
    local_conn.close()
    
    if not sym_key:
        print("Single message can be sent only after making friend")
        return
    else:
        sym_key = sym_key[0]

    key = sym_key.encode()

    # Encrypt and send
    key_obj = Fernet(key)
    encrypted_message = key_obj.encrypt(message.encode())

    msg = {"type": "single_message",
        "Recipient": recipient,
        "message": encrypted_message.decode(format)}

    send_msg(servers[curr_server_ID],json.dumps(msg).encode(format))

# Sends single image
def single_image():
    """When we want to send an image to a friend
    """
    recipient = int(input("Enter Recipient ID: "))
    path = input("Enter image path: ")
    title = os.path.basename(path)
    img = None
    with open(path, mode='rb') as file:
        img = file.read()
    
    message = base64.encodebytes(img)
    
    # Get AES key from local database
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "Symmetric Key" FROM "Single_keys" WHERE "ID" = {recipient}
    """)
    sym_key = local_curr.fetchone()
    local_curr.close()
    local_conn.close()
    
    if not sym_key:
        print("Single message can be sent only after making friend")
        return
    else:
        sym_key = sym_key[0]

    key = sym_key.encode()
    key_obj=Fernet(key)

    # Encrypt and send 
    encrypted_message = key_obj.encrypt(message)

    msg = {"type": "single_image",
        "title": title,
        "Recipient": recipient,
        "message": encrypted_message.decode(format)}

    send_msg(servers[curr_server_ID],json.dumps(msg).encode(format))

# Creates new group 
def create_group():
    """
    Creates a group with us as the only member. We can keep adding more people.
    """
    name = input("Enter Group Name: ")
    Members = [my_ID]
    msg = {"type":"create_group", "Group_Name":name}
    send_msg(servers[curr_server_ID], json.dumps(msg).encode(format))

# Send a Group Message to a group
def group_message():
    """For messaging in a group. It is encrypted using a symmetric key which is only with the members of the group.
    """
    Group=int(input("Enter group ID: "))
    message=input("Enter Message: ")
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor()
    local_curr.execute(f"""
        SELECT "Key" FROM "Group_keys" WHERE "ID" = {Group}
    """)
    k=local_curr.fetchone()[0]
    obj=Fernet(k)
    message=obj.encrypt(message.encode())
    mess={"type":"group_message","group_id":Group,"message":message.decode()}
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    local_curr.close()
    local_conn.close()

# Send a group Image to a group
def group_image():
    """For sending an image in a group. It is encrypted using a symmetric key which is only with the members of the group.
    """
    Group = int(input("Enter group ID: "))
    path = input("Enter image path: ")

    title = os.path.basename(path)
    img = None
    with open(path, mode='rb') as file:
        img = file.read()
    
    message = base64.encodebytes(img)

    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor()
    local_curr.execute(f"""
        SELECT "Key" FROM "Group_keys" WHERE "ID" = {Group}
    """)
    k=local_curr.fetchone()[0]
    obj=Fernet(k)
    encrypted_message = obj.encrypt(message)

    mess = {"type":"group_image", "title": title,"group_id":Group, "message":encrypted_message.decode(format)}
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    local_curr.close()
    local_conn.close()

# Kick a particular person from a group and change the keys
def kick():
    """For kicking someone from a group. It is also ensured that we generate a new key and share to all members except the removed one 
    through RSA for each member. Also only admin can kick from a group.
    """
    g_ID=int(input("Enter group ID: "))
    ban_ID=int(input("Enter ID to kick: "))
    mess={"type":"kick","g_ID":g_ID, "ban_ID":ban_ID}
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "Members" FROM "Group_keys" WHERE "ID" = {g_ID}
    """)
    prev_mem = eval(local_curr.fetchone()[0])
    prev_mem.remove(ban_ID)
    newkey = Fernet.generate_key().decode()
    local_curr.execute(f"""
        UPDATE "Group_keys"
        SET "Key" = "{newkey}",
            "Members" = "{str(prev_mem)}"
        WHERE "ID" = {g_ID}
    """)
    local_conn.commit()
    local_curr.close()
    local_conn.close()
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    for i in prev_mem:
        Send_group_key(i,g_ID)

# Sends the group key to a recipient
def Send_group_key(recipient,g_id):
    """
    Sending the group key to someone. Used when we need to add someone or kick a person.
    """
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 

    db_cur.execute(f"""
        SELECT "Public Key" FROM "Clients" WHERE "ID" = {recipient}
    """)
    a = db_cur.fetchone()
    receiver_pubk = rsa.key.PublicKey.load_pkcs1(a[0].encode(), format='PEM')

    local_curr.execute(f"""
        SELECT "Key" FROM "Group_keys" WHERE "ID" = {g_id}
    """)
    message = local_curr.fetchone()[0]

    msg = {"type":"Send_group_key", "Recipient":recipient, "message":base64.encodebytes(rsa.encrypt(message.encode(), receiver_pubk)).decode(format), "ID":my_ID,"Group_ID":g_id}
    send_msg(servers[curr_server_ID],json.dumps(msg).encode(format))

    local_curr.close()
    local_conn.close()

# Adds a person to a group
def add():
    """Used for adding a member to the group.
    """
    g_ID=int(input("Enter group ID: "))
    add_ID=int(input("Enter ID to add: "))
    mess={"type":"add","g_ID":g_ID, "add_ID":add_ID}

    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "Members" FROM "Group_keys" WHERE "ID" = {g_ID}
    """)
    prev_mem = local_curr.fetchone()[0]
    if prev_mem == None:
        prev_mem = []
    else:
        prev_mem = eval(prev_mem)
    prev_mem.append(add_ID)
    prev_mem = str(prev_mem)
    local_curr.execute(f"""
        UPDATE "Group_keys" 
        SET "Members" = "{prev_mem}"
        WHERE "ID" = {g_ID}
    """)
    local_conn.commit()

    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    Send_group_key(add_ID, g_ID)

# Exit from the program
def q():
    """
    Used for exiting the user
    """
    mess={"type":"\q"}
    send_msg(servers[curr_server_ID], json.dumps(mess).encode(format))
    os._exit(1)

# Get the help menu from the program
def help():
    """
    Prints the basic commands for the help of the user
    """
    print("""\n
    == Command Menu ==
    - add_friend : Add a new friend
    - single_message : Direct message a friend
    - single_image : Send an image to a friend
    - create_group : Create a new group
    - add_member : Add a new member to group
    - group_message : Send a group message
    - group_image : Send an image to a group
    - kick : Kick a member from the group
    - \q : Quit app
    - \help : Display Command Menu
        """)


####------------------HANDLE FUNCTIONS OF CLIENTS------------------####

# Accept friend request, generate and send AES key
def handle_accept_friend(message):
    """Handles when someone sends a friend request. It generates a symmetric key and sends the friend back using RSA
    
    :param message: The message the person sent in dict format with all fields
    :type message: dict
    """
    sender = message["Sender"]

    print(f"{sender}: [Friend request]")

    # Generate AES Key
    key = Fernet.generate_key()

    # Get name and public key of sender from main database and store into local database
    db_cur.execute(f"""
        SELECT "Name", "Public Key" FROM "Clients" WHERE "ID" = {sender}
    """)
    sender_info = db_cur.fetchone()

    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 

    local_curr.execute(f"""
        INSERT INTO "Single_Keys" ("ID","Name","Symmetric Key")
        VALUES ({sender},"{sender_info[0]}","{key.decode()}")
        ON CONFLICT("ID")
        DO UPDATE SET
        "Symmetric Key" = "{key.decode()}"
    """)
    local_conn.commit()

    # Send RSA encrypted AES Key to Sender
    receiver_pubk = rsa.key.PublicKey.load_pkcs1(sender_info[1].encode(), format='PEM')

    cmd = {"type": "friend_key",
        "Recipient": sender,
        "message": base64.encodebytes(rsa.encrypt(key, receiver_pubk)).decode(format)
        }
    send_msg(servers[curr_server_ID],json.dumps(cmd).encode(format))

    local_curr.close()
    local_conn.close()

# Receive friend AES key from previously sent friend request
def handle_friend_key(message):
    """Handles the case when a friend send us a key for communication
    
    :param message: The message the person/server sent in dict format with all fields
    :type message: dict
    """
    friend_ID = message["Sender"]
    friend_name = get_name_locally(friend_ID)
    print(f"[{friend_ID}] {friend_name}: [Request accepted!]")
    # Store key in local database
    key = rsa.decrypt(base64.decodebytes(message["message"].encode(format)),private_key)

    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        UPDATE "Single_Keys" 
        SET "Symmetric Key" = "{key.decode()}"
        WHERE "ID" = {friend_ID}
    """)
    local_curr.close()
    local_conn.commit()
    local_conn.close()

# Handles single message
def handle_single_message(message):
    """Handles the case when a friend sends us a message
    
    :param message:  The message the person/server sent in dict format with all fields
    :type message: dict
    """
    sender_id = message["Sender"]
    sender_name = get_name_locally(sender_id)

    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "Symmetric Key" FROM "Single_keys" WHERE "ID" = {sender_id}
    """)
    key = local_curr.fetchone()[0]  # AES key
    local_curr.close()
    local_conn.close()

    key_obj = Fernet(key.encode())

    msg = key_obj.decrypt(message["message"].encode()).decode()

    print(f"[{sender_id}] {sender_name}: {msg}")


# Handles single Image
def handle_single_image(message):
    """Handles the case when a friend sends us an image. It is stored in our system as received_(image title)
    
    :param message:  The message the person/server sent in dict format with all fields
    :type message: dict
    """
    sender_id = message["Sender"]
    sender_name = get_name_locally(sender_id)

    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "Symmetric Key" FROM "Single_keys" WHERE "ID" = {sender_id}
    """)
    key = local_curr.fetchone()[0]  # AES key
    local_curr.close()
    local_conn.close()

    key_obj = Fernet(key.encode())

    msg = key_obj.decrypt(message["message"].encode())
    with open("received_"+message["title"], mode='wb') as file:
        file.write(base64.decodebytes(msg))

    print(f"[{sender_id}] {sender_name}: [{message['title']}]")

# Adds the group ID to local database and generates and Group-Key and stores it.
def handle_New_group(message):
    """This is used for getting the group_ID of the group the client created from the server
    
    :param message:  The message the server sent in dict format with all fields
    :type message: dict
    """
    key=Fernet.generate_key()
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    print("[Group created with group ID: " + str(message["Group_ID"]) + "]")
    local_curr.execute(f"""
        INSERT INTO "Group_keys" ("ID", "Key", "Members") VALUES ({message["Group_ID"]}, "{key.decode()}", "{str([my_ID])}")
    """)
    local_conn.commit()
    local_curr.close()
    local_conn.close()

# Updates the Group key of the Specific Group
def handle_group_key(message):
    """When we are new to a group the admin send us the key through RSA. This function stores that key in our local database.
    
    :param message:  The message the person/server sent in dict format with all fields
    :type message: dict
    """
    s=rsa.decrypt(base64.decodebytes(message["message"].encode(format)),private_key).decode(format)
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor() 
    local_curr.execute(f"""
        SELECT "Key" FROM "Group_keys" WHERE "ID" = {message["Group_ID"]}
    """)
    if local_curr.fetchone() == None:
        local_curr.execute(f"""
            INSERT INTO "Group_keys" ("ID", "Key") VALUES ({message["Group_ID"]}, "{s}")
        """)
    else:
        local_curr.execute(f"""
            UPDATE "Group_keys" 
            SET "Key" = "{s}"
            WHERE "ID" = {message["Group_ID"]}
        """)
    local_conn.commit()
    local_curr.close()
    local_conn.close()

#Handles group messages
def handle_group_message(message):
    """When we recieve a message in a group
    
    :param message: The message the person/server sent in dict format with all fields
    :type message: dict
    """
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor()
    local_curr.execute(f"""
        SELECT "Key" FROM "Group_keys" WHERE "ID" = {message["group_id"]}
    """)
    k = local_curr.fetchone()[0]
    obj=Fernet(k.encode())
    msg=obj.decrypt(message["message"].encode()).decode()
    print("[Group: " + str(message["group_id"]) + "] " + str(message["Sender"]) + ": " + msg)
    local_curr.close()
    local_conn.close()
    
# Handles group image
def handle_group_image(message):
    """When we recieve an image in a group. It is stored in our system as received_(image title) format
    
    :param message: The message the person/server sent in dict format with all fields
    :type message: dict
    """
    local_conn = sqlite3.connect(f"{my_ID}.db")
    local_curr = local_conn.cursor()
    local_curr.execute(f"""
        SELECT "Key" FROM "Group_keys" WHERE "ID" = {message["group_id"]}
    """)
    k=local_curr.fetchone()[0]
    obj=Fernet(k.encode())
    msg=obj.decrypt(message["message"].encode())
    print("Image [Group: "+str(message["group_id"]) +"] "+ str(message["Sender"]) + ": " + message["title"])
    with open("received_"+message["title"], mode='wb') as file:
        file.write(base64.decodebytes(msg))

    local_curr.close()
    local_conn.close()

# Remove the Group entry from local database    
def handle_kick(message):
    """When someone is kicked from a group. It can be us or someone else. It is also ensured that new key will be generated for the group.
    
    :param message: The message the person/server sent in dict format with all fields.
    :type message: dict
    """
    if message["ban_ID"]==my_ID:
        local_conn = sqlite3.connect(f"{my_ID}.db")
        local_curr = local_conn.cursor()
        local_curr.execute(f"""
            DELETE FROM "Group_keys" WHERE "ID" = {message["g_ID"]} 
        """)
        local_conn.commit()
        local_curr.close()
        local_conn.close()
    print("[Group: " + str(message["g_ID"]) + "] " + ": " + message["message"])

# Prints message if somebody is added to the group
def handle_add(message):
    """
    The case when someone is added to the group.
    
    :param message: The message the person/server sent in dict format with all fields.
    :type message: dict
    """
    print("[Group: " + str(message["g_ID"]) + "] " + ": " + message["message"])

# Infinite loop for listening to the server
def handle_server(server):
    """
    The main handle function when we recieve something from the server. Different actions are taken depending on the type of message recieved.

    :param server: the server socket
    :type server: socket
    """
    while True:
        try:
            message_str = recv_msg(server).decode(format)
            message = json.loads(message_str)

            if message["type"] == "single_message":
                handle_single_message(message)
            elif message["type"] == "single_image":
                handle_single_image(message)
            elif message["type"] == "add_friend":
                handle_accept_friend(message)
            elif message["type"] == "friend_key":
                handle_friend_key(message)
            elif message["type"]=="New_group":
                handle_New_group(message)
            elif message["type"]=="Send_group_key":
                handle_group_key(message)
            elif message["type"] == "group_message":
                handle_group_message(message)
            elif message["type"] == "group_image":
                handle_group_image(message)
            elif message["type"] == "kick":
                handle_kick(message)
            elif message["type"] == "add":
                handle_add(message)
            else:
                print(message)

        except Exception as error:
            print(error)
            server.close()
            print("An error occured!")
            break


####------------------PROCESS COMMMANDS FROM CLIENTS------------------####

def execute_command(Command_type):
    """
    The main execute function which is used when the user wants us to do something. 

    :param Command_type: The command the user want to perform.
    :type Command_type: str
    :return: True for valid command else False
    :rtype: bool
    """
    if Command_type == "add_friend":
        add_friend()
    elif Command_type=="create_group":
        create_group()
    elif Command_type=="single_message":
        single_message()
    elif Command_type == "single_image":
        single_image()
    elif Command_type=="group_message":
        group_message()
    elif Command_type == "group_image":
        group_image()
    elif Command_type=="kick":
        kick()
    elif Command_type=="add_member":
        add()
    elif Command_type=="\q":
        q()
    elif Command_type == "\help":
        help()
    else:
        return False
    return True

# Infinite loop for commands from client side
def write(balancer_sock):
    """
    Gets a server from the balancer and takes a command from the user and executes the command through the server the balancer gave.

    :param balancer_sock: The socket of the balancer
    :type balancer_sock: socket
    """
    count = 0
    while True:
        # Get new server ID after token_size number of messages are sent
        if count <= 0:
            global curr_server_ID
            curr_server_ID = get_server(balancer_sock)
            count = token_size
        Command_type = input("")
        if execute_command(Command_type) == 1:
            count -= 1
        else:
            print("Invalid command!")


### MAIN RUNNER CODE ###

# Connects to database and returns connection object
(db_conn, db_cur) = connect()

# Display Menu
print("\n==== Welcome to FASTCHAT! =====")

# Register/Login
print("\n== Menu ==")
print(" 1. Register")
print(" 2. Login")
new_old = int(input("\nSelection: "))

#Client Informations 
my_name = None
my_ID = None  
my_pass = None
my_info = None
public_key = None
private_key = None

if new_old == 1:    
    my_name = input("\nEnter Your Name: ")
    my_ID = 0   # my_ID will be 0 if new user, else old ID
else:
    my_ID = int(input("\nEnter your ID: "))
    my_name = input("Enter Your Name: ")

my_pass = input("Enter Your Password: ")
# my_pass_hash = None

# Create local database if not present already
if my_ID <= 0 : 
    personal_conn = sqlite3.connect(f"tmp.db")
    personal_curr = personal_conn.cursor()

    personal_curr.execute("""
        CREATE TABLE IF NOT EXISTS "My_Info" 
        (   
            "ID" integer NOT NULL,
            "Name" text,
            "Private Key" text,
            "Public Key" text,
            CONSTRAINT "My_Info_pkey" PRIMARY KEY ("ID")
        )
    """)
    personal_curr.execute("""
        CREATE TABLE IF NOT EXISTS "Single_keys" 
        (   
            "ID" integer NOT NULL,
            "Name" text,
            "Symmetric Key" text,
            CONSTRAINT "Single_keys_pkey" PRIMARY KEY ("ID")
        )
    """)
    personal_curr.execute("""
        CREATE TABLE IF NOT EXISTS "Group_keys" 
        (
            "ID" integer NOT NULL,
            "Name" text,
            "Key" text NOT NULL,
            "Members" text,
            CONSTRAINT "Groups_keys_pkey" PRIMARY KEY ("ID")
        )
    """)
    personal_conn.commit()
    personal_curr.close()
    personal_conn.close()
else:
    personal_conn = sqlite3.connect(f"{my_ID}.db")
    personal_curr = personal_conn.cursor()
    personal_curr.execute(f"""
        SELECT * FROM "My_Info" WHERE "ID" = {my_ID}
    """)
    my_info = personal_curr.fetchone()
    personal_curr.close()
    personal_conn.close()


# Connect to balancer
balancerIP = "localhost"
balancerPort = 9091
balancer_sock = connect_balancer(balancerIP, balancerPort)

# Connect to all Online Servers
servers = {}        # Dictionary from server ID -> server socket
connect_servers()   # Fills above dictionary with required sockets

# Requests for pending messages if any from server
while(server_count!=len(servers)):
    time.sleep(1)    
request_pending_msgs()
    
# ID of the current server assigned to client.
curr_server_ID = 0

# Display command menu
help()

# Starting Thread for entering commands from client side
write_thread = threading.Thread(target=write, args=(balancer_sock,))
write_thread.start()