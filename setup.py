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
        gta = sheets.Gtasheet(True, True)
        gta.update_database()
        print("... Finished")

def createTabletop(force : bool):
    ### Tabletop ###
    if force == False and os.path.exists('db/tabletop.db'):
        print("db/tabletop.db already exists. Skipping")
    else:
        print("Creating db/tabletop.db ...")
        tts = sheets.Tabletop(True, True)
        tts.update_database()
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

def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", help="tts, gta or quotes, commaseperated")
    parser.add_argument("--noauth_local_webserver", action="store_true")
    #example: python setup.py --force gta,tabletop
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

if __name__ == '__main__':
    setup()

