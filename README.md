This Repo contains implementation of FastChat Application, a chat application for users.
Whenever you want to send message to some client use mess_json function
it returns a json string with the message type server/private/group etc and the text of the message
Whenever the client recieves anything it just prints its type and the text.
The function implementations may have many errors.
client sends json of different types for different types of commands and the server responds differently