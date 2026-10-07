from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SchedulingRequest(Base):
    __tablename__ = "scheduling_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    meeting_id: Mapped[int] = mapped_column(
    ForeignKey("meetings.id"),
    nullable=False,
    index=True
)

    created_by: Mapped[int] = mapped_column(
    ForeignKey("users.id"),
    nullable=False,
    index=True
)

    status: Mapped[str] = mapped_column(
    String(50),
    nullable=False,
    default="pending"
)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    meeting: Mapped["Meeting"] = relationship()

    creator: Mapped["User"] = relationship()