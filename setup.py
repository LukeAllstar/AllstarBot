import sqlite3

### Tabletop DB ###
tabletopConn = sqlite3.connect('tabletop.db')
tabletopCur = tabletopConn.cursor()

### player
tabletopCur.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='player' ''')
if len(tabletopCur.fetchall()) <= 0:
    tabletopCur.execute('''CREATE TABLE player(
                name TEXT)''')
    print("Created table player")
else:
    print("Table player already exists.")
                
# game
tabletopCur.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='game' ''')
if len(tabletopCur.fetchall()) <= 0:
    tabletopCur.execute('''CREATE TABLE game(
                name TEXT,
                gametype TEXT,
                minplayers INT,
                maxplayers INT)''')
    print("Created game played")
else:
    print("Table game already exists.")
    
# played    
tabletopCur.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='played' ''')
if len(tabletopCur.fetchall()) <= 0:
    tabletopCur.execute('''CREATE TABLE played(
            playedId INT,
            playerId INT,
            gameId INT,
            points INT,
            iscoop INT,
            rank INT,
            playdate TEXT,
            FOREIGN KEY(gameid) REFERENCES game(ROWID),
            FOREIGN KEY(playerid) REFERENCES player(ROWID))''')
    print("Created table played")
else:
    print("Table played already exists.")
            
tabletopConn.commit()


### Quotes ###
quotesConn = sqlite3.connect('quotes.db')
quotesCur = quotesConn.cursor()
quotesCur.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='quotes' ''')
if len(quotesCur.fetchall()) <= 0:
    quotesCur.execute('''CREATE TABLE quotes(quote, name, addedBy)''')
    quotesConn.commit()
else:
    print("Table quotes already exists.")