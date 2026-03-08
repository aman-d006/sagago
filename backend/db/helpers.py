import logging
from typing import Optional, List, Any, Dict
from datetime import datetime
import json

from db.database import get_turso_client, settings

logger = logging.getLogger(__name__)

def get_value(cell):
    if cell is None:
        return None
    if isinstance(cell, dict):
        return cell.get('value')
    return cell

def get_user_by_id(user_id: int) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            escaped_id = str(user_id)
            sql = f"SELECT id, username, email, full_name, bio, avatar_url, is_active, created_at FROM users WHERE id = {escaped_id}"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "email": get_value(row[2]),
                    "full_name": get_value(row[3]),
                    "bio": get_value(row[4]),
                    "avatar_url": get_value(row[5]),
                    "is_active": bool(int(get_value(row[6]))) if get_value(row[6]) else False,
                    "created_at": get_value(row[7])
                }
            return None
    except Exception as e:
        logger.error(f"Error in get_user_by_id: {e}")
        return None

def get_user_by_username(username: str) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            escaped_username = username.replace("'", "''")
            sql = f"SELECT id, username, email, full_name, bio, avatar_url, password_hash, is_active, created_at FROM users WHERE username = '{escaped_username}'"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "email": get_value(row[2]),
                    "full_name": get_value(row[3]),
                    "bio": get_value(row[4]),
                    "avatar_url": get_value(row[5]),
                    "password_hash": get_value(row[6]),
                    "is_active": bool(int(get_value(row[7]))) if get_value(row[7]) else False,
                    "created_at": get_value(row[8])
                }
            return None
    except Exception as e:
        logger.error(f"Error in get_user_by_username: {e}")
        return None

def get_user_by_email(email: str) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            escaped_email = email.replace("'", "''")
            sql = f"SELECT id, username, email, full_name, bio, avatar_url, password_hash, is_active, created_at FROM users WHERE email = '{escaped_email}'"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "email": get_value(row[2]),
                    "full_name": get_value(row[3]),
                    "bio": get_value(row[4]),
                    "avatar_url": get_value(row[5]),
                    "password_hash": get_value(row[6]),
                    "is_active": bool(int(get_value(row[7]))) if get_value(row[7]) else False,
                    "created_at": get_value(row[8])
                }
            return None
    except Exception as e:
        logger.error(f"Error in get_user_by_email: {e}")
        return None

def create_user(user_data: dict) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            existing = client.query_one(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                [user_data['username'], user_data['email']]
            )
            if existing:
                return None
            
            def escape_string(s):
                return s.replace("'", "''")
            
            username = escape_string(user_data['username'])
            email = escape_string(user_data['email'])
            password_hash = escape_string(user_data['password_hash'])
            
            sql = f"""
                INSERT INTO users (username, email, password_hash, is_active)
                VALUES ('{username}', '{email}', '{password_hash}', 1)
            """
            
            result = client.execute(sql, [])
            
            if result and 'results' in result:
                if result['results'][0].get('type') == 'error':
                    logger.error(f"Insert failed: {result['results'][0]['error']}")
                    return None
            
            return get_user_by_username(user_data['username'])
    except Exception as e:
        logger.error(f"Error in create_user: {e}")
        return None

def search_users(query: str, limit: int = 10) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            escaped_query = query.replace("'", "''")
            sql = f"""
                SELECT id, username, full_name, avatar_url 
                FROM users 
                WHERE username LIKE '%{escaped_query}%' OR full_name LIKE '%{escaped_query}%'
                LIMIT {limit}
            """
            rows = client.query(sql, [])
            result = []
            for row in rows:
                result.append({
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "full_name": get_value(row[2]),
                    "avatar_url": get_value(row[3])
                })
            return result
    except Exception as e:
        logger.error(f"Error in search_users: {e}")
        return []

def get_followers_count(user_id: int) -> int:
    if not settings.USE_TURSO:
        return 0
    try:
        with get_turso_client() as client:
            escaped_id = str(user_id)
            sql = f"SELECT COUNT(*) FROM follows WHERE followed_id = {escaped_id} AND is_active = 1"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                val = get_value(rows[0][0])
                return int(val) if val else 0
            return 0
    except Exception as e:
        logger.error(f"Error in get_followers_count: {e}")
        return 0

def get_following_count(user_id: int) -> int:
    if not settings.USE_TURSO:
        return 0
    try:
        with get_turso_client() as client:
            escaped_id = str(user_id)
            sql = f"SELECT COUNT(*) FROM follows WHERE follower_id = {escaped_id} AND is_active = 1"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                val = get_value(rows[0][0])
                return int(val) if val else 0
            return 0
    except Exception as e:
        logger.error(f"Error in get_following_count: {e}")
        return 0

def get_following(user_id: int, limit: int = 100) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            escaped_id = str(user_id)
            limit_str = str(limit)
            sql = f"""
                SELECT u.id, u.username, u.full_name, u.avatar_url
                FROM follows f
                JOIN users u ON f.followed_id = u.id
                WHERE f.follower_id = {escaped_id} AND f.is_active = 1
                LIMIT {limit_str}
            """
            rows = client.query(sql, [])
            result = []
            for row in rows:
                result.append({
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "full_name": get_value(row[2]),
                    "avatar_url": get_value(row[3])
                })
            return result
    except Exception as e:
        logger.error(f"Error in get_following: {e}")
        return []

def get_followers(user_id: int, limit: int = 20) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            escaped_id = str(user_id)
            limit_str = str(limit)
            sql = f"""
                SELECT u.id, u.username, u.full_name, u.avatar_url
                FROM follows f
                JOIN users u ON f.follower_id = u.id
                WHERE f.followed_id = {escaped_id} AND f.is_active = 1
                LIMIT {limit_str}
            """
            rows = client.query(sql, [])
            result = []
            for row in rows:
                result.append({
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "full_name": get_value(row[2]),
                    "avatar_url": get_value(row[3])
                })
            return result
    except Exception as e:
        logger.error(f"Error in get_followers: {e}")
        return []

def get_follow_suggestions(user_id: int, limit: int = 10) -> List[Dict]:
    """Get follow suggestions for a user"""
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            limit_str = str(limit)
            
            following_ids_query = client.query(
                f"SELECT followed_id FROM follows WHERE follower_id = {user_id_str} AND is_active = 1",
                []
            )
            
            following_ids = [str(get_value(row[0])) for row in following_ids_query] if following_ids_query else []
       
            exclude_ids = [user_id_str] + following_ids
            exclude_clause = f"AND id NOT IN ({','.join(exclude_ids)})" if exclude_ids else ""
      
            sql = f"""
                SELECT id, username, full_name, avatar_url, bio
                FROM users
                WHERE is_active = 1
                {exclude_clause}
                ORDER BY RANDOM()
                LIMIT {limit_str}
            """
            rows = client.query(sql, [])
            result = []
            for row in rows:
                result.append({
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "full_name": get_value(row[2]),
                    "avatar_url": get_value(row[3]),
                    "bio": get_value(row[4])
                })
            return result
    except Exception as e:
        logger.error(f"Error in get_follow_suggestions: {e}")
        return []

def is_following(follower_id: int, followed_id: int) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            follower_id_str = str(follower_id)
            followed_id_str = str(followed_id)
            sql = f"SELECT 1 FROM follows WHERE follower_id = {follower_id_str} AND followed_id = {followed_id_str} AND is_active = 1"
            result = client.query_one(sql, [])
            return result is not None
    except Exception as e:
        logger.error(f"Error in is_following: {e}")
        return False

def get_unread_notification_count(user_id: int) -> int:
    if not settings.USE_TURSO:
        return 0
    try:
        with get_turso_client() as client:
            tables = client.query("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'", [])
            if not tables:
                logger.warning("Notifications table not found")
                return 0
            escaped_id = str(user_id)
            sql = f"SELECT COUNT(*) FROM notifications WHERE user_id = {escaped_id} AND is_read = 0"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                val = get_value(rows[0][0])
                return int(val) if val else 0
            return 0
    except Exception as e:
        logger.error(f"Error in get_unread_notification_count: {e}")
        return 0

def get_user_notifications(user_id: int, limit: int = 20) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            limit_str = str(limit)
            sql = f"""
                SELECT id, type, content, related_id, is_read, created_at
                FROM notifications
                WHERE user_id = {user_id_str}
                ORDER BY created_at DESC
                LIMIT {limit_str}
            """
            rows = client.query(sql, [])
            result = []
            for row in rows:
                result.append({
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "type": get_value(row[1]),
                    "content": get_value(row[2]),
                    "related_id": int(get_value(row[3])) if len(row) > 3 and get_value(row[3]) else None,
                    "is_read": bool(int(get_value(row[4]))) if len(row) > 4 and get_value(row[4]) else False,
                    "created_at": get_value(row[5]) if len(row) > 5 else None
                })
            return result
    except Exception as e:
        logger.error(f"Error in get_user_notifications: {e}")
        return []

def mark_notification_read(notification_id: int, user_id: int) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            notification_id_str = str(notification_id)
            user_id_str = str(user_id)
            sql = f"UPDATE notifications SET is_read = 1 WHERE id = {notification_id_str} AND user_id = {user_id_str}"
            client.execute(sql, [])
            return True
    except Exception as e:
        logger.error(f"Error in mark_notification_read: {e}")
        return False

def mark_all_notifications_read(user_id: int) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            sql = f"UPDATE notifications SET is_read = 1 WHERE user_id = {user_id_str} AND is_read = 0"
            client.execute(sql, [])
            return True
    except Exception as e:
        logger.error(f"Error in mark_all_notifications_read: {e}")
        return False

def create_notification(user_id: int, type: str, content: str, related_id: Optional[int] = None) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            escaped_type = type.replace("'", "''")
            escaped_content = content.replace("'", "''")
            related_id_str = str(related_id) if related_id else "NULL"
            
            sql = f"""
                INSERT INTO notifications (user_id, type, content, related_id, created_at)
                VALUES ({user_id_str}, '{escaped_type}', '{escaped_content}', {related_id_str}, CURRENT_TIMESTAMP)
            """
            client.execute(sql, [])
            return True
    except Exception as e:
        logger.error(f"Error in create_notification: {e}")
        return False

def get_comment(comment_id: int) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            comment_id_str = str(comment_id)
            sql = f"SELECT * FROM comments WHERE id = {comment_id_str}"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                return comment_to_dict(rows[0])
            return None
    except Exception as e:
        logger.error(f"Error in get_comment: {e}")
        return None

def create_comment(story_id: int, user_id: int, content: str, parent_id: Optional[int] = None) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            story_id_str = str(story_id)
            user_id_str = str(user_id)
            escaped_content = content.replace("'", "''")
            parent_id_str = str(parent_id) if parent_id else "NULL"
            
            sql = f"""
                INSERT INTO comments (content, user_id, story_id, parent_id, created_at)
                VALUES ('{escaped_content}', {user_id_str}, {story_id_str}, {parent_id_str}, CURRENT_TIMESTAMP)
            """
            client.execute(sql, [])
            
            client.execute(f"UPDATE stories SET comment_count = comment_count + 1 WHERE id = {story_id_str}", [])
            
            select_sql = f"""
                SELECT c.*, u.username, u.avatar_url
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.story_id = {story_id_str} AND c.user_id = {user_id_str} 
                ORDER BY c.id DESC LIMIT 1
            """
            rows = client.query(select_sql, [])
            if rows and len(rows) > 0:
                return comment_to_dict(rows[0])
            return None
    except Exception as e:
        logger.error(f"Error in create_comment: {e}")
        return None

def get_story_comments(story_id: int) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            story_id_str = str(story_id)
            sql = f"""
                SELECT c.*, u.username, u.avatar_url,
                       (SELECT COUNT(*) FROM comments WHERE parent_id = c.id) as reply_count
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.story_id = {story_id_str} AND c.parent_id IS NULL
                ORDER BY c.created_at DESC
            """
            rows = client.query(sql, [])
            return [comment_to_dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error in get_story_comments: {e}")
        return []

def get_comment_replies(comment_id: int) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            comment_id_str = str(comment_id)
            sql = f"""
                SELECT c.*, u.username, u.avatar_url
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.parent_id = {comment_id_str}
                ORDER BY c.created_at ASC
            """
            rows = client.query(sql, [])
            return [comment_to_dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error in get_comment_replies: {e}")
        return []

def update_comment(comment_id: int, user_id: int, content: str) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            comment_id_str = str(comment_id)
            user_id_str = str(user_id)
            escaped_content = content.replace("'", "''")
            
            check_sql = f"SELECT user_id FROM comments WHERE id = {comment_id_str}"
            check_row = client.query_one(check_sql, [])
            if not check_row:
                return False
            
            owner_id = int(get_value(check_row[0])) if get_value(check_row[0]) else None
            if owner_id != user_id:
                return False
            
            sql = f"UPDATE comments SET content = '{escaped_content}', is_edited = 1 WHERE id = {comment_id_str}"
            client.execute(sql, [])
            return True
    except Exception as e:
        logger.error(f"Error in update_comment: {e}")
        return False

def delete_comment(comment_id: int, user_id: int) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            comment_id_str = str(comment_id)
            user_id_str = str(user_id)
            
            check_sql = f"SELECT user_id, story_id FROM comments WHERE id = {comment_id_str}"
            check_row = client.query_one(check_sql, [])
            if not check_row:
                return False
            
            owner_id = int(get_value(check_row[0])) if get_value(check_row[0]) else None
            if owner_id != user_id:
                return False
            
            story_id = int(get_value(check_row[1])) if get_value(check_row[1]) else None
            
            client.execute(f"DELETE FROM comments WHERE id = {comment_id_str} OR parent_id = {comment_id_str}", [])
            
            if story_id:
                count_sql = f"SELECT COUNT(*) FROM comments WHERE story_id = {story_id}"
                count_row = client.query_one(count_sql, [])
                count = int(get_value(count_row[0])) if count_row and len(count_row) > 0 else 0
                client.execute(f"UPDATE stories SET comment_count = {count} WHERE id = {story_id}", [])
            
            return True
    except Exception as e:
        logger.error(f"Error in delete_comment: {e}")
        return False

def is_comment_liked(user_id: int, comment_id: int) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            comment_id_str = str(comment_id)
            sql = f"SELECT 1 FROM comment_likes WHERE user_id = {user_id_str} AND comment_id = {comment_id_str}"
            result = client.query_one(sql, [])
            return result is not None
    except Exception as e:
        logger.error(f"Error in is_comment_liked: {e}")
        return False

def toggle_comment_like(user_id: int, comment_id: int) -> Dict:
    if not settings.USE_TURSO:
        return {"liked": False, "like_count": 0}
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            comment_id_str = str(comment_id)
            
            check_sql = f"SELECT id FROM comment_likes WHERE user_id = {user_id_str} AND comment_id = {comment_id_str}"
            existing = client.query_one(check_sql, [])
            
            if existing:
                client.execute(f"DELETE FROM comment_likes WHERE user_id = {user_id_str} AND comment_id = {comment_id_str}", [])
                client.execute(f"UPDATE comments SET like_count = like_count - 1 WHERE id = {comment_id_str}", [])
                liked = False
            else:
                client.execute(f"INSERT INTO comment_likes (user_id, comment_id) VALUES ({user_id_str}, {comment_id_str})", [])
                client.execute(f"UPDATE comments SET like_count = like_count + 1 WHERE id = {comment_id_str}", [])
                liked = True
            
            count_sql = f"SELECT like_count FROM comments WHERE id = {comment_id_str}"
            count_row = client.query_one(count_sql, [])
            like_count = int(get_value(count_row[0])) if count_row and len(count_row) > 0 else 0
            
            return {"liked": liked, "like_count": like_count}
    except Exception as e:
        logger.error(f"Error in toggle_comment_like: {e}")
        return {"liked": False, "like_count": 0}

def comment_to_dict(row) -> Dict:
    if not row or len(row) == 0:
        return {}
    return {
        "id": int(get_value(row[0])) if get_value(row[0]) else None,
        "content": get_value(row[1]),
        "user_id": int(get_value(row[2])) if get_value(row[2]) else None,
        "story_id": int(get_value(row[3])) if get_value(row[3]) else None,
        "parent_id": int(get_value(row[4])) if len(row) > 4 and get_value(row[4]) else None,
        "like_count": int(get_value(row[5])) if len(row) > 5 and get_value(row[5]) else 0,
        "is_edited": bool(int(get_value(row[6]))) if len(row) > 6 and get_value(row[6]) else False,
        "created_at": get_value(row[7]) if len(row) > 7 else None,
        "updated_at": get_value(row[8]) if len(row) > 8 else None,
        "username": get_value(row[9]) if len(row) > 9 else None,
        "avatar_url": get_value(row[10]) if len(row) > 10 else None,
        "reply_count": int(get_value(row[11])) if len(row) > 11 and get_value(row[11]) else 0
    }

def create_story(story_data: dict, user_id: int) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            def escape_string(s):
                if s is None:
                    return "NULL"
                return f"'{s.replace("'", "''")}'"
            
            title = escape_string(story_data['title'])
            content = escape_string(story_data.get('content', ''))
            excerpt = escape_string(story_data.get('excerpt', ''))
            cover_image = escape_string(story_data.get('cover_image', ''))
            story_type = escape_string(story_data.get('story_type', 'written'))
            genre = escape_string(story_data.get('genre', ''))
            is_published = 1 if story_data.get('is_published', False) else 0
            is_premium = 1 if story_data.get('is_premium', False) else 0
            
            sql = f"""
                INSERT INTO stories (
                    title, content, excerpt, cover_image, user_id, story_type, 
                    genre, is_published, is_premium
                ) VALUES ({title}, {content}, {excerpt}, {cover_image}, {user_id}, {story_type}, {genre}, {is_published}, {is_premium})
            """
            
            client.execute(sql, [])
            
            user_id_str = str(user_id)
            select_sql = f"SELECT * FROM stories WHERE user_id = {user_id_str} ORDER BY id DESC LIMIT 1"
            rows = client.query(select_sql, [])
            if rows and len(rows) > 0:
                return story_to_dict(rows[0])
            return None
    except Exception as e:
        logger.error(f"Error in create_story: {e}")
        return None

def get_story(story_id: int) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            escaped_id = str(story_id)
            sql = f"""
                SELECT s.*, u.username, u.full_name, u.avatar_url 
                FROM stories s
                JOIN users u ON s.user_id = u.id
                WHERE s.id = {escaped_id}
            """
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                return story_to_dict(rows[0])
            return None
    except Exception as e:
        logger.error(f"Error in get_story: {e}")
        return None

def get_user_stories(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            limit_str = str(limit)
            offset_str = str(offset)
            sql = f"SELECT * FROM stories WHERE user_id = {user_id_str} ORDER BY created_at DESC LIMIT {limit_str} OFFSET {offset_str}"
            rows = client.query(sql, [])
            result = []
            for row in rows:
                result.append(story_to_dict(row))
            return result
    except Exception as e:
        logger.error(f"Error in get_user_stories: {e}")
        return []

def story_to_dict(row) -> Dict:
    if not row or len(row) == 0:
        return {}
    return {
        "id": int(get_value(row[0])) if get_value(row[0]) else None,
        "title": get_value(row[1]),
        "content": get_value(row[2]),
        "excerpt": get_value(row[3]),
        "cover_image": get_value(row[4]),
        "user_id": int(get_value(row[5])) if get_value(row[5]) else None,
        "story_type": get_value(row[6]),
        "genre": get_value(row[7]),
        "view_count": int(get_value(row[8])) if get_value(row[8]) else 0,
        "like_count": int(get_value(row[9])) if get_value(row[9]) else 0,
        "comment_count": int(get_value(row[10])) if get_value(row[10]) else 0,
        "is_published": bool(int(get_value(row[11]))) if get_value(row[11]) else False,
        "is_premium": bool(int(get_value(row[12]))) if get_value(row[12]) else False,
        "created_at": get_value(row[13]),
        "username": get_value(row[14]) if len(row) > 14 else None,
        "avatar_url": get_value(row[15]) if len(row) > 15 else None
    }

def is_liked(user_id: int, story_id: int) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            story_id_str = str(story_id)
            sql = f"SELECT 1 FROM likes WHERE user_id = {user_id_str} AND story_id = {story_id_str}"
            result = client.query_one(sql, [])
            return result is not None
    except Exception as e:
        logger.error(f"Error in is_liked: {e}")
        return False

def toggle_story_like(user_id: int, story_id: int) -> Dict:
    if not settings.USE_TURSO:
        return {"liked": False, "like_count": 0}
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            story_id_str = str(story_id)
            
            check_sql = f"SELECT id FROM likes WHERE user_id = {user_id_str} AND story_id = {story_id_str}"
            existing = client.query_one(check_sql, [])
            
            if existing:
                delete_sql = f"DELETE FROM likes WHERE user_id = {user_id_str} AND story_id = {story_id_str}"
                client.execute(delete_sql, [])
                update_sql = f"UPDATE stories SET like_count = like_count - 1 WHERE id = {story_id_str}"
                client.execute(update_sql, [])
                liked = False
            else:
                insert_sql = f"INSERT INTO likes (user_id, story_id) VALUES ({user_id_str}, {story_id_str})"
                client.execute(insert_sql, [])
                update_sql = f"UPDATE stories SET like_count = like_count + 1 WHERE id = {story_id_str}"
                client.execute(update_sql, [])
                liked = True
            
            count_sql = f"SELECT like_count FROM stories WHERE id = {story_id_str}"
            count_row = client.query_one(count_sql, [])
            like_count = int(get_value(count_row[0])) if count_row and len(count_row) > 0 else 0
            return {"liked": liked, "like_count": like_count}
    except Exception as e:
        logger.error(f"Error in toggle_story_like: {e}")
        return {"liked": False, "like_count": 0}

def toggle_follow(follower_id: int, followed_id: int) -> Dict:
    if not settings.USE_TURSO:
        return {"following": False}
    try:
        with get_turso_client() as client:
            if follower_id == followed_id:
                return {"following": False}
            
            follower_id_str = str(follower_id)
            followed_id_str = str(followed_id)
            
            check_sql = f"SELECT 1 FROM follows WHERE follower_id = {follower_id_str} AND followed_id = {followed_id_str} AND is_active = 1"
            existing = client.query_one(check_sql, [])
            
            if existing:
                delete_sql = f"DELETE FROM follows WHERE follower_id = {follower_id_str} AND followed_id = {followed_id_str}"
                client.execute(delete_sql, [])
                following = False
            else:
                insert_sql = f"INSERT INTO follows (follower_id, followed_id, is_active) VALUES ({follower_id_str}, {followed_id_str}, 1)"
                client.execute(insert_sql, [])
                following = True
            
            return {"following": following}
    except Exception as e:
        logger.error(f"Error in toggle_follow: {e}")
        return {"following": False}

def send_message(sender_id: int, receiver_id: int, content: str) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            sender_id_str = str(sender_id)
            receiver_id_str = str(receiver_id)
            escaped_content = content.replace("'", "''")
            
            insert_sql = f"""
                INSERT INTO messages (sender_id, receiver_id, content, created_at)
                VALUES ({sender_id_str}, {receiver_id_str}, '{escaped_content}', CURRENT_TIMESTAMP)
            """
            client.execute(insert_sql, [])
            
            select_sql = f"""
                SELECT m.*, u_s.username as sender_name, u_r.username as receiver_name
                FROM messages m
                JOIN users u_s ON m.sender_id = u_s.id
                JOIN users u_r ON m.receiver_id = u_r.id
                WHERE m.id = (SELECT last_insert_rowid())
            """
            rows = client.query(select_sql, [])
            if rows and len(rows) > 0:
                return message_to_dict(rows[0])
            return None
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        return None

def get_conversation(user_id: int, other_id: int, limit: int = 50) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            other_id_str = str(other_id)
            limit_str = str(limit)
            sql = f"""
                SELECT m.*, u_s.username as sender_name, u_r.username as receiver_name
                FROM messages m
                JOIN users u_s ON m.sender_id = u_s.id
                JOIN users u_r ON m.receiver_id = u_r.id
                WHERE (m.sender_id = {user_id_str} AND m.receiver_id = {other_id_str}) 
                   OR (m.sender_id = {other_id_str} AND m.receiver_id = {user_id_str})
                ORDER BY m.created_at ASC
                LIMIT {limit_str}
            """
            rows = client.query(sql, [])
            result = []
            for row in rows:
                result.append(message_to_dict(row))
            return result
    except Exception as e:
        logger.error(f"Error in get_conversation: {e}")
        return []

def get_conversations(user_id: int) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            sql = f"""
                SELECT 
                    u.id as user_id,
                    u.username,
                    u.full_name,
                    u.avatar_url,
                    m.content as last_message,
                    m.created_at as last_message_at,
                    (SELECT COUNT(*) FROM messages 
                     WHERE receiver_id = {user_id_str} AND sender_id = u.id AND is_read = 0) as unread_count
                FROM (
                    SELECT DISTINCT 
                        CASE WHEN sender_id = {user_id_str} THEN receiver_id ELSE sender_id END as other_id,
                        MAX(created_at) as last_time
                    FROM messages
                    WHERE sender_id = {user_id_str} OR receiver_id = {user_id_str}
                    GROUP BY other_id
                ) conv
                JOIN users u ON u.id = conv.other_id
                JOIN messages m ON (m.sender_id = {user_id_str} AND m.receiver_id = u.id) 
                                OR (m.sender_id = u.id AND m.receiver_id = {user_id_str})
                WHERE m.created_at = conv.last_time
                ORDER BY m.created_at DESC
            """
            rows = client.query(sql, [])
            conversations = []
            for row in rows:
                conversations.append({
                    "user_id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "full_name": get_value(row[2]),
                    "avatar_url": get_value(row[3]),
                    "last_message": get_value(row[4]),
                    "last_message_at": get_value(row[5]),
                    "unread_count": int(get_value(row[6])) if get_value(row[6]) else 0
                })
            return conversations
    except Exception as e:
        logger.error(f"Error in get_conversations: {e}")
        return []

def mark_messages_read(user_id: int, sender_id: int) -> int:
    if not settings.USE_TURSO:
        return 0
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            sender_id_str = str(sender_id)
            sql = f"UPDATE messages SET is_read = 1 WHERE receiver_id = {user_id_str} AND sender_id = {sender_id_str} AND is_read = 0"
            client.execute(sql, [])
            return 1
    except Exception as e:
        logger.error(f"Error in mark_messages_read: {e}")
        return 0

def get_unread_count(user_id: int) -> Dict:
    if not settings.USE_TURSO:
        return {"total_unread": 0, "conversations": []}
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            rows = client.query(
                f"""
                SELECT 
                    u.id as user_id,
                    u.username,
                    u.full_name,
                    u.avatar_url,
                    COUNT(*) as unread_count
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.receiver_id = {user_id_str} AND m.is_read = 0
                GROUP BY m.sender_id
                """,
                []
            )
            conversations = []
            total = 0
            for row in rows:
                count = int(get_value(row[4])) if get_value(row[4]) else 0
                conversations.append({
                    "user_id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "username": get_value(row[1]),
                    "full_name": get_value(row[2]),
                    "avatar_url": get_value(row[3]),
                    "unread_count": count
                })
                total += count
            return {"total_unread": total, "conversations": conversations}
    except Exception as e:
        logger.error(f"Error in get_unread_count: {e}")
        return {"total_unread": 0, "conversations": []}

def message_to_dict(row) -> Dict:
    if not row or len(row) == 0:
        return {}
    return {
        "id": int(get_value(row[0])) if get_value(row[0]) else None,
        "sender_id": int(get_value(row[1])) if get_value(row[1]) else None,
        "receiver_id": int(get_value(row[2])) if get_value(row[2]) else None,
        "content": get_value(row[3]),
        "is_read": bool(int(get_value(row[4]))) if get_value(row[4]) else False,
        "created_at": get_value(row[5]),
        "sender_name": get_value(row[6]) if len(row) > 6 else None,
        "receiver_name": get_value(row[7]) if len(row) > 7 else None
    }

def toggle_bookmark(user_id: int, story_id: int) -> Dict:
    if not settings.USE_TURSO:
        return {"bookmarked": False}
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            story_id_str = str(story_id)
            
            check_sql = f"SELECT id FROM bookmarks WHERE user_id = {user_id_str} AND story_id = {story_id_str}"
            existing = client.query_one(check_sql, [])
            
            if existing:
                delete_sql = f"DELETE FROM bookmarks WHERE user_id = {user_id_str} AND story_id = {story_id_str}"
                client.execute(delete_sql, [])
                bookmarked = False
            else:
                insert_sql = f"INSERT INTO bookmarks (user_id, story_id) VALUES ({user_id_str}, {story_id_str})"
                client.execute(insert_sql, [])
                bookmarked = True
            
            return {"bookmarked": bookmarked}
    except Exception as e:
        logger.error(f"Error in toggle_bookmark: {e}")
        return {"bookmarked": False}

def is_bookmarked(user_id: int, story_id: int) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            story_id_str = str(story_id)
            sql = f"SELECT 1 FROM bookmarks WHERE user_id = {user_id_str} AND story_id = {story_id_str}"
            result = client.query_one(sql, [])
            return result is not None
    except Exception as e:
        logger.error(f"Error in is_bookmarked: {e}")
        return False

def get_user_bookmarks(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            limit_str = str(limit)
            offset_str = str(offset)
            sql = f"""
                SELECT s.*, u.username, u.avatar_url, b.created_at as bookmarked_at
                FROM bookmarks b
                JOIN stories s ON b.story_id = s.id
                JOIN users u ON s.user_id = u.id
                WHERE b.user_id = {user_id_str}
                ORDER BY b.created_at DESC
                LIMIT {limit_str} OFFSET {offset_str}
            """
            rows = client.query(sql, [])
            stories = []
            for row in rows:
                story_dict = story_to_dict(row[:16])
                bookmarked_at = get_value(row[16]) if len(row) > 16 else None
                story_dict["bookmarked_at"] = bookmarked_at
                stories.append(story_dict)
            return stories
    except Exception as e:
        logger.error(f"Error in get_user_bookmarks: {e}")
        return []

def get_template(template_id: int) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            template_id_str = str(template_id)
            sql = f"SELECT * FROM templates WHERE id = {template_id_str}"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "title": get_value(row[1]),
                    "description": get_value(row[2]),
                    "genre": get_value(row[3]),
                    "content_structure": json.loads(get_value(row[4])) if get_value(row[4]) else {},
                    "prompt": get_value(row[5]),
                    "cover_image": get_value(row[6]),
                    "is_premium": bool(int(get_value(row[7]))) if get_value(row[7]) else False,
                    "usage_count": int(get_value(row[8])) if get_value(row[8]) else 0
                }
            return None
    except Exception as e:
        logger.error(f"Error in get_template: {e}")
        return None

def get_templates(genre: Optional[str] = None, search: Optional[str] = None, sort: str = "popular", limit: int = 20, offset: int = 0) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            where_clauses = []
            if genre and genre != "all":
                escaped_genre = genre.replace("'", "''")
                where_clauses.append(f"genre = '{escaped_genre}'")
            if search:
                escaped_search = search.replace("'", "''")
                where_clauses.append(f"(title LIKE '%{escaped_search}%' OR description LIKE '%{escaped_search}%')")
            
            where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            order = "ORDER BY usage_count DESC" if sort == "popular" else "ORDER BY created_at DESC"
            limit_str = str(limit)
            offset_str = str(offset)
            
            sql = f"""
                SELECT * FROM templates
                {where}
                {order}
                LIMIT {limit_str} OFFSET {offset_str}
            """
            rows = client.query(sql, [])
            result = []
            for row in rows:
                result.append({
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "title": get_value(row[1]),
                    "description": get_value(row[2]),
                    "genre": get_value(row[3]),
                    "content_structure": json.loads(get_value(row[4])) if get_value(row[4]) else {},
                    "prompt": get_value(row[5]),
                    "cover_image": get_value(row[6]),
                    "is_premium": bool(int(get_value(row[7]))) if get_value(row[7]) else False,
                    "usage_count": int(get_value(row[8])) if get_value(row[8]) else 0
                })
            return result
    except Exception as e:
        logger.error(f"Error in get_templates: {e}")
        return []

def get_template_by_title(title: str) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            escaped_title = title.replace("'", "''")
            sql = f"SELECT * FROM templates WHERE title = '{escaped_title}'"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "title": get_value(row[1]),
                    "description": get_value(row[2]),
                    "genre": get_value(row[3]),
                    "content_structure": json.loads(get_value(row[4])) if get_value(row[4]) else {},
                    "prompt": get_value(row[5]),
                    "cover_image": get_value(row[6]),
                    "is_premium": bool(int(get_value(row[7]))) if get_value(row[7]) else False,
                    "usage_count": int(get_value(row[8])) if get_value(row[8]) else 0
                }
            return None
    except Exception as e:
        logger.error(f"Error in get_template_by_title: {e}")
        return None

def create_template(template_data: dict) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            title = template_data['title'].replace("'", "''")
            description = template_data.get('description', '').replace("'", "''")
            genre = template_data.get('genre', '').replace("'", "''")
            content_structure = json.dumps(template_data.get('content_structure', {}))
            prompt = template_data.get('prompt', '').replace("'", "''")
            cover_image = template_data.get('cover_image', '').replace("'", "''")
            is_premium = 1 if template_data.get('is_premium', False) else 0
            created_by = template_data.get('created_by', 0)
            
            sql = f"""
                INSERT INTO templates (
                    title, description, genre, content_structure, prompt, 
                    cover_image, is_premium, created_by
                ) VALUES (
                    '{title}', '{description}', '{genre}', '{content_structure}', 
                    '{prompt}', '{cover_image}', {is_premium}, {created_by}
                )
            """
            client.execute(sql, [])
            
            select_sql = f"SELECT * FROM templates WHERE title = '{title}' ORDER BY id DESC LIMIT 1"
            rows = client.query(select_sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "title": get_value(row[1]),
                    "description": get_value(row[2]),
                    "genre": get_value(row[3]),
                    "content_structure": json.loads(get_value(row[4])) if get_value(row[4]) else {},
                    "prompt": get_value(row[5]),
                    "cover_image": get_value(row[6]),
                    "is_premium": bool(int(get_value(row[7]))) if get_value(row[7]) else False,
                    "usage_count": int(get_value(row[8])) if get_value(row[8]) else 0,
                    "created_by": int(get_value(row[9])) if get_value(row[9]) else None,
                    "created_at": get_value(row[10])
                }
            return None
    except Exception as e:
        logger.error(f"Error in create_template: {e}")
        return None

def use_template(template_id: int, user_id: int, custom_title: Optional[str] = None) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        template = get_template(template_id)
        if not template:
            return None
        
        title = custom_title or f"Story using {template['title']}"
        content = f"# {title}\n\nBased on the {template['title']} template\n\n"
        
        story_data = {
            "title": title,
            "content": content,
            "excerpt": f"A story created using the {template['title']} template",
            "story_type": "written",
            "genre": template.get('genre'),
            "is_published": False
        }
        
        story = create_story(story_data, user_id)
        return {
            "story_id": story["id"] if story else None,
            "title": title,
            "message": f"Story created using template '{template['title']}'"
        }
    except Exception as e:
        logger.error(f"Error in use_template: {e}")
        return None

def toggle_template_favorite(template_id: int, user_id: int) -> Dict:
    if not settings.USE_TURSO:
        return {"message": "Template not favorited"}
    try:
        with get_turso_client() as client:
            template_id_str = str(template_id)
            user_id_str = str(user_id)
            
            check_sql = f"SELECT id, is_favorite FROM user_templates WHERE user_id = {user_id_str} AND template_id = {template_id_str}"
            existing = client.query_one(check_sql, [])
            
            if existing:
                fav_value = int(get_value(existing[1])) if get_value(existing[1]) else 0
                new_value = 0 if fav_value else 1
                update_sql = f"UPDATE user_templates SET is_favorite = {new_value}, last_used = CURRENT_TIMESTAMP WHERE user_id = {user_id_str} AND template_id = {template_id_str}"
                client.execute(update_sql, [])
                message = "added to" if new_value else "removed from"
            else:
                insert_sql = f"INSERT INTO user_templates (user_id, template_id, is_favorite) VALUES ({user_id_str}, {template_id_str}, 1)"
                client.execute(insert_sql, [])
                message = "added to"
            
            return {"message": f"Template {message} favorites"}
    except Exception as e:
        logger.error(f"Error in toggle_template_favorite: {e}")
        return {"message": "Failed to toggle favorite"}

def get_favorite_templates(user_id: int) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            sql = f"""
                SELECT t.*, ut.last_used
                FROM templates t
                JOIN user_templates ut ON t.id = ut.template_id
                WHERE ut.user_id = {user_id_str} AND ut.is_favorite = 1
                ORDER BY ut.last_used DESC
            """
            rows = client.query(sql, [])
            templates = []
            for row in rows:
                template_dict = {
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "title": get_value(row[1]),
                    "description": get_value(row[2]),
                    "genre": get_value(row[3]),
                    "content_structure": json.loads(get_value(row[4])) if get_value(row[4]) else {},
                    "prompt": get_value(row[5]),
                    "cover_image": get_value(row[6]),
                    "is_premium": bool(int(get_value(row[7]))) if get_value(row[7]) else False,
                    "usage_count": int(get_value(row[8])) if get_value(row[8]) else 0,
                    "created_by": int(get_value(row[9])) if get_value(row[9]) else None,
                    "created_at": get_value(row[10]),
                    "is_favorite": True
                }
                templates.append(template_dict)
            return templates
    except Exception as e:
        logger.error(f"Error in get_favorite_templates: {e}")
        return []

def create_job(job_data: dict) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            job_id = job_data['job_id'].replace("'", "''")
            session_id = job_data.get('session_id', '').replace("'", "''")
            theme = job_data.get('theme', '').replace("'", "''")
            status = job_data.get('status', 'pending').replace("'", "''")
            
            sql = f"""
                INSERT INTO jobs (job_id, session_id, theme, status, created_at)
                VALUES ('{job_id}', '{session_id}', '{theme}', '{status}', CURRENT_TIMESTAMP)
            """
            client.execute(sql, [])
            return get_job(job_data['job_id'])
    except Exception as e:
        logger.error(f"Error in create_job: {e}")
        return {"job_id": job_data['job_id'], "status": job_data.get('status', 'pending')}

def update_job_status(job_id: str, status: str, result: Optional[str] = None) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            job_id_escaped = job_id.replace("'", "''")
            status_escaped = status.replace("'", "''")
            result_escaped = result.replace("'", "''") if result else ""
            
            if status in ['completed', 'failed']:
                sql = f"""
                    UPDATE jobs 
                    SET status = '{status_escaped}', result = '{result_escaped}', completed_at = CURRENT_TIMESTAMP
                    WHERE job_id = '{job_id_escaped}'
                """
            else:
                sql = f"UPDATE jobs SET status = '{status_escaped}' WHERE job_id = '{job_id_escaped}'"
            
            client.execute(sql, [])
            return True
    except Exception as e:
        logger.error(f"Error in update_job_status: {e}")
        return False

def get_job(job_id: str) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            job_id_escaped = job_id.replace("'", "''")
            sql = f"SELECT * FROM jobs WHERE job_id = '{job_id_escaped}'"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "job_id": get_value(row[0]),
                    "session_id": get_value(row[1]),
                    "theme": get_value(row[2]),
                    "status": get_value(row[3]),
                    "result": get_value(row[4]) if len(row) > 4 else None,
                    "created_at": get_value(row[5]) if len(row) > 5 else None,
                    "completed_at": get_value(row[6]) if len(row) > 6 else None
                }
            return None
    except Exception as e:
        logger.error(f"Error in get_job: {e}")
        return None

def get_user_count() -> int:
    if not settings.USE_TURSO:
        return 0
    try:
        with get_turso_client() as client:
            sql = "SELECT COUNT(*) FROM users"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                val = get_value(rows[0][0])
                return int(val) if val else 0
            return 0
    except Exception as e:
        logger.error(f"Error in get_user_count: {e}")
        return 0

def get_feed_stories(feed_type: str, timeframe: str, page: int = 1, limit: int = 20) -> List[Dict]:
    if not settings.USE_TURSO:
        return []
    with get_turso_client() as client:
        offset = (page - 1) * limit
        offset_str = str(offset)
        limit_str = str(limit)
        
        if feed_type == "trending":
            time_filter = ""
            if timeframe == "day":
                time_filter = "AND s.created_at > datetime('now', '-1 day')"
            elif timeframe == "week":
                time_filter = "AND s.created_at > datetime('now', '-7 days')"
            elif timeframe == "month":
                time_filter = "AND s.created_at > datetime('now', '-30 days')"
            
            query = f"""
                SELECT s.*, u.username, u.avatar_url,
                       (s.view_count + s.like_count * 10) as score
                FROM stories s
                JOIN users u ON s.user_id = u.id
                WHERE s.is_published = 1 {time_filter}
                ORDER BY score DESC
                LIMIT {limit_str} OFFSET {offset_str}
            """
            rows = client.query(query, [])
            
        elif feed_type == "latest":
            query = f"""
                SELECT s.*, u.username, u.avatar_url
                FROM stories s
                JOIN users u ON s.user_id = u.id
                WHERE s.is_published = 1
                ORDER BY s.created_at DESC
                LIMIT {limit_str} OFFSET {offset_str}
            """
            rows = client.query(query, [])
        else:
            query = f"""
                SELECT s.*, u.username, u.avatar_url
                FROM stories s
                JOIN users u ON s.user_id = u.id
                WHERE s.is_published = 1
                ORDER BY (s.view_count + s.like_count * 10) DESC
                LIMIT {limit_str} OFFSET {offset_str}
            """
            rows = client.query(query, [])
        
        result = []
        for row in rows:
            result.append(story_to_dict(row))
        return result
    
def create_job(job_data: dict) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            job_id = job_data['job_id'].replace("'", "''")
            session_id = job_data.get('session_id', '').replace("'", "''")
            theme = job_data.get('theme', '').replace("'", "''")
            status = job_data.get('status', 'pending').replace("'", "''")
            
            sql = f"""
                INSERT INTO jobs (job_id, session_id, theme, status, created_at)
                VALUES ('{job_id}', '{session_id}', '{theme}', '{status}', CURRENT_TIMESTAMP)
            """
            client.execute(sql, [])
            return get_job(job_data['job_id'])
    except Exception as e:
        logger.error(f"Error in create_job: {e}")
        return {"job_id": job_data['job_id'], "status": job_data.get('status', 'pending')}

def update_job_status(job_id: str, status: str, result: Optional[str] = None) -> bool:
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            job_id_escaped = job_id.replace("'", "''")
            status_escaped = status.replace("'", "''")
            result_escaped = result.replace("'", "''") if result else ""
            
            if status in ['completed', 'failed']:
                sql = f"""
                    UPDATE jobs 
                    SET status = '{status_escaped}', result = '{result_escaped}', completed_at = CURRENT_TIMESTAMP
                    WHERE job_id = '{job_id_escaped}'
                """
            else:
                sql = f"UPDATE jobs SET status = '{status_escaped}' WHERE job_id = '{job_id_escaped}'"
            
            client.execute(sql, [])
            return True
    except Exception as e:
        logger.error(f"Error in update_job_status: {e}")
        return False

def get_job(job_id: str) -> Optional[Dict]:
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            job_id_escaped = job_id.replace("'", "''")
            sql = f"SELECT * FROM jobs WHERE job_id = '{job_id_escaped}'"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "job_id": get_value(row[0]),
                    "session_id": get_value(row[1]) if len(row) > 1 else None,
                    "theme": get_value(row[2]) if len(row) > 2 else None,
                    "status": get_value(row[3]) if len(row) > 3 else None,
                    "result": get_value(row[4]) if len(row) > 4 else None,
                    "created_at": get_value(row[5]) if len(row) > 5 else None,
                    "completed_at": get_value(row[6]) if len(row) > 6 else None
                }
            return None
    except Exception as e:
        logger.error(f"Error in get_job: {e}")
        return None

def create_notification(user_id: int, type: str, content: str, related_id: Optional[int] = None) -> bool:
    """Create a notification in Turso"""
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            escaped_type = type.replace("'", "''")
            escaped_content = content.replace("'", "''")
            related_id_str = str(related_id) if related_id else "NULL"
            
            sql = f"""
                INSERT INTO notifications (user_id, type, content, related_id, created_at)
                VALUES ({user_id_str}, '{escaped_type}', '{escaped_content}', {related_id_str}, CURRENT_TIMESTAMP)
            """
            client.execute(sql, [])
            return True
    except Exception as e:
        logger.error(f"Error in create_notification: {e}")
        return False
    
def create_job(job_data: dict) -> Optional[Dict]:
    """Create a background job"""
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            job_id = job_data['job_id'].replace("'", "''")
            session_id = job_data.get('session_id', '').replace("'", "''")
            theme = job_data.get('theme', '').replace("'", "''")
            status = job_data.get('status', 'pending')
            
            sql = f"""
                INSERT INTO jobs (job_id, session_id, theme, status, created_at)
                VALUES ('{job_id}', '{session_id}', '{theme}', '{status}', CURRENT_TIMESTAMP)
            """
            client.execute(sql, [])
            return get_job(job_data['job_id'])
    except Exception as e:
        logger.error(f"Error in create_job: {e}")
        return {"job_id": job_data['job_id'], "status": job_data.get('status', 'pending')}

def update_job_status(job_id: str, status: str, result: Optional[str] = None) -> bool:
    """Update job status"""
    if not settings.USE_TURSO:
        return False
    try:
        with get_turso_client() as client:
            job_id_escaped = job_id.replace("'", "''")
            status_escaped = status
            result_escaped = result.replace("'", "''") if result else ""
            
            if status in ['completed', 'failed']:
                sql = f"""
                    UPDATE jobs 
                    SET status = '{status_escaped}', result = '{result_escaped}', completed_at = CURRENT_TIMESTAMP
                    WHERE job_id = '{job_id_escaped}'
                """
            else:
                sql = f"UPDATE jobs SET status = '{status_escaped}' WHERE job_id = '{job_id_escaped}'"
            
            client.execute(sql, [])
            return True
    except Exception as e:
        logger.error(f"Error in update_job_status: {e}")
        return False

def get_job(job_id: str) -> Optional[Dict]:
    """Get job by ID"""
    if not settings.USE_TURSO:
        return None
    try:
        with get_turso_client() as client:
            job_id_escaped = job_id.replace("'", "''")
            sql = f"SELECT * FROM jobs WHERE job_id = '{job_id_escaped}'"
            rows = client.query(sql, [])
            if rows and len(rows) > 0:
                row = rows[0]
                return {
                    "job_id": get_value(row[0]),
                    "session_id": get_value(row[1]) if len(row) > 1 else None,
                    "theme": get_value(row[2]) if len(row) > 2 else None,
                    "status": get_value(row[3]) if len(row) > 3 else None,
                    "result": get_value(row[4]) if len(row) > 4 else None,
                    "created_at": get_value(row[5]) if len(row) > 5 else None,
                    "completed_at": get_value(row[6]) if len(row) > 6 else None
                }
            return None
    except Exception as e:
        logger.error(f"Error in get_job: {e}")
        return None
    
def get_favorite_templates(user_id: int) -> List[Dict]:
    """Get favorite templates for a user"""
    if not settings.USE_TURSO:
        return []
    try:
        with get_turso_client() as client:
            user_id_str = str(user_id)
            sql = f"""
                SELECT t.*, ut.last_used
                FROM templates t
                JOIN user_templates ut ON t.id = ut.template_id
                WHERE ut.user_id = {user_id_str} AND ut.is_favorite = 1
                ORDER BY ut.last_used DESC
            """
            rows = client.query(sql, [])
            templates = []
            for row in rows:
                template_dict = {
                    "id": int(get_value(row[0])) if get_value(row[0]) else None,
                    "title": get_value(row[1]),
                    "description": get_value(row[2]),
                    "genre": get_value(row[3]),
                    "content_structure": json.loads(get_value(row[4])) if get_value(row[4]) else {},
                    "prompt": get_value(row[5]),
                    "cover_image": get_value(row[6]),
                    "is_premium": bool(int(get_value(row[7]))) if get_value(row[7]) else False,
                    "usage_count": int(get_value(row[8])) if get_value(row[8]) else 0,
                    "created_by": int(get_value(row[9])) if get_value(row[9]) else None,
                    "created_at": get_value(row[10]),
                    "is_favorite": True
                }
                templates.append(template_dict)
            return templates
    except Exception as e:
        logger.error(f"Error in get_favorite_templates: {e}")
        return []