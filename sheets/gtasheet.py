import httplib2
import os
import sqlite3
from pathlib import Path

from googleapiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools
from oauth2client.file import Storage
import datetime

class Gtasheet:
    conn = None
    cur = None
    playernames = {}
    delete = False
    create = False
    noauth = False
    closeConn = False
    
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/sheets.googleapis.com-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Allstar Bot Gta'
    
    def __init__(self, delete, create, noauth, conn):
        self.delete = delete
        self.create = create
        self.noauth = noauth
        self.conn = conn
        self.playernames = {}
    
    #def __init__(self, delete, create, noauth):
    #    self.delete = delete
    #    self.create = create
    #    self.noauth = noauth
    
    def __init(self):
        self.delete = False
        self.create = False
        self.noauth = False
        self.playernames = {}
        
    def initgta(self):
        print('initgta')
        playernames = {}
        
        if not os.path.exists('db'):
            print('Creating directory db')
            os.makedirs('db')

        try:
            if self.delete == True:
                print("- deleting gta db")
                dbfile = Path("db/gta.db")
                if dbfile.exists():
                    try:
                        print("removing db/gta.db")
                        os.remove('db/gta.db')
                        print("removed db/gta.db")
                    except OSError as e:
                        print(e)
                        raise Exception("can't remove file db/gta.db")
            
            if self.conn == None:
                self.conn = sqlite3.connect('db/gta.db')
                self.closeConn = True
                
            self.cur = self.conn.cursor()
                    
            if self.create == True:
                print("creating gta db")
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
                                racename TEXT,
                                socialclub TEXT,
                                mapper TEXT,
                                desiredvehicle TEXT,
                                FOREIGN KEY (playlistid) REFERENCES playlist(ROWID))''')
                self.cur.execute('''CREATE TABLE player(
                                name TEXT)''')
                self.cur.execute('''CREATE TABLE raced(
                            raceid INT,
                            playerid INT,
                            rank INT,
                            bestlap INT,
                            racetime INT,
                            vehicle TEXT,
                            money INT,
                            isdnf INT,
                            isdsq INT,
                            FOREIGN KEY(raceid) REFERENCES race(rowid),
                            FOREIGN KEY(playerid) REFERENCES player(ROWID))''')
                self.cur.execute('''Create View playerstats as 
                                    with tt(playlistid, playlistname, playername, points) as (
                                                Select playlistid, x.name as playlistname, player.name as playername, sum(points) as points from
                                                    ( Select *,
                                                            CASE
                                                            WHEN isdsq = 'True' OR isdnf = 'True' THEN 0
                                                            WHEN rank = 1 THEN 15
                                                            WHEN rank = 2 THEN 12
                                                            WHEN rank = 3 THEN 10
                                                            WHEN rank BETWEEN 4 AND 10 THEN 12 - rank
                                                            ELSE 1
                                                            END as points from
                                                        playlist
                                                        join race on race.playlistid = playlist.rowid
                                                        join raced on raced.raceid = race.rowid
                                                    ) as x
                                                    join player on playerid = player.rowid
                                                        group by playlistid, x.name, playername
                                                        order by playlistid asc, points desc)
                                    Select s.playlistid, s.playlistname, s.playername, s.points, (
                                            Select count(*)+1 
                                                from tt as my 
                                                where my.points > s.points and my.playlistid = s.playlistid) as rank
                                    from tt as s''')
                self.conn.commit()
            else:
                self.cur.execute('''Delete from raced''')
                self.cur.execute('''Delete from race''')
                self.cur.execute('''Delete from playlist''')
                self.cur.execute('''Delete from player''')
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
            if self.noauth == True:
                flags = tools.argparser.parse_args(args=['--noauth_local_webserver'])
            else:
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
            secret = Path(self.CLIENT_SECRET_FILE)
            if secret.exists():
                flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            else:
                print("client_secret.json not found, using env vars")
                if not os.environ.get('client_id') or not os.environ.get('client_secret'): 
                    print("env vars client_id and client_secret not found. canceling")
                    raise Exception("client secret error")
                else:
                    flow = OAuth2WebServerFlow(
                        os.environ.get('client_id'),
                        os.environ.get('client_secret'),
                        self.SCOPES)    
            
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
        rangeName = 'Statistiken (Details) #2017!A1:M'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName, valueRenderOption='FORMULA').execute()
        values = result.get('values', [])
        
        rangeName = 'Statistiken (Details) #2018!A1:M'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName, valueRenderOption='FORMULA').execute()
        values += result.get('values', [])
        
        players = [None] * 7
        points = [None] * 7
        game = ''
        playDate = 0
        raceid = None
        playlistid = None
        
        if not values:
            print('No data found.')
        else:
            for row in values:
                #print('%s' % row)
                
                if(len(row) >= 9 and row[8] != None):
                    # new playlist
                    self.insertPlaylist(row[8], row[9])
                
                if len(row) >= 8 and row[2] != None and row[2] != "":
                    # new race
                    if raceid == None:
                        isCanceled = False
                        if row[1] == None or row[1] == "":
                            isCanceled = True
                        playlistid = int(self.getCurrentPlaylistId())
                        racenumber = self.getNextRaceNumber(playlistid)
                        self.insertRace(playlistid, racenumber, isCanceled)
                        raceid = self.getCurrentRaceId()
                        rank = 0
            
                    # new raced
                    rank = row[1]
                    player = row[2].lower()
                    vehicle = row[3]
                    racetime = row[4]
                    bestlap = row[5]
                    money = row[6]                   
                    
                    self.checkPlayer(player)
                    self.insertRaced(raceid, rank, bestlap, racetime, vehicle, player, money, "")
                    rank += 1
                else:
                    playlistid = None
                    raceid = None
                
        # 2019 sheet has a different structure
        rangeName = 'Statistiken (Details) #2019!A2:N'
        result2019 = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName, valueRenderOption='FORMULA').execute()
        values2019 = result2019.get('values', [])


        if not values2019:
            print('No data found.')
        else:
            for row in values2019:
                #print('%s' % row)
                
                if(len(row) >= 13 and row[12] != None):
                    # new playlist
                    #print('%s' % row)
                    if(len(row) < 14):
                        print("missing date for playlist " + str(row[12]))
                        playlistdate = ''
                    else:
                        playlistdate = str(row[13])
                    print('new 2019 playlist' + str(row[12]) + ' - ' + playlistdate)
                    self.insertPlaylist(row[12], playlistdate)

                if len(row) >= 12 and row[8] != None:
                    # new race
                    #print("new race")
                    vehicle = row[11]
                    isCanceled = False
                    if row[1] == None or row[1] == "":
                        isCanceled = True
                    playlistid = int(self.getCurrentPlaylistId())
                    racenumber = self.getNextRaceNumber(playlistid)
                    self.insertRaceWithMetadata(playlistid, racenumber, isCanceled, row[8], row[9], row[10], row[11])
                    raceid = self.getCurrentRaceId()
                    rank = 0
                    rankmod = 0

                if len(row) >= 7 and row[1] != None and row[2] != None and row[2] != "":
                    # new raced
                    #print("new raced")
                    rank = row[1]
                    player = row[2].lower()
                    wrongvehicle = row[3]
                    if wrongvehicle == "x":
                        rankmod += 1
                        rank = 0
                    racetime = row[4]
                    bestlap = row[5]
                    money = row[6]
                    
                    self.checkPlayer(player)
                    self.insertRaced(raceid, rank - rankmod, bestlap, racetime, vehicle, player, money, wrongvehicle)
                    rank += 1

        # close
        self.conn.commit()
        self.end()


    def insertPlaylist(self, name, date):
        # Date conversion needed: https://developers.google.com/sheets/api/guides/concepts#datetime_serial_numbers
        try:
            calcDate = (datetime.datetime(1899,12,30) + datetime.timedelta(days=int(date))).isoformat()
        except Exception:
            calcDate = ''
        print("Inserting %s at date %s" % (name, calcDate))
        self.cur.execute("""INSERT INTO playlist(name, date)
                            VALUES('"""+name+"""', '""" + calcDate + """')""")
    

    def checkPlayer(self, playername):
        # search for player in local var and database, otherwise create him
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
            
    def getCurrentPlaylistId(self):
        self.cur.execute("""Select COALESCE(MAX(rowid), 0) from playlist""")
        rows = self.cur.fetchone()
        return rows[0]
    
    def insertRace(self, playlistid, racenumber, isCanceled):
        self.insertRaceWithMetadata(playlistid, racenumber, isCanceled, "", "", "", "")
        #self.cur.execute("""INSERT INTO race (playlistid, racenumber, isCanceled)
        #                    VALUES(%s, %s, '%s')""" % (playlistid, racenumber, isCanceled))

    def insertRaceWithMetadata(self, playlistid, racenumber, isCanceled, racename, socialclub, mapper, desiredvehicle):
        print("inserting into race '%s', '%s', '%s', '%s', '%s', '%s', '%s'" % (playlistid, racenumber, isCanceled, racename, socialclub, mapper, desiredvehicle))
        self.cur.execute("""INSERT INTO race (playlistid, racenumber, isCanceled, racename, socialclub, mapper, desiredvehicle)
                            VALUES(?, ?, ?, ?, ?, ?, ?)""", (playlistid, racenumber, isCanceled, racename, socialclub, mapper, desiredvehicle))
    
    def insertRaced(self, raceid, rank, bestlap, racetime, vehicle, player, money, wrongvehicle):
        if bestlap == "-":
            bestlap = 0
        isdnf = False    
        if racetime == "DNF":
            racetime = 0
            isdnf = True

        isDisqualified = False
        if vehicle == "DSQ" or wrongvehicle == "x":
            isDisqualified = True
            vehicle = ""
            rank = 0
            
        playerid = self.playernames[player]
        #print("Inserting player %s, raceid %s, bestlap %s, racetime %s, vehicle %s, rank %s, money %s, isdnf %s, isdsq %s"
        #        % (playerid, raceid, bestlap, racetime, vehicle, rank, money, isdnf, isDisqualified))

        self.cur.execute("""INSERT INTO raced(playerid, raceid, bestlap, racetime, vehicle, rank, money, isdnf, isdsq)
                        VALUES("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""
                        % (playerid, raceid, bestlap, racetime, vehicle, rank, money, isdnf, isDisqualified))
    
    def getNextRaceNumber(self, playlistid):
        self.cur.execute("""Select COALESCE(MAX(racenumber), 0) from race
                            WHERE playlistid = %s""" % playlistid)
        rows = self.cur.fetchone()
        return rows[0] + 1
    
    def getCurrentRaceId(self):
        self.cur.execute("""Select COALESCE(MAX(rowid), 0) from race""")
        rows = self.cur.fetchone()
        return rows[0]
        
    def end(self):
        if self.closeConn == True:
            #self.cur.close()
            self.conn.close()
 
# just here for testing 
if __name__ == '__main__':
    gtaConn = sqlite3.connect('db/gta.db')
    gta = Gtasheet(False, True, False, gtaConn) 
    gta.update_database()
