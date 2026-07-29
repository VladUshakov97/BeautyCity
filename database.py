import psycopg2

conn = psycopg2.connect(
	host='localhost',
	port=5432,
	database='beauty_base',
	user='postgres',
	password='12345678'
)

cursor = conn.cursor()

print('Подключение успешно')