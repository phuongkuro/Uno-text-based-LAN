import random

class Game:
    def start_game(self):
        # Shuffle and deal the cards here, then set starting_top_card to None
        self.deck.shuffle()
        self.player_hands = self.deck.deal(self.players)

        # Let the game begin without a starting top card
        self.top_card = None

        return self.player_hands
    
    def draw_card(self, player_name):
        # Draw only 1 card from the deck and add it to the player's hand.
        if not self.deck.cards:  # If the deck is empty, reshuffle the discard pile
            self.reshuffle_discard_pile()
        if self.deck.cards:
            card = self.deck.cards.pop()
            self.player_hands[player_name].append(card)
            self.players_drawn[player_name] = True
            return card  # Return the drawn card not as a list, but rather as a Card object
        return None  # If no cards in the deck, return None

    # Modify or add a method to set the top card when the first player plays
    def set_top_card(self, card):
        self.top_card = card
        
    def __init__(self, deck):
        self.deck = deck  # Use the deck instance passed in as an argument
        self.discard_pile = []  # Initialize an empty discard pile        
        self.players = []  # Will keep track of player order
        self.players_drawn = {}  # Initialize the empty dictionary for tracking draws
        self.top_card = None
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.current_index = 0
        self.player_hands = {}  # Initialize the player_hands dictionary here


    def add_player(self, player_name):
        self.players.append(player_name)
        self.players_drawn[player_name] = False  # Initialize draw tracking to False

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
        # Reset draw flag for the current player
        self.players_drawn[self.get_current_player()] = False
        # Move to the next player
        self.current_index = (self.current_index + self.direction) % len(self.players)

    def reverse_direction(self):
        self.direction *= -1
        # Skip over the next player in the new direction
        self.advance_to_next_player()

    def play_card(self, player_name, card):
        if self.get_current_player() != player_name:
            # It's not the player's turn, so they can't play a card
            return False

        # If it's the first turn of the game (indicated by `self.top_card` being None)
        # set the first played card as the top card if it's in the player's hand
        if self.top_card is None or (
           card.color == self.top_card.color or
           card.value == self.top_card.value or
           card.color == 'Black'):
            # The play is valid
            player_hand = self.player_hands[player_name]
            if card in player_hand:
                player_hand.remove(card)
                self.top_card = card
                self.discard_pile.append(card)
                if card.value == 'Reverse':
                    self.reverse_direction()
                elif card.value == 'Skip':
                    self.advance_to_next_player()
                # Successfully played a card
                return True
        
        # The play was not valid 
        return False

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.color == other.color and self.value == other.value
        return False
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
                    print(f"Dealed {card} to {player_name}")
                else:
                    print("The deck is out of cards!")
                    break
        return player_hands
    def __repr__(self):
        return f"Deck of {len(self.cards)} cards"

