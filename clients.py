import socket
import threading

#Take the input ID of the port you want to connect to
port = int(input("Please Input port No "))

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
            # Receive Message From Server
            # If 'NICK' Send Nickname
            message = client.recv(1024).decode('ascii')
            if message == '/AUTH':
                client.send(ID.encode('ascii'))
            else:
                print(message)
        except:
            # Close Connection When Error
            print("An error occured!")
            client.close()
            break

# Sending Messages To Server from this client
def write():
    while True:
        pID = input("kisko bhejna hai? ")
        msg = input("Kya bhejna hai? ")
        message = '{}: {}'.format(pID, msg)
        client.send(message.encode('ascii'))

# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()