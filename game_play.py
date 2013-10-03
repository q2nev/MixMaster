import game
import twitter as TW
import ascii as ASC
import msvcrt
import os
import time
import logging
import pygame.mixer as mix
import string
import sys
import Q2logging

mix.init()
logging.basicConfig(filename='game_play.log',logging=logging.DEBUG)

stops = dict()
current_sound = None
g_map = None
rhymes = 20
ats = 20
desc_ct = 0

def main():
    logging.info('Entering main function')
    global g_map
    # load game map
    with open("game.xml") as f:
        xml_file = f.read()
    success, g_map = game.obj_wrapper(xml_file) #turn into python object via Q2API
    if not success:
        logging.warning('obj_wrapper failed in main() before stops')
        print "no object"
        exit()
    # construct global dicts: stops
    global stops # possible positions
    for stop in g_map.stop:
        nomen = stop.attrs["nomen"]
        stops[nomen] = stop

    stop = g_map.stop[0] #inital stop

    print_animation(stop)
    # initialize player
    global player
    player = g_map.player[0]
    # initialize extras - list of printable items
    global extras
    extras = ['stop_desc','stop_name','play_music']
    logging.info('Entering main() game loop')
    os.system('cls')
    # enter main game loop
    while True:
        describe(stop, extras)
        command = raw_input(">>").lower()
        os.system('cls') #clearing for better user experience
        #put directly after command so we can print on either side and it looks cohesive.
        stop = process_command(stop, command)
        logging.info('Command Processed')
        logging.info(str(type(stop))) #make sure that we're passing in variable into loop!

def describe(stop,extras):
    '''
    stop: current stop
    stop_name: don't print the name of the current station
    stop_desc: don't print out the stops name
    ascii: don't print the ascii
    sound: don't play the song
    desc_ct: current description
    '''
    logging.info("Current Extras",extras)
    global desc_ct
    if extras:
        if 'stop_name' in extras:
            print stop.attrs["nomen"].upper(), "STATION"

        if 'stop_desc' in extras:
            print stop.desc[desc_ct].value
        if 'ascii' in extras:
            image_to_ascii(stop)
        if 'ascii_animate' in extras:
            print_animation(stop)
        if 'pause_music' in extras:
            play_music(stop,True)
        if 'play_music' in extras:
            play_music(stop)
        if 'around' in extras:
            for p in stop.place:
                    print "\n\t"+"Name for place:", p.attrs.get("nomen")+".", "Direction for place:", p.attrs.get("dir")
                    print "\n\t"+"Place description:", str(p.desc[0].value).strip(string.whitespace)
                    print "_________________________________________________________"
            for i in stop.item:
                    print "\n\t"+"Name for item:", i.attrs.get("nomen")+".", "Direction for place:", i.attrs.get("dir")
                    print "\n\t"+"Item description:", str(i.desc[0].value).strip(string.whitespace)
                    print "__________________________________________________________"
        if 'results' in extras:
            print "After that game you have",rhymes, "rhymes, and",ats,"Ats."
            # print "You also have", followers,"Followers."
        if 'inventory' in extras:
            print "Rhymes:", rhymes
            print "\t\t__________________________________________________________"
            print "Ats:",ats
            print "\t\t__________________________________________________________"
            for itm in g_map.player[0].item:
                print str(itm.attrs["nomen"]).upper()
                print "Uses:"
                try:
                    for use in itm.usage:
                        print use.attrs["nomen"]
                except:
                    print "No uses..."
            print "\t\t__________________________________________________________"
        if 'ascii_challenge' in extras:
            pass


        if 'unknown' in extras:
            print "We don't know what you're talkin' about."
    return stop

def image_to_ascii(stop,pause_sound=False, guess_name=False):
    '''
    separate image_to_ascii function to have guessing game.
    image_folder: where the images are stored
    (All images need to have 3-letter formats a.k.a. .jpegs won't work)
    img: string from stop.attrs
    img_txt: possible text string that would've already been generated
    '''
    image_folder = os.listdir('images/')
    logging.debug('Image folder found.')
    img = str(stop.attrs["im"]).strip(string.whitespace)
    img_txt = img[:-4]+'.txt'
    logging.info(img_txt) #log image text for debugging
    play_music(stop)
    if img_txt in image_folder:
        with open('images/'+img_txt) as f:
            lines = f.read()
            print "Guess ascii by pressing enter!"
            for l in lines.split('\t'):
                time.sleep(1.5)
                print l
    else:
        ascii_string = ASC.image_diff('images/'+img)
        fin = open('images/'+img_txt,'w')
        print "file opened"
        for i in range(len(ascii_string)):
            fin.write(ascii_string[i]+'\t')
        fin.close()

def play_music(stop, pause_sound=False):
    '''
    pause most recent sound before passing in new sound for current_sound (global variable)
    '''
    global current_sound

    if current_sound and pause_sound:
        current_sound.stop()

    try:
        sound_file = "sounds/"+str(stop.attrs["sd"]).strip(string.whitespace)
        if not pause_sound:
            current_sound = mix.Sound(sound_file)
            logging.info('music loaded')
            current_sound.play()
    except:
        print "No music found"

def twitter_data(stop,boss, noun):
    '''
    call_prompt: users input keyword
    rhyme_diff: difference in rhymes for a RT boss
    ats_diff: difference in ats for a RT boss
    rhymes: currently tabulated rhymes
    ats: currently tabulated rhymes
    '''
    global rhymes
    global ats
    print "\t\t\tIt's a glare from",noun,"with call:",boss,
    call_prompt = raw_input("\n\n\t\t\tWhat's your call against this mean muggin?!")
    try:
        rhyme_diff, at_diff = twitter_battle(call_prompt,boss)
        rhymes += rhyme_diff
        ats += at_diff
        if rhymes <0 or ats<0: #breaks if either returns zero
            print "You're as dead as a doornail."
            print "Would you like to restart?"
            restart = raw_input(">>")
            while True:
                if restart =="Y":
                    return main()
                elif restart == "N":
                    exit()
                else:
                    print "Unknown command"
                    continue
    except:
        print "You have over exerted Twitter!"
        ascii_challenge(stop)
    return rhymes,ats #returns to

def twitter_battle(call_prompt, boss): # add on followers and amt later
    '''
    Input: boss (boss kw) and prompt (player kw)
    Output: rhymes_diff, ats_diff
    '''
    boss_ats = TW.recent_tweets([boss],2)[1]
    boss_rhymes = TW.recent_tweets([boss],2)[2]
    player_ats = TW.recent_tweets([call_prompt],3)[1]
    player_rhymes = TW.recent_tweets([call_prompt],3)[2]
    ats_diff = player_ats - boss_ats
    rhymes_diff = player_rhymes - boss_rhymes
    print "Rhyme-Count from battle:", rhymes_diff
    print "Holler-Ats from battle:",ats_diff
    if ats_diff > 0:
        ats_winner = 'player'
    elif ats_diff == 0:
        ats_winner = 'equal'
    else:
        ats_winner = 'boss'
    if rhymes_diff >0:
        rhymes_winner = 'player'
    elif rhymes_diff ==0:
        rhymes_winner = 'equal'
    else:
        rhymes_winner = 'boss'
    #add in check for followers here.
    for scen in g_map.scenario:
        if scen.attrs.get('rhymes') == rhymes_winner and scen.attrs.get('ats')==ats_winner:
            print scen.value
    return rhymes_diff, ats_diff #returns to twitter_data

def process_command(stop, command): #can also pass stop!
    '''
    1. Parse Command
    2. Get Items and places from Command
    3. Handles Twitter Battle
    4. Twitter Game play : if desc or stop, or item contains name in fight dict.

    Output: global extras and global stop.
    '''
    global desc_ct
    global rhymes
    global ats
    global extras
    global logging

    descs = descs_dict(stop)
    extras = []
    if len(command) == 0:
        logging.info('Pressed Enter.')
        enter_command(stop,descs)
        return stop
    else:
        verb, noun = parse(command)
        if verb == "go":
            return go_command(stop,noun)
        elif verb == "describe":
            return describe_command(stop,player,noun)
        elif verb== "take":
            return take_command(stop,noun)
        elif verb == "load": #loads game from save directory
            return load_command(stop)
        elif verb == "score": #score board functionality
            return score_command(stop)
        elif verb =="cur":
            extras=["inventory"]
            return stop
        elif verb=="save":
            return save_command(stop)
        elif verb =="restart":
            return restart_command(stop)
        elif verb =="how":
            print player.item[0].desc[0].value #goal: callable from anywhere in game.
            #add to it's relevancy as you go along...
            return stop
        elif verb == "exit":
            print "Do you want to save your game? (Y,N)?"
            save_file = raw_input('>>')
            if save_file == "Y":
                process_command(stop,'save')
            elif save_file == "N":
                print "OK!"
                exit()
            else:
                print "What?! (Exit Prompt Error)"
                process_command(stop,'exit')
        else:
            print "Unrecognized command"
        return stop

def enter_command(stop,descs):
    '''
    via stop, command and descs
    desc_ct: counter of most recently printed desc
    extras: global dict of what to print next
    '''
    global desc_ct
    global extras
    max_desc = max(descs.keys())
    if max_desc > desc_ct:
        desc_ct+=1
    elif max_desc == desc_ct: # the end of the descs
        print "\n\n You have reached the end of this info. \n\n"
        print "Try typing 'describe around' to learn more options."
        desc_ct = 0
    else: # the beginning of the descs
        desc_ct=0
    extras = ['stop_desc']
    return stop

def descs_dict(stop): #can also pass place and will have same result
    descs = dict()
    desc_ct = 0
    for d in stop.desc:
        descs[desc_ct] = d.value
        desc_ct+=1
    return descs

def parse(cmd):
    cmd = one_word_cmds.get(cmd, cmd)
    print "\n\n\n\n\t\t\tMost recent command:", cmd, "\n\n"
    words = cmd.split()
    verb = words[0]
    verb = translate_verb.get(verb, "BAD_VERB")
    noun = " ".join(words[1:])
    noun = translate_noun.get(noun, noun)
    return verb, noun

def ascii_challenge(stop):
    '''
    separate image_to_ascii function to have guessing game.
    image_folder: where the images are stored
    (All images need to have 3-letter formats a.k.a. .jpegs won't work)
    img: string from stop.attrs
    img_txt: possible text string that would've already been generated
    '''
    global rhymes
    global ats
    play_music(stop,True) #pauses music
    image_folder = os.listdir('images/')
    img = str(stop.attrs["im"]).strip(string.whitespace)
    img_txt = img[:-4]+'.txt'
    logging.debug("Image Text:",img_txt) #log image text for debugging
    play_music(stop)
    boss = str(stop.attrs["kw"]).strip(string.whitespace)
    if img_txt not in image_folder: #convert image to txt file if not already.
        print "Converting jpg to txt!"
        ascii_string = ASC.image_diff('images/'+img)
        fin = open('images/'+img_txt,'w')
        print "file opened"
        for i in range(len(ascii_string)):
            fin.write(ascii_string[i]+'\t')
        fin.close()
    with open('images/'+img_txt) as f:
        lines = f.read()
        print "Guess ascii by pressing enter!"
        for l in lines.split('\t'):
            while not msvcrt.kbhit():
                time.sleep(1.2)
                print l
                break

            while msvcrt.kbhit():
                play_music(stop,True)
                msvcrt.getch()
                print "_________________________________________________________________"
                print "What's your guess?"
                print boss
                boss_guess = raw_input(">>")
                if boss_guess == boss:
                    play_music(stop)
                    print "You guessed right! Here are 5 hashes and ats for your prowess!"
                    rhymes += 5
                    ats += 5
                    return rhymes, ats
                else:
                    print "You guessed wrong!"
                    play_music(stop)
    return rhymes,ats

def go_command(stop,noun):
    global desc_ct
    global extras
    global rhymes
    global ats
    for pl in stop.place:
        if noun in pl.attrs.get("nomen"):
            access = str(pl.attrs["access"])
            if access.split(',')[0] == "cost":
                rhymes_cost= int(access.split(',')[1])
                ats_cost = int(access.split(',')[2])
                print "\n\n\t\t\t\tDo you want to pay for this? (y/n)?"
                print "\t\t\t",rhymes_cost,"rhymes"
                print "\t\t\t",ats_cost,"Ats"
                pay_cost = raw_input('>>')
                if pay_cost.lower() == 'y':
                    rhymes -= rhymes_cost
                    ats -= ats_cost
                    try:
                        link = pl.attrs["link"]
                        if link =="":
                            print "Link empty"
                            exit()
                        stop = stops[link]
                        desc_ct = 0
                        extras=["stop_name",'stop_desc','pause_music','play_music']
                    except:
                        print "There is not a link here."
                    return stop
                else:
                    print "Well that's ok?"
            for itm in player.item:
                if str(itm.attrs['nomen'])==access:
                    print '\t\t\n\nYou have a',access, 'To gain access to this stop. Use your',access,'?'
                    access_q = raw_input('>>')
                    if access_q.lower() == "y":
                        extras =['stop_name','stop_desc','pause_music','play_music']

                        try:
                            link = pl.attrs["link"]
                            if link =="":
                                exit()
                            stop = stops[link]
                        except:
                            print "There is not a link here."
                        desc_ct=0
                        return stop
                    else:
                        print "Well, then you can't go there."
                        extras =['stop_name','stop_desc']
                        return stop
                elif access == "": #if there is no access key in the xml then leave it and let them go.
                    desc_ct = 0
                    extras =['stop_name','stop_desc','pause_music','play_music']
                    try:
                        link = pl.attrs["link"]
                        if link =="":
                            print "exiting at place and empty string access"
                            exit()
                        stop = stops[link]
                    except:
                        print "No link found."
                    return stop
            print "\n\t\tYou don't currently have the items necessary to go this way."
            print "\n\t\t Try to find this item or try another way!"
            print "\n\t\tWell then I guess you'll just have to find another way!"
            return stop
    else:
        extras=["bad_go"]
        print "You can't go there."
        extras =['stop_name','stop_desc']
        return stop

def take_command(stop,noun):
    global desc_ct
    global extras
    global player
    try:
        for itm in stop.item:
            access = str(itm.attrs["access"])
            logging.info('access:',access)
            logging.info('access type:',type(access))
            if itm.attrs.get("nomen") == noun:
                if access.split(',')[0] =='cost':
                    rhymes_cost= int(access[1])
                    ats_cost = int(access[2])
                    print "\t\t\tDo you want to pay for this? (y/n)?\n\n"
                    print rhymes_cost,"rhymes.\n\n"
                    print ats_cost,"Ats\n\n"
                    pay_cost = raw_input('>>')
                    if pay_cost.lower() == 'y':
                        rhymes -= rhymes_cost
                        ats -= ats_cost
                        player.item.append(itm)
                        player.children.append(itm)
                        stop.item.remove(itm)
                        stop.children.remove(itm)
                    else:
                        print "\t\t\tWell that's ok?"
                    print "\t\t\tYou get the " + noun
                elif access=="":
                    player.item.append(itm)
                    player.children.append(itm)
                    stop.item.remove(itm)
                    stop.children.remove(itm)
                    print "\t\t\tYou get the " + noun
        return stop
    except:
        print "This item does not exist at this stop!"
        return stop

def describe_command(stop, player, noun):
    global extras
    global rhymes
    global ats
    if noun == "around": #functionality to show current landscape.
        extras = ["around"]
        return stop
    for itm in stop.item:
        if itm.attrs["nomen"] == noun:
            boss = itm.attrs.get("kw")
            if itm.attrs["fights"]=="true":
                rhymes, ats = twitter_data(stop,boss, noun)
                extras= ["rhymes", "ats", "battle_results"]
                print "You now have", rhymes,"rhymes in your rep!"
                print "And",ats, "holler-ats from the crowd!"

                player.item.append(itm)
                player.children.append(itm)
                stop.item.remove(itm)
                stop.children.remove(itm)
                return stop

            elif itm.attrs["fights"]=="challenge":
                extras=["ascii_challenge"]
                return stop

    for it in player.item:
        if noun == it.attrs.get("nomen"):
            print "\t\t\tYou already have the", noun,'\n\n'
            extras = ['describe_place','describe_access']
            return stop

    for pl in stop.place:
        if pl.attrs.get("nomen")==noun:
            extras= ['describe_place', 'describe_access']
            return stop
    extras = ['unknown']
    return stop

def restart_command():
    print "Restart game? (Y/N)"
    restart_game = raw_input('>>').lower()
    if restart_game == "y":
        print "Do you want to save first? (Y/N)"
        save_first = raw_input('>>').lower()
        if save_first == 'y':
            return save_command()
        else:
            return main()
    elif restart_game == "N":
        print "OK!"
        exit()
    else:
        print "Unrecognized command, I'll just let you keep playing!"

def save_command(stop):
    global ats
    global rhymes
    stop_nomen = stop.attrs["nomen"]
    player.attrs["stop"] = str(stop_nomen)
    player.attrs["rhymes"] = str(rhymes)
    player.attrs["ats"]= str(ats)
    save_file = raw_input("\t\t\tEnter a name for the save file >")
    with open("save\\" + save_file + ".xml", "w+") as f:
        f.write(g_map.flatten_self())
        print "game saved!"
    print "Continue game ? (Y/N) (Pressing N will put exit the game!)"
    continue_game = raw_input('>>').lower()
    if continue_game == "y":
        return stop
    elif continue_game == "n":
        print "OK!"
        exit()
    else:
        print "Unrecognized noun, I'll just let you keep playing!"
        return stop

def score_command(stop):
    games = os.listdir("save")
    save_count = 0
    for i, file_name in enumerate(games): #prints the players
        if file_name[-4:]=='.xml':
            try:
                print str(i) + "\t" + file_name.split(".")[0]
            except:
                print "couldn't print game"
            try:
                print "Ats:",load_ats_rhymes(file_name)[0]  + "\t" + "rhymes:",load_ats_rhymes(file_name)[1]
            except:
                print "couldn't find scores"
            try:
                for it in load_items(file_name):
                    print "Player item:", it
            except:
                pass
        save_count += 1
    if save_count == 0:
        print "No saved games!"
        return stop
    return stop

def load_command(stop):
    games = os.listdir("save")
    ct=0
    for i, file_name in enumerate(games): #prints the players to console
        if file_name.split(".")[1]=='.xml':
            print str(i) + "\t" + file_name.split(".")[0]
            ct+=1
    if ct>0:
        print "Choose a game by its number, or type new for new game.\n"
        choice = raw_input(">>").lower()
        if choice not in [ "n", "new"]:
            try:
                game_file = "save\\" + games[int(choice)]

            except:
                print "You didn't give a proper number..."
                game_file = 'game.xml'
            return load_game(game_file)

    else:
        print "\n\t\tCould not find any saved games!"
        print "\n\t\tType start or exit!"
        return stop

def load_game(game_file):
    '''
    Input: game_file from load command()
    Output: stop object from player profile.

    '''
    global g_map
    logging.info('Found load_game')
    with open(game_file) as f:
        xml_file = f.read()
    #wrap player map here
    success, g_map = game.obj_wrapper(xml_file)
    if not success:
        logging.info('From Q2API - Obj_wrapper failed when loading game')
        exit()
    global player #only need player from file
    global stops #grab dict from main file so that we can call current stop from nomen attribute

    player = g_map.player[0] #assign player via Q2API.xml.mk_class syntax
    nomen = player.attrs["stop"] #grab stop from player's xml file and return for game play
    stop = stops[nomen]

    logging.info('Leaving load_game')
    return stop

def load_ats_rhymes(game_file):
    '''
    Loads ats and rhymes from player given profile.

    '''
    logging.info('Found load_ats_rhymes')
    with open('save/'+game_file) as f:
        xml_file = f.read()

    success, p_map = game.obj_wrapper(xml_file)
    #call player map here because we are not altering most of the file.
    if not success:
        print "Failure to wrap object."
        exit()
    #only need player from file
    player = p_map.player[0]
    ats = player.attrs["ats"] #grab stop from player's xml file and return for game play
    rhymes = player.attrs["rhymes"]
    logging.info('Leaving load_ats_rhymes')
    return ats,rhymes
def load_items(game_file):
    '''
    load items and names in list
    '''
    logging.info('Found load_ats_rhymes')
    with open('save/'+game_file) as f:
        xml_file = f.read()

    success, p_map = game.obj_wrapper(xml_file)
    #call player map here because we are not altering most of the file.
    if not success:
        print "Failure to wrap object."
        exit()
    #only need player from file
    player = p_map.player[0]
    item_list=[]
    for it in player.item:
        item_list.append(it.attrs["nomen"])

    logging.info('Leaving load_items')
    return item_list

def print_animation(stop):
    print
    stop_nomen = stop.attrs["nomen"]
    ims = dict()
    pts = dict()
    ct=0
    for i in g_map.ascii[0].im:
        nomen = i.attrs["nomen"]
        if stop_nomen == nomen:
            for pt in i.part:
                pts[ct]=pt
                ct+=1
    ct=0
    while ct in pts:
        print pts[ct].value
        time.sleep(.2)
        ct+=1
        os.system('cls')

translate_verb = {"g" : "go","go" : "go","walk" : "go","jump" : "go",
                  "t" : "take", "take" : "take","grab" : "take","get":"take",
                  "l":"describe","look":"describe","describe" : "describe","desc":"describe",
                  "current":"cur","cur":"cur","give":"cur",
                  "load":"load","save":"save",
                  "how":"how","help":"how",
                  "exit":"exit",
                  "score":"score"
                  }

translate_noun = {"n": "n","north":"n",
                  "s": "s","south": "s",
                  "e" : "e","east" : "e",
                  "w" : "w","west" : "w",
                  "u" : "u", "up" : "u","surface":"u",
                  "d" : "d", "down" : "d",
                  "a" : "a","across":"a","over":"a","cross":"a",
                  "i":"i","h":"i", "inventory":"i",
                  "board":"board",
                  "start":"start",
                  }

one_word_cmds = {"n" : "describe n","s" : "describe s","e" : "describe e","w" : "describe w",
                 "u" : "describe u","up": "describe u",
                 "d" : "describe d",
                 "off" :"describe outside",
                 "on":"describe on",
                 "l":"load game","load":"load game",
                 "current": "describe around","now": "describe around","around":"describe around","describe":"describe around",
                 "i":"cur inventory","h":"cur inventory",
                 "rules":"how to","how":"how to","help":"how to",
                 "next": "go start","begin":"go start","start":"go start",
                 "score":"score board",
                 "commands":"commands",
                 }
main()