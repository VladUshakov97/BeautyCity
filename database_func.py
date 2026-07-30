import psycopg2


def connect_to_database():
	conn = psycopg2.connect(
		host='localhost',
		port=5432,
		database='beauty_base',
		user='postgres',
		password='12345678'
	)

	cursor = conn.cursor()

	return conn, cursor