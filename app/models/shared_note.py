from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SharedNote(Base):
    __tablename__ = "shared_notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id"), nullable=False)
    shared_with_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    note: Mapped["Note"] = relationship("Note", back_populates="shared_entries")
    shared_with_user: Mapped["User"] = relationship(
        "User",
        back_populates="shared_notes",
        foreign_keys=[shared_with_user_id],
    )
