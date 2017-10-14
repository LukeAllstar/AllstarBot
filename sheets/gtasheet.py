#from __future__ import print_function
import httplib2
import os
#import psycopg2
import sqlite3

from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

class Gtasheet:
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
    APPLICATION_NAME = 'Allstar Bot Gta'
    
    def __init__(self, delete, create):
        self.delete = delete
        self.create = create
    
    def __init(self):
        self.delete = False
        self.create = False
        
    def initgta(self):
        print('initgta')
        if not os.path.exists('db'):
            print('Creating directory db')
            os.makedirs('db')

        try:
            if self.delete == True:
                try:
                    #self.conn.close()
                    print("removing db/gta.db")
                    os.remove('db/gta.db')
                    print("removed db/gta.db")
                except OSError as e:
                    print(e)
                    raise Exception("can't remove file db/gta.db")
                
            self.conn = sqlite3.connect('db/gta.db')
            self.cur = self.conn.cursor()
                    
            if self.create == True:
                self.cur.execute('''CREATE TABLE playlist(
                                name TEXT,
                                date TEXT,
                                crasherid INT,
                                FOREIGN KEY (crasherid) REFERENCES player(ROWID))''')
                self.cur.execute('''CREATE TABLE race(
                                racenumber INT,
                                playlistid INT,
                                name TEXT,
                                vehicleclass TEXT,
                                isCanceled INT,
                                FOREIGN KEY (playlistid) REFERENCES playlist(ROWID))''')
                self.cur.execute('''CREATE TABLE player(
                                name TEXT)''')
                self.cur.execute('''CREATE TABLE raced(
                            racenumber INT,
                            playerid INT,
                            rank INT,
                            bestlap INT,
                            racetime INT,
                            vehicle TEXT,
                            money INT,
                            isdnf INT,
                            FOREIGN KEY(racenumber) REFERENCES race(racenumber),
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
            flow.params['access_type'] = 'offline'
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
        
        self.initgta()
       
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        spreadsheetId = '1Avxh9i3ObSn7rf8iA75JBwdmdWRis7FS8WezsO9E6sE'
        rangeName = 'Statistiken (Details)!A2:M'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName, valueRenderOption='FORMULA').execute()
        values = result.get('values', [])
        
        players = [None] * 7
        points = [None] * 7
        game = ''
        playDate = 0
        racenumber = None
        playlistid = None
        
        if not values:
            print('No data found.')
        else:
            counter = 0
            isCoop = False
            for row in values:
                # Print columns A and E, which correspond to indices 0 and 4.
                #print('%s, %s, %s, %s, %s' % (row[2],row[3],row[4],row[5],row[6]))
                print('%s' % row)
                
                if(len(row) >= 9 and row[8] != None):
                    # new playlist
                    print(str(row[8]) + " - " + str(row[9]))
                    self.insertPlaylist(row[8], row[9])
                
                if len(row) >= 8 and row[0] != None and row[0] != "":
                    # new race
                    if racenumber == None:
                        isCanceled = False
                        if row[1] == None or row[1] == "":
                            isCanceled = True
                        playlistid = int(self.getCurrentPlaylistId())
                        racenumber = self.getNextRaceNumber(playlistid)
                        self.insertRace(playlistid, racenumber, isCanceled)
                        rank = 0

                    # new raced
                    rank = row[1]
                    player = row[2].lower()
                    vehicle = row[3]
                    racetime = row[4]
                    bestlap = row[5]
                    money = row[6]                   
                    
                    self.checkPlayer(player)
                    self.insertRaced(racenumber, rank, bestlap, racetime, vehicle, player, money)
                    
                else:
                    playlistid = None
                    racenumber = None
                
        self.conn.commit()
        self.end()
        
    def isInt(self,s):
        try: 
            int(s)
            return True
        except ValueError:
            return False

    def insertPlaylist(self, name, date):
        print("Inserting %s at date %s" % (name, date))
        self.cur.execute("""INSERT INTO playlist(name, date)
                            VALUES('"""+name+"""', strftime('%d.%m.%Y','"""+date+"""'))""")
    
    
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
                # spieler zur db fuegen

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
            #playernames.append([])       
            self.cur.execute("""Select rowid from player where name='%s'""" % playername)
            rows = self.cur.fetchall()
            if len(rows) == 0:
                # nicht gefunden
                self.cur.execute("""Insert Into player (name) VALUES ('%s')""" % playername)
                print("#### Added player %s to the database ####" % playername)
                # need the id after its inserted
                self.cur.execute("""Select rowid from player where name='%s'""" % playername)
                rows = self.cur.fetchall()
            # erste zeile erste spalte
            self.playernames[playername] = rows[0][0]
            #print("playernames")
            #print(playernames)
            
    def checkGame(self, game):
        if game not in self.games:
            #games.append(game)
            self.cur.execute("""Select rowid from game where name='%s'""" % game)
            rows = self.cur.fetchall()
            if len(rows) == 0:
                # nicht gefunden
                self.cur.execute("""Insert Into game (name) VALUES ('%s')""" % game)
                print("#### Added game %s to the database ####" % game)
                # need the id after its inserted
                self.cur.execute("""Select rowid from game where name='%s'""" % game)
                rows = self.cur.fetchall()
            # erste zeile erste spalte
            self.games[game] = rows[0][0]
            #print("games")
            #print(games)
            
    def addPlayed(self, player, playedId, game, playDate, rank, points, isCoop):
        playerId = self.playernames[player]
        gameId = self.games[game]

        #print("""Insert into played (rowid, playerId, gameId, rank, points, isCoop, playDate)
        #VALUES ('%s','%s','%s','%s','%s','%s', to_date('1900.01.01','YYYY.MM.DD') + interval '1 day' * (%d - 2))""" % (playedId, playerId, gameId, rank, points, isCoop, playDate))
        
        # playDate ist ein 5 stelliger wert der die tage ab dem 1.1.1900 angiebt. minus 2 weil keine ahnung .. war immer um 2 zu viel
        #cur.execute("""Insert into played (rowid, playerId, gameId, rank, points, isCoop, playDate)
        #VALUES ('%s','%s','%s','%s','%s','%s', to_date('1900.01.01','YYYY.MM.DD') + interval '1 day' * (%d - 2))""" % (playedId, #playerId, gameId, rank, points, isCoop, playDate))
        print("playdate: %s" % playDate)
        self.cur.execute("""Insert into played (playedId, playerId, gameId, rank, points, isCoop, playDate)
        VALUES ('%s','%s','%s','%s','%s','%s', datetime(0000000000, 'unixepoch', '-70 year', '+%s day'))""" % (playedId, playerId, gameId, rank, points, isCoop, playDate-2))

    def getCurrentPlaylistId(self):
        self.cur.execute("""Select COALESCE(MAX(rowid), 0) from playlist""")
        rows = self.cur.fetchone()
        return rows[0]
    
    def insertRace(self, playlistid, racenumber, isCanceled):
        self.cur.execute("""INSERT INTO race (playlistid, racenumber, isCanceled)
                            VALUES(%s, %s, '%s')""" % (playlistid, racenumber, isCanceled))
    
    def insertRaced(self, racenumber, rank, bestlap, racetime, vehicle, player, money):
        if bestlap == "-":
            bestlap = 0
        isdnf = False    
        if racetime == "DNF":
            racetime = 0
            isdnf = True
            
        playerid = self.playernames[player]
        print("Inserting player %s, race %s, bestlap %s, racetime %s, vehicle %s, rank %s, money %s, isdnf %s"
                % (playerid, racenumber, bestlap, racetime, vehicle, rank, money, isdnf))

        self.cur.execute("""INSERT INTO raced(playerid, racenumber, bestlap, racetime, vehicle, rank, money, isdnf)
                        VALUES("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""
                        % (playerid, racenumber, bestlap, racetime, vehicle, rank, money, isdnf))
    
    def getNextRaceNumber(self, playlistid):
        self.cur.execute("""Select COALESCE(MAX(racenumber), 0) from race
                            WHERE playlistid = %s""" % playlistid)
        rows = self.cur.fetchone()
        return rows[0] + 1
    
    def getNextPlayedId(self):
        self.cur.execute("""Select COALESCE(MAX(rowid),0) from played""")
        rows = self.cur.fetchall()
        return rows[0][0] + 1
        
    def end(self):
        self.cur.close()
        self.conn.close()
    
if __name__ == '__main__':
    gta = Gtasheet(True, True) 
    gta.update_database()
