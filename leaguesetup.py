import discord, json, os

data_dir = "data"
config_filename = os.path.join(data_dir, "config.json")

client = discord.Client()

class Command:
    def isauthorized(self, user):
        return True

    async def execute(self, msg, command):
        return

class CommandError(Exception):
    pass


class HelpCommand(Command):
    name = "help"
    template = "k;help [command]"
    description = "Shows the instructions from the readme for a given command. If no command is provided, we will instead provide a list of all of the commands that instructions can be provided for."

    async def execute(self, msg, command):
        query = command.strip()
        if query == "":
            text = "Here's everything I know how to do; use `k;help [command]` for more info:"
            for comm in commands:
                if comm.isauthorized(msg.author):
                    text += f"\n  - {comm.name}"
        else:
            try:
                comm = next(c for c in commands if c.name == query and c.isauthorized(msg.author))
                text = f"`{comm.template}`\n{comm.description}"
            except:
                text = "Can't find that command, boss; try checking the list with `m;help`."
        await msg.channel.send(text)

def config():
    if not os.path.exists(os.path.dirname(config_filename)):
        os.makedirs(os.path.dirname(config_filename))
    if not os.path.exists(config_filename):
        #generate default config
        config_dic = {
                "token" : "",
                "owners" : [
                    0000
                    ],
                "league_cat_id" : 816424161651589120,
                "prefix" : ["k;", "k!"]
            }
        with open(config_filename, "w") as config_file:
            json.dump(config_dic, config_file, indent=4)
            print("please fill in bot token and any bot admin discord ids to the new config.json file!")
            quit()
    else:
        with open(config_filename) as config_file:
            return json.load(config_file)

class AddLeagueCommishCommand(Command):
    name = "addcommissioner"
    template = "k;addcommissioner [league name]\n[any number of mentions]"
    description = "Gives a given user message and pin privileges in a given league's pair of channels."

    def isauthorized(self, user):
        return user.guild_permissions.manage_roles

    async def execute(self, msg, command):
        if not self.isauthorized(msg.author):
            return

        try:
            league_name = command.split("\n")[0].strip()
            users = msg.mentions
        except IndexError:
            await msg.channel.send("Not enough lines in the command!")
            return

        if users == []:
            await msg.channel.send("I need at least one user!")
            return

        chat_channel = discord.utils.find(lambda channel: channel.name == f"{league_name.lower().replace(' ', '-')}-chat" and channel.guild.id == msg.guild.id, client.get_all_channels())
        feed_channel = discord.utils.find(lambda channel: channel.name == f"{league_name.lower().replace(' ', '-')}-feed" and channel.guild.id == msg.guild.id, client.get_all_channels())

        if chat_channel is None or feed_channel is None:
            await msg.channel.send("Those league channels don't exist!")
            return

        com_role = discord.utils.find(lambda role: role.name == f"{league_name} Commissioner" and role.guild.id == msg.guild.id, msg.guild.roles)

        if com_role is None:
            com_role = await make_role(league_name, chat_channel, feed_channel)

        for user in users:
            await user.add_roles(com_role)

        await msg.channel.send("Done!")

class AddLeagueCommand(Command):
    name = "addleague"
    template = "k;addleague [league name]\n[any number of mentions]"
    description = "Creates a pair of league channels, and gives the mentiones users message and pin privileges."

    def isauthorized(self, user):
        return user.guild_permissions.manage_channels

    async def execute(self, msg, command):
        if not self.isauthorized(msg.author):
            return

        try:
            league_name = command.split("\n")[0].strip()
            users = msg.mentions
        except IndexError:
            await msg.channel.send("Not enough lines in the command!")
            return

        if users == []:
            await msg.channel.send("I need at least one user!")
            return

        leagues_category = discord.utils.find(lambda cat: cat.id == config()["league_cat_id"], msg.guild.categories)
       
        if leagues_category is None:
            await msg.channel.send("Can't find the leagues category!")
            return

        chat_channel = await msg.guild.create_text_channel(f"{league_name.lower().replace(' ', '-')}-chat", category=leagues_category)
        feed_channel = await msg.guild.create_text_channel(f"{league_name.lower().replace(' ', '-')}-feed", category=leagues_category)
        com_role = await make_role(league_name, chat_channel, feed_channel)

        for user in users:
            await user.add_roles(com_role)

        await msg.channel.send("Done!")



@client.event
async def on_ready():
    print(f"logged in as {client.user} with token {config()['token']} to {len(client.guilds)} servers")

@client.event
async def on_message(msg):

    if msg.author == client.user or not msg.webhook_id is None:
        return

    command_b = False
    for prefix in config()["prefix"]:
        if msg.content.startswith(prefix):
            command_b = True
            command = msg.content.split(prefix, 1)[1]
    if not command_b:
        return

    try:
        comm = next(c for c in commands if command.startswith(c.name))
        await comm.execute(msg, command[len(comm.name):])
    except StopIteration:
        await msg.channel.send("I can't find that command! Try checking the list with `k;help`.")
    except CommandError as ce:
        await msg.channel.send(str(ce))

commands = [
        HelpCommand(),
        AddLeagueCommishCommand(),
        AddLeagueCommand()
    ]

async def make_role(league_name, chat_channel, feed_channel):
    com_role = await chat_channel.guild.create_role(name=f"{league_name} Commissioner", mentionable=True)
    await chat_channel.set_permissions(com_role, manage_messages=True)
    await feed_channel.set_permissions(com_role, manage_messages=True)
    return com_role

client.run(config()["token"])