from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

import api.user_repo
from db import create_db_and_tables
from scheduler import init_scheduler

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    init_scheduler()
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(api.user_repo.router)


app.mount("/", StaticFiles(directory="static"), name="static")
