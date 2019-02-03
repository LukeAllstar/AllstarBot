import sqlite3
import sheets
import os
import argparse

def createGta(force : bool):
    ### GTA ###
    if force == False and os.path.exists('db/gta.db'):
        print("db/gta.db already exists. Skipping")
    else:
        print("Creating db/gta.db ...")
        #gtaConn = sqlite3.connect('db/gta.db')
        gta = sheets.Gtasheet(True, True, True, None)
        gta.initgta()
        print("... Finished")

def createTabletop(force : bool):
    ### Tabletop ###
    if force == False and os.path.exists('db/tabletop.db'):
        print("db/tabletop.db already exists. Skipping")
    else:
        print("Creating db/tabletop.db ...")
        tts = sheets.Tabletop(True, True, True)
        tts.update_database()
        print("... Finished")

def createBotdb(force : bool):
    ### Tabletop ###
    if force == False and os.path.exists('db/bot.db'):
        print("db/bot.db already exists. Skipping")
    else:
        try:
            print("removing db/bot.db")
            os.remove('db/bot.db')
            print("removed db/bot.db")
        except OSError:
            pass
        print("Creating db/bot.db ...")
        botConn = sqlite3.connect('db/bot.db')
        botCur = botConn.cursor()
        botCur.execute('''CREATE TABLE allowedroles(server, name)''')
        botConn.commit()
        print("... Finished")
        
def createQuotes(force : bool):
    ### Quotes ###   
    if force == False and os.path.exists('db/quotes.db'):
        print("db/quotes.db already exists. Skipping")
    else:
        try:
            print("removing db/quotes.db")
            os.remove('db/quotes.db')
            print("removed db/quotes.db")
        except OSError:
            pass
        print("Creating db/quotes.db ...")
        quotesConn = sqlite3.connect('db/quotes.db')
        quotesCur = quotesConn.cursor()
        #quotesCur.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='quotes' ''')
        #if len(quotesCur.fetchall()) <= 0:
        quotesCur.execute('''CREATE TABLE quotes(quote, name, addedBy)''')
        quotesConn.commit()
        #else:
        #    print("Table quotes already exists.")
        print("... Finished")

def createGifs(force : bool):
    ### Gifs ###   
    if force == False and os.path.exists('db/gifs.db'):
        print("db/gifs.db already exists. Skipping")
    else:
        try:
            print("removing db/gifs.db")
            os.remove('db/gifs.db')
            print("removed db/gifs.db")
        except OSError:
            pass
        print("Creating db/gifs.db ...")
        gifConn = sqlite3.connect('db/gifs.db')
        gifCur = gifConn.cursor()
        gifCur.execute('''CREATE TABLE gifs(url, game, comment, addedBy, addedOn, messageId, channelId)''')
        gifCur.execute('''CREATE TABLE comboGifs(id1, id2)''')
        gifConn.commit()
        print("... Finished")
        
def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", help="tts, gta, quotes or gifs. comma seperated")
    parser.add_argument("--noauth_local_webserver", action="store_true")
    #example: python3 setup.py --force gta,tabletop
    args = parser.parse_args()
    forceArgs = None

    if args.force:
        print(args.force)
        forceArgs = args.force.split(",")
        print(forceArgs)

    if not os.path.exists('db'):
        print('Creating directory db')
        os.makedirs('db')

    ### Gta ###
    if forceArgs != None and "gta" in forceArgs:
        print("forcing gta")
        createGta(True)
    else:
        createGta(False)

    ### Tabletop ###    
    if forceArgs != None and ("tts" in forceArgs or "tabletop" in forceArgs):
        print("forcing tabletop")
        createTabletop(True)
    else:
        createTabletop(False)
        
    ### Quotes ###
    if forceArgs != None and ("quote" in forceArgs or "quotes" in forceArgs):
        print("forcing quote")
        createQuotes(True)
    else:
        createQuotes(False)
        
    ### Gifs ###
    if forceArgs != None and ("gif" in forceArgs or "gifs" in forceArgs):
        print("forcing gifs")
        createGifs(True)
    else:
        createGifs(False)

    ### General Bot db ###
    if forceArgs != None and ("bot" in forceArgs or "bot" in forceArgs):
        print("forcing bot")
        createBotdb(True)
    else:
        createBotdb(False)

if __name__ == '__main__':
    setup()

