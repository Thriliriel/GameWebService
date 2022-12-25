import cherrypy
import pandas as pd
import os
import gc
from Database import Database
from datetime import datetime
import pandas as pd
import hashlib

import cherrypy_cors

#cherrypy.config.update({'server.socket_port': 5000})

database = Database()

class RestGaldur(object):
	def checkauth(self):
		auth = cherrypy.request.headers['Authorization']
		#if equal "rendervouz", it is the correct one
		#TODO: create a better auth
		if auth != "rendervouz":
			return False
		else:
			return True

	@cherrypy.expose
	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def matchmaking(self):
		"""Handle HTTP requests against ``/tokenize`` URI."""
		if cherrypy.request.method == 'OPTIONS':
		#	# This is a request that browser sends in CORS prior to
		#	# sending a real request.

		#	# Set up extra headers for a pre-flight OPTIONS request.
			return cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])
		
		#check auth token
		if not self.checkauth():
			return [1, "Auth Error!"]

		#id of the player comes as param
		data = cherrypy.request.json
		#print(data)
		df = pd.DataFrame(data)
		idPlayer = int(df["idPlayer"][0])

		#print(idPlayer)

		#return value
		output = []

		#connect to database
		database.ConnectDB()

		#before anything, checks if this player actually exists
		playerExists = database.LoadDatabase(["id"], "player", "id = " + str(idPlayer))

		#just keep going if player exists
		if len(playerExists) == 1:
			#before trying to start a match, check if this player is not already playing
			playing = database.LoadDatabase(["id"], "game", "player1 = " + str(idPlayer) + " or player2 = " + str(idPlayer))

			#just keep going if not
			if len(playing) == 0:
				#before inserting into a new matchmaking, we need to check if there is already someone waiting
				waiting = database.LoadDatabase(["id", "player1"], "matchmaking")
		
				#if waiting is an empty list, there is no one waiting, so we can insert
				if len(waiting) == 0:
					database.InsertDatabase("matchmaking", ["player1"], [idPlayer])

					#waiting for game
					output = [42, "Waiting for game..."]
				#else, there is aleady someone waiting to play. Get the player who is waiting, insert both into game and delete from matchmaking
				else:
					idMatch = waiting[0][0]
					idPlayer1 = waiting[0][1]
					#Check if it is not the same player... just keep going if different players
					if idPlayer != idPlayer1:
						#insert into game
						idGame = database.InsertDatabase("game", ["player1", "player2"], [idPlayer1, idPlayer])

						#delete from matchmaking
						database.DeleteDatabase("matchmaking", "id = " + str(idMatch))

						#return the game id
						output = [42, idGame]
					#else, player already waiting, warning
					else:
						output = [2, "Player already waiting for match!"]

			#if player already in a match, warning
			else:
				output = [3, "Player already in a match!"]
		#if player does not exist, warning
		else:
			output = [5, "Player does not exist!"]

		#disconnect from database
		database.DisconnectDB()
		#output.show()
		
		gc.collect()

		#format the return
		output = pd.DataFrame(output)
		return output.to_json()

	@cherrypy.expose
	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def signup(self):
		"""Handle HTTP requests against ``/tokenize`` URI."""
		if cherrypy.request.method == 'OPTIONS':
		#	# This is a request that browser sends in CORS prior to
		#	# sending a real request.

		#	# Set up extra headers for a pre-flight OPTIONS request.
			return cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])

		#check auth token
		if not self.checkauth():
			return [1, "Auth Error!"]

		#player info comes as param
		data = cherrypy.request.json
		#print(data)
		df = pd.DataFrame(data)
		email = df["email"][0]
		user = df["user"][0]
		password = df["password"][0]

		#print(email, user, password)

		#return value
		output = []

		#connect to database
		database.ConnectDB()

		#before anything, checks if this player actually exists
		playerExists = database.LoadDatabase(["id"], "player", "email =	'" + str(email) + "'")

		#just keep going if player does not exists
		if len(playerExists) == 0:
			#insert new player
			md5hash = hashlib.md5(password.encode())
			idPlayer = database.InsertDatabase("player", ["email", "name", "password"], ["'"+email+"'", "'"+user+"'", "'"+md5hash.hexdigest()+"'"])

			#return the new player id
			output = [42, idPlayer]
		#if player exist, cant register again
		else:
			output = [4, "Player already exists!"]

		#disconnect from database
		database.DisconnectDB()
		#output.show()
		
		gc.collect()

		#format the return
		output = pd.DataFrame(output)
		return output.to_json()

	@cherrypy.expose
	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def login(self):
		"""Handle HTTP requests against ``/tokenize`` URI."""
		if cherrypy.request.method == 'OPTIONS':
		#	# This is a request that browser sends in CORS prior to
		#	# sending a real request.

		#	# Set up extra headers for a pre-flight OPTIONS request.
			return cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])

		#check auth token
		if not self.checkauth():
			return [1, "Auth Error!"]

		#player info comes as param
		data = cherrypy.request.json
		#print(data)
		df = pd.DataFrame(data)
		user = df["user"][0]
		password = df["password"][0]

		print(user, password)

		#return value
		output = []

		#connect to database
		database.ConnectDB()

		#before anything, checks if this player actually exists
		playerExists = database.LoadDatabase(["id"], "player", "name =	'" + str(user) + "'")

		#just keep going if player exists
		if len(playerExists) == 1:
			#check if user and password are ok
			md5hash = hashlib.md5(password.encode())
			logPlayer = database.LoadDatabase(["id", "name"], "player", "name =	'" + str(user) + "' AND password = '" +md5hash.hexdigest()+"'")

			#if found, return the id
			if len(logPlayer) > 0:
				idPlayer = logPlayer[0][0]
				namePlayer = logPlayer[0][1]
				output = [42, idPlayer, namePlayer]
			#else, password must be wrong
			else:
				output = [6, "Wrong password. Try again!"]			
		#if player does not exist, cant login
		else:
			output = [5, "Player does not exists!"]

		#disconnect from database
		database.DisconnectDB()
		#output.show()
		
		gc.collect()

		#format the return
		output = pd.DataFrame(output)
		return output.to_json()

if __name__ == '__main__':
	cherrypy_cors.install()
	config = {'tools.sessions.timeout': 60, 'server.socket_host': '0.0.0.0', 'server.socket_port': int(os.environ.get('PORT', 5000)), 'cors.expose.on': True} #, 'cors.expose.on': True
	cherrypy.config.update(config)
	cherrypy.quickstart(RestGaldur())

#quick documentation of warnings and errors:
#any sucess: 42
#auth api error: 1
#player already waiting for match: 2
#player does not exists: 5
#player already in a game: 3
#player already exists: 4
#wrong password: 6

#running:
#matchmaking: 
#curl -d "{\"idPlayer\" : [1]}" -H "Content-Type: application/json" -X POST http://localhost:5000/matchmaking