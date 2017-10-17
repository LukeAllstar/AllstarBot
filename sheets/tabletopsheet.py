import httplib2
import os
import sqlite3
from pathlib import Path

from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

class Tabletop:
    conn = None
    cur = None
    playernames = {}
    games = {}
    delete = False
    create = False
    
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/sheets.googleapis.com-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Allstar Bot Tabletop'
    
    def __init__(self, delete, create):
        self.delete = delete
        self.create = create
    
    def __init(self):
        self.delete = False
        self.create = False
   
    def inittabletop(self):
        if not os.path.exists('db'):
            print('Creating directory db')
            os.makedirs('db')

        try:
            if self.delete == True:
                dbfile = Path("db/tabletop.db")
                if dbfile.exists():
                    try:
                        print("removing db/tabletop.db")
                        os.remove('db/tabletop.db')
                        print("removed db/tabletop.db")
                    except OSError as e:
                        print(e)
                        raise Exception("can't remove file db/tabletop.db")

            self.conn = sqlite3.connect('db/tabletop.db')
            self.cur = self.conn.cursor()
            
            if self.create == True:
                self.cur.execute('''CREATE TABLE player(
                                name TEXT)''')
                self.cur.execute('''CREATE TABLE game(
                                name TEXT,
                                gametype TEXT,
                                minplayers INT,
                                maxplayers INT)''')
                self.cur.execute('''CREATE TABLE played(
                            playedId INT,
                            playerId INT,
                            gameId INT,
                            points INT,
                            iscoop INT,
                            rank INT,
                            playdate TEXT,
                            FOREIGN KEY(gameid) REFERENCES game(ROWID),
                            FOREIGN KEY(playerid) REFERENCES player(ROWID))''')
                self.conn.commit()
                
        except Exception as e:
            print(e)
            raise Exception("Error removing or creating the database")

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        
        try:
            import argparse
            #flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
            flags = tools.argparser.parse_args(args=[])
        except ImportError:
            flags = None
        
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,'sheets.googleapis.com-allstarbot.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def update_database(self):  
        """Shows basic usage of the Sheets API.

        Creates a Sheets API service object and prints the names and majors of
        students in a sample spreadsheet:
        https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
        """
        
        self.inittabletop()
        
        credentials = self.get_credentials()
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
                if len(row) == 1:
                    # nur ein eintrag in der zeile -> neuer spielname
                    # zuvor ueberpruefen ob vorige daten rausgeschrieben werden muessen
                    self.insertPlayed(players, points, game, playDate)
                    players = [None] * 7
                    points = [None] * 7
                    isCoop = False     
                    game=row[0]
                    print('+++++ Game: %s +++++' % game)
                    # spiele zur db und lokalen liste fuegen
                    self.checkGame(game)
                elif len(row) != 0:
                    # counter will be used to count the number of cells
                    counter = 0
                    for cell in row:
                        if counter == 0:
                            # image .. maybe use this later
                            print("Cell 0: %s" % cell)
                        if counter == 1:
                            if cell != '':
                                # neuer eintrag -> vorherige daten rausschreiben, anschliesen neu initialisieren   
                                self.insertPlayed(players, points, game, playDate)
                                
                                players = [None] * 7
                                points = [None] * 7
                                isCoop = False               
                                playDate = cell
                                #print('date: %s' % playDate)
                        elif counter > 1:
                            if cell != '' and cell != '-':
                                # minus 2 because first two cells are for screenshot and date
                                if self.isInt(cell) == True:
                                    points[counter-2] = cell
                                else:
                                    if players[counter-2] == None:
                                        players[counter-2] = []
                                    players[counter-2].append(cell)
                        counter += 1
                        
        # write last row because we normally write when the next row has been found
        self.insertPlayed(players, points, game, playDate)
        self.conn.commit()
        self.end()
                    
    def isInt(self,s):
        try: 
            int(s)
            return True
        except ValueError:
            return False

    def insertPlayed(self,players, points, game, playDate):
        print('players')
        print(players)
        playedId = self.getNextPlayedId()
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
                # add player to database
                if isCoop == True:
                    p = player[0]
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
                        self.addPlayed(coopPlayer.strip(), playedId, game, playDate, 0, 0, True)
                    isCoop = True
                else:
                    for p in player:
                        print(points)
                        print("Spieler %s mit platzierung %s und punkten %s" % (p, idx+1, points[idx]))
                        self.checkPlayer(p)
                        self.addPlayed(p, playedId, game, playDate, idx + 1, points[idx], False)

    def checkPlayer(self, playername):
        if playername not in self.playernames:     
            self.cur.execute("""Select rowid from player where name='%s'""" % playername)
            rows = self.cur.fetchall()
            if len(rows) == 0:
                # nicht gefunden
                self.cur.execute("""Insert Into player (name) VALUES ('%s')""" % playername)
                print("#### Added player %s to the database ####" % playername)
                # need the id after its inserted
                self.cur.execute("""Select rowid from player where name='%s'""" % playername)
                rows = self.cur.fetchall()
            self.playernames[playername] = rows[0][0]
            
    def checkGame(self, game):
        if game not in self.games:
            self.cur.execute("""Select rowid from game where name='%s'""" % game)
            rows = self.cur.fetchall()
            if len(rows) == 0:
                # nicht gefunden
                self.cur.execute("""Insert Into game (name) VALUES ('%s')""" % game)
                print("#### Added game %s to the database ####" % game)
                # need the id after its inserted
                self.cur.execute("""Select rowid from game where name='%s'""" % game)
                rows = self.cur.fetchall()
            self.games[game] = rows[0][0]
            
    def addPlayed(self, player, playedId, game, playDate, rank, points, isCoop):
        playerId = self.playernames[player]
        gameId = self.games[game]
        # playDate ist ein 5 stelliger wert der die tage ab dem 1.1.1900 angiebt. minus 2 weil keine ahnung .. war immer um 2 zu viel
        #print("playdate: %s" % playDate)
        self.cur.execute("""Insert into played (playedId, playerId, gameId, rank, points, isCoop, playDate)
        VALUES ('%s','%s','%s','%s','%s','%s', datetime(0000000000, 'unixepoch', '-70 year', '+%s day'))""" % (playedId, playerId, gameId, rank, points, isCoop, playDate-2))

    def getNextPlayedId(self):
        self.cur.execute("""Select COALESCE(MAX(rowid),0) from played""")
        rows = self.cur.fetchall()
        return rows[0][0] + 1
        
    def end(self):
        self.cur.close()
        self.conn.close()
    
# just here for testing 
#if __name__ == '__main__':
#    tabletop = Tabletop(True, True) 
#    tabletop.update_database()
