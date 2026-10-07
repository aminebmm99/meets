from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Participant(Base):
    __tablename__ = "participants"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "meeting_id",
            name="uq_participant_user_meeting"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id"),
    nullable=False,
    index=True
)

    meeting_id: Mapped[int] = mapped_column(
    ForeignKey("meetings.id"),
    nullable=False,
    index=True
)

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="invited"
    )

    user: Mapped["User"] = relationship()

    meeting: Mapped["Meeting"] = relationship()