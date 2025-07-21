import fastapi
import requests

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/users")
def get_user_info():
    response = requests.get("http://user-service:8080/users")
    return response.json()