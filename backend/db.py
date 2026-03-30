import psycopg2

conn = psycopg2.connect(
    dbname="doctor_ai",
    user="postgres",
    password="",
    host="localhost",
    port="5432"
)

def get_cursor():
    return conn.cursor()

