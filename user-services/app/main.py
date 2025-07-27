import fastapi
from fastapi import HTTPException
from pydantic import BaseModel
import requests
from shared.models import connect_to_db, query_db, close_db

app = fastapi.FastAPI()

# Helper function to connect to db
def connect():
    return connect_to_db("user-db", "root", "userpassword", "user_database")

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

@app.get("/profile")
async def get_user_profile(user_id: int):
    conn = connect()
    query = "SELECT * FROM users WHERE user_id = %s"
    result = query_db(conn, query, (user_id,))
    close_db(conn)
    return result