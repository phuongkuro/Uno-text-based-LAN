import random

class Game:
    def start_game(self):
        # Shuffle and deal the cards here, then set starting_top_card to None
        self.deck.shuffle()
        player_hands = self.deck.deal(self.players)

        # Let the game begin without a starting top card
        self.top_card = None

        return player_hands
    
    # Modify or add a method to set the top card when the first player plays
    def set_top_card(self, card):
        self.top_card = card
        
    def __init__(self):
        self.deck = Deck()
        self.players = []  # Will keep track of player order
        self.top_card = None
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.current_index = 0

    def add_player(self, player_name):
        self.players.append(player_name)

    def set_starting_top_card(self):
        # Make sure there's a card to draw
        if self.deck.cards:
            self.top_card = self.deck.cards.pop()
    def can_play_card(self, player_name, card):
        current_player = self.get_current_player()
        if player_name != current_player:
            # It's not the player's turn
            return False

        # Check if the card being played matches the top card's color or value,
        # or if it's a wild card.
        if (card.color == self.top_card.color or
            card.value == self.top_card.value or
            card.color == 'Black'):  # Assuming 'Black' is the color for Wild cards
            return True
        else:
            # The card does not match the color or value, and it's not a wild card
            return False
    def get_current_player(self):
        return self.players[self.current_index]

    def advance_to_next_player(self):
        self.current_index = (self.current_index + self.direction) % len(self.players)

    def reverse_direction(self):
        self.direction *= -1
        # Skip over the next player in the new direction
        self.advance_to_next_player()

    def play_card(self, player_name, card):
        # Additional logic here to check for move validity
        self.top_card = card
        if card.value == 'Reverse':
            self.reverse_direction()

        # Broadcast the top card and the current player's turn
        # Note: The server handles broadcasting, not the Game class
        return True

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def __repr__(self):
        return f"{self.color} {self.value}"

class Deck:
    def __init__(self):
        self.cards = []
        self.create_deck()  # Create the deck when object is instantiated

    def create_deck(self):
        colors = ['Red', 'Yellow', 'Green', 'Blue']
        values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'Skip', 'Reverse', 'Draw Two']
        specials = ['Wild', 'Wild Draw Four']
        # Add number cards
        for color in colors:
            # Add one '0' card per color
            self.cards.append(Card(color, '0'))
            # Add two of each number for each color
            for value in values[1:]:
                self.cards.append(Card(color, value))
                self.cards.append(Card(color, value))
        # Add wild and wild draw four cards
        for special in specials:
            for _ in range(4):
                self.cards.append(Card('Black', special))

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, player_names, num_cards=7):
        player_hands = {player_name: [] for player_name in player_names}
        for _ in range(num_cards):
            for player_name in player_names:
                if self.cards:  # Check that there are still cards to deal
                    card = self.cards.pop()
                    player_hands[player_name].append(card)
                else:
                    print("The deck is out of cards!")
                    break
        return player_hands
    def __repr__(self):
        return f"Deck of {len(self.cards)} cards"

