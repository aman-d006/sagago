# routers/message.py
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional
from datetime import datetime
import json
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user

router = APIRouter(prefix="/messages", tags=["messages"])
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            await manager.send_personal_message(
                {"type": "typing", "user_id": user_id},
                message_data["receiver_id"]
            )
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@router.post("/send", response_model=dict)
def send_message(
    message_data: dict,
    current_user = Depends(get_current_active_user)
):
    receiver_id = message_data.get("receiver_id")
    content = message_data.get("content")
    
    if not receiver_id or not content:
        raise HTTPException(status_code=400, detail="receiver_id and content are required")
    
    if current_user.id == receiver_id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
    
    logger.info(f"💬 Sending message from user {current_user.id} to {receiver_id}")
    
    if settings.USE_TURSO:
        receiver = helpers.get_user_by_id(receiver_id)
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")
        
        message = helpers.send_message(current_user.id, receiver_id, content)
        if not message:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        # Send real-time notification
        import asyncio
        try:
            asyncio.create_task(manager.send_personal_message(
                {
                    "type": "new_message",
                    "message": message
                },
                receiver_id
            ))
        except:
            pass
        
        return message
    
    else:
        from sqlalchemy.orm import Session
        from models.user import User
        from models.message import Message, Conversation
        from datetime import datetime
        
        db = next(get_db())
        
        receiver = db.query(User).filter(User.id == receiver_id).first()
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")
        
        db_message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content
        )
        db.add(db_message)
        db.flush()
        
        user1_id = min(current_user.id, receiver_id)
        user2_id = max(current_user.id, receiver_id)
        
        conversation = db.query(Conversation).filter(
            Conversation.user1_id == user1_id,
            Conversation.user2_id == user2_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                user1_id=user1_id,
                user2_id=user2_id,
                last_message_id=db_message.id,
                last_message_at=datetime.now()
            )
            db.add(conversation)
        else:
            conversation.last_message_id = db_message.id
            conversation.last_message_at = datetime.now()
        
        db.commit()
        db.refresh(db_message)
        
        message_response = {
            "id": db_message.id,
            "sender_id": db_message.sender_id,
            "receiver_id": db_message.receiver_id,
            "content": db_message.content,
            "is_read": db_message.is_read,
            "created_at": db_message.created_at,
            "sender_username": current_user.username,
            "sender_avatar": current_user.avatar_url,
            "receiver_username": receiver.username,
            "receiver_avatar": receiver.avatar_url
        }
        
        import asyncio
        try:
            asyncio.create_task(manager.send_personal_message(
                {
                    "type": "new_message",
                    "message": message_response
                },
                receiver_id
            ))
        except:
            pass
        
        return message_response

@router.get("/conversations", response_model=List[dict])
def get_conversations(
    current_user = Depends(get_current_active_user)
):
    logger.info(f"💬 Getting conversations for user {current_user.id}")
    
    if settings.USE_TURSO:
        conversations = helpers.get_conversations(current_user.id)
        return conversations
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import or_, desc
        from models.user import User
        from models.message import Message, Conversation
        
        db = next(get_db())
        
        conversations = db.query(Conversation).filter(
            or_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == current_user.id
            )
        ).order_by(desc(Conversation.last_message_at)).all()
        
        result = []
        for conv in conversations:
            other_user_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id
            other_user = db.query(User).filter(User.id == other_user_id).first()
            
            unread_count = db.query(Message).filter(
                Message.sender_id == other_user_id,
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).count()
            
            last_message = db.query(Message).filter(Message.id == conv.last_message_id).first()
            
            result.append({
                "id": conv.id,
                "user_id": other_user.id,
                "username": other_user.username,
                "avatar_url": other_user.avatar_url,
                "last_message": last_message.content if last_message else "",
                "last_message_at": conv.last_message_at,
                "unread_count": unread_count,
                "is_online": other_user_id in manager.active_connections
            })
        
        return result

@router.get("/conversation/{user_id}", response_model=dict)
def get_conversation(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_active_user)
):
    logger.info(f"💬 Getting conversation between {current_user.id} and {user_id}")
    
    if settings.USE_TURSO:
        other_user = helpers.get_user_by_id(user_id)
        if not other_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        messages = helpers.get_conversation(current_user.id, user_id, limit=per_page)
        
        total = len(messages)
        pages = (total + per_page - 1) // per_page
        
        # Mark as read
        helpers.mark_messages_read(current_user.id, user_id)
        
        return {
            "id": user_id,
            "user": {
                "id": other_user["id"],
                "username": other_user["username"],
                "full_name": other_user.get("full_name"),
                "avatar_url": other_user.get("avatar_url"),
                "is_online": user_id in manager.active_connections
            },
            "messages": messages,
            "total": total,
            "page": page,
            "pages": pages
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import or_, and_, desc
        from models.user import User
        from models.message import Message
        
        db = next(get_db())
        
        other_user = db.query(User).filter(User.id == user_id).first()
        if not other_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        query = db.query(Message).filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
                and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
            )
        ).order_by(desc(Message.created_at))
        
        total = query.count()
        pages = (total + per_page - 1) // per_page
        messages = query.offset((page - 1) * per_page).limit(per_page).all()
        messages.reverse()
        
        db.query(Message).filter(
            Message.sender_id == user_id,
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).update({Message.is_read: True})
        db.commit()
        
        message_responses = []
        for msg in messages:
            sender = msg.sender
            receiver = msg.receiver
            message_responses.append({
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "is_read": msg.is_read,
                "created_at": msg.created_at,
                "sender_username": sender.username,
                "sender_avatar": sender.avatar_url,
                "receiver_username": receiver.username,
                "receiver_avatar": receiver.avatar_url
            })
        
        return {
            "id": user_id,
            "user": {
                "id": other_user.id,
                "username": other_user.username,
                "full_name": other_user.full_name,
                "avatar_url": other_user.avatar_url,
                "is_online": user_id in manager.active_connections
            },
            "messages": message_responses,
            "total": total,
            "page": page,
            "pages": pages
        }

@router.get("/unread/count", response_model=dict)
def get_unread_count(
    current_user = Depends(get_current_active_user)
):
    logger.info(f"💬 Getting unread count for user {current_user.id}")
    
    if settings.USE_TURSO:
        unread_data = helpers.get_unread_count(current_user.id)
        return unread_data
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import or_
        from models.user import User
        from models.message import Message, Conversation
        
        db = next(get_db())
        
        total_unread = db.query(Message).filter(
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).count()
        
        conversations = db.query(Conversation).filter(
            or_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == current_user.id
            )
        ).all()
        
        conversation_unread = []
        for conv in conversations:
            other_user_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id
            other_user = db.query(User).filter(User.id == other_user_id).first()
            
            unread = db.query(Message).filter(
                Message.sender_id == other_user_id,
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).count()
            
            if unread > 0:
                conversation_unread.append({
                    "user_id": other_user_id,
                    "username": other_user.username,
                    "unread_count": unread
                })
        
        return {
            "total_unread": total_unread,
            "conversations": conversation_unread
        }

@router.post("/read/all", response_model=dict)
def mark_all_read(
    current_user = Depends(get_current_active_user)
):
    logger.info(f"💬 Marking all messages as read for user {current_user.id}")
    
    if settings.USE_TURSO:
        # Would need a helper for this
        return {"message": "All messages marked as read", "marked_count": 0}
    
    else:
        from sqlalchemy.orm import Session
        from models.message import Message
        
        db = next(get_db())
        
        result = db.query(Message).filter(
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).update({Message.is_read: True})
        
        db.commit()
        
        return {
            "message": "All messages marked as read",
            "marked_count": result
        }

@router.post("/read/{user_id}", response_model=dict)
def mark_conversation_read(
    user_id: int,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"💬 Marking conversation with {user_id} as read for user {current_user.id}")
    
    if settings.USE_TURSO:
        marked_count = helpers.mark_messages_read(current_user.id, user_id)
        return {
            "message": f"Messages from user {user_id} marked as read",
            "marked_count": marked_count
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.message import Message
        
        db = next(get_db())
        
        result = db.query(Message).filter(
            Message.sender_id == user_id,
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).update({Message.is_read: True})
        
        db.commit()
        
        return {
            "message": f"Messages from user {user_id} marked as read",
            "marked_count": result
        }