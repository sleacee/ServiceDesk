import psycopg

def get_connection():
    return psycopg.connect(
        host="localhost",
        port=5432,
        dbname="servicedesk",
        user="postgres",
        password="12345678"
    )