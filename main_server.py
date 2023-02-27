
import socket
import typing as tp
import sys
from threading import Thread
import json
from time import sleep


class MainServer:
	
	__slots__  = (
		"server" , "accept" , "clients" ,
		"accept_clients_thread" , "process_activity_thread"
		)
	
	def __init__(self) :
		# Variables
		self.server : socket.socket = None
		self.accept = False
		self.clients = { "accepted" : [] , "process" : [] , "done" : [] , "error" : [] }
		self.accept_clients_thread : Thread = None
		self.process_activity_thread : Thread = None
	
	def save_activity(self , filename : str) -> bool :
		try :
			with open(file=filename , mode="w") as jf :
				json.dump(self.clients , jf)
		except Exception as e :
			print(f"[ ! ] Error accur in saving : {e}")
			return False
		return True
	
	def load_past_activity(self , filename : str ) -> bool :
		try :
			with open(filename , "r") as jf :
				self.clients = json.load(jf)
		except Exception as e :
			print(f"[ ! ] Error accur in loading : {e}")
			return False
		return True
	
	def run(self) :
		# Start Activity
		self.server = self.create_server()
		self.accept_clients_thread = Thread(target=self.accept_clients)
		self.accept_clients_thread.start()
		self.process_activity_thread = Thread(target=self.process_activity )
		self.process_activity_thread.start()
	
	def process_activity(self) :
		print("[ √ ] Server is processing the clients activity")
		while True :
			if self.clients["accepted"] :
				client : tuple[socket.socket , str] = self.clients["accepted"].pop()
				self.clients["process"].append(client)
				Thread(target=self.process_client ,args=(client ,)).start()
	
	def process_client(self , client = tuple[socket.socket , str]) :
		pass
		
		
	def accept_clients(self) :
		print("[ √ ] Server is accepting clients")
		self.accept = True
		while True :
			if self.accept :
				client , addr = self.server.accept()
				self.clients["accepted"].append((client , addr))
	
	def create_server(self , listen = None) -> socket.socket :
		print("[ √ ] Server is created")
		try :
			server = socket.socket( socket.AF_INET , socket.SOCK_STREAM)
			if listen :
				server.listen(listen)
			else :
				server.listen()
		except Exception as e :
			print(f"[ ! ] Can't Create Server : {e}")
			sys.exit()
		return server


if __name__ == "__main__" :
	MainServer().run()
