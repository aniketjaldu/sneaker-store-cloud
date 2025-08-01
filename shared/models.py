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

def query_db(conn, query, params=None):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    result = cursor.fetchall()
    cursor.close()
    return result

def execute_db(conn, query, params=None):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    conn.commit()
    cursor.close()

def close_db(conn):
    conn.close()
