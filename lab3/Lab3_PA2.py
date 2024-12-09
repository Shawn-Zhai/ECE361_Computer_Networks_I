# Assume the image is named as "image" and is in the same directory as this file
# The output image file is named as "image_copy", also in the same directory as this file
# The maximum size of the image to echo is 16KB
# Run directly in Sypder

import socket
import sys

SERVER_IP_ADDRESS = "127.0.0.1"
PORT = 2024
read_buffer = ""

def get_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((SERVER_IP_ADDRESS, PORT))
    print(f" The UDP server is available on << { SERVER_IP_ADDRESS }:{ PORT } >>")
    return server

def get_client():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def exitSafe(message, client, server):
    print(message)
    client.close()
    server.close()
    sys.exit()

path_to_image = "image"
path_to_image_copy = "image_copy"

def echoImage():
    # setup
    server = get_server()
    client = get_client()

    # read image
    try:
        with open(path_to_image, 'rb') as image: # wb stands for write binary .
            image_bytes = image.read()
    except OSError:
        exitSafe(f" Could not open/read file {path_to_image}", client, server)

    # echo image
    try:
        # send to server
        client.sendto(image_bytes, (SERVER_IP_ADDRESS, PORT))
        print(" Sent image to server.")

        # server read
        read_buffer = server.recvfrom(16384)
        message = read_buffer[0]
        sender = read_buffer[1]
        print(f" Received image on server from {sender}.")

        # server write
        server.sendto(message, sender)
        print(" Echoed image back to sender.")

        # client read
        read_buffer = client.recvfrom(16384)
        print(" Received image on client.")
    except socket.error as exc:
        exitSafe(f"Encountered issue during transmission: {exc}", client, server)

    # copy response to hard drive
    try:
        with open(path_to_image_copy, 'wb') as image: # wb stands for write binary .
            image.write(read_buffer[0]) # assume that you store the image replied from UDP server in read_buffer variable 
    except OSError:
        exitSafe(f"Could not open/write file: {path_to_image_copy}", client, server)

    exitSafe(" Copy written, shutting down.", client, server)

echoImage()

