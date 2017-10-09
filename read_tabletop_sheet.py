#!/usr/bin/python2.4

#from __future__ import print_function
import httplib2
import os
#import psycopg2
import sqlite3

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


try:
    #conn = psycopg2.connect("dbname='Tabletop' user='postgres' host='localhost' password=''")

    #cur.execute("SET search_path TO public")

    delete = True
    if delete == True:
        os.remove('tabletop.db')

    conn = sqlite3.connect('tabletop.db')
    cur = conn.cursor()
        
    create = True
    if create == True:
        cur.execute('''CREATE TABLE player(
                        name TEXT)''')
        cur.execute('''CREATE TABLE game(
                        name TEXT,
                        gametype TEXT,
                        minplayers INT,
                        maxplayers INT)''')
        cur.execute('''CREATE TABLE played(
                    playedId INT,
                    playerId INT,
                    gameId INT,
                    points INT,
                    iscoop INT,
                    rank INT,
                    playdate TEXT,
                    FOREIGN KEY(gameid) REFERENCES game(ROWID),
                    FOREIGN KEY(playerid) REFERENCES player(ROWID))''')
        conn.commit()

    # einmal am anfang alles loeschen und neu einfuegen (simpler als update)
    clean = True
    if clean == True:
        cur.execute("Delete from played")
        
except:
    print "I am unable to connect to the database"#
    exit()
    
        
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'

playernames = {}
games = {}

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():       
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '17wTH0ebxrnbdZUlJJrb0tYDUdsMPkS7nMCKWnC2agYI'
    rangeName = 'Punkte 2017!A20:I'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName, valueRenderOption='FORMULA').execute()
    values = result.get('values', [])
    
    players = [None] * 7
    points = [None] * 7
    game = ''
    playDate = 0
    
    if not values:
        print('No data found.')
    else:
        counter = 0
        isCoop = False
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            #print('%s, %s, %s, %s, %s' % (row[2],row[3],row[4],row[5],row[6]))
            #print('%s' % row)
            #print('Players')
            if len(row) == 1:
                # nur ein eintrag in der zeile -> neuer spielname
                # zuvor ueberpruefen ob vorige daten rausgeschrieben werden muessen
                insertPlayed(players, points, game, playDate)
                players = [None] * 7
                points = [None] * 7
                isCoop = False     
                game=row[0]
                print('+++++ Game: %s +++++' % game)
                # spiele zur db und lokalen liste fuegen
                checkGame(game)
            elif len(row) != 0:
                # counter will be used to count the number of cells
                counter = 0
                #pointsRow = False
                for cell in row:
                    if counter == 0:
                        # image .. maybe use this later
                        print("Cell 0: %s" % cell)
                    if counter == 1:
                        if cell != '':
                            # neuer eintrag -> vorherige daten rausschreiben, anschliesen neu initialisieren   
                            
                            #print('players')
                            #print(players)
                            #playedId = getNextPlayedId()
                            #for idx, player in enumerate(players):
                            #    # we have a 2 dimensional array
                            #    print(idx, player)
                            #    if player != None:
                            #        for p in player:
                            #            # spieler zur db fuegen
                            #            if "," in p:
                            #                print("--- FOUND COOP GAME ---")
                            #                isCoop = True
                            #            elif isCoop == False:
                            #                print("Spieler %s mit platzierung %s und punkten %s" % (p, idx+1, points[idx]))
                            #                checkPlayer(p)
                            #                addPlayed(p, playedId, game, playDate, idx + 1, points[idx], False)
                                   
                            insertPlayed(players, points, game, playDate)
                            
                            #print('score')
                            #print(points)
                            players = [None] * 7
                            points = [None] * 7
                            isCoop = False               
                            playDate = cell
                            print('date: %s' % playDate)
                    elif counter > 1:
                        if cell != '' and cell != '-':
                            # minus 2 because first two cells are for screenshot and date
                            if isInt(cell) == True:
                                points[counter-2] = cell
                            else:
                                if players[counter-2] == None:
                                    players[counter-2] = []
                                players[counter-2].append(cell)
                    counter += 1
                    
    # letzten datensatz schreiben
    insertPlayed(players, points, game, playDate)
    conn.commit()
                
def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def insertPlayed(players, points, game, playDate):
    print('players')
    print(players)
    playedId = getNextPlayedId()
    isCoop = False
    for idx, player in enumerate(players):
        if player != None:
            for p in player:
                if "," in p:
                    isCoop = True
            
    if isCoop == True:
        print("--- FOUND COOP GAME ---")
        
    for idx, player in enumerate(players):
        # we have a 2 dimensional array
        print(idx, player)
        if player != None:
            # spieler zur db fuegen
            p = player[0]
            if isCoop == True:
                if len(player) == 2:
                    text = player[1]
                else:
                    text = ''
                # TODO: Add victory text
                # TODO: Add game won/lost
                coopPlayers = p.split(",")
                for coopPlayer in coopPlayers:
                    print("Coop Player %s with text %s" % (coopPlayer.strip(),text))
                    # Rank and Points are set to 0 for now
                    addPlayed(coopPlayer.strip(), playedId, game, playDate, 0, 0, True)
                isCoop = True
            else:
                print(points)
                print("Spieler %s mit platzierung %s und punkten %s" % (p, idx+1, points[idx]))
                checkPlayer(p)
                addPlayed(p, playedId, game, playDate, idx + 1, points[idx], False)

def checkPlayer(playername):
    if playername not in playernames:
        #playernames.append([])       
        cur.execute("""Select rowid from player where name='%s'""" % playername)
        rows = cur.fetchall()
        if len(rows) == 0:
            # nicht gefunden
            cur.execute("""Insert Into player (name) VALUES ('%s')""" % playername)
            print("#### Added player %s to the database ####" % playername)
            # need the id after its inserted
            cur.execute("""Select rowid from player where name='%s'""" % playername)
            rows = cur.fetchall()
        # erste zeile erste spalte
        playernames[playername] = rows[0][0]
        #print("playernames")
        #print(playernames)
        
def checkGame(game):
    if game not in games:
        #games.append(game)
        cur.execute("""Select rowid from game where name='%s'""" % game)
        rows = cur.fetchall()
        if len(rows) == 0:
            # nicht gefunden
            cur.execute("""Insert Into game (name) VALUES ('%s')""" % game)
            print("#### Added game %s to the database ####" % game)
            # need the id after its inserted
            cur.execute("""Select rowid from game where name='%s'""" % game)
            rows = cur.fetchall()
        # erste zeile erste spalte
        games[game] = rows[0][0]
        #print("games")
        #print(games)
        
def addPlayed(player, playedId, game, playDate, rank, points, isCoop):
    playerId = playernames[player]
    gameId = games[game]

    #print("""Insert into played (rowid, playerId, gameId, rank, points, isCoop, playDate)
    #VALUES ('%s','%s','%s','%s','%s','%s', to_date('1900.01.01','YYYY.MM.DD') + interval '1 day' * (%d - 2))""" % (playedId, playerId, gameId, rank, points, isCoop, playDate))
    
    # playDate ist ein 5 stelliger wert der die tage ab dem 1.1.1900 angiebt. minus 2 weil keine ahnung .. war immer um 2 zu viel
    #cur.execute("""Insert into played (rowid, playerId, gameId, rank, points, isCoop, playDate)
    #VALUES ('%s','%s','%s','%s','%s','%s', to_date('1900.01.01','YYYY.MM.DD') + interval '1 day' * (%d - 2))""" % (playedId, #playerId, gameId, rank, points, isCoop, playDate))
    print("playdate: %s" % playDate)
    cur.execute("""Insert into played (playedId, playerId, gameId, rank, points, isCoop, playDate)
    VALUES ('%s','%s','%s','%s','%s','%s', datetime(0000000000, 'unixepoch', '-70 year', '+%s day'))""" % (playedId, playerId, gameId, rank, points, isCoop, playDate))

def getNextPlayedId():
    cur.execute("""Select COALESCE(MAX(rowid),0) from played""")
    rows = cur.fetchall()
    return rows[0][0] + 1
    
if __name__ == '__main__':
    main()
    cur.close()
    conn.close()
