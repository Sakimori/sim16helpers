from discord import Embed, Color
from enum import Enum
from random import shuffle

class deck(object):

    

    def new_deck(self):
        newdeck = []
        for i in range(0,22):
            newdeck.append(card(suit.Majors, i))

        for this_suit in [suit.Cups, suit.Wands, suit.Swords, suit.Pentacles]:
            for j in range(1,15):
                newdeck.append(card(this_suit, j))

        return newdeck

    def __init__(self):
        self.deck = self.new_deck()

    def shuffle(self): #literally just to have a nice function instead of having to import shuffle on main
        shuffle(self.deck)

    def draw(self):
        try:
            return self.deck.pop(0)
        except:
            return False

class suit(Enum):
    Majors = ""
    Cups = "of Cups"
    Wands = "of Wands"
    Swords = "of Swords"
    Pentacles = "of Pentacles"

class card(object):
    roman_map = ["Egg", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XIX"]
    majors = ["The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", "The Heirophant", "The Lovers", "The Chariot", "Justice", "The Hermit", "Wheel of Fortune",
              "Strength", "The Hanged Man", "Death", "Temperance", "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"]
    court_conversion = {11 : "Sister", 12 : "Brother", 13 : "Mother", 14 : "Father"}

    color_map = {suit.Majors : Color.dark_purple(),
                 suit.Cups : Color.blue(),
                 suit.Wands : Color.red(),
                 suit.Swords : Color.gold(),
                 suit.Pentacles : Color.green(),
                 "back" : Color.dark_grey()}

    def __init__(self, suit, number):
        self.suit = suit
        self.number = number
        self.flipped = False

    def __str__(self):
        if not self.flipped:
            return "Hidden Card"
        elif self.suit == suit.Majors:
            return f"{card.roman_map[self.number]}: {card.majors[self.number]}"
        elif self.number in card.court_conversion:
            return f"{card.court_conversion[self.number]} {self.suit.value}"
        else:
            return f"{card.roman_map[self.number]} {self.suit.value}"

    def embed(self):
        this_embed = Embed(color=card.color_map[self.suit] if self.flipped else card.color_map["back"], title=str(self))
        return this_embed