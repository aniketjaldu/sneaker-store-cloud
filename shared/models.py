import mysql.connector

def connect_to_db(host, user, password, database, port):
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        autocommit=True
    )

def query_db(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

def close_db(conn):
    conn.close()