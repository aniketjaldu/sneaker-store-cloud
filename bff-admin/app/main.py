import fastapi
import requests

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
