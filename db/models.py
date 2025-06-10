from sqlmodel import SQLModel, Field, Text


class GitRepo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_url: str
    
    
class Report(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str =  Field(sa_type=Text)
    date: str
    username: str
    commit: str | None


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field( index=True)


class UserRepo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field( index=True)
    repo_url: str


