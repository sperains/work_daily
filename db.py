from typing import Annotated

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Field, Session
from fastapi import Depends


class GitRepo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field( index=True)
    repo_url: str



sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"


connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session



SessionDep = Annotated[Session, Depends(get_session)]
