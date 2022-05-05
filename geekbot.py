from twitchio.ext import eventsub, commands
from twitchio.ext.routines import routine
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import requests
import json
import asyncio
import espeak
from config import *
from Geekle import Geekle
from mycroft_bus_client import MessageBusClient, Message
import os
from time import time

class Bot(commands.Bot):
    online = False
    msgq = []
    tw_or_gh = "firstrun"
    game_in_progress = False
    def __init__(self):
        super().__init__(token=TMI_TOKEN, prefix=BOT_PREFIX, initial_channels=CHANNEL)

        # Connect bot to MQTT Broker
        mqttc = mqtt.Client()
        mqttc.on_connect = Bot.on_connect
        mqttc.on_message = Bot.on_message

        # Connect bot to Mycroft
        self.mycroft = MessageBusClient()
        self.mycroft.run_in_thread()
        self.say("The Geekbot is online.")

        if MQTT_AUTH == None:
            mqttc.username_pw_set(
                username=None,
                password=None,
            )
        else:
            mqttc.username_pw_set(
                username=MQTT_AUTH['username'],
                password=MQTT_AUTH['password'],
            )
        mqttc.connect(MQTT_HOST, MQTT_PORT)
        # Non-Blocking Loop
        mqttc.loop_start()

    def say(self, msg):
        self.mycroft.emit(Message('speak', data={'utterance': msg}))
    
    def chat(self, msg):
        chan = self.get_channel("theunwisegeek")
        loop = asyncio.get_event_loop()
        loop.create_task(chan.send(msg))

    def on_connect(mqttc, userdata, flags, rc):
        print(f"Connected to MQTT with result code {str(rc)}")
        mqttc.subscribe("ytchat")

    def on_message(mqttc, userdata, msg):
        payload = eval(msg.payload.decode('utf-8'))
        if payload['author'] != "None":
            if "[Twitch]" not in payload['msg']:
                Bot.msgq.append(f"[YouTube] {payload['author']}: {payload['msg']}")
        else:
            Bot.msgq.append(payload['msg'])

    def mqtt_publish(author, msg):
        publish.single(
                'twchat', 
                str(dict(author=author, msg=msg, service="Twitch")),
                qos=0, 
                retain=False, 
                hostname=MQTT_HOST,
                port=MQTT_PORT, 
                client_id="", 
                keepalive=60,
                will=None,
                auth=MQTT_AUTH,
                tls=None,
                protocol=mqtt.MQTTv311,
                transport="tcp",
                )

    async def event_ready(self):
        print(f"{BOT_NICK} is online and connecting to Twitch.")

    async def event_raw_usernotice(self, message, channel=['theunwisegeek']):
        print(message)

    async def event_message(self, message):
        print(message.raw_data)
        if f"{BOT_NICK}!{BOT_NICK}@{BOT_NICK}" in message.raw_data:
            author = "6E3KBot"
            color = "FFD700"
            msg = message.content
            if "PRIVMSG(ECHO)" not in message.raw_data and "[YouTube]" not in message.raw_data and "[Twitch]" not in message.raw_data and msg[0] != "!":
                Bot.mqtt_publish(author, msg)
                r = requests.get(f"http://{API_HOST}:{API_PORT}/api/newchatmsg?author={author}&color={color}&msg={msg}&service=Twitch")
        else:
            try:
                author = message.tags['display-name']
                color = message.tags['color'].strip("#") if message.tags['color'] != '' else '0000FF'
                msg = message.content
                if msg[0] != "!":
                    Bot.mqtt_publish(author, msg)
                    r = requests.get(f"http://{API_HOST}:{API_PORT}/api/newchatmsg?author={author}&color={color}&msg={msg}&service=Twitch")
                await self.handle_commands(message)
            except:
                pass
        

    @commands.command()
    async def hello(self, ctx: commands.Context):
        msg = f"Hello! I am {BOT_NICK}, human-cyborg-human-computer-API-computer-then-back-around-to-human relations."
        r = requests.get(f"http://{API_HOST}:{API_PORT}/api/newchatmsg?author=6E3KBot&color=FFD700&msg={msg}&service=Twitch")
        await ctx.send(msg)

    @commands.command()
    async def tso(self, ctx: commands.Context, arg):
        msg = f"Check out {arg} on their Twitch channel at https://twitch.tv/{arg}!!"
        r = requests.get(f"http://{API_HOST}:{API_PORT}/api/newchatmsg?author=6E3KBot&color=FFD700&msg={msg}&service=Twitch")
        await ctx.send(msg)

    def get_user_from_rawdata(self, msg):
        tags = msg.split(';')
        for tag in tags:
            if 'display-name' in tag:
                return tag.split('=')[1]

    def get_perms(self, usr):
        if usr in OWNER:
            return 0
        if usr in MODS:
            return 1
        if usr in VIPS:
            return 2
        return 3

    @commands.command()
    async def bot(self, ctx: commands.Context, arg):
        usr = self.get_user_from_rawdata(ctx.message.raw_data)
        usr_perm = self.get_perms(usr)
        print(arg)
        if usr_perm == 0 and arg == 'start':
            self.send_yt_msgs.start()
            self.twitterandgithub.start()
            self.refreshsongsource.start()
            self.geeklecron.start()
            await ctx.send("The Geekbot is listening. Connecting to YouTube.")
        elif usr_perm == 0 and arg == 'stop':
            self.send_yt_msgs.stop()
            self.twitterandgithub.stop()
            self.refreshsongsource.stop()
            await ctx.send("The Geekbot is now offline.")

    @commands.command()
    async def geekle(self, ctx: commands.Context, arg):
        def handle_msgs(msg, game):
            step = msg[0]
            msg_list = msg[1]
            ALLOWED_TYPES = ('TEXT', 'SPEECH', 'WORD', 'PREV', 'STATUS')
            for msg in msg_list:
                print(msg)
                if 'GUESS' in step:
                    game.inturn = True
                    with open('geeklecron', 'w') as f:
                        f.write(str(time()))
                if 'GAMEOVER' in msg['type']:
                    self.inturn = False
                    
                    self.game_in_progress = False

                if msg['type'] in ALLOWED_TYPES:
                    if msg['type'] in ('TEXT', 'PREV', 'STATUS'):
                        text = ""
                        text += f"Previous Message: " if msg['type'] == 'PREV' else ""
                        text += f"Status: " if msg['type'] == 'STATUS' else ""
                        text += msg['msg']
                        self.chat(text)
                    if msg['type'] == 'SPEECH':
                        self.say(msg['msg'])
                    if msg['type'] == 'WORD':
                        text = f"The word from this game was: {msg['msg']}"
                        self.chat(text)

        usr = self.get_user_from_rawdata(ctx.message.raw_data)
        usr_perm = self.get_perms(usr)
        print(arg)
        if arg == 'go':
            if self.game_in_progress:
                await ctx.send("There is a game already in progress. We cannot start another.")
            else:
                self.game_in_progress = True
                self.new_game = Geekle()
                game_status = self.new_game.start_game()
                handle_msgs(game_status, self.new_game)
        elif arg == 'cancel' or arg == 'stop':
            if usr_perm <= 1:
                self.game_in_progress = False
                self.new_game = ""
                self.say("The previous game of Geekle has been stopped.")
                await ctx.send(f"{usr} has stopped the previous game of Geekle. Game on!")
            else:
                await ctx.send(f"{usr} does not have the permission to stop a game. Further attempts will result in trolls returning beneath bridges.")
        elif arg == 'status':
            handle_msgs(self.new_game.get_status(), self.new_game)
        elif arg == 'prev':
            prev = self.new_game.get_previous()
            handle_msgs(prev, self.new_game)
        elif arg == 'tiebreak':
            if arg in self.new_game.final_votes:
                self.new_game.process_vote(arg)
            else:
                self.say("That was not one of the votes, John. Try again.")
                self.chat("That was not one of the votes, John. Try again.")
        else:
            # Accept a vote from each person per turn (no multiple votes, Monica)
            ## Routine to start the turn
            ## At completion of routine, send most voted to Geekle or send votes list to John
            ## Start a new turn
            # Vote must be timeboxed for 2.5 minutes
            try:
                if self.new_game.inturn:
                    result = self.new_game.process_guess(arg, usr)
                    handle_msgs(result, self.new_game)
            except AttributeError:
                pass

    @routine(seconds=1)
    async def geeklecron(self):
        try:
            game = self.new_game
            turntime = 30.0
            if os.path.exists('geeklecron'):
                with open('geeklecron', 'r') as f:
                    crontime = float(f.read().strip('\n'))
                    if time() >= crontime + turntime:
                        game.final_votes = game.tally_votes()
                        if len(game.final_votes) > 1:
                            self.speak("There is a tie! John the Unwise Geek, break the tie.")
                            self.chat(f"There is a tie! John the Unwise Geek, break the tie using one of the following words: {game.final_votes}")
                        else:
                            game.process_vote(game.final_votes[0])
                        os.remove('geeklecron')
        except AttributeError:
            pass


    @routine(seconds=1)
    async def send_yt_msgs(self):
        if len(self.msgq) > 0:
            for i in range(0, len(self.msgq)):
                self.chat(self.msgq.pop(0))

    @routine(minutes=30)
    async def twitterandgithub(self):
        if self.tw_or_gh == True:
            self.chat(f"Follow John on Twitter! https://twitter.com/TheUnwiseGeek/")
            self.tw_or_gh = False
        elif self.tw_or_gh == "firstrun":
            print("Skipping linkdrop for the first run.")
            self.tw_or_gh = False
        elif self.tw_or_gh == False:
            self.chat(f"Want a closer look at the code you see on this Stream? Want to contribute to the Buttonbox? Follow John on Github https://github.com/unwisegeek")
            self.tw_or_gh = True

    @routine(seconds=15)
    async def refreshsongsource(self):
        r = requests.get(f"http://{API_HOST}:{API_PORT}/api/refreshsongsource")

bot = Bot()
bot.run()
