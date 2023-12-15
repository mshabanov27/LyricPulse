from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import pages, recognition, database, history, user, login, admin
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

app.include_router(pages.router)
app.include_router(database.router)
app.include_router(recognition.router)
app.include_router(history.router)
app.include_router(user.router)
app.include_router(login.router)
app.include_router(admin.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
