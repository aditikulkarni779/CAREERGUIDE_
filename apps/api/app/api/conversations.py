"""Conversation endpoints + streaming chat (SSE)."""
from __future__ import annotations

import uuid
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.adapters.db import get_db, new_session
from app.adapters.models import User
from app.agents.orchestrator import get_streamer
from app.api.deps import get_current_user
from app.schemas import ConversationOut, MessageOut, SendMessage
from app.services.conversation_service import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
)

router = APIRouter(prefix="/conversations", tags=["chat"])


@router.get("", response_model=list[ConversationOut])
def list_convos(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ConversationOut]:
    return [ConversationOut.model_validate(c) for c in list_conversations(db, user.id)]


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def new_convo(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ConversationOut:
    return ConversationOut.model_validate(create_conversation(db, user.id))


@router.get("/{conv_id}/messages", response_model=list[MessageOut])
def get_messages(
    conv_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MessageOut]:
    conv = get_conversation(db, user.id, conv_id)
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")
    return [MessageOut.model_validate(m) for m in list_messages(db, conv_id)]


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_convo(
    conv_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not delete_conversation(db, user.id, conv_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")


@router.post("/{conv_id}/messages")
def send_message(
    conv_id: uuid.UUID,
    data: SendMessage,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    conv = get_conversation(db, user.id, conv_id)
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")

    streamer = get_streamer()
    user_id = str(user.id)
    query = data.content

    def event_stream() -> Iterator[str]:
        # Own session so it survives the streaming response lifecycle.
        session = new_session()
        try:
            yield from streamer.stream(session, user_id, conv_id, query)
        finally:
            session.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
