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

	#puts the player in the matchmaking room
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
						#starting player. Always the first player who entered matchmaking. We can random it later.
						startPlayer = idPlayer1

						#insert into game
						idGame = database.InsertDatabase("game", ["player1", "player2", "startplayer"], [idPlayer1, idPlayer, startPlayer])

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

	#checks if the player waiting for a game already got a match
	@cherrypy.expose
	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def checkMM(self):
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
			#checks if a game was already started with this fella
			playing = database.LoadDatabase(["id"], "game", "player1 = " + str(idPlayer) + " or player2 = " + str(idPlayer))

			#just not, ok.
			if len(playing) == 0:
				output = [2, "Player already waiting for match!"]
			#if player already in a match, need to redirect him on the app
			else:
				idMatch = playing[0][0]
				output = [42, idMatch]
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

	#gets the information of a game, back to the client
	@cherrypy.expose
	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def checkGame(self):
		"""Handle HTTP requests against ``/tokenize`` URI."""
		if cherrypy.request.method == 'OPTIONS':
		#	# This is a request that browser sends in CORS prior to
		#	# sending a real request.

		#	# Set up extra headers for a pre-flight OPTIONS request.
			return cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])
		
		#check auth token
		if not self.checkauth():
			return [1, "Auth Error!"]

		#id of the game comes as param
		data = cherrypy.request.json
		#print(data)
		df = pd.DataFrame(data)
		idGame = int(df["idGame"][0])

		#print(idPlayer)

		#return value
		output = []

		#connect to database
		database.ConnectDB()

		#before anything, checks if this game actually exists
		gameExists = database.LoadDatabase(["id","player1","player2","extract('epoch' from starttime)","startplayer"], "game", "id = " + str(idGame))

		#just keep going if game exists
		if len(gameExists) == 1:
			#return all the information about the game
			output = [42, gameExists[0][0], gameExists[0][1], gameExists[0][2], gameExists[0][3], gameExists[0][4]]
		#if game does not exist, warning
		else:
			output = [8, "Game does not exist!"]

		#disconnect from database
		database.DisconnectDB()
		#output.show()
		
		gc.collect()

		#format the return
		output = pd.DataFrame(output)
		return output.to_json()

	#register a new player
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

	#player login, check if exists in the database and if data provided is correct
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

		#print(user, password)

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

	#cancel the matchmaking of the player
	@cherrypy.expose
	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def cancelMatchMaking(self):
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
		idPlayer = df["idPlayer"][0]

		#return value
		output = []

		#connect to database
		database.ConnectDB()

		#before anything, checks if this player actually exists
		playerExists = database.LoadDatabase(["id"], "player", "id = " + str(idPlayer))

		#just keep going if player exists
		if len(playerExists) == 1:
			#check if user is really waiting for a match
			waiting = database.LoadDatabase(["id"], "matchmaking", "player1 = " + str(idPlayer) + " or player2 = " + str(idPlayer))
		
			#if waiting is an empty list, the player is not there...
			if len(waiting) == 0:
				output = [7, "Player not waiting for a match!"]
			#else, we take the player out of there
			else:
				database.DeleteDatabase("matchmaking", "player1 = " + str(idPlayer) + " or player2 = " + str(idPlayer))
				output = [42, "Player removed from the queue!"]
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

	#all the initial inserts, to keep database integrity with the files
	@cherrypy.expose
	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def dataInserts(self):
		"""Handle HTTP requests against ``/tokenize`` URI."""
		if cherrypy.request.method == 'OPTIONS':
		#	# This is a request that browser sends in CORS prior to
		#	# sending a real request.

		#	# Set up extra headers for a pre-flight OPTIONS request.
			return cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])

		#check auth token
		if not self.checkauth():
			return [1, "Auth Error!"]

		#gameClass comes as param
		data = cherrypy.request.json
		#print(data['gameClass']['allRaces'])
		#df = pd.DataFrame(data)
		#idPlayer = df["idPlayer"][0]

		#return value
		output = [42, "Done!"]

		#connect to database
		database.ConnectDB()
		
		#insert all initial stuff
		#race
		for race in data['gameClass']['allRaces']:
			database.InsertDatabase("race", ["id", "name"], [int(race['id']), "'"+race['name']+"'"])
		#end race

		#vocation
		for vocation in data['gameClass']['allVocations']:
			database.InsertDatabase("vocation", ["id", "name"], [int(vocation['id']), "'"+vocation['name']+"'"])
		#end vocation

		#heroes
		for hero in data['gameClass']['allHeroes']:
			database.InsertDatabase("hero", ["id", "name"], [int(hero['id']), "'"+hero['name']+"'"])
		#end heroes

		#general effects
		for ge in data['gameClass']['allGeneralEffects']:
			database.InsertDatabase("generaleffect", ["id", "name"], [int(ge['id']), "'"+ge['name']+"'"])
		#end heroes

		#all cards
		for card in data['gameClass']['allCards']:
			database.InsertDatabase("card", ["id", "name"], [int(card['id']), "'"+card['name']+"'"])
		#end all cards
		#end insert all initial stuff

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
#player not found in matchmaking: 7
#game does not exists: 8

#running:
#matchmaking: 
#curl -d "{\"idPlayer\" : [1]}" -H "Content-Type: application/json" -X POST http://localhost:5000/matchmaking