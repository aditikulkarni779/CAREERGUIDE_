"""Conversation and message persistence."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.models import Conversation, Message, MessageRole


def create_conversation(db: Session, user_id: uuid.UUID, title: str = "New chat") -> Conversation:
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def list_conversations(db: Session, user_id: uuid.UUID) -> list[Conversation]:
    return list(
        db.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        )
    )


def get_conversation(
    db: Session, user_id: uuid.UUID, conv_id: uuid.UUID
) -> Conversation | None:
    return db.scalar(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user_id
        )
    )


def list_messages(db: Session, conv_id: uuid.UUID) -> list[Message]:
    return list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at.asc())
        )
    )


def add_message(
    db: Session,
    conv_id: uuid.UUID,
    role: MessageRole,
    content: str,
    citations: list[Any] | None = None,
    agent_trace: list[Any] | None = None,
) -> Message:
    msg = Message(
        conversation_id=conv_id,
        role=role,
        content=content,
        citations=citations or [],
        agent_trace=agent_trace or [],
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def delete_conversation(db: Session, user_id: uuid.UUID, conv_id: uuid.UUID) -> bool:
    conv = get_conversation(db, user_id, conv_id)
    if conv is None:
        return False
    db.delete(conv)
    db.commit()
    return True
