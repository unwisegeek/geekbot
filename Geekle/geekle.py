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

from random import randint
from colors import *
from time import time
import requests
from mycroft_bus_client import MessageBusClient, Message

SPEAK = True

mycroft = MessageBusClient()
mycroft.run_in_thread()

wordlist_file = "wordlist"

def update_wordlist(word, operation, WORDS):
    if operation == 'remove':
        f = open('wordlist', 'w')
        new_words = ""
        counter = 0
        for wil in WORDS:
            if wil['word'] == word:
                pass
            else:
                new_words += f"{wil['word']},{wil['lastsolved']}"
                new_words += "\n" if counter != len(WORDS) - 1 else ""
            counter += 1
        f.write(new_words)
        f.close()
        return True
    if operation == 'update':
        f = open('wordlist', 'w')
        new_words = ""
        counter = 0
        for wil in WORDS:
            new_time = wil['lastsolved']
            if str(wil['word']).upper() == word.upper():
                new_time = str(int(time()))
            new_words += f"{wil['word']},{new_time}"
            new_words += "\n" if counter != len(WORDS) - 1 else ""
            counter += 1
        f.write(new_words)
        f.close()
        return True
    if operation == 'evaluate':
        r = requests.get(f'http://api.dictionaryapi.dev/api/v2/entries/en/{word}')
        if type(r.json()) == type({}):
            print("This is not a word.")
            return False
        elif type(r.json()) == type([]):
            f = open('wordlist', 'w')
            new_words = ""
            new_dict = {}
            for wil in WORDS:
                new_dict['word'] = wil['word']
                new_dict['lastsolved'] = wil['lastsolved']
                new_words += f"{new_dict['word']},{new_dict['lastsolved']}\n"
                new_dict = {}
            new_dict['word'] = word
            new_dict['lastsolved'] = 0
            new_words += f"{new_dict['word']},{new_dict['lastsolved']}"
            f.write(new_words)
            f.close()
            return True
    return False

def get_wordlist(WORDS):
    wordlist = []
    for i in range(0, len(WORDS)):
        wordlist += [ WORDS[i]['word'] ]
    return tuple(wordlist)

def get_words(wl_file):
    new_words = []
    lines = open(wl_file, 'r').read().split('\n')
    for line in lines:
        entry = line.split(',')
        new_words += [ dict(word=entry[0], lastsolved=entry[1]) ]
    return tuple(new_words)

def speak(msg):
    if SPEAK:
        mycroft.emit(Message('speak', data={'utterance': msg}))
    else:
        pass

def emit(msg):
    print(msg)
    speak(msg)

WORDS = get_words(wordlist_file)
wordlist = get_wordlist(WORDS)
n = randint(0, len(wordlist))
word = wordlist[n].upper()
guesses = 1
guess = ""
status = ""
emit("Welcome to Geekle. Please enter your first guess.")
while guesses <= 6:
    while len(guess) != 5:
        guess = input("Enter guess: ").upper()
        if len(guess) > 5:
            emit("This word is too long.")
            guess = ""
            continue
        if guess not in wordlist:
            if update_wordlist(guess, 'evaluate', WORDS):
                print("Added word to list. Thank you for making me a little smarter.")
                WORDS = get_words(wordlist_file)
                wordlist = get_wordlist(WORDS)
            else:
                guess = ""
                continue
        for i in range(0, 5):
            # Letter is not in word
            if guess[i] not in word:
                status += guess[i]
            # Letter is in word, wrong place
            if guess[i] in word:
                status += color(guess[i], fg='red', style="bold") if guess[i] != word[i] else color(guess[i], fg='green', style="bold")
        if guess == word:
            emit("Congratulations. You've guessed correctly.")
            guesses = 100
    print(status)
    guesses += 1
    guess = ""
    status = ""

if update_wordlist(word, 'update', WORDS):
    print("Wordlist updated.")
else:
    print("Wordlist not updated.")

msg = ""
if guesses != 100:
    msg += "I'm sorry. "
else:
    msg += "Congratulations! "
emit(f"The word was {word}.")
r = requests.get(f'http://api.dictionaryapi.dev/api/v2/entries/en/{word}')
wordinfo = r.json()
if "<title>Error</title>" in r.text or "No Definitions Found" in r.text:
    emit(f"No definitions were found for this word. It is possibly slang. Removing from the list. Sorry.")
    update_wordlist(word, 'remove', WORDS)
else:
    multiple = False
    if len(wordinfo[0]['meanings']) > 1:
        multiple = True
        i = randint(0, len(wordinfo[0]['meanings']) - 1)
        msg += "There are multiple meanings of this word. In one of the meanings, "
    word = wordinfo[0]['meanings'][i]
    preposition = "an" if word['partOfSpeech'][0] in ("aeiou") else "a"
    msg += f"It is {preposition} {word['partOfSpeech']}, "
    msg += f"meaning {word['definitions'][randint(0, len(word['definitions']) - 1)]['definition']}. "
    if multiple:
        msg += "For other uses of the word, please visit the link in chat."
        print(wordinfo[0]['sourceUrls'][0])
    emit(msg)