# 'Chat Room Connection - Client-To-Client'
import sys
import threading
import socket
import json
import sqlite3
from connect import connect
from packets import send_msg
from packets import recv_msg
import bcrypt
import psutil

#type variables
buffer = 1024
format = 'utf-8'

#server IP, PORT and ID
hostIP = "localhost"
hostPort = int(sys.argv[1])
my_ID = int(sys.argv[2])

#Initialising the server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((hostIP, hostPort))
server.listen()

#stores the sockets of other servers
other_servers = {}
#stores sockets of all clients
clients = {}

#Connection to the database
(db_conn, db_cur) = connect()


####------------------GROUP FUNCTIONS------------------####

#sends the message to all the members specified as argument
def send_members(message, members):
    """Sends the message to all the clients specified in the members list.
       Calls send_client function on each of the client present in the list.

    :param message: The message to be sent to all the recipients present in the list.
    :type message: dictionary
    :param members: The list of persons whom the message has to be sent.
    :type members: list
    """
    if len(members) == 0:
        return
 
    curr = db_conn.cursor()

    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" IN %s
    """, (tuple(members),))

    participants_all = curr.fetchall()

    for p in participants_all:
        send_client(p[1], p[0], message)

#Distributes the messages among different servers based on their load.
def distribute_grp(message, group_members):
    """Function to distribute the messages of a group among the servers.\n
       Messages are distributed among the servers based upon inverse ratio of their loads.
       For a server i with load L_i the number of messages it has to deliver is proportional to 1/L_i.
       It calculates the number of messages to be sent by individual servers and distributes them using "sent_msg" function.

    :param message: Message to be sent to the recipients
    :type message: json 

    :param group_members: List of people whom the message has to be sent
    :type group_members: list

    :return: The function makes call to the send_msg function for different servers and calls send_members on messages it sends by itself
    :rtype: void
    """

    curr = db_conn.cursor()
    curr.execute("""
        SELECT "ID", "Load" FROM "Server Info" WHERE "Status" = true
    """)
    server_info = curr.fetchall()

    server_info.sort(key=lambda tup: tup[1])
    server_info.reverse()

    inverse_loads = [ 1/l[1] for l in server_info ]

    c = 1 / sum(inverse_loads)
    N = len(group_members)

    distribution = [ int(N*c//s[1]) for s in server_info ]
    distribution[-1] += N - sum(distribution)
    
    msg = {"type": "grp_msg", "message": json.dumps(message)}
    for i, s in enumerate(server_info):
        if s[0] != my_ID:
            mem_list = group_members[:distribution[i]]
            group_members = group_members[distribution[i]:]
            msg["members"] = mem_list
            send_msg(other_servers[s[0]], json.dumps(msg).encode(format))

    send_members(message, group_members)

#creating a group
def create_group(message, sender_ID):
    """Handle the create_group query from a client.
       Assigns a Key to the group requested by the client using the Groups table in database.
       Sends a confirmation message back to the client including the group ID assigned.
       Adds the group created into the original database.

    :param message: Contains the Name of the group to be created.
    :type message: dictionary
    :param sender_ID: Client who has sent the message
    :type sender_ID: int
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT COUNT("ID") FROM "Groups";
    """)
    gid = (int(curr.fetchone()[0])+1)
    msg = {"type":"New_group","Group_ID":gid}
    send_client(1,sender_ID,msg)
    curr.execute("""
        INSERT INTO "Groups" ("ID", "Name", "Admin ID", "Participants") VALUES (%s,%s,%s,%s)
    """, (gid, message["Group_Name"],sender_ID,[sender_ID]))
    db_conn.commit()
    curr.close()
    return True

#sending a group message.
def group_message(message,sender_ID):
    """Sends a group message by calling the distribute_group function on the participants of the group.
    
    :param message: The message that has to be delivered in the group.
    :type message: dictionary

    :param sender_ID: The sender's ID
    :type sender_ID: int
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Participants" FROM "Groups" WHERE "ID" = %s
    """,(message["group_id"],))
    participants = curr.fetchone()[0]
    participants.remove(sender_ID)
    message["Sender"] = sender_ID

    distribute_grp(message, participants)


#sending an image in a group
def group_image(message, sender_ID):
    """Sends a group image to all the participants of the group by calling the distribute_grp.
    
    :param message: The message that has to be delivered in the group.
    :type message: dictionary

    :param sender_ID: The sender's ID
    :type sender_ID: int
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Participants" FROM "Groups" WHERE "ID" = %s
    """,(message["group_id"],))
    participants = curr.fetchone()[0]
    participants.remove(sender_ID)
    message["Sender"] = sender_ID

    distribute_grp(message, participants)

#kicking a member from the group
def kick(message, sender_ID):
    """Kicks a client from the group specified in the message. \n
       Checks whether the Admin of the group has made the request.
       It sends a kick message to the specified person and acknowledge to the other participants.
    
    :param message: The message contains the ID to be kicked and the group number.
    :type message: dictionary
    :param sender_ID: The ID of the client that requested the message
    :type sender_ID: int
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Participants","Admin ID" FROM "Groups" WHERE "ID" = %s
    """, (message["g_ID"],))
    
    fetched = curr.fetchone()
    old_party = fetched[0]
    admin = fetched[1]

    #only admins can remove
    if admin!=sender_ID:
        return False

    old_party.remove(message["ban_ID"])

    curr.execute("""
            UPDATE "Groups"
            SET "Participants" = %s
            WHERE "ID" = %s
        """, (old_party, message["g_ID"]))
    db_conn.commit()

    message["message"] = str(message["ban_ID"]) + " was KICKED from the group " + str(message["g_ID"]) + " by " + str(sender_ID)
    
    distribute_grp(message,old_party)
    

    curr.execute("""
        SELECT "Status" FROM "Clients" WHERE "ID" = %s
    """,(message["ban_ID"],))
    statustokick = curr.fetchone()[0]
    message["message"] = "You were KICKED from group " + str(message["g_ID"]) + " by " + str(sender_ID)
    send_client(statustokick,message["ban_ID"],message)
    curr.close()

# Adding to a group
def add(message , sender_ID):
    """Adding a member to the group.\n
       Function checks whether the request has been made by the admin of the group.
       Send a message to the other members and another message to the person added. 
    
    :param message: Message to add a specified ID to the group.
    :type message: dictionary

    :param sender_ID: The ID of the client that requested the message.
    :type sender_ID: int
    """
    curr = db_conn.cursor()
    if message["add_ID"] not in clients.keys():
        return False

    curr.execute("""
        SELECT "Participants","Admin ID" FROM "Groups" WHERE "ID" = %s
    """, (message["g_ID"],))
    (old_party,admin) = curr.fetchone()

    if admin!=sender_ID:
        return False
    
    new_party=old_party+[]
    new_party.append(message["add_ID"])
    
    curr.execute("""
            UPDATE "Groups"
            SET "Participants" = %s
            WHERE "ID" = %s
        """, (new_party, message["g_ID"]))
    db_conn.commit()

    curr.execute("""
        SELECT "Status" FROM "Clients" WHERE "ID" = %s
    """,(message["add_ID"],))
    statustoadd = curr.fetchone()[0]

    message["message"] = "You were Added to group " + str(message["g_ID"]) + " by " + str(sender_ID)
    send_client(statustoadd,message["add_ID"],message)    
    
    message["message"] = str(message["add_ID"]) + " was added to the group " + str(message["g_ID"]) + " by " + str(sender_ID)

    distribute_grp(message,old_party)
    
    db_conn.commit()
    curr.close()

# Sharing key with a group member
def Send_group_key(message, sender_ID):
    """Share the group key with a single participant of the group
    
    :param message: The message contains the ID of the client whom the message has to be sent.
    :type message: dictionary
    :param sender_ID: The ID of the client that requested the message
    :type sender_ID: int 
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "ID", "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    send_client(recipient[1],recipient[0],message)
    curr.close()

####------------------SINGLE CLIENT FUNCTIONS------------------####

#Send message to client or append to its pending messages based on status
def send_client(status, ID, msg):
    """Sends the message to the client specified by the ID.
       If the client is online it delivers the message else stores it in the pending messages of client.

    :param msg: The message to be sent to the recipient.
    :type msg: dictionary

    :param ID: Client ID whom the message has to be delivered.
    :type ID: int
    
    :param status: The status of client (online or offline)
    :type status: bool

    :return: | (status = True) The function calls the send function on the socket of respective client.  
             | (status = False) 
    """

    curr = db_conn.cursor()
    if status:
        send_msg(clients[ID], json.dumps(msg).encode(format))
    else:
        curr.execute("""
            UPDATE "Clients"
            SET "Pending Messages" = array_append("Pending Messages", %s)
            WHERE "ID" = %s
        """, (json.dumps(msg), ID))
        db_conn.commit()
    curr.close()

# Add friend command
def add_friend(message, sender_ID):
    """Add a client as a friend from the users of the application.

    :param message: The message contains the ID of the client whom we want to add as friend.
    :type message: dictionary
    :param sender_ID: The ID of the client that requested the message
    :type sender_ID: int
    """
    
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    recipient_status = None
    if not recipient:
        return
    else:
        recipient_status = recipient[0]
    
    msg = {"type": message["type"], "Sender": sender_ID}
    send_client(recipient_status, message["Recipient"], msg)
    curr.close()

# Forward friend The symmetric encryption key
def friend_key(message, sender_ID):
    """Send encrypted symmetric key to the client_ID specified by the sender 

    :param message: The message contains the ID of the client to whom the encrypted key has to be sent.
    :type message: dictionary
    :param sender_ID: The ID of the client that requested the message
    :type sender_ID: int
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient_status = curr.fetchone()[0]
    
    msg = {"type": message["type"], "message": message["message"], "Sender": sender_ID}
    send_client(recipient_status, message["Recipient"], msg)
    curr.close()

# Send a friend a single message
def single_message(message, sender_ID):
    """Send a personal message to a friend.
    
    :param message: The message contains the ID of the client whom the message has to be sent.
    :type message: dictionary
    :param sender_ID: The ID of the client that requested the message
    :type sender_ID: int 
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()
    
    msg = {"type": message["type"], "message": message["message"], "Sender": sender_ID}
    send_client(recipient[0], message["Recipient"], msg)
    curr.close()

# Send a friend a single image
def single_image(message, sender_ID):
    """Send a personal image to a friend.
    
    :param message: The message contains the ID of the client whom the message has to be sent.
    :type message: dictionary
    :param sender_ID: The ID of the client that requested the message
    :type sender_ID: int 
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Status" FROM "Clients" WHERE "ID" = %s
    """, (message["Recipient"],))
    recipient = curr.fetchone()

    msg = {"type": message["type"], "title": message["title"], "message": message["message"], "Sender": sender_ID}
    send_client(recipient[0], message["Recipient"],msg)
    curr.close()

#Send the pending messages
def send_pending(sender_ID):
    """Sends the pending messages of a user whenever the user queries for it.
       Updates the database and removes the pending messages of the client. 
    
    :param sender_ID: The ID of the client that requested the message
    :type sender_ID: int
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Pending Messages" FROM "Clients" WHERE "ID" = %s
    """, (sender_ID,))
    msgs = curr.fetchone()[0]
    curr.execute("""
        UPDATE "Clients"
        SET "Pending Messages" = NULL
        WHERE "ID" = %s
    """,(sender_ID,))
    db_conn.commit()
    
    if not msgs == None:
        for msg in msgs:
            send_client(1,sender_ID, json.loads(msg))
    curr.close()

#Quits the connection with the client.
def q(sender_ID):
    """Function ends the socket connection with the client that requested for exit.
    
    :param sender_ID: The ID of the client that requested to quit
    :type sender_ID: int 
    """
    curr = db_conn.cursor()
    curr.execute("""
        UPDATE "Clients"
        SET "Status" = false
        WHERE "ID" = %s
    """,(sender_ID,))

    db_conn.commit()
    curr.close()
    clients[sender_ID].close()
    del clients[sender_ID]

####------------------SERVER-SERVER FUNCTIONS ------------------####

#handling requests from other servers.
def handle_server(server):
    """Function that handles any request from the other servers.
       If the request is to send messages to members of a group it calls the send_members function.
    
    :param server: The recieving socket.
    :type server: socket
    """
    while True:
        try:
            message = json.loads(recv_msg(server).decode(format))

            if message["type"] == "grp_msg":
                send_members(json.loads(message["message"]), message["members"])

        except:
            print("A server-server error occured!")
            server.close()
            break    

#Makees server-server connections
def connect_server(server):
    """Connect to a server with the given information.
       Sends the server authentication message to the another server.
       Adds the other server to the list of others_servers
    
    :param server: The information of the server with which this server has to connect.
    :type server: tuple
    """
    ID = int(server[0])
    IP = server[1]
    Port = int(server[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((IP, Port))
    credentials = {"type":"server_auth","ID":my_ID,"password":"server_pass"}
    sock.send(json.dumps(credentials).encode(format))

    print(f"Connected to server with ID:{ID}, IP:{IP}, Port:{Port}")
    other_servers[ID] = sock

    handle_server(sock)

# connects with all servers
def connect_servers():
    """Connect with the servers that are online by fetching their information from the database.
       Starts a separate thread for each server.

    """
    db_cur.execute("""
        SELECT * FROM "Server Info" WHERE "Status"='true'
    """)
    online_servers = db_cur.fetchall()

    db_cur.execute(f"""
        UPDATE "Server Info"
        SET "Status" = true
        WHERE "IP" = %s AND "Port" = %s
    """, (hostIP, hostPort))
    db_conn.commit()


    print("Connecting to previously online servers...")

    for server in online_servers:
        connect_server_thread = threading.Thread(target=connect_server, args=(server,))
        connect_server_thread.start()

# Recieving a server.
def receive_server(sock, ID):
    """Recieves the server to be handled from the accept connection function.  
       Adds the server to the dictionary of other_servers. 
    
    :param client: The socket of the client that has to be recieved.
    :type client: socket
    :param ID: The ID of the client that has to be handled
    :type ID: int
    """
    other_servers[ID] = sock
    handle_server(sock)


####------------------SERVER-CLIENT FUNCTIONS ------------------####

# Handling different types of queries from client
def handle_client(client, client_ID):
    """Handles the Queries requested by the clients based on the message type.
    Recieves the messages on the socket and calls the involved function.
    Removes the connection with the client in case of any exception.
    
    :param client_ID: The ID of the client that requested the message
    :type client_ID: int
    """
    while True:
        try:
            message = json.loads(recv_msg(client).decode(format))
            msg_type = message["type"]

            if msg_type == "single_message":
                single_message(message, client_ID)
            elif msg_type == "add_friend":
                add_friend(message, client_ID)
            elif msg_type == "friend_key":
                friend_key(message, client_ID)
            elif msg_type == "single_image":
                single_image(message, client_ID)
            elif msg_type == "create_group":
                create_group(message, client_ID)
            elif msg_type == "group_message":
                group_message(message, client_ID)
            elif msg_type == "group_image":
                group_image(message, client_ID)
            elif msg_type == "kick":
                kick(message, client_ID)    
            elif msg_type == "add":
                add(message, client_ID) 
            elif msg_type == "Send_group_key":
                Send_group_key(message,client_ID)
            elif msg_type == "req_pending_msg":
                send_pending(client_ID)
            elif msg_type == "\q":
                print(f"{client_ID} left")
                q(client_ID)
                break
            else:
                print("invalid query")

        except Exception as error:
            print(f"Error occured while handling client {client_ID} !")
            print(error)
            q(client_ID)
            break

# Receiving / Listening Function
def receive_client(client, ID):
    """Recieves the client to be handled from the accept connection function.  
       Adds the client to the dictionary of clients 
    
    :param client: The socket of the client that has to be recieved.
    :type client: socket
    :param ID: The ID of the client that has to be handled
    :type ID: int
    """
    clients[ID] = client
    handle_client(client, ID)


# Registers a client (When he arrives at the first time)
def client_reg(credentials):
    """Registers the clients into the application.
       Creates a new ID and sends that ID to the client.
    
    :param credentials: The credentials of the client
    :type credentials: dictionary
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT COUNT("ID") FROM "Clients"
    """)
    count = int(curr.fetchone()[0])

    hashed_pass=bcrypt.hashpw(credentials["Pass"].encode(),bcrypt.gensalt()).decode()
    curr.execute("""
        INSERT INTO "Clients" ("ID","Name", "Password", "Public Key", "Status")
        VALUES (%s, %s, %s, %s, %s)
    """, (count+1, credentials["Name"], hashed_pass, credentials["Public Key"], True))
    db_conn.commit()    
    curr.close()
    return (count+1)

# Verifies a clients
def client_verify(credentials):
    """Verifies the clients by authorising it from the servers by matching its information from the database.
       Closes the socket if the credentials are incorrect.
       Returns an acknowledgement to the client whether it was verified.
    
    :param credentials: The credentials of the client
    :type credentials: dictionary
    """
    curr = db_conn.cursor()
    curr.execute("""
        SELECT "Password","Status" FROM "Clients" WHERE "ID" = %s
    """, (credentials["ID"],))
    details = curr.fetchone()

    if not details[1]:
        curr.execute("""
            UPDATE "Clients"
            SET "Status" = true
            WHERE "ID" = %s
        """, (credentials["ID"],))
    
    db_conn.commit()
    
    k = details[0]
    if bcrypt.checkpw(credentials["Pass"].encode(), k.encode()):
        curr.close()
        return int(credentials["ID"])
    else:
        curr.close()
        return 0


####------------------ACCEPT ALL THE CONNECTIONS ------------------####

#A function which runs in an infinite loop and main purpose of this is to listen to any new connection.
def accept_connections():
    """Function accepts any connection and processes it based upon the type of the message recieved.
    
    """
    print("Listening for new Connections...")
    while True:
        sock, addr = server.accept()

        credentials = sock.recv(buffer).decode(format)
        credentials = json.loads(credentials)

        is_server = 0
        server_id = None
        client_id = None

        if credentials["type"] == "server_auth":
            if credentials["password"] == "server_pass":
                is_server = 1
                server_id = credentials["ID"]
            else:
                sock.close()
                continue
        elif credentials["type"] == "client_auth":
            client_id = client_verify(credentials)
            if not client_id:
                msg = json.dumps({"verified":0, "msg": "Invalid credentials, please try again"})
                sock.send(msg.encode(format))
                sock.close()
                continue
            else:
                msg = json.dumps({"verified":1, "msg": "Successfully verified"})
                sock.send(msg.encode(format))
        elif credentials["type"] == "client_reg":
            client_id = client_reg(credentials)
            msg = {"type": "server", "ID": client_id}
            sock.send(json.dumps(msg).encode(format))
            sock.close()
            continue
        
        if is_server:
            print(f"Connected to server with ID:{server_id}, IP:{addr[0]}, Port:{addr[1]}")
            receive_server_thread = threading.Thread(target=receive_server, args=(sock,server_id))
            receive_server_thread.start()
        else:
            print(f"Connected to client with IP:{addr[0]}, Port:{addr[1]}")
            receive_client_thread = threading.Thread(target=receive_client, args=(sock,client_id))
            receive_client_thread.start()


def update_load():
    current_process_pid = psutil.Process().pid
    p = psutil.Process(current_process_pid)
    while True:
        tot_load_from_process = p.cpu_percent(interval=3)/psutil.cpu_count()
        db_cur.execute("""
            UPDATE "Server Info"
            SET "Load" = %s
            WHERE "ID" = %s
        """,(tot_load_from_process+1, sys.argv[2]))
        db_conn.commit()


if __name__ == "__main__":
    update_load_thread = threading.Thread(target=update_load)
    update_load_thread.start()
    connect_servers()
    accept_connections()