import uuid

from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(Text, nullable=True)
    content_type = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)
    file_path = Column(Text, nullable=True)
    file_name = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="new", server_default="new")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
