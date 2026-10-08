from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base



class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    organizer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
    String(50),
    nullable=False,
    default="open"
)

    scheduled_start: Mapped[Optional[datetime]] = mapped_column(
    DateTime,
    nullable=True
    )

    scheduled_end: Mapped[Optional[datetime]] = mapped_column(
    DateTime,
    nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    organizer: Mapped["User"] = relationship(
        foreign_keys=[organizer_id]
    )

    organization: Mapped["Organization"] = relationship(
        foreign_keys=[organization_id]
    )