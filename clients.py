import socket
import threading

#Take the input ID of the port you want to connect to
port = 9087

# Choosing Nickname
ID = input("Enter Your ID: ")
passwd = (input("Enter Your Password: "))

# Connecting To the main load balancer server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', port))

# Listening to Server and Sending Nickname
def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            print(message)
            if message == '/AUTH':
                client.send((ID+":"+passwd).encode('ascii'))
        except:
            # Close Connection When Error
            print("An error occured!")
            client.close()
            break

# Sending Messages To Server from this client
def write():
    while True:
        pID = input("kisko bhejna hai? ")
        msg = input("Are bhai kehna kya chahte ho? ")
        message =pID+":"+msg
        print(message)
        client.send(message.encode('ascii'))
        

# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()