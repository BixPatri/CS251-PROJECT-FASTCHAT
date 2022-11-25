# CS251-PROJECT-FASTCHAT
This project is a Chat application made using python sockets on terminal with the aim of getting minimum latency and maximum throughput by using a load balancer.

## Features

- Multiple Clients and **multiple servers** integrated along with load balancer and database

- Clients can send messages and images with **End-to-end encryption** security (using RSA and AES keys)

- Registered clients can login and view thier **pending messages** while they were offline

- Server to server load distribution for group messages which require large number of messages to be sent

- Server load updated in **real time** on the basis of CPU usage

## Structure

- Each of the folders in this is supposed to be on different machines

- client.py, server.py, balancer.py are the main runner scripts 

- config.py, connect.py and database.ini in every folder help to connect with the main database.

- database.py sets up the main database 

- script_many.py in client folder runs program automatically and outputs data into results.csv

- parser.py in client folder parses the csv file and outputs latency and throughputs

- packets.py is helper module which defines send and receive functions


## Running instructions

1. Go to database directory and setup database using the dumped schema db.sql or execute database.py to setup automatically

      `python3 database.py`
     
2. Go to balancer directory and setup balancer using
    
      `python3 balancer.py <balancing_strategy>`
      
      (<balancing_strategy> can be specified as "rand" or "round_robin" or "min_load")

3. Go to server directory and setup servers
      
      `python3 server.py <port> <id>`
      
      (Use the same Port and ID as specified in the database)

4. Go to client directory and setup clients

      `python3 client.py`


## COMPONENTS
### Servers
The servers are connected with each other and have a high speed connection withtin them. Whenever a Client joins the server it either logs into 
the application or sends authentication to the servers it is connected to. Servers identify the client and stores its **credentials** (if new user) 
or **authenticates** it and send all the pending message of that client. The **bcrypt** library is used for authentication purposes.
If a server recieves multiple messages from any client (for example group_messages) then the messages are redistributed 
within the servers and sent to the recipients. This redistribution happens in inverse proportion to the load on the server. The server with a greater load gets less number of messages and that with maximum load gets more number of messages.

### Clients
Whenever a client joins the application, it sends its id to the server which loadbalancer has assigned to it. If the Client is a new user then the ID
sent is 0. There are various commands that the client can give such as **single_message** (Message to a single user) , **group_message** 
(Message to a group), **create_group** (create new group) etc.
We maintain a **local database** at client side to store the IDs and **shared symmetric key** of its friends. The local database also stores the user **Private and Public keys** and **Shared Symmetric Group keys** of the groups it is present in.


### Database
There is a main database of the program which is shared among servers and some of the specific columns of the database are shared with the Clients.
#### Client Table 
  Stores the info of all the clients connected with the chat application.
#### Server Info
  The info of all the servers is predefined using a simple text file.
  Contains field such as **Load**, **ID**, **IP**, **Port** of the respective server.
#### Groups
  Stores the **Admin**, **Group ID** and **Participants** list.
  
### Balancer
  Listens for new connections with the Clients and assigns them a server based on some strategy.
  This strategy can be based upon the Load of the servers or either be deterministic such as random or round robin.
#### Random
  The balancer just randomly returns a server from the list of online servers.
#### Round Robin
  The balancer goes in a circular fashion if there are 5 servers present the the balancer would give 1->2->3->4->5->1.
#### Min_Load
  The balancer checks from the server info table which server has the lowest load and gives the client that server. The load for each server is dynamically stored in the server info table. Load is calculated using **CPU usage of the server** in the server.py program and stored in the table.

## E2E encryption
We used the **rsa library** to share the **symmetric keys** generated using **Cryptography.Fernet** library within friends. 

Every Group has its own **symmetric key** that is known by all the participants of the group. This symmetric key is shared to a person when he is added to the group and a new key is established when a person is removed from the group.

### Documentation
The pdfs for **balancer**, **client**, **server** are in their respective folders, also the zipped build folders generated by sphinx are present in the folders. Which can be used for getting the html files.
