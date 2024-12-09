# Assume the image is named as "image" and is in the same directory as this file
# The output image saved by the server is named as "server_received_image", also in the same directory as this file
# There's no upper limit on the input image size
# run directly in Spyder

import socket
import sys

SERVER_IP_ADDRESS = "127.0.0.1"
PORT = 2024
BUFFER_SIZE = 1000  # maximum chunk size
path_to_image = "image"
path_to_image_on_server = "server_received_image"

def exit_safe(message, client=None, server=None):
    print(message)
    if client:
        client.close()
    if server:
        server.close()
    sys.exit()

def save_image(chunks, file_path):
    try:
        with open(file_path, 'wb') as f:
            for chunk in chunks:
                f.write(chunk)
        print(f"Image saved as {file_path}.")
    except OSError as e:
        exit_safe(f"Error writing image file: {e}")

def main():
    
    # setup server and client
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((SERVER_IP_ADDRESS, PORT))
    print(f"Server is running on << {SERVER_IP_ADDRESS}:{PORT} >>")
    
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(2)  # timeout for acknowledgments

    # read image
    try:
        with open(path_to_image, 'rb') as f:
            image_data = f.read()
    except OSError:
        exit_safe(f"Could not open/read file: {path_to_image}", client, server)

    total_chunks = (len(image_data) + BUFFER_SIZE - 1) // BUFFER_SIZE
    print(f"Image divided into {total_chunks} chunks.")

    # send image from client to server
    next_chunk_id = 0
    chunks_to_send = 1
    received_chunks = {}

    try:
        while next_chunk_id < total_chunks:
            
            # client sends chunks
            sent_chunks = 0
            for _ in range(chunks_to_send):
                if next_chunk_id >= total_chunks:
                    break
                chunk_start = next_chunk_id * BUFFER_SIZE
                chunk_end = min(chunk_start + BUFFER_SIZE, len(image_data))
                chunk_data = image_data[chunk_start:chunk_end]
                chunk_id_bytes = next_chunk_id.to_bytes(4, "big")
                client.sendto(chunk_id_bytes + chunk_data, (SERVER_IP_ADDRESS, PORT))
                print(f"Client sent chunk ID {next_chunk_id}.")
                next_chunk_id += 1
                sent_chunks += 1

            # server receives chunks
            for _ in range(sent_chunks):
                data, client_address = server.recvfrom(BUFFER_SIZE + 4)
                chunk_id = int.from_bytes(data[:4], "big")
                chunk_data = data[4:]
                received_chunks[chunk_id] = chunk_data
                print(f"Server received chunk ID {chunk_id} from {client_address}.")

            # server sends acknowledgment - cummulative ACK
            ack_id = max(received_chunks.keys())
            server.sendto(ack_id.to_bytes(4, "big"), client_address)
            print(f"Server sent acknowledgment for chunk ID {ack_id}.")

            # client processes acknowledgment
            try:
                ack_data, _ = client.recvfrom(4)
                ack_id = int.from_bytes(ack_data, "big")
                print(f"Client received acknowledgment for chunk ID {ack_id}.")
                
                # client doubles the chunks to send everytime it receives an ACK
                chunks_to_send = min(2 * chunks_to_send, total_chunks - ack_id - 1)
            except socket.timeout:
                print("Client acknowledgment timeout. Resending last chunks.")
                next_chunk_id -= chunks_to_send

        print("All chunks transmitted and acknowledged.")
    except socket.error as exc:
        exit_safe(f"Encountered socket error: {exc}", client, server)

    # save the image on the server
    save_image([received_chunks[i] for i in sorted(received_chunks.keys())], path_to_image_on_server)

    # clean up
    exit_safe("Image transmission complete. Shutting down.", client, server)

if __name__ == "__main__":
    main()



