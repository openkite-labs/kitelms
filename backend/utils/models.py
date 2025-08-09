from datetime import datetime

from sqlmodel import Field, SQLModel

from backend.utils.ids import generate_id


class BaseModel(SQLModel):
    id: str = Field(primary_key=True, default_factory=generate_id)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)

