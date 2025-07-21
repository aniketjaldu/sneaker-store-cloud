import fastapi
import requests

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/users")
def get_user_info():
    response = requests.get("http://localhost:8082/users")
    return response.json()