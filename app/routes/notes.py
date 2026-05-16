from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.note import Note, NoteVersion
from app.models.shared_note import SharedNote
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
    NoteVersionResponse,
    PinResponse,
    ShareNoteRequest,
)

router = APIRouter(prefix="/notes", tags=["notes"])


def _get_note_or_404(note_id: int, db: Session) -> Note:
    note = db.query(Note).filter(Note.id == note_id).first()
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    return note


def _is_owner(note: Note, user: User) -> bool:
    return note.owner_id == user.id


def _has_shared_access(note: Note, user: User, db: Session) -> bool:
    shared = (
        db.query(SharedNote)
        .filter(
            SharedNote.note_id == note.id,
            SharedNote.shared_with_user_id == user.id,
        )
        .first()
    )
    return shared is not None


def _can_read(note: Note, user: User, db: Session) -> bool:
    return _is_owner(note, user) or _has_shared_access(note, user, db)


@router.get("", response_model=list[NoteResponse])
def list_notes(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve notes owned by or shared with the authenticated user with pagination.
    """
    # Get all accessible note IDs first to handle pagination correctly across owned and shared
    owned_note_ids = [r[0] for r in db.query(Note.id).filter(Note.owner_id == current_user.id).all()]
    shared_note_ids = [r[0] for r in db.query(SharedNote.note_id).filter(SharedNote.shared_with_user_id == current_user.id).all()]
    
    all_accessible_ids = list(set(owned_note_ids + shared_note_ids))
    
    notes = (
        db.query(Note)
        .filter(Note.id.in_(all_accessible_ids))
        .order_by(Note.is_pinned.desc(), Note.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    ) if all_accessible_ids else []
    
    return notes


@router.get("/search", response_model=list[NoteResponse])
def search_notes(
    q: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search notes by title or content with pagination.
    Pinned notes are prioritized in results.
    """
    if not q.strip():
        return []

    # Get all accessible note IDs
    owned_note_ids = [r[0] for r in db.query(Note.id).filter(Note.owner_id == current_user.id).all()]
    shared_note_ids = [r[0] for r in db.query(SharedNote.note_id).filter(SharedNote.shared_with_user_id == current_user.id).all()]
    all_accessible_ids = list(set(owned_note_ids + shared_note_ids))

    if not all_accessible_ids:
        return []

    search_query = f"%{q.strip()}%"
    notes = (
        db.query(Note)
        .filter(Note.id.in_(all_accessible_ids))
        .filter(
            (Note.title.ilike(search_query)) | 
            (Note.content.ilike(search_query))
        )
        .order_by(Note.is_pinned.desc(), Note.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notes


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific note by its ID. 
    Requires ownership or shared access.
    """
    note = _get_note_or_404(note_id, db)
    if not _can_read(note, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this note",
        )
    return note


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new note for the authenticated user.
    """
    note = Note(
        title=payload.title.strip(),
        content=payload.content.strip(),
        owner_id=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing note. Only the owner can modify the content.
    """
    note = _get_note_or_404(note_id, db)
    if not _is_owner(note, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this note",
        )

    # Save current state as a version before updating
    version_number = db.query(NoteVersion).filter(NoteVersion.note_id == note.id).count() + 1
    history_version = NoteVersion(
        note_id=note.id,
        version_number=version_number,
        title=note.title,
        content=note.content,
        created_at=note.updated_at,
    )
    db.add(history_version)

    note.title = payload.title.strip()
    note.content = payload.content.strip()
    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note


@router.patch("/{note_id}/pin", response_model=PinResponse)
def toggle_pin_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Toggle the pinned status of a note. Only the owner can pin/unpin.
    """
    note = _get_note_or_404(note_id, db)
    if not _is_owner(note, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pin this note",
        )

    note.is_pinned = not note.is_pinned
    db.commit()
    db.refresh(note)
    return PinResponse(
        message="Note pin status updated",
        is_pinned=note.is_pinned,
    )


@router.get("/{note_id}/history", response_model=list[NoteVersionResponse])
def get_note_history(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the version history for a specific note. Only the owner can access.
    """
    note = _get_note_or_404(note_id, db)
    if not _is_owner(note, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access history for this note",
        )

    versions = (
        db.query(NoteVersion)
        .filter(NoteVersion.note_id == note.id)
        .order_by(NoteVersion.version_number.desc())
        .all()
    )
    return versions


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete a note. Only the owner can perform this action.
    """
    note = _get_note_or_404(note_id, db)
    if not _is_owner(note, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this note",
        )

    db.delete(note)
    db.commit()
    return None


@router.post("/{note_id}/share", response_model=MessageResponse)
def share_note(
    note_id: int,
    payload: ShareNoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Share a note with another user by their email address.
    """
    note = _get_note_or_404(note_id, db)
    if not _is_owner(note, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to share this note",
        )

    target_user = db.query(User).filter(User.email == payload.share_with_email).first()
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share note with yourself",
        )

    existing_share = (
        db.query(SharedNote)
        .filter(
            SharedNote.note_id == note.id,
            SharedNote.shared_with_user_id == target_user.id,
        )
        .first()
    )
    if existing_share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note already shared with this user",
        )

    shared = SharedNote(note_id=note.id, shared_with_user_id=target_user.id)
    db.add(shared)
    db.commit()

    return MessageResponse(message="Note shared successfully")
