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


class Geekle:
    def __init__(self):
        self.wordlist_file = "wordlist"
        self.WORDS = self.get_words(self.wordlist_file)
        self.wordlist = self.get_wordlist(self.WORDS)
        self.n = randint(0, len(self.wordlist))
        self.word = self.wordlist[self.n].upper()
        self.guesses = 1
        self.guess = ""
        self.status = ""
        self.status_output = "HTML"
        self.step = ""
        self.prev_message = ""
        self.votes = []
        self.inturn = False
        self.turnstep = 0
        self.final_votes = []

    def update_wordlist(self, word, operation, WORDS):
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

    def get_wordlist(self, WORDS):
        wordlist = []
        for i in range(0, len(WORDS)):
            wordlist += [ WORDS[i]['word'] ]
        return tuple(wordlist)

    def get_words(self, wl_file):
        new_words = []
        lines = open(wl_file, 'r').read().split('\n')
        for line in lines:
            entry = line.split(',')
            new_words += [ dict(word=entry[0], lastsolved=entry[1]) ]
        return tuple(new_words)
    
    def make_msg(self, msg, type):
        return dict(msg=msg, type=type)

    def get_previous(self):
        return ('PREV', [self.make_msg(self.prev_message, 'TEXT')])

    def get_word(self):
        return ('WORD', [self.make_msg(self.word, 'WORD')])
    
    def get_status(self):
        return ('STATUS', [self.make_msg(self.status, 'TEXT')])
    
    def start_game(self):
        self.inturn = True
        self.step = f"GUESS{self.guesses}"
        self.prev_message = "Welcome to Geekle. Please vote on your first guess."
        msg_list = [
            self.make_msg(self.prev_message, 'TEXT'),
            self.make_msg(self.prev_message, 'SPEECH'),
        ]
        return (self.step, msg_list)
    
    def process_guess(self, guess, usr):
        msg = ""
        passed = True
        for i in range(0, len(self.votes)):
            if usr in self.votes[i]:
                passed = False
        if passed:
            if len(guess) > 5:
                msg += f"{usr}: Error. This word is too long. Please retry your guess. "
                passed = False
            elif len(guess) < 5:
                msg += f"{usr}: Error. This word is too short. Please retry your guess. "
                passed = False
            elif guess not in self.wordlist:
                if self.update_wordlist(guess, 'evaluate', self.WORDS):
                    msg += f"{usr}: Added word to list. Thank you for making me a little smarter. "
                    self.WORDS = self.get_words(self.wordlist_file)
                    self.wordlist = self.get_wordlist(self.WORDS)
                else:
                    msg += f"{usr}: Error. This guess is not a word. "
                    passed = False
        else:
            msg += f"{usr}: Error. A vote has already been recorded for you."
        if passed:
            self.votes += [ (usr, guess) ]
        return ('PROC', [self.make_msg(msg, 'TEXT')])

    def tally_vote(self):
        votes = {}
        vote_list = []
        tie = False
        for i in range(0, len(self.votes)):
            word = self.votes[i][1]
            try:
                votes[word] += 1
            except KeyError:
                votes[word] = 1
        thevote = {k: v for k, v in sorted(votes.items(), reverse=True, key=lambda item: item[1])}
        keys = thevote.keys()
        for i in range(0, len(keys)):
            if i == 0:
                vote_list += [ thevote[keys[i]] ]
            else:
                if thevote[keys[i]] == thevote[keys[i-1]]:
                    vote_list += [ thevote[keys[i]] ]
        return vote_list[0]
            
    def process_vote(self, guess):
        html_red = '<span style="color: red;">'
        html_green = '<span style="color: green;">'
        close = "</span>"
        msg = ""
        for i in range(0, 5):
            # Letter is not in word
            if guess[i] not in self.word:
                self.status += guess[i]
            # Letter is in word, wrong place
            if guess[i] in self.word:
                if self.status_output == "ANSI":
                    self.status += color(guess[i], fg='red', style="bold") if guess[i] != self.word[i] else color(guess[i], fg='green', style="bold")
                if self.status_output == "HTML":
                    self.status += f"{html_red}{guess[i]}{close}" if guess[i] != self.word[i] else f"{html_green}{guess[i]}{close}"
        if guess == self.word:
            msg += "Congratulations. You've guessed correctly. "
            self.guesses = 100
        self.guesses += 1
        self.step = "GAMEOVER" if self.guesses == 101 else f"GUESS{self.guesses}"
        self.prev_message = msg
        msg_list = [
            self.make_msg(self.prev_message, 'TEXT'),
            self.make_msg(self.prev_message, 'SPEECH'),
        ]
        return (self.step, msg_list)

# while guesses <= 6:
#     while len(guess) != 5:
#         guess = input("Enter guess: ").upper()
        
#     print(status)
#     guesses += 1
#     guess = ""
#     status = ""

# if update_wordlist(word, 'update', WORDS):
#     print("Wordlist updated.")
# else:
#     print("Wordlist not updated.")

# msg = ""
# if guesses != 100:
#     msg += "I'm sorry. "
# else:
#     msg += "Congratulations! "
# emit(f"The word was {word}.")
# r = requests.get(f'http://api.dictionaryapi.dev/api/v2/entries/en/{word}')
# wordinfo = r.json()
# if "<title>Error</title>" in r.text or "No Definitions Found" in r.text:
#     emit(f"No definitions were found for this word. It is possibly slang. Removing from the list. Sorry.")
#     update_wordlist(word, 'remove', WORDS)
# else:
#     multiple = False
#     if len(wordinfo[0]['meanings']) > 1:
#         multiple = True
#         i = randint(0, len(wordinfo[0]['meanings']) - 1)
#         msg += "There are multiple meanings of this word. In one of the meanings, "
#     word = wordinfo[0]['meanings'][i]
#     preposition = "an" if word['partOfSpeech'][0] in ("aeiou") else "a"
#     msg += f"It is {preposition} {word['partOfSpeech']}, "
#     msg += f"meaning {word['definitions'][randint(0, len(word['definitions']) - 1)]['definition']}. "
#     if multiple:
#         msg += "For other uses of the word, please visit the link in chat."
#         print(wordinfo[0]['sourceUrls'][0])
#     emit(msg)