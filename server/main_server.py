import socket
import sys
from cryptography.fernet import Fernet
import typing as tp
from threading import Thread
import time
import pickle
from uuid import uuid4

from database_handler import *

def decrypt_data( decrypt : Fernet , data : bytes ) -> tp.Union[None , bytes ] :
    try :
        return decrypt.decrypt(data)
    except ValueError :
        return None
    except Exception :
        return None

def encrypt_data( encrypt : Fernet , data : bytes ) -> tp.Union[None , bytes ] :
    try :
        return encrypt.decrypt(data)
    except ValueError :
        return None
    except Exception :
        return None

def convert_to_object( data : bytes ) -> tp.Union[ None , object ] :
    try :
        return pickle.loads(data)
    except pickle.UnpicklingError :
        return None
    except Exception :
        return None

def convert_to_bytes( data : object ) -> tp.Union[ None , bytes ] :
    try :
        return pickle.dumps(data)
    except pickle.PicklingError :
        return None
    except Exception :
        return None

def send(client : socket.socket , data : bytes ) -> bool :
    try :
        client.sendall(data)
    except socket.error as e :
        print(f'[ ! ] Cant send : {e}')
        return False
    except Exception as e :
        print(f'[ ! ] Cant send : {e}')
        return False
    return True

def recieve(client : socket.socket , byte = 1024) -> tp.Union[ bytes , None ] :
    datas : list[bytes , ... ] = []
    try :
        while True :
            data = client.recv(byte)
            if not data :
                break
            datas.append(data)
    except socket.error as e:
        print(f'[ ! ] Cant received : {e}')
        return None
    except Exception as e:
        print(f'[ ! ] Cant received : {e}')
        return None
    return b''.join(datas)

def done_transaction(data : dict , encrypt : Fernet  , client : socket.socket ):
    data = convert_to_bytes(data)
    data = encrypt_data( encrypt, data)
    send(client, data)


class OCEnvelopesMainServer:

    server : socket.socket = None
    ADDR = ('localhost', 45678)
    LISTEN = None

    INFO = { 'server id' : 'makieyot' }
    clients_ids = []
    clients = {'connected': [] , 'verified' : [] , 'processing': [] , 'success': [] , 'failed' : [] , 'not users' : [] }
    accept_users = False
    activities = ( 'log in' , 'sign up' , 'ranking' , 'search' , 'news' , 'send' )
    # connected : ( socket.socket , str )
    # verified : ( Fernet , dict , socket.socket , str )
    # processing : ( Fernet , dict , socket.socket , str )
    # success : str
    # failed : str
    # not users : str

    write_in_database = DatabaseWritingHandler()

    def __init__(self , addr = None , listen = None):
        if addr :
            self.ADDR = addr
        if listen :
            self.LISTEN = listen

    # ----------- Server Attributes -------
    def run(self):
        print(' Run Server '.center(40, '-'))
        self.create_server()
        Thread(target=self.accept_clients).start()
        time.sleep(1)
        Thread(target=self.verifiying_clients).start()
        time.sleep(1)
        Thread(target=self.processing_clients_activity).start()
        time.sleep(1)
        self.write_in_database.run()
        time.sleep(5)
        self.stop()
        sys.exit()

    def stop(self):
        print()
        print(' Close Server '.center(40 , '-'))
        print('\n[ ! ] Clossing the activities ')
        self.accept_users = False
        print(f'[ ? ] Connected : {len(self.clients["connected"])}')
        while self.clients['connected'] :
            pass
        time.sleep(1)
        print(f'[ ? ] Verified : {len(self.clients["verified"])}')
        while self.clients['verified']:
            pass
        time.sleep(1)
        print(f'[ ? ] Proccessing : {len(self.clients["processing"])}')
        while self.clients['processing']:
            pass
        self.server.close()
        print('[ / ] Done closing the network ')
        self.write_in_database.stop()

    def processing_clients_activity(self):
        print('[ / ] Server is processing clients')
        while True:
            if self.clients['processing']:
                client = self.clients['verified'].pop()
                self.clients['processing'].append(client)
                Thread(target=self.process_client_activity , args=(client ,)).start()

    def process_client_activity(self , client : tuple[Fernet , dict , socket.socket , str ]):
        '''
            This where the main activities start
            activities = ( 'log in' , 'sign up' , 'ranking' , 'search' , 'news' , 'send' )
            client[1] = { activity : must be in activities , activity data : data that server need }
            recieved = { result : ( success , error , failed ) , data : ( None , dict , list , tuple ) }
        '''

        # ----> Log In
        if client[1]['activity'] == self.activities[0] :
            # activity data : ( username , password )
            user_datas = findTheUser( client[1]['activity data'][0] , client[1]['activity data'][1] )
            if not user_datas :
                data = { 'result' : 'error' , 'data' : None }
            else :
                data = { 'result' : 'success' , 'data' : user_datas }
            # recieved : id , server id , user id , username , password , sent , recieved , filename , number of activity
            done_transaction( data , client[0] , client[2] )

            # do the activity needed in the database

        # ----> Sign Up
        elif client[1]['activity'] == self.activities[1]:
            # activity data : ( username , password )
            user_datas = findTheUserByUsername( client[1]['activity data'][0] )
            if user_datas :
                data = { 'result' : 'error' , 'data' : None }
            else :
                user_datas = ( self.INFO['server id'], uuid4(),
                               client[1]['activity data'][0] , client[1]['activity data'][1] ,
                               0 , 0 ,
                               f'{uuid4()}.db' , 0
                            )
                data = { 'result' : 'success' , 'data' : user_datas }
            # recieved : id , server id , user id , username , password , sent , recieved , filename , number of activity
            done_transaction( data , client[0] , client[2] )

            # do the activity needed in the database

        # ----> Ranking
        elif client[1]['activity'] == self.activities[2]:
            # activity data : str
            ranking_data = [ [] , [] ]
            ranking_data[0] = findHighestRecieved()
            ranking_data[1] = findHighestSent()
            data = {'result' : 'success' , 'data' : ranking_data }
            # recieved : list[ ( rank : int , username : str )  ]
            done_transaction( data , client[0] , client[2] )

            # do the activity needed in the database


        # ----> Search
        elif client[1]['activity'] == self.activities[3]:
            # activity data : ( username : str , ids : list )
            user_database : tuple = findTheUser( client[1]['username'] , client[1]['password'] )
            if not user_database : # If user is not registered then stop the activities
                data = {'result': 'error', 'data': None}
                done_transaction(data, client[0], client[2])
            filename = user_database[-2]
            found_data = getDataByFind(filename , user_recieved_table ,
                                       client[1]['activity data'][0] , client[1]['activity data'][1]
                                       )
            data = {'result' : 'success' , 'data' : found_data }
            # recieved : tuple[ list[ ids , ... ]  , list[ ( id , nickname , date , message ), ... ] ]
            done_transaction(data , client[0] , client[2])

            # do the activity needed in the database

        # ----> News
        elif client[1]['activity'] == self.activities[4]:
            # activity data : current : int
            user_database: tuple = findTheUser(client[1]['username'], client[1]['password'])
            if not user_database:  # If user is not registered then stop the activities
                data = {'result': 'error', 'data': None}
                done_transaction(data, client[0], client[2])
            filename = user_database[-2]
            newest_recieved = getDataByNewestAdded(filename , user_recieved_table , client[1]['activity data'] )
            data = { 'result' : 'success' , 'data' : newest_recieved }
            done_transaction(data , client[0] , client[2] )

            # do the activity needed in the database

        client[2].close()
        self.clients['processing'].remove(client)




    # ============ Verifiying_ Clients
    def verifiying_clients(self):
        print('[ / ] Server is verifiying clients')
        while True :
            if self.clients['connected'] :
                client = self.clients['connected'].pop()
                Thread( target= self.verifiying_client , args=(client , ) ).start()

    def verifiying_client(self , client : tuple[socket.socket , str] ):
        client_key = recieve(client[0])
        if not client_key :
            self.clients['not users'].append(client[1])
            client[0].close()
            return
        try :
            decrypt = Fernet(client_key)
        except ValueError :
            self.clients['not users'].append(client[1])
            client[0].close()
            return
        except Exception :
            self.clients['not users'].append(client[1])
            client[0].close()
            return

        client_data = recieve(client[0])
        if not client_data :
            self.clients['not users'].append(client[1])
            client[0].close()
            return

        client_data = decrypt_data(decrypt , client_data )
        if not client_data :
            self.clients['not users'].append(client[1])
            client[0].close()
            return

        client_data = convert_to_object(client_data)
        if not client_data :
            self.clients['not users'].append(client[1])
            client[0].close()
            return

        self.clients['processing'].append( ( client_key , client_data , client[0] , client[1] ) )


    # ============ Accepting Clients
    def accept_clients(self):
        print('[ / ] Server is accepting users')
        self.accept_users = True
        while True :
            if self.accept_users:
                try :
                    client = self.server.accept()
                except socket.error as e :
                    print(f'\n[ ! ] Server Error : {e}')
                except Exception :
                    print(f'\n[ ! ] Server Error : {e}')
                else:
                    self.clients['connected'].append(client)

    def create_server(self):
        try :
            self.server = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
            self.server.bind(self.ADDR)
        except socket.error :
            print('[ ! ] Cant create server')
            sys.exit()
        else :
            if self.LISTEN :
                self.server.listen(self.LISTEN)
            else :
                self.server.listen()
            print('[ / ] Server is created')


if __name__ == "__main__":
    test = OCEnvelopesMainServer()
    test.run()