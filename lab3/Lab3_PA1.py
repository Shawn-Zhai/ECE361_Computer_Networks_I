# 4 clients connect to the server and send a message
# server receives all messages and broadcast
# it then shuts down and notify all clients
# run directly in Spyder

import socket
import os
from _thread import *
from datetime import datetime
import time

SERVER_IP_ADDRESS = "127.0.0.1"
PORT = 2024
NUM_CLIENTS = 4

clients = []
messages = {}
clients_lock = allocate_lock()

#Global variable to keep track of server status
server_running = True

#Handles message receiving on clients
def receive_messages(connection, client_id):
    global server_running
    try:
        while server_running:
            read_buffer = connection.recv(1024)
            if not read_buffer:
                print(f"Client {client_id} not connected")
                break
            #Printing message received on client
            print(f"CLIENT {client_id} - Message from server: {read_buffer.decode()}")
    except Exception as e:
        print(f"Error on client {client_id}: {e}")

#TCP client code, listens for messages on new thread, sends message to server
def run_client(client_id, message):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_IP_ADDRESS, PORT))
        print(f"Client {client_id} connected")
        start_new_thread(receive_messages, (client, client_id))
        while server_running:
            client.sendall(f"{message}".encode())
            time.sleep(1)
    except socket.error as err:
        print(f"Client {client_id} connection error: {str(err)}")
    finally:
        client.close()

#Setting up TCP server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((SERVER_IP_ADDRESS, PORT))
    server.listen(NUM_CLIENTS)
    print(f"SERVER - Listening on << {SERVER_IP_ADDRESS}:{PORT} >>")
    time.sleep(1)

    for i in range(NUM_CLIENTS):
        start_new_thread(run_client, (i, f"This is a message from client {i}",))

    while server_running:
        connection, client_address = server.accept()
        print(f"SERVER - Client has connected from IP address << {client_address[0]} >> and TCP port number << {client_address[1]} >>!")
        with clients_lock:
            clients.append(connection)
        read_buffer = connection.recv(1024)

        if not read_buffer:
            break
        else:
            messages[connection] = read_buffer

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"SERVER - [{timestamp}] {client_address[0]}:{client_address[1]} says: {read_buffer.decode()}")
        #Retransmitting messages once all received
        if len(messages) == NUM_CLIENTS:
            with clients_lock:
                for connection_socket, message in messages.items():
                    for client_socket in clients:
                        if client_socket != connection_socket:
                            client_socket.sendall(message)
                            time.sleep(0.5)
            server_running = False
            
    #Notify clients of server shutdown 
    print("\nSERVER - Notifying clients of shutdown...\n") 
    with clients_lock: 
        for client_socket in clients: 
            try: 
                client_socket.sendall("SERVER - Shutting down".encode()) 
            except Exception as e: 
                print(f"Error notifying client: {e}")
    
    #Shutting down server after sending out all messages
    print("\nShutting down server\n")
    with clients_lock:
        for client_socket in clients:
            try:
                client_socket.close()
                print("Client socket closed")
            except Exception as e:
                print(f"Error closing client socket: {e}")
        clients.clear()
    print("Server shutdown complete")

