"""
Filename: game.py
Team: Pavo
Members: Emily Caveness, Alexander Laquitara, Johannes Pikel
Class: CS467-400
Assignment: CMD1:Adventure
Description:
"""

import sys
import json
import pdb  #toggle off in main
import file_handler.file_lib as files
import file_handler.help_file as help_file
from file_handler.name_lists import verb_info as verbs
import language_parser.command_parser as parse
import game_engine.player as player
#from game_engine.engine_helpers import response_struct
import game_engine.engine_helpers as helpers
import random

USE_CURSES = False
if sys.platform == 'linux' or sys.platform == 'linux2':
    import curses
    USE_CURSES = True
    game_ui = helpers.ui()
    if game_ui.terminal_size() == False:
        USE_CURSES = False


ALL_VERBS = verbs().get_verbs()
DO_WHAT = 'What would you like to do?'

#DEBUG SECTION, you can set these values to 1 to get the desired affect
#later in the game engine
#if set to 1 prints the value returned from the parser
DEBUG_PARSE = 0
#if set to 1 prints the value in the response json from the action_item etc
DEBUG_RESPONSE = 0
#prints the entire room json after it has been updated in post process
DEBUG_ROOM = 0
#prints the current room's title at the begining of each cycle
#comes after the description etc
DEBUG_PRINT_ROOM_TITLE = 0
#loads into a specific room set in the newGame()
LOAD_SPECIFIC_ROOM_ON_NEW_GAME = 0
SPECIFIC_ROOM = 'woods'


class Game():
    def __init__(self):
        self.player = None
        self.current_room = None
        # Inventory will be a list of dicts, each element of which is an item.
        self.current_time = 0
        self.number_of_turns = 0
        self.saved = False

    #-------------------------------------------------------------------------
    # Methods for managing game start, end, and basic flow
    #-------------------------------------------------------------------------
    def startGame(self, is_new_game):
        """
        Prints a splash to the screen and allows the user to load a game
        or start a new game
        """
        newgame = ["new", "new game", "n", "newgame"]
        loadgame = ["load", "load game", "l", "loadgame"]
        quit = ["quit", "q", "close", "exit" , "quit game", "close game", "exit game"]
        cmds = [newgame, loadgame, quit]
        invalid_message = [
                "Please choose from the menu:",
                "New Game",
                "Load Game",
                "Quit"]
        #preload choiceLow so we get the invalid message automatically when
        #not a new game
        choiceLow = ""

        if is_new_game:
            #print the big splash page here!
            if USE_CURSES:
                game_ui.write_main(helpers.SPLASH_MESSAGE, col=5)
                game_ui.refresh_all()
                choiceLow = game_ui.get_input()
            else:
                helpers.multi_printer(helpers.SPLASH_MESSAGE)
                choiceLow=helpers.get_input()
        while (not choiceLow in cmds[0] and
            not choiceLow in cmds[1] and
            not choiceLow in cmds[2]):
            if USE_CURSES:
                game_ui.write_main(invalid_message, col=5)
                game_ui.refresh_all()
                choiceLow = game_ui.get_input()
            else:
                helpers.multi_printer(invalid_message)
                choiceLow=helpers.get_input()
        if choiceLow in cmds[0]:
            self.newGame()
            self.gameCycle()
        elif choiceLow in cmds[1]:
            self.load_from_file()
            self.gameCycle()
        else:
            self.exitGame()

    def newGame(self):
        """
        copies the files over from template dir to the temp save dir
        and starts a new player
        """
        files.new_game()
        self.player = self.gen_player()
        #New games start at the shore
        self.current_room = files.load_room("shore")
        #for testing purposes load a specific room and start from there
        if LOAD_SPECIFIC_ROOM_ON_NEW_GAME:
            self.current_room = files.load_room(SPECIFIC_ROOM)

    def load_from_file(self):
        """
        gets the player and room files from the save game dir.  moves the room and items
        files to the temp save dir.  Restores the player state
        """
        p, r = files.load_game()
        #if something went wrong returning the player from the
        #checking for False because p could return as False if the files did not
        #get copied correctly
        if p is None or p is False:
            if USE_CURSES:
                game_ui.write_main('ERROR: Player not found.')
            else:
                helpers.multi_printer('ERROR: Player not found.\n')
            self.player = self.gen_player()
        else:
            #load player info from saved game
            self.player = self.player.set_player_stats(p)
        #r could be set to False if the files were not transferred correctly
        if r is not None and r is not False:
            self.current_room = r
        else:
            text = 'Something went wrong loading the rooms in loadgame. Please try again'
            if USE_CURSES:
                game_ui.write_main(text)
            else:
                helpers.multi_printer(text)

    def exitGame(self):
        """
            prints a good bye message and exits
        """
        if USE_CURSES:
            game_ui.write_main('Thanks for playing')
        else:
            helpers.multi_printer("Thanks for playing")
        exit()

    def gen_player(self):
        """
        this function asks the player to enter a name and then creates a new player
        object that the game holds on to for future use
        """
        if USE_CURSES:
            player_name = game_ui.get_input('Hello dreary traveler. What is your name? ')
        else:
            player_name = raw_input('Hello dreary traveler. What is your name? ')
        return player.Player(player_name)

    def gameCycle(self):
        """
        This is the big game cycle
            get user input
                check if savegame, loadgame, or quit
            otherwise send to parser
            process the parsed command
            output to screen
            update player
            update rooms
            update items
            check if dead or rescued
        """
        #inital room description after new game or loading game
        lines = self.get_room_desc()
        self.player.updatePlayerCondition(self.number_of_turns, 0)
        if USE_CURSES:
            game_ui.write_main(lines)
            game_ui.write_time(self.getTimeOfDay())
            game_ui.write_stat(self.player.getCondition())
            game_ui.refresh_all()
        else:
            helpers.multi_printer(lines)
            helpers.multi_printer(self.getTimeOfDay())
            helpers.multi_printer(self.player.getCondition())
        #updated this while loop the previous one did not seem to evaluate the
        #dead correctly
        while True:
            if DEBUG_PRINT_ROOM_TITLE:
                helpers.multi_printer("Current Room: " + self.current_room['title'])

#            userInput = helpers.get_input(DO_WHAT)
#            userInput = self.check_save_load_quit(userInput)
#            if userInput == None:
#                userInput = helpers.get_input(DO_WHAT)
#            processed_command = parse.parse_command(userInput)
#
            # If the game does not understand the user's command, prompt the
            # user for a new command.
#            while processed_command['processed'] == False:
#                text = "Sorry I did not understand that.\n"
#                text += DO_WHAT
#                userInput = helpers.get_input(text)
#                userInput = self.check_save_load_quit(userInput)
#                if userInput == None:
#                    userInput = helpers.get_input(DO_WHAT)
#                processed_command = parse.parse_command(userInput)
            processed_command = None
            while True:
                if processed_command is not None and processed_command['processed'] == False:
                    text = "Sorry I did not understand that." + DO_WHAT
                else:
                    text = DO_WHAT
                if USE_CURSES:
                    userInput = game_ui.get_input(text)
                else:
                    userInput = helpers.get_input(text)
                userInput = self.check_save_load_quit(userInput)
                if userInput == None:
                    if USE_CURSES:
                        userInput = game_ui.get_input(DO_WHAT)
                    else:
                        userInput = helpers.get_input(DO_WHAT)
                processed_command = parse.parse_command(userInput)
                #line below for testing
                if DEBUG_PARSE:
                    print json.dumps(processed_command, indent=4)
                if processed_command['processed'] == True:
                    break

            # If the game understands the user's command, process that command
            # according to the command type.
            output_type = processed_command["type"]

            #this is temporary and may very well be removed
            #just a possible option to help with assigning title and action
            top_level = ["item", "room", "feature"]
            for word in top_level:
                if word in processed_command['command']:
                    title = processed_command['command'][word]
            if "action" in processed_command['command']:
                action = processed_command['command']['action']

            if output_type == "item_action":
                self.process_item_action(title, action)
            elif output_type == "action_only":
                self.process_action_only(action)
            elif output_type == "room_action":
                self.process_room_action(title, action)
            elif output_type == "item_only":
                self.process_item_only(title)
            elif output_type == "feature_action":
                self.process_feature_action(title, action)
            elif output_type == "feature_only":
                self.process_feature_only(title)
            elif output_type == "room_only":
                self.process_room_only(title)
            else:
                "Error command type not supported yet."

            if self.player.get_death_status() or self.player.get_rescue_status():
                #would be good to add a restart loop in here
                #this break should be all that is needed and then we can startGame
                #again to allow loadgame or newgame
                #we submit False to let startGame know this is not a newGame
                #it will not print the Splash screen again
                #works well.  rescued myself with the flare gun !
                helpers.multi_printer(self.player.get_reason_for_death())
                break
        self.startGame(False)

    #-------------------------------------------------------------------------
    # This is the check for savegame, loadgame, quit function
    #-------------------------------------------------------------------------
    def check_save_load_quit(self, userInput):
        #save
        if userInput == "savegame":
            checkYes = helpers.get_input('Are you sure you wish to save y/n')
            if checkYes == "y":
                files.save_game(self.player, self.current_room)
                self.saved = True
                userInput = None
                helpers.multi_printer('Game saved successfully')
            else:
                helpers.multi_printer('continuing game...')
        #load
        elif userInput == "loadgame":
            text = "Loading will exit game.  Are you sure you wish to load? y/n"
            checkYes = helpers.get_input(text)
            self.saved = False
            if checkYes == "y":
                self.load_from_file()
                userInput = None
                helpers.multi_printer('Game loaded successfully')
                #adding this here so after we successfully load a game we get something
                #back and not just the what do you want to do... maybe better some
                #where else
                try:
                    res['description'] = self.get_room_long_desc()
                    self.post_process(res)
                except:
                    pass
            else:
                helpers.multi_printer('continuing game...')
        #quit
        elif userInput == "quit":
            if self.saved ==False:
                text = "Are you sure you want to quit without saving? y/n"
                checkYes = helpers.get_input(text)
                if checkYes == "y":
                    self.exitGame()
                else:
                    checkYes = helpers.get_input("Do you wish to save and quit? y/n")
                    if checkYes == "y":
                        files.save_game(self.player, self.current_room)
                        self.exitGame()
                    else:
                        helpers.multi_printer('continuing game...')
            else:
                checkYes = helpers.get_input("Are you sure you want to quit? y/n")
                if checkYes == "y":
                    self.exitGame()
        else:
            #if one of the above commands was not found we want to reset saved to False
            #because we may have changed something in the game
            self.saved = False
            return userInput

    #-------------------------------------------------------------------------
    # This ends the check for savegame, loadgame, quit
    #-------------------------------------------------------------------------
    #-------------------------------------------------------------------------
    # Top-level methods for handling user commands.
    #-------------------------------------------------------------------------
    def process_item_action(self, title, action):
        if title in self.player.get_items_inventory_titles():
            res = self.item_action_inventory(title, action)
        else:
            res = self.item_action_room(title, action)
        self.post_process(res)

    def process_action_only(self, action):
        res = helpers.response_struct().get_response_struct()
        if action == "look":
            res['description'] = self.get_room_long_desc()
        elif action == "inventory":
            res['description'] = self.player.print_inventory()
        elif action == "help":
            help_file.main()
            return
        else:
            #also sent to the funny script writer
            res = self.get_humor(action, 'action')
        self.post_process(res)

    def process_room_action(self, room, action):
        res = self.room_action(room, action)
        self.post_process(res)

    def process_item_only(self, name):
        self.post_process(self.get_humor(name, 'noun'))

    def process_feature_action(self, feature, action):
        res = self.feature_action(feature, action)
        self.post_process(res)

    def process_feature_only(self, feature):
        self.post_process(self.get_humor(feature, 'noun'))

    def process_room_only(self, room):
        res = self.room_action(room, 'go')
        self.post_process(res)


    #-------------------------------------------------------------------------
    # The post process function, handles printing descriptive text
    # and assigning the various update functions as necessary
    #-------------------------------------------------------------------------
    def post_process(self, res):
        """
        divides handling printing, updating character, inventory
        updating room's dynamically
        """
        self.number_of_turns += 1
        #at some point in the future hopefully this will be where
        #we can send parts to the room to be updated if appropriate
        #and the player state if for instance the player has
        #eaten something and gets a boost to hunger

        #set DEBUG_RESPONSE to 1 for debuggin
        if DEBUG_RESPONSE:
            print(json.dumps(res, indent=4))

        if 'modifiers' in res:
            #update the player with any particular modifiers from the action
            self.update_player(res)
            #update the room dict through recursion
            self.update_room(res)
            #update the items dict
            self.update_item(res)

        #after modifiers have been applied update the player's condition
        room_temp = int(self.current_room['room_temp'])
        self.player.updatePlayerCondition(self.number_of_turns,room_temp)

        if DEBUG_ROOM:
            print(json.dumps(self.current_room, indent=4))
        #print the messages to screen here
        if USE_CURSES:
            if (not self.player.get_death_status() 
                    and not self.player.get_rescue_status()):
                game_ui.write_time(self.getTimeOfDay())
                game_ui.write_stat(self.player.getCondition())
            game_ui.write_main(res['description'], self.player.getName())
            if 'artifact' in res:
                lines = res['artifact']
            #    game_ui.write_main(lines, None, 22)
            game_ui.refresh_all()
        else:
            helpers.multi_printer(res['description'], self.player.getName())
            if 'artifact' in res:
                lines = res['artifact']
                helpers.multi_printer(lines)
            if not self.player.get_death_status() and not self.player.get_rescue_status():
                helpers.multi_printer(self.getTimeOfDay())
                helpers.multi_printer(self.player.getCondition())

        #description should always come with process functions so we
        #automatically print out something to the user

    #-------------------------------------------------------------------------
    # This section dedicated to functions relating to moving from one
    # room to another
    #-------------------------------------------------------------------------
    def room_action(self, title_or_compass, action):
        """
            tries to move to the passed in room title or compass direction
            also expects a list of items currently held in the inventory
            defaults to None
        """
        res = self.check_connections(title_or_compass)
        if action == "go":
            if res["success"] == True:
                #before we leave the room we set the field visited to true
                self.current_room['visited'] = True
                files.store_room(self.current_room)
                self.current_room = files.load_room(res['title'])
                res['description'] = self.get_room_desc()
            elif res['success'] == False and res['description'] is None:
                res['description'] = "You were not able to move in that direction.  "
        elif action == 'look':
            res['description'] = self.get_room_long_desc()
        else:
            res['description'] = "You can't " + action + " the " + title_or_compass+". "
        return res

    def check_connections(self, title_or_direction):
        """
        when given an official room title or compass direction, iterates
        through the current room's connected_rooms object to see if the compass
        or room title exist
        checks if an item is required to pass into this room
        Also checks if the rooms is accessible meaning passable
        if an item is required checks to see if that item is active as in worn or on
        writes the appropriate response into
        description
        move = boolean whether or not the move was successful
        title = the new room's title
        distance_from_room = distance traveled to the new room
        """
        res = helpers.response_struct().get_response_struct()
        res['success'] = False
        items = self.player.get_items_inventory_titles()
        for room_key in self.current_room['connected_rooms']:
            #this line added as a result of the connected_rooms refactoring
            #all other functionality remains the same
            room = self.current_room['connected_rooms'][room_key]
            if (title_or_direction == room['title']
                or title_or_direction == room['compass_direction']
                or title_or_direction in room['aliases']):
                res['title'] = room['title']
                if 'modifiers' in room:
                    res['modifiers'] = room['modifiers']
                if (room['item_required'] == True and
                    room['item_required_title'] in items and
                    room['accessible'] == True):
                        item = self.player.search_inventory(room['item_required_title'])
                        if item['active'] == True:
                            res['success'] = True
                            res['distance_from_room'] = room['distance_from_room']
                        else:
                            res['description'] = room['pre_item_description']
                elif room['item_required'] == False and room['accessible'] == True:
                    res['success'] = True
                    res['distance_from_room'] = room['distance_from_room']
                    res['description'] = room['pre_item_description']
                else:
                    res['description'] = room['pre_item_description']
                #we can return the response as soon as we have found a match
                return res
        return res
    #------------------------------------------------------------------------
    # This ends the movement related functions
    #------------------------------------------------------------------------
    #------------------------------------------------------------------------
    # This begins room getters section
    #------------------------------------------------------------------------

    def get_room_desc(self):
        """
            returns either the long or short description
            if the room has been previously visited
        """
        if self.get_visited() == False:
            return self.get_room_long_desc()
        else:
            return self.get_room_short_desc()

    def get_room_long_desc(self):
        """
        returns a string of the long description and items in room
        """
        return self.current_room['long_description'] + self.get_items_in_room()

    def get_room_short_desc(self):
        """
        returns a string of the short description and items in room
        """
        return self.current_room['short_description'] + self.get_items_in_room()

    def get_items_in_room(self):
        """
        if the room has been searched appropriately and there are items in the room
        then returns the items in the room as a string for descriptive purposes
        """
        text = " Looking around you see "
        if (self.current_room['feature_searched'] == True and
                self.current_room['items_in_room'] and
                len(self.current_room['items_in_room']) > 0):
            items = self.current_room['items_in_room']
            for item in items:
                text += "a " + item + ", "
            text = text[:-2]
        else:
            text = ""
        return text

    def get_visited(self):
        """
        returns the boolean in visited
        """
        return self.current_room['visited']
    #------------------------------------------------------------------------
    # This ends room getters section
    #------------------------------------------------------------------------
    #------------------------------------------------------------------------
    # This begins room modifiers section
    #------------------------------------------------------------------------
    def remove_item_from_room(self, title):
        """
        removes an items from the inventory of a room
        do not attempt to remove something not already there
        """
        if title in self.current_room['items_in_room']:
            self.current_room['items_in_room'].remove(title)

    def add_item_to_room(self, title):
        """
        adds an item to the room, does not allowed for duplicates
        """
        if title not in self.current_room['items_in_room']:
            self.current_room['items_in_room'].append(title)
    #------------------------------------------------------------------------
    # This ends the room  section
    #------------------------------------------------------------------------
    #------------------------------------------------------------------------
    # This begins the feature related section
    #------------------------------------------------------------------------

    def feature_action(self, title, verb):
        """
            looks up to see if the title passed in is a feature in the current room
            if so and the verb is in the list of possible verbs for that feature then
        """
        res = helpers.response_struct().get_response_struct()
        if title in self.current_room['features']:
            feature = self.current_room['features'][title]
            if verb in feature['verbs']:
                res['description'] = feature['verbs'][verb]['description']
                res['modifiers'] = feature['verbs'][verb]['modifiers']
                if 'artifact' in feature['verbs'][verb]:
                    res['artifact'] = feature['verbs'][verb]['artifact']
            else:
                res['description'] = 'You are not able to ' + verb + ' the ' + title
        else:
            res['description'] = 'Sorry, ' + title + ' not found in this room.'
        return res
    #------------------------------------------------------------------------
    # This ends the feature section
    #------------------------------------------------------------------------
    #------------------------------------------------------------------------
    # This section relates to item actions
    #------------------------------------------------------------------------

    def item_action_inventory(self, item_title, action):
        """
        called by the verb handler.  Looks up the item file and opens it
        returns the description listed for the particular verb at this moment.
        and modifiers if any
        """
        res = helpers.response_struct().get_response_struct()
        item = self.player.search_inventory(item_title)
        res['title'] = item_title
        res["description"] = item['verbs'][action]['description']
        res['modifiers'] = item['verbs'][action]['modifiers']
        res["success"] = True
        if 'artifact' in item['verbs'][action]:
            res['artifact'] = item['verbs'][action]['artifact']
        if action == "use" and item['activatable'] == True:
            if item['active'] == True:
                item['active'] = False
                if 'de_mods' in item['verbs']['use']:
                    res['modifiers'] = item['verbs']['use']['de_mods']
                res['description'] = item['verbs']['use']['deactivate_description']
            else:
                item['active'] = True
                if 'act_mods' in item['verbs']['use']:
                    res['modifiers'] = item['verbs']['use']['act_mods']

        elif action == "drop" and self.current_room['feature_searched'] == False:
            res['description'] = "There is no where secure to drop the item"
            res['modifiers'] = {}
        return res

    def item_action_room(self, title, verb):
        """
        acts on an item in the room only the look at verb is allowed at this moment
        adds the item to the inventory as well if it is
        """
        res = helpers.response_struct().get_response_struct()
        res['title'] = title
        allowed_verbs = ["look at", "take"]
        if self.current_room['feature_searched'] and verb in allowed_verbs:
            if title in self.current_room['items_in_room']:
                item = files.load_item(title)
                #print item
                res['description'] = item['verbs'][verb]['description']
                res['modifiers'] = item['verbs'][verb]['modifiers']
                res["success"] = True
            else:
                text = "You can't find the " + title + " to " + verb +". "
                res['description'] = text
        elif self.current_room['feature_searched'] and verb not in allowed_verbs:
            res['description'] = "You need to be holding " + title + " to " + verb + " it."
        else:
            res['description'] = "You don't see any items around. "
        return res

    #------------------------------------------------------------------------
    # This ends the items and inventory section
    #------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Methods that are used in otherwise managing game flow.
    # and updating the room, player and items
    #-------------------------------------------------------------------------
    def update_room(self, res):
        """
        this function is used to update the current room's parameters
        """
        #this is the add and rop to rooms
        #if dropping is allowed is handled above in the item_action_room
        if "room" in res['modifiers']:
            mods = res['modifiers']['room']
            if self.current_room['title'] == mods['title'] or "any" == mods['title']:
                if "items_in_room" in mods and mods['items_in_room'] == "add":
                    self.add_item_to_room(res['title'])
                elif "items_in_room" in mods and mods['items_in_room'] == "drop":
                    self.remove_item_from_room(res['title'])

        #This is the test of the the dynamic room updates
        #Since all titles are unique that is our identifier!! very important
        #it can only currently update the room the player is in, so no
        #outside rooms, but we could easily change that
        #we just need to make sure that our rules about what can change
        #what are consistent.  that comes from the way the 'updates' dict
        #is written in the 'modifiers' dict for a particular verb of a feature
        #or an item
        if 'room_updates' in res['modifiers']:
            for key in res['modifiers']['room_updates']:
                updates = res['modifiers']['room_updates'][key]
                if self.current_room['title'] == key:
                    self.current_room = files.update(updates, self.current_room)
                #affect any room that is a room other than the current room
                elif key in files.ROOM_TITLES:
                    self.update_external_room(updates, key)
        #this field is used in the modifiers field to only update adjacent rooms
        #this will also validate that the room specified is the current room
        if 'adjacent_room_updates' in res['modifiers']:
            if self.current_room['title'] == res['modifiers']['adjacent_room_updates']['self']:
                for key in res['modifiers']['adjacent_room_updates']:
                    if key in self.current_room['connected_rooms']:
                        updates = res['modifiers']['adjacent_room_updates'][key]
                        self.update_external_room(updates, key)


        #hopefully file_lib will have a method where we can pass the 
        #modifiers dict to and it will do the remaining processing returning 
        #the updated room so we can just do 
    def update_external_room(self, updates, key):
        """
           opens the room file named in the key, updates that room and then 
           stores that room back to file
        """
        other_room = files.load_room(key)
        other_room = files.update(updates, other_room)
        files.store_room(other_room)


    def update_player(self, res):
        """
        This function is used to update player state variables, including
        player inventory
        """
        if 'player' in res['modifiers']:
            modifiers = res['modifiers']['player']
            if 'inventory' in modifiers and modifiers['inventory'] == 'add':
                item = files.load_item(res['title'])
                self.player.add_item_to_inventory(item)
            elif 'inventory' in modifiers and modifiers['inventory'] == 'drop':
                #when the player drops the item it gets written to file
                item = self.player.search_inventory(res['title'])
                if item:
                    files.store_item(item)
                self.player.remove_item_from_inventory(res['title'])
            if 'illness' in modifiers:
                self.player.add_to_illness(int(modifiers['illness']))
            if 'hunger' in modifiers:
                self.player.add_to_hunger(int(modifiers['hunger']))
            if 'cold' in modifiers:
                self.player.add_to_cold(int(modifiers['cold']))
            if 'rescued' in modifiers:
                self.player.set_rescue(modifiers['rescued'])

    def update_item(self, res):
        """
        this function is used to update an item's dict.
        it requires that the field modifiers and item_updates are in the response
        received.  The item must have the same structure as that of an actual item
        file.  The dict trees will be updated with the new information recursively
        """
        if 'item_updates' in res['modifiers']:
            for key in res['modifiers']['item_updates']:
                updates = res['modifiers']['item_updates'][key]
                #first check if the item is in the player inventory and update that
                item = self.player.search_inventory(key)
                if item is not None:
                    item = files.update(updates, item)
                #if the item is not in the player inventory maybe it is in the room
                #and we can act upon it.  This maybe needs to go away
                elif key in self.current_room['items_in_room']:
                    item = files.load_item(key)
                    item = files.update(updates, item)
                    files.store_item(item)

    def getTimeOfDay(self):
        if self.number_of_turns % 4 == 0:
            text = "It is morning. "
        elif self.number_of_turns % 4 == 1:
            text = "It is afternoon. "
        elif self.number_of_turns % 4 == 2:
            text = "It is evening. "
        elif self.number_of_turns % 4 == 3:
            text = "It is night. "
        return text

    #-------------------------------------------------------------------------
    # This begins the humorous section
    #-------------------------------------------------------------------------
    def get_humor(self, word, type_of):
        """
        depending on whether it is an action or noun puts together a random
        string to return
        """
        action_prefix = ['Sadly you cannot ', 'Nope maybe try to ',
                'Wait... hold on a sec... nope you cannot just ']
        action_post = [' yourself.', ' something in the real world.',
                ' -- every DM ever.']
        noun_prefix = ['The ', 'That ', 'Try doing something to the ']
        noun_post = [' is a thing in the world you are correct sir.',
                ' might be nearby but you need to perform something on it.',
                ' something imaginary.']
        index = random.randint(0,2)
        text = ''

        res = helpers.response_struct().get_response_struct()
        if type_of == 'noun':
            text += noun_prefix[index] + word + noun_post[index]
        elif type_of == 'action':
            text += action_prefix[index] + word + action_post[index]
        res['description'] = text
        return res

    #suggest update player conditions relocated to the helper file player.py
#    def updatePlayerCondition(self):
#        # Degrade the player's condition every three moves.
#        if self.number_of_turns % 3 == 0:
#            self.player.illness += 1
#        if (self.player.illness > 50 or
#            self.player.hunger > 50 or
#            self.player.cold > 50):
#            self.player.dead = True


    #-------------------------------------------------------------------------
    # Temporary code used for testing
    #-------------------------------------------------------------------------

#def testParse():
#    test_input = "go cave"
#    print "The test input is: " + test_input
#    print "The parsed command output is:"
#    print parse.parse_command(test_input)
#    print parse.parse_command(test_input)['room']['action']
#    print parse.parse_command(test_input)['room']['name']
#    print parse.parse_command(test_input)['other']['processed']
#    print parse.parse_command(test_input)['room']['action']
#    # parse.parse_command(test_input[0,0])
#    print ""
#

#testParse()
#startGame()
#loadGame()
#newGame()
#playerDead()
#testNew()



def main():
    if USE_CURSES:
        curses.wrapper(game_ui.init_windows)
    random.seed()
    current_game = Game()
    current_game.startGame(True)

if __name__ == "__main__":
    #pdb.set_trace() #toggle for debugging
    main()
