from sqlmodel import SQLModel, Field, Text


class Report(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(sa_type=Text)
    date: str
    username: str
    commit_log: str | None = Field(sa_type=Text)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)


class UserRepo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    repo_url: str
    branch: str | None = None


class DailyReportRequest(SQLModel):
    date: str | None = None


class PromptUpdateRequest(SQLModel):
    prompt: str
