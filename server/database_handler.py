import os.path
import sqlite3
import time
from threading import  Thread
import typing as tp

server_datas = (
    'id' ,
    'server_id' , 'user_id' ,
    'username' , 'password' ,
    'sent' , 'recieved' ,
    'filename' , 'number_of_activity'
)
server_table = 'primary_datas'

user_recieved_datas = (
    'id' , 'nickname' , 'date' , 'title' ,'message'
)
user_recieved_table = 'recieves'

user_sent_datas = (
    'id' , 'nickname' , 'date' , 'title' , 'message'
)
user_sent_table = 'sents'

def createPrimaryDatabase():
    conn = sqlite3.connect('primary database.db')
    cur = conn.cursor()
    cur.execute(
        f'CREATE TABLE IF NOT EXISTS {server_table} ( id INTEGER PRIMARY KEY , server_id TEXT , user_id TEXT , username TEXT , password TEXT , sent INTEGER , received INTEGER , filename TEXT , number_of_activity INT )')
    conn.commit()
    conn.close()

def createUserDatabase( filename : str  , table : str ) :
    conn = sqlite3.connect( os.path.join('users database' , filename) )
    cur = conn.cursor()
    command = f'CREATE TABLE IF NOT EXISTS {table} ( id INTEGER PRIMARY KEY , nickname TEXT , date TEXT , title TEXT , message TEXT )'
    cur.execute(command)
    conn.commit()
    conn.close()

# =====  Reading Primary Database
def findTheUser( username : str , password : str ) -> tp.Union[ None , tuple ] :
    conn = sqlite3.connect('primary database.db')
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {server_table} WHERE username=? AND password=? " , (username , password ) )
    result = cur.fetchone()
    conn.close()
    return result

def findTheUserByUsername( username : str ) -> tp.Union[ None , tuple ] :
    conn = sqlite3.connect('primary database.db')
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {server_table} WHERE username=?", (username, ))
    result = cur.fetchone()
    conn.close()
    return result


def findHighestSent( limit = 10 ) -> list :
    conn = sqlite3.connect('primary database.db')
    cur = conn.cursor()
    cur.execute(f"SELECT sent , username FROM {server_table} ORDER BY sent DESC LIMIT ?" , (limit , ))
    result = cur.fetchall()
    conn.close()
    return result

def findLowestSent( limit = 10 ) -> list :
    conn = sqlite3.connect('primary database.db')
    cur = conn.cursor()
    cur.execute(f"SELECT sent , username FROM {server_table} ORDER BY sent ASC LIMIT ?" , (limit , ))
    result = cur.fetchall()
    conn.close()
    return result

def findHighestRecieved( limit = 10 ) -> list :
    conn = sqlite3.connect('primary database.db')
    cur = conn.cursor()
    cur.execute(f"SELECT recieved , username FROM {server_table} ORDER BY recieved DESC LIMIT ?" , (limit , ))
    result = cur.fetchall()
    conn.close()
    return result

def findLowestRecieved( limit = 10 ) -> list :
    conn = sqlite3.connect('primary database.db')
    cur = conn.cursor()
    cur.execute(f"SELECT recieved , username FROM {server_table} ORDER BY recieved ASC LIMIT ?" , (limit , ))
    result = cur.fetchall()
    conn.close()
    return result

# =====  Writing In Primary Database
def addNewUser( server_id : str , user_id : str , username : str , password : str , sent : int , received : int , database : str , activity : int ):
    conn = sqlite3.connect('primary database.db')
    cur = conn.cursor()
    values = ( server_id , user_id , username , password , sent , received , database , activity)
    cur.execute(f"INSERT INTO {server_table} (server_id , user_id , username , password , sent , received , filename , number_of_activity ) VALUES ( ? , ? , ? , ? , ? , ? , ? , ? )" , values)
    conn.commit()
    conn.close()

def increaseTheNumberOfActivity( username : str , password : str ,increase = 1 ):
    conn = sqlite3.connect('primary database.db' , timeout=10)
    cur = conn.cursor()
    cur.execute(f"UPDATE {server_table} SET number_of_activity = number_of_activity + ? WHERE username = ? AND password = ? " , (increase , username , password ))
    conn.commit()
    conn.close()

# ======= Reading User Database
def checkHowManyRowsItContain(filename , table : str) -> int :
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table} ")
    result = cur.fetchall()
    conn.close()
    return result[0][0]

def getDataByNewestAdded( filename : str , table : str , current_getted : int ,limit = 10 ) -> tuple[ int , list] :
    filename = os.path.join('users database', filename)
    rows_num = checkHowManyRowsItContain(filename, table)
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    already_getted = [i for i in range(current_getted, rows_num)]
    command = f"SELECT * FROM {table} WHERE "
    for num in already_getted :
        command = command + f'id != {num} AND '
    command = command + f'ORDER BY id DESC LIMIT {limit}'
    cur.execute(command)
    result = cur.fetchall()
    conn.close()
    return ( current_getted - len(result) , result )

def getDataByFind(filename : str , table : str , find : str , excepted_ids : list[int , ...] , limit = 10 ) -> tuple[ list[int , ...] , list[list, ...] ]:
    filename = os.path.join('users database', filename)
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    command = f"SELECT * FROM {table} WHERE "
    for num in excepted_ids :
        command = command + f'id != ? AND '
    command = command + f'nickname = ? OR date = ? OR title = ? OR message = ? '
    command = command + f'ORDER BY id DESC LIMIT {limit}'
    cur.execute(command , ( *excepted_ids , find , find , find , find ) )
    result = cur.fetchall()
    conn.close()
    if len(result) > 0 :
        excepted_ids = excepted_ids + [ data[0] for data in result ]
    return ( excepted_ids , result )

# ======= Writing In User Database
def addNewDataInUserDatabase( filename : str , table : str ,nickname : str , date : str , title : str , message : str ) :
    filename = os.path.join('users database', filename)
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {table} ( nickname , date , title , message ) VALUES ( ? ? ? ? )", (nickname , date , title , message ))
    conn.commit()

# Database Handler
class DatabaseWritingHandler :
    # 'main' means if the writing happening in primary database
    # 'users' means if the writing happening in clients database
    activity = { 'pending' : [] , 'main' : [] , 'user' : [] , 'processing' : [] , 'done' : [] }
    # pending : dict = { activity : str , activity data : tuple or list , main : bool }
    # done : pending value
    activity_thread : Thread = None

    def run(self):
        print('[ / ] Database is ready to write data')
        self.activity_thread = Thread( target= self.do_pending_activities )
        self.activity_thread.start()
        Thread( target=self.do_main_activities ).start()
        Thread( target=self.do_user_activities ).start()

    def stop(self):
        print('\n[ ! ] Please wait , finishing up the items ')
        activities = len(self.activity['pending']) + len(self.activity['main']) + len(self.activity['user']) + len(self.activity['processing'])
        print(f'[ ? ] Finishing Up : {activities}')
        time.sleep(1)
        print(f'[ ? ] Pending : {len(self.activity["pending"])}')
        while self.activity['pending']:
            pass
        time.sleep(1)
        print(f'[ ? ] Users Activities : {len(self.activity["user"]) + len(self.activity["main"])}')
        while self.activity['user'] or self.activity['main'] :
            pass
        time.sleep(1)
        print(f'[ ? ] Processing Activities : {len(self.activity["processing"])}')
        while self.activity['processing'] :
            pass
        time.sleep(1)
        print(f'[ / ] Done the writing activities : {len(self.activity["done"])} ')

    def add_activity(self , activity : dict ) -> bool:
        if not isinstance(activity , dict ):
            return False
        self.activity['pending'].append(activity)
        return True

    # ===== Do the User Activity
    def do_user_activities(self):
        while True:
            if self.activity['user']:
                client = self.activity['user'].pop(0)
                self.activity['processing'].append(client)
                self.do_user_activity(client)

    def do_user_activity(self, activity: dict):
        ''' This is where all activities start '''
        if activity['activity'] == 'recieving': # it means there is a incomimg envelope to a user
            addNewDataInUserDatabase(
                activity['activity data'][0] , activity['activity data'][1] ,
                activity['activity data'][2] , activity['activity data'][3] ,
                activity['activity data'][4] , activity['activity data'][5]
            )
        elif activity['activity'] == 'sending': # it means there is a user who sent a envelope
            addNewDataInUserDatabase(
                activity['activity data'][0] , activity['activity data'][1] ,
                activity['activity data'][2] , activity['activity data'][3] ,
                activity['activity data'][4] , activity['activity data'][5]
            )

    # ===== Do the Main Activity
    def do_main_activities(self):
        while True :
            if self.activity['main'] :
                client = self.activity['main'].pop(0)
                self.activity['processing'].append(client)
                self.do_user_activity(client)

    def do_main_activity(self , activity : dict ):
        ''' This is where all activities start '''
        if activity['activity'] == 'enter' : # it means that user has transaction with server
            increaseTheNumberOfActivity( activity['activity data'][0] , activity['activity data'][1] )
        elif activity['activity'] == 'create account' :
            addNewUser(
                activity['activity data'][0] , activity['activity data'][1] ,
                activity['activity data'][2] , activity['activity data'][3],
                activity['activity data'][4], activity['activity data'][5],
                activity['activity data'][6], activity['activity data'][7],
            )

    # ===== Do The Pending Activity
    def do_pending_activities(self):
        while True :
            if self.activity['pending'] :
                self.do_pending_activity( self.activity['pending'].pop(0) )

    def do_pending_activity(self , activity : dict ):
        if activity['main'] :
            self.activity['main'].append(activity)
        else :
            self.activity['user'].append(activity)


if __name__ == "__main__" :
    createPrimaryDatabase()
    print(checkHowManyRowsItContain('primary database.db' , server_table))
    a = [1 , 2 , 3]
    print( (*a , 2 ,3 , 4 ))

