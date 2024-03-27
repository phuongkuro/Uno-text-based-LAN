import socket
import threading
import pickle
import time

# Server's IP address
SERVER_IP = '192.168.1.34'  # Replace with your server's IP address
SERVER_PORT = 65432

def get_valid_username(prompt="Enter your username: "):
    """Prompt the user for a valid username, which cannot be blank or contain only spaces."""
    while True:
        username = input(prompt).strip()  # Removes leading and trailing whitespace
        if username:
            return username  # Valid username entered
        print("Username cannot be blank or only contain spaces. Please enter a valid username.")

my_turn = False  # Global flag to indicate if it's my turn

def receive_messages(client_socket, username):
    """Handles incoming messages from the server."""
    global my_turn

    while True:
        try:
            # First, receive the length of the pickled data
            header = client_socket.recv(4)
            if not header:
                print("Server closed the connection unexpectedly.")
                break
            message_length = int.from_bytes(header, byteorder='big')
            if message_length:
                # Now, receive the designated length of bytes
                message = client_socket.recv(message_length)
                if not message:
                    print("Server closed the connection.")
                    break

                # Logic to handle different message types
                if message.startswith(b'PICKLE:'):
                    hand = pickle.loads(message[7:])  # Remove the PICKLE: prefix
                    print("Received your hand of cards:", hand)
                elif message.startswith(b'TEXT:'):
                    text_message = message[5:].decode('utf-8')  # Remove the TEXT: prefix
                    print(text_message)
                    if f"It's {username}'s turn." in text_message:
                        my_turn = True
                    else:
                        my_turn = False
                else:
                    print("Unknown message type.")
        except Exception as e:
            print("An error occurred:", e)
            break

def send_messages(client_socket):
    global my_turn
    while True:
        # Continually check if it's our turn to play
        if my_turn:
            card = input("Enter the card you want to play (e.g., 'Red 4'): ")
            message = f'PLAY {card}'
            client_socket.sendall(message.encode('utf-8'))
            
            # Now, wait for the server's response after attempting to play
            response = client_socket.recv(1024).decode('utf-8')

            if response.startswith('TEXT:'):
                text_response = response[5:]
                print(text_response)
                if "played:" in text_response:
                    # The card was successfully played, so now it's not our turn
                    my_turn = False
                else:
                    # The play was invalid, so let the player know and try again
                    my_turn = True
        else:
            # It's not our turn, let's not burn the CPU
            time.sleep(0.1)



def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("Connected to server.")
        
        # Request and send the username to the server
        username = get_valid_username()
        client_socket.sendall(username.encode('utf-8'))

        # Wait for a response regarding username acceptance
        while True:
            response_header = client_socket.recv(4)
            if not response_header:
                print("Connection closed by server.")
                return

            message_length = int.from_bytes(response_header, byteorder='big')
            response = client_socket.recv(message_length)

            if response.startswith(b'TEXT:'):
                text_response = response[5:].decode('utf-8')
                print(text_response)
                if "Welcome to the game!" in text_response or "has joined the game." in text_response:
                    # The username was accepted; move on to the main part of the client
                    break
                elif "Username has been taken" in text_response:
                    # The username was rejected; prompt for a new username
                    username = get_valid_username()
                    client_socket.sendall(username.encode('utf-8'))

        # Now that the username has been accepted, start receiving messages
        thread_receiving = threading.Thread(target=receive_messages, args=(client_socket, username))
        thread_receiving.start()

        # Also start sending messages (like card plays)
        send_messages(client_socket)

    except Exception as e:
        print(f"An exception occurred: {e}")
    finally:
        client_socket.close()
        print("Client socket closed.")

if __name__ == "__main__":
    start_client()