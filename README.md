# CS251-PROJECT-FASTCHAT
The directories present in this branch contain the respective scripts of the individual programs of client, server, database and balancer.
## COMPONENTS
### Servers
The servers are connected with each other and have a high speed connection withtin them. Whenever a Client joins the server it either logs into 
the application or sends authentication to the servers it is connected to. Servers identify the client and stores its **credentials** (if new user) 
or **authenticates** it and send all the pending message of that client. 
If a server recieves multiple messages from any client (for example group_messages) then the messages are redistributed 
within the servers and sent to the recipients.

### Clients
Whenever a client joins the application, it sends its id to the server which loadbalancer has assigned to it. If the Client is a new user then the ID
sent is 0. There are various commands that the client can give such as **single_message** (Message to a single user) , **group_message** 
(Message to a group), **create_group** (create new group) etc.
We maintain a **local database** at client side to store the IDs and **shared symmetric key** of its friends.
A client can only b

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

## E2E encryption
We used the **rsa library** to share the **symmetric keys** generated using **Cryptography.Fernet** library within friends. 

Every Group has its own **symmetric key** that is known by all the participants of the group.



  

