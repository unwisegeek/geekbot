from twitchio.ext import commands
from twitchio.ext.routines import routine
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import requests
import json
import asyncio
import espeak
from config import *

class Bot(commands.Bot):
    online = False
    msgq = []
    tw_or_gh = "firstrun"
    def __init__(self):
        super().__init__(token=TMI_TOKEN, prefix=BOT_PREFIX, initial_channels=CHANNEL)

        # Connect bot to MQTT Broker
        mqttc = mqtt.Client()
        mqttc.on_connect = Bot.on_connect
        mqttc.on_message = Bot.on_message

        # Connect bot to espeak
        espeak.init()
        voice = espeak.Espeak()
        voice.rate = 125
        voice.voice = {"language": "mb-us2"}
        voice.say("The Geekbot is online.")

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

    def on_connect(mqttc, userdata, flags, rc):
        print(f"Connected to MQTT with result code {str(rc)}")
        mqttc.subscribe("ytchat")

    def on_message(mqttc, userdata, msg):
        payload = eval(msg.payload.decode('utf-8'))
        if payload['author'] != "None":
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

    async def event_message(self, message):
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
            await ctx.send("The Geekbot is listening. Connecting to YouTube.")
        elif usr_perm == 0 and arg == 'stop':
            self.send_yt_msgs.stop()
            self.twitterandgithub.stop()
            await ctx.send("The Geekbot is now offline.")

    @routine(seconds=1)
    async def send_yt_msgs(self):
        if len(self.msgq) > 0:
            chan = self.get_channel("theunwisegeek")
            loop = asyncio.get_event_loop()
            for i in range(0, len(self.msgq)):
                loop.create_task(chan.send(self.msgq.pop(0)))

    @routine(minutes=30)
    async def twitterandgithub(self):
        chan = self.get_channel("theunwisegeek")
        loop = asyncio.get_event_loop()
        if self.tw_or_gh == True:
            loop.create_task(chan.send(f"Follow John on Twitter! https://twitter.com/TheUnwiseGeek/"))
            self.tw_or_gh = False
        elif self.tw_or_gh == "firstrun":
            print("Skipping linkdrop for the first run.")
            self.tw_or_gh = False
        elif self.tw_or_gh == False:
            loop.create_task(chan.send(f"Want a closer look at the code you see on this Stream? Want to contribute to the Buttonbox? Follow John on Github https://github.com/unwisegeek"))
            self.tw_or_gh = True

bot = Bot()
bot.run()
