# Picks a five letter word
# Takes the first guess as input
# Outputs black letters for incorrect guesses, yellow letters for correct 
# guesses in the wrong position, and green letters for guesses in the right position.
# Six guesses total

# ToDO
# Command to start game
# Accept guesses via chat
# Status command
# Notify winners
# Stop game and prep for next game
# Need to keep score, for a yet to be determined period of time.
# Keep full head of hair


from wordlist import WORDS
from random import randint
from colors import *

n = randint(0, len(WORDS))
word = WORDS[n].upper()
print(word)
guesses = 0
guess = ""
status = ""
while guesses <= 6:
    while len(guess) != 5:
        guess = input("Enter guess: ").upper()
        if guess == word:
            print("You won!")
            guesses = 100
        if guess not in WORDS:
            print("This is not a word.")
            guess = ""
        if len(guess) > 5:
            print("This word is too long.")
            guess = ""
        for i in range(0, 5):
            # Letter is not in word
            if guess[i] not in word:
                status += guess[i]
            # Letter is in word, wrong place
            if guess[i] in word:
                status += color(guess[i], fg='red', style="bold") if guess[i] != word[i] else color(guess[i], fg='green', style="bold")
    print(status)
    guesses += 1
    guess = ""
    status = ""