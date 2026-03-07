import logging
from typing import Optional, List, Any, Dict
from datetime import datetime
import json

from db.database import get_turso_client, settings

logger = logging.getLogger(__name__)

def get_value(cell):
    """Helper function to extract value from Turso response cell"""
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
            
            check_sql = f"SELECT 1 FROM follows WHERE follower_id = {follower_id_str} AND followed_id = {followed_id_str}"
            existing = client.query_one(check_sql, [])
            
            if existing:
                delete_sql = f"DELETE FROM follows WHERE follower_id = {follower_id_str} AND followed_id = {followed_id_str}"
                client.execute(delete_sql, [])
                following = False
            else:
                insert_sql = f"INSERT INTO follows (follower_id, followed_id) VALUES ({follower_id_str}, {followed_id_str})"
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
    
    
def get_feed_stories(feed_type: str, timeframe: str, page: int = 1, limit: int = 20) -> List[Dict]:
    """Get stories for feed"""
    if not settings.USE_TURSO:
        return []
    with get_turso_client() as client:
        offset = (page - 1) * limit
        
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
                LIMIT ? OFFSET ?
            """
            rows = client.query(query, [limit, offset])
            
        elif feed_type == "latest":
            rows = client.query(
                """
                SELECT s.*, u.username, u.avatar_url
                FROM stories s
                JOIN users u ON s.user_id = u.id
                WHERE s.is_published = 1
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
                """,
                [limit, offset]
            )
        else:
            rows = client.query(
                """
                SELECT s.*, u.username, u.avatar_url
                FROM stories s
                JOIN users u ON s.user_id = u.id
                WHERE s.is_published = 1
                ORDER BY (s.view_count + s.like_count * 10) DESC
                LIMIT ? OFFSET ?
                """,
                [limit, offset]
            )
        return [story_to_dict(row) for row in rows]