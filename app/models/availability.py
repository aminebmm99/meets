from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Availability(Base):
    __tablename__ = "availabilities"

    __table_args__ = (
        CheckConstraint(
            "start_time < end_time",
            name="ck_availability_start_before_end"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id"),
        nullable=False,
        index=True
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    participant: Mapped["Participant"] = relationship()