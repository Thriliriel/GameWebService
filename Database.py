import psycopg2
import os

class Database():
	#connection
	conn = None

	def ConnectDB(self):
		self.conn = psycopg2.connect(host="localhost",
								database="galdur",
								user="postgres",
								password="postgres")
		
		#heroku
		#DATABASE_URL = os.environ.get('DATABASE_URL')
		#self.conn = psycopg2.connect(DATABASE_URL)

	def DisconnectDB(self):
		#need to see how to do it
		i = 0
		
		#heroku
		#DATABASE_URL = os.environ.get('DATABASE_URL')
		#self.conn = psycopg2.connect(DATABASE_URL)
			
	def InsertDatabase(self, table, fields, values, returnField = "id"):
		#check conection first
		if self.conn == None:
			print("No connection!!")
			return

		#assemble the sql string
		sql = "INSERT INTO public." + table + "("

		#for each field...
		i = 0
		for field in fields:
			if i == 0:
				sql += str(field)
			else:
				sql += ", " + str(field)

			i += 1

		sql += ") VALUES ("
		#for each value...
		i = 0
		for value in values:
			if i == 0:
				sql += str(value)
			else:
				sql += ", " + str(value)

			i += 1

		sql += ")"

		#return field
		sql += " RETURNING " + returnField

		print (sql)
		cursor = self.conn.cursor()
		cursor.execute(sql)
		self.conn.commit()

		#get last id
		data = cursor.fetchone()

		cursor.close()
		
		#return last id inserted
		return data[0]

	def LoadDatabase(self, what, table, condition = ""):
		#check conection first
		if self.conn == None:
			print("No connection!!")
			return

		#assemble the sql string
		sql = "SELECT "

		#what is to be selected?
		#if it is all, just include
		if "*" in what:
			sql += "*"
		#otherwise, attach the values
		else:
			i = 0
			for field in what:
				if i == 0:
					sql += str(field)
				else:
					sql += ", " + str(field)

				i += 1

		sql += " FROM public." + table
		
		#if we have condition, add it
		if condition != "":
			sql += " WHERE " + condition
		
		#print (sql)
		cursor = self.conn.cursor()
		cursor.execute(sql)
		self.conn.commit()
		myresult = cursor.fetchall()

		#print(myresult)

		cursor.close()
		
		return myresult

	def DeleteDatabase(self, table, condition = ""):
		#check conection first
		if self.conn == None:
			print("No connection!!")
			return

		sql = "DELETE from public." + table

		#if condition, add
		if condition != "":
			sql += " WHERE " + condition

		cursor = self.conn.cursor()
		cursor.execute(sql)
		self.conn.commit()
		cursor.close()