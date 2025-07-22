import fastapi
from shared.models import connect_to_db, query_db, close_db

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/users")
def get_user_info():
    conn = connect_to_db("user-db", "root", "userpassword", "user_database")
    query = f"SELECT * FROM users"
    result = query_db(conn, query)
    close_db(conn)
    return result