import discord, json, os, tarot, perennial, asyncio

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
            com_role = await make_admin_role(league_name, chat_channel, feed_channel)

        for user in users:
            await user.add_roles(com_role)

        await msg.channel.send("Done!")

class AddLeagueCommand(Command):
    name = "addleague"
    template = "k;addleague [league name]\n[any number of mentions]"
    description = "Creates a pair of league channels, and gives the mentioned users message and pin privileges."

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

        leagues_category = find_league_category(msg.guild)
       
        if leagues_category is None:
            await msg.channel.send("Can't find the leagues category!")
            return

        chat_channel = await msg.guild.create_text_channel(f"{league_name.lower().replace(' ', '-')}-chat", category=leagues_category)
        feed_channel = await msg.guild.create_text_channel(f"{league_name.lower().replace(' ', '-')}-feed", category=leagues_category)
        com_role = await make_admin_role(league_name, chat_channel, feed_channel)

        for user in users:
            await user.add_roles(com_role)

        await msg.channel.send("Done!")

class ManagerSignupCommand(Command):
    name = "managersignup"
    template = "k;managersignup [league name]"
    description = "Signs you up as a team manager for the given league. This role is pingable."

    async def execute(self, msg, command):
        league_name = command.strip()
        leagues_category = find_league_category(msg.guild)
       
        if leagues_category is None:
            await msg.channel.send("Can't find the leagues category!")
            return

        chat_channel = discord.utils.find(lambda channel: channel.name == f"{league_name.lower().replace(' ', '-')}-chat" and channel.guild.id == msg.guild.id, client.get_all_channels())
        if chat_channel is None:
            await msg.channel.send("That league doesn't have channels on this server!")
            return

        role = discord.utils.find(lambda role: role.name == f"{league_name} Team Manager" and role.guild.id == msg.guild.id, msg.guild.roles)

        if role is None:
            role = await make_vanity_role(msg.guild, f"{league_name} Team Manager", pingable=True)
        await msg.author.add_roles(role)
        await msg.channel.send("Done!")

class ManagerStepdownCommand(Command):
    name = "managerstepdown"
    template = "k;managerstepdown [league name]"
    description = "Removes the team manager role for the given league."

    async def execute(self, msg, command):
        league_name = command.strip()
        leagues_category = find_league_category(msg.guild)
       
        if leagues_category is None:
            await msg.channel.send("Can't find the leagues category!")
            return

        chat_channel = discord.utils.find(lambda channel: channel.name == f"{league_name.lower().replace(' ', '-')}-chat" and channel.guild.id == msg.guild.id, client.get_all_channels())
        if chat_channel is None:
            await msg.channel.send("That league doesn't have channels on this server!")
            return

        role = discord.utils.find(lambda role: role.name == f"{league_name} Team Manager" and role.guild.id == msg.guild.id, msg.author.roles)

        if role is None:
            await msg.channel.send("You already don't have that role. Congratulations! <:ElfneinWeld:497869710654963723>")
            return

        await msg.author.remove_roles(role)
        await msg.channel.send("Done!")

perennial_box = None

class PerennialStartCommand(Command):
    name = "perennialstart"
    template = "k;perennialstart [spreadsheet id]\n[# of draft rounds]\n[mention]\n[first team name]\n..."
    description = "love youuuu 💜"
    

    def isauthorized(self, user):
        return user.id == 147166236223078411 or user.id == 102691114762371072

    async def execute(self, msg, command):
        global perennial_box
        if perennial_box is not None:
            await msg.channel.send("I'm already running the draft!!")
            return 

        team_dic = {}
        teams_list = []
        sheet_id = command.split("\n")[0].strip()
        rounds = int(command.split("\n")[1].strip())
        msg_lines = command.split("\n")
        this_user = None
        for i in range(2, len(msg_lines)):
            if i % 2 == 0:
                this_user = discord.utils.find(lambda user : user.id == (int(''.join(c for c in msg_lines[i] if c.isdigit()))), msg.mentions)
                if this_user is None:
                    await msg.channel.send("At least one of the mention lines is wrong, so I've stopped it for you to try again.")
                    return
            else:
                team_name = msg_lines[i].strip()
                teams_list.append(team_name)
                team_dic[team_name] = this_user
        perennial_box = perennial.perennial(msg.channel, team_dic, teams_list, rounds)
        perennial_box.connect(sheet_id)
        next_team, next_user = perennial_box.current_drafter()
        await msg.channel.send("<:MikuPraise:643957692326739968>")
        await msg.channel.send("First up:")
        await msg.channel.send(f"{next_user.mention} for {next_team}!")

class PerennialViewCommand(Command):
    name = "perennialcheck"
    template = "k;perennialcheck"
    description = "Shows whose turn it is!"

    async def execute(self, msg, command):
        global perennial_box
        if perennial_box is None:
            await msg.channel.send("No draft running right now. Sorry!!")
            return
        team, owner = perennial_box.current_drafter()
        await msg.channel.send(f"Now drafting: {owner.display_name} for {team}.")

class PerennialPassCommand(Command):
    name = "perennialpass"
    template = "k;perennialpass"
    description = "Use to pass on your draft, or, if you're star, use to skip someone who's taking way too long!"

    async def execute(self, msg, command):
        global perennial_box
        if perennial_box is None:
            await msg.channel.send("No draft running right now. Sorry!!")
            return
        team, owner = perennial_box.current_drafter()
        if msg.author.id != owner.id and msg.author.id not in [147166236223078411, 102691114762371072]:
            await msg.channel.send("This team ain't yours!! Be patient <:AngerDess:535188304165994506>")
            return

        perennial_box.counter += 1
        next_team, next_user = perennial_box.current_drafter()
        if next_team:
            await msg.channel.send("Skipped! Up next:")
            await msg.channel.send(f"{next_user.mention} for {next_team}!")
        else:
            await msg.channel.send("Starrrrrr, we're done!!")
            perennial_box = None

class PerennialDraftPlayer(Command):
    name = "draftplayer"
    template = "k;draftplayer [player name]\n[player to return to the draft]"
    description = "Run this to draft a player to the team currently drafting! Only works if you're the registered founder, mind you."
    

    async def execute(self, msg, command):
        global perennial_box
        if perennial_box is None:
            await msg.channel.send("No draft running right now. Sorry!!")
            return

        team, owner = perennial_box.current_drafter()
        if msg.author.id != owner.id:
            await msg.channel.send("This team ain't yours!! Be patient <:AngerDess:535188304165994506>")
            return

        player_add_name = command.split("\n")[0].strip()
        player_remove_name = command.split("\n")[1].strip()
        if not perennial_box.check_for_name(player_add_name):
            await msg.channel.send("I can't find that player on the spreadsheet. Is that a me or a you problem?")
            return

        perennial_box.remove_available(player_add_name)
        await asyncio.sleep(1)
        perennial_box.add_available(player_remove_name)

        command_to_send = f"""m;replaceplayer
{team}
{player_remove_name}
{player_add_name}
"""
        perennial_box.counter += 1
        next_team, next_user = perennial_box.current_drafter()
        await msg.channel.send(command_to_send)
        await asyncio.sleep(8)

        if next_team:
            await msg.channel.send("Done! Up next:")
            await msg.channel.send(f"{next_user.mention} for {next_team}!")
        else:
            await msg.channel.send("Starrrrrr, we're done!!")
            perennial_box = None


class PerennialFixCommand(Command):
    name = "perennialfix"
    template = "k;perennialfix [available|taken]\n[player name]"
    description = "in case someone typos a player name or something, this is here for you to fix the spreadsheet without breaking the automation 💜"

    def isauthorized(self, user):
        return user.id == 147166236223078411 or user.id == 102691114762371072

    async def execute(self, msg, command):
        global perennial_box
        if perennial_box is None:
            await msg.channel.send("No spreadsheet connection, start a fake draft to make one!")
            return

        if "available" in command.split("\n")[0].lower():
            perennial_box.add_available(command.split("\n")[1].strip())
        elif "taken" in command.split("\n")[0].lower():
            perennial_box.add_taken(command.split("\n")[1].strip())
        else:
            await msg.channel.send("Tell me if it's an available name or one taken, please!")
            return
        await msg.channel.send("Done!")


decks = {}
spreads = {}

class DeckCommand(Command):
    name = "tarotdeck"
    template = "k;tarotdeck"
    description = "Gives you a brand new, unshuffled tarot deck!"

    async def execute(self, msg, command):
        if msg.author.id in decks:
            await msg.channel.send("You already have a deck! Use k;shuffle or k;draw!")
            return
        decks[msg.author.id] = tarot.deck()
        await msg.channel.send("You now have a tarot deck! Be sure to shuffle it before use!")

class DeckShuffleCommand(Command):
    name = "shuffle"
    template = "k;shuffle"
    description = "Shuffles your tarot deck."

    async def execute(self, msg, command):
        if msg.author.id not in decks:
            await msg.channel.send("You don't have a deck! Try k;tarotdeck.")
            return
        decks[msg.author.id].shuffle()
        await msg.channel.send("📇")

class DrawCardCommand(Command):
    name = "drawcard"
    template = "k;drawcard"
    description = "Draws a card into your current spread."

    async def execute(self, msg, command):
        if msg.author.id not in decks:
            await msg.channel.send("You don't have a deck! Try k;tarotdeck.")
            return
        if msg.author.id not in spreads:
            spreads[msg.author.id] = []
        card = decks[msg.author.id].draw()
        if not card:
            raise CommandError("That deck is out of cards! Wow!!")
        card_embed = card.embed()
        card_embed.add_field(name=f"Card {len(spreads[msg.author.id])+1}", value=f"{msg.author.display_name}'s spread")
        new_message = await msg.channel.send(embed=card_embed)
        await new_message.add_reaction("🔄")
        spreads[msg.author.id].append((new_message, card))

class ReturnCardsCommand(Command):
    name = "gathercards"
    template = "k;gathercards"
    description = "Gathers your spread back into your deck."

    async def execute(self, msg, command):
        if msg.author.id not in decks:
            await msg.channel.send("You don't have a deck! Try k;tarotdeck.")
            return
        if msg.author.id not in spreads:
            raise CommandError("You don't have any cards in a spread right now!")
        for message, card in spreads[msg.author.id]:
            card.flipped = False
            decks[msg.author.id].return_card(card)
            await message.delete()
        del spreads[msg.author.id]
        await msg.channel.send("Your cards are safe and sound! <:habbycat:651503718436438017>")

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

@client.event
async def on_reaction_add(reaction, user):
    if user.id in spreads:
        for message, card in spreads[user.id]:
            if reaction.message == message and reaction.emoji == "🔄":
                await reaction.remove(user)
                old_embed = message.embeds[0]
                card.flipped = not card.flipped
                new_embed = card.embed()
                new_embed.add_field(name=old_embed.fields[0].name, value=old_embed.fields[0].value)
                await message.edit(embed=new_embed)

commands = [
        HelpCommand(),
        AddLeagueCommishCommand(),
        AddLeagueCommand(),
        ManagerSignupCommand(),
        ManagerStepdownCommand(),
        DeckCommand(),
        DeckShuffleCommand(),
        DrawCardCommand(),
        ReturnCardsCommand(),
        PerennialStartCommand(),
        PerennialViewCommand(),
        PerennialPassCommand(),
        PerennialDraftPlayer(),
        PerennialFixCommand()
    ]

async def make_admin_role(league_name, chat_channel, feed_channel):
    com_role = await chat_channel.guild.create_role(name=f"{league_name} Commissioner", mentionable=True)
    await chat_channel.set_permissions(com_role, manage_messages=True, manage_channels=True)
    await feed_channel.set_permissions(com_role, manage_messages=True, manage_channels=True)
    return com_role

async def make_vanity_role(guild, role_name, pingable = False):
    role = await guild.create_role(name=role_name, mentionable=pingable)
    return role

def find_league_category(guild):
    return discord.utils.find(lambda cat: cat.id == config()["league_cat_id"], guild.categories)

client.run(config()["token"])