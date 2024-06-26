import socket
import threading
import pickle
from card import Deck
from card import Game
from card import Card

# Dictionary to hold client info
clients = {}

# Initialize deck
deck = Deck()
game = Game(deck)


def send_hand(client_socket, hand):
    pickled_hand = pickle.dumps(hand)
    hand_message = b'PICKLE:' + pickled_hand
    # Prefix each message with a 4-byte length header
    prefixed_message = len(hand_message).to_bytes(4, byteorder='big') + hand_message
    client_socket.send(prefixed_message)

def send_turn_notification(client_socket, player_name):
    turn_message = f"It's {player_name}'s turn."
    encoded_message = b'TEXT:' + turn_message.encode('utf-8')
    prefixed_message = len(encoded_message).to_bytes(4, byteorder='big') + encoded_message
    client_socket.send(prefixed_message)

# Function to broadcast messages to one client
# Function to send a message to the client with message type prefixed
def send_to_client(client_socket, message, message_type):
    if isinstance(message, str):
        message = message.encode('utf-8')

    if message_type == 'text':
        header = b'TEXT:'
    elif message_type == 'pickle':
        header = b'PICKLE:'
    else:
        raise ValueError(f"Unknown message type: {message_type}")

    # Prepend header and length of message
    full_message = header + message
    message_with_length = len(full_message).to_bytes(4, 'big') + full_message

    try:
        client_socket.sendall(message_with_length)
        print(f"Sent to {client_socket.getpeername()}: {message.decode('utf-8')}")
    except Exception as e:
        print(f"Error sending message: {e}")

# Function to handle '/s' command from clients
def start_game():
    global clients, deck, game
    if len(clients) < 2:
        broadcast("At least two players are needed to start the game.",'text')
        return  # Exit the function if not enough players
    print(f"Number of cards in the deck before shuffling and dealing: {len(deck.cards)}")  # Debug print

    deck.shuffle()
    game.players = list(clients.keys())  # Set player order to the order of connections    
    print("Shuffling deck and starting the game with players: " + ", ".join(clients.keys()))

    # Dealing cards
    player_hands = game.start_game()
    for username, hand in player_hands.items():
        client_socket = clients[username]
        send_hand(client_socket, hand)  # Use the send_hand method to send the pickled hand 

        print(f"Dealt hand to {username}.")
    print(f"Number of cards remaining in the deck after dealing: {len(deck.cards)}")  # Debug print

    announce_turn()
    
    # This is where we're adding the print statement for debugging
    print(f"Number of cards remaining in the deck after dealing: {len(deck.cards)}")
    print(f"ID of global deck object: {id(deck)}")  # Debug print
    print(f"ID of game's deck object: {id(game.deck)}")  # Debug print

    if id(deck) != id(game.deck):
        print("Different deck instances are being used!")  # Debug notice
        return  # Exit the function
def announce_turn():
    current_player = game.get_current_player()

    # Send text messages to each client announcing the current player's turn
    for client_name, client_socket in clients.items():
        if client_name == current_player:
            send_to_client(client_socket, f"It's your turn to play.", 'text')
        else:
            send_to_client(client_socket, f"It's {current_player}'s turn.", 'text')

def handle_play_card(player_name, card):
    if game.get_current_player() != player_name:
        # It's not the player's turn
        send_to_client(clients[player_name], "It's not your turn.", 'text')
    elif game.top_card is None:
        # If it's the first turn of the game, any card can be played if it's in the player's hand
        if card in game.player_hands[player_name]:
            game.play_card(player_name, card)  # Play the card
            broadcast(f"Player {player_name} played: {card}", 'text')

            # Send the updated hand back to the player after playing
            send_hand(clients[player_name], game.player_hands[player_name])

            game.advance_to_next_player()
            announce_turn()
        else:
            # The card is not in the player's hand, don't advance the turn
            send_to_client(clients[player_name], "You don't have that card. Try again.", 'text')
    elif game.can_play_card(player_name, card):
        # If the played card is valid and it's in the player's hand
        if card in game.player_hands[player_name]:
            game.play_card(player_name, card)  # Play the card
            broadcast(f"Player {player_name} played: {card}", 'text')

            # Send the updated hand back to the player after playing
            send_hand(clients[player_name], game.player_hands[player_name])

            game.advance_to_next_player()
            announce_turn()
        else:
            # It's a valid play in terms of game rules, but the card isn't in the player's hand
            send_to_client(clients[player_name], "Invalid card played. Try again.", 'text')
    else:
        # It's not the first play, and the card isn't valid to be played according to the game rules
        send_to_client(clients[player_name], "Invalid card played. Try again.", 'text')

# Function to broadcast messages to all connected clients
def broadcast(message, message_type='text', exclude_user=None):
    global clients

    # Prepare the message based on type
    if message_type == 'text':
        message = 'TEXT:' + message
        message = message.encode('utf-8')  # Encode the text message as bytes
    elif message_type == 'pickle':
        message = 'PICKLE:' + message  # Pickle message should already be in bytes

    # Include message size prefix
    message_size = len(message).to_bytes(4, 'big')
    full_message = message_size + message

    # Send the full_message to each client
    to_remove = []  # Keep track of clients to remove after iteration
    for username, client_socket in clients.items():
        if username == exclude_user:
            continue
        try:
            client_socket.sendall(full_message)  # Send the encoded message with the header
        except Exception as e:
            print(f"Error broadcasting message to {username}: {e}",'text')
            to_remove.append(username)

    # Remove clients that could not receive the message
    for username in to_remove:
        if username in clients:
            # Close the connection gracefully
            clients[username].close()
            del clients[username]
            # Inform other clients that this user has left
            broadcast(f"{username} has left the game.", 'text')  # Make sure to specify the message type here

def is_valid_play(message):
    # Assuming a valid play message is "PLAY <Color> <Value>"
    parts = message.split()
    if len(parts) != 3:
        return False
    color, value = parts[1], parts[2]
    # Define the valid colors and values based on your game rules
    valid_colors = ['Red', 'Yellow', 'Green', 'Blue', 'Black']
    valid_values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'Skip', 'Reverse', 'Draw Two', 'Wild', 'Wild Draw Four']
    return color in valid_colors and value in valid_values


def handle_client(client_socket, client_address):
    global clients
    print(f"Connection attempt from {client_address}")
    username = None

    try:
        while True:
            username = client_socket.recv(1024).decode('utf-8').strip()
            if username in clients:
                send_to_client(client_socket, "Username has been taken, please choose another", 'text')
                continue  # Wait for the user to enter another username
            if not username:
                send_to_client(client_socket, "Invalid username; username cannot be blank.", 'text')
                continue  # Wait for the user to enter another username

            clients[username] = client_socket
            game.add_player(username)  # Add the new player to the Game
            print(f"Connection established with {username} from {client_address}")
            broadcast(f"{username} has joined the game.", 'text')
            send_to_client(client_socket, "Welcome to the game! When all players have joined, the host will start the game.", 'text')
            break  # Exit the loop as a valid username has been set

        # Main loop to receive messages from this client
        while True:
            # Receives a message
            received_data = client_socket.recv(1024)
            if not received_data:
                break  # If no message, assume the client disconnected

            message = received_data.decode('utf-8').strip()
            
            if message.startswith('DRAW') and game.get_current_player() == username:
                handle_draw_card(username)            
            elif message.startswith('PLAY'): 
                if is_valid_play(message):
                    # Here you can process the card play because it's a valid format
                    card_info = message.split()
                    card_color, card_value = card_info[1], card_info[2]
                    card_to_play = Card(card_color, card_value)
                    handle_play_card(username, card_to_play)
                else:
                    # This is where you tell the client that the play is invalid
                    send_to_client(client_socket, "Invalid card format. Try again.", 'text')
            else:
                broadcast(f"{username}: {message}",'text', username)
    except ConnectionResetError:
        print(f"Connection lost with {username or client_address} unexpectedly.")
    except Exception as e:
        print(f"An exception occurred with {username or client_address}: {e}")
    finally:
        # Cleanup and inform other players if a client disconnects
        if username and username in clients:
            clients.pop(username, None)
            broadcast(f"{username} has left the game.", 'text')
            # If a disconnect occurs during the game, handle any necessary game state adjustments here

        if username in game.players:
            game.players.remove(username)
            # Also remove from players_drawn if using that to track who has drawn a card
            if username in game.players_drawn:
                del game.players_drawn[username]
        
        client_socket.close()
        print(f"Connection closed for {username or client_address}")


def handle_draw_card(player_name):
    # If it's the first turn and the current player is trying to draw, stop them
    if game.top_card is None and game.get_current_player() == game.players[0]:
        send_to_client(clients[player_name], "You shall not pass on the first turn!", 'text')
        send_to_client(clients[player_name], f"It's your turn to play.", 'text')
        return

    # If the player has already drawn a card during their turn, skip them
    if game.players_drawn[player_name]:
        send_to_client(clients[player_name], "You have already drawn a card. Turn moves to next player.", 'text')
        game.advance_to_next_player()
        announce_turn()
        return

    # Draw a card and announce it to the player
    drawn_card = game.draw_card(player_name)
    send_to_client(clients[player_name], f"You drew: {drawn_card}", 'text')
    send_hand(clients[player_name], game.player_hands[player_name])  # Send updated hand

    # Allow the player to decide if they want to play if they have a playable card
    if any(game.can_play_card(player_name, card) for card in game.player_hands[player_name]):
        send_to_client(clients[player_name], f"It's your turn to play.", 'text')
    else:
        # Player doesn't have a playable card or chooses to pass after draw, move to the next player
        game.advance_to_next_player()
        announce_turn()


# Function to accept new connections
def accept_connections(server_socket):
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.start()
        except Exception as e:
            print(f"Error accepting new connections: {e}")
            break


def server_input_handler():
    while True:
        cmd = input("Enter '/s' to begin: ")  # Prompt for the command
        if cmd.lower() == '/s':
            if len(clients) >= 2:
                start_game()
            else:
                print("At least two players are needed to start the game.")
        # No 'else' block that leads to server shutdown or 'break' statement

# Main function to start the server
def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        accept_connections(server_socket)
    finally:
        server_socket.close()


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        return local_ip
    except Exception as e:
        print("Không thể lấy địa chỉ IP:", e)
        return None


if __name__ == "__main__":
    HOST = get_local_ip()
    PORT = 65432

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server listening on {HOST}:{PORT}")

    accept_thread = threading.Thread(target=accept_connections, args=(server_socket,))
    accept_thread.start()

    server_input_thread = threading.Thread(target=server_input_handler)
    server_input_thread.start()

    # Main server loop
    try:
        accept_thread.join()  # Wait for the thread to finish, which should be never unless the server intentionally shuts down
        server_input_thread.join()
    except KeyboardInterrupt:
        print("Server shut down by keyboard interrupt.")
    finally:
        print("Shutting down the server.")
        for _, client in clients.items():  # Use .values() if client is just the socket
            client.close()
        server_socket.close()

# Corrected the structure of the server's main loop.
