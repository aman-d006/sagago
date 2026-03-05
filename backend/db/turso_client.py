# db/turso_client.py
import requests
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime, timedelta
from threading import Lock
import queue

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Connection pool for Turso clients"""
    
    def __init__(self, database_url: str, auth_token: str, max_connections: int = 5, timeout: int = 30):
        self.database_url = database_url
        self.auth_token = auth_token
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = queue.Queue(maxsize=max_connections)
        self._lock = Lock()
        self._active_connections = 0
        self._created_count = 0
        
        # Pre-create connections
        for _ in range(max_connections):
            self._create_connection()
    
    def _create_connection(self):
        """Create a new connection"""
        client = TursoClient(self.database_url, self.auth_token)
        self._pool.put(client)
        self._active_connections += 1
        self._created_count += 1
    
    def get_client(self, timeout: Optional[float] = None) -> 'TursoClient':
        """Get a client from the pool"""
        try:
            client = self._pool.get(timeout=timeout or self.timeout)
            # Test if connection is still alive
            try:
                client.query("SELECT 1")
                return client
            except:
                # Connection dead, create new one
                self._active_connections -= 1
                return self._create_and_get()
        except queue.Empty:
            logger.warning("Connection pool timeout, creating temporary connection")
            return self._create_temp_client()
    
    def _create_and_get(self):
        """Create and return a new client"""
        client = TursoClient(self.database_url, self.auth_token)
        self._active_connections += 1
        self._created_count += 1
        return client
    
    def _create_temp_client(self):
        """Create a temporary client (not pooled)"""
        self._created_count += 1
        return TursoClient(self.database_url, self.auth_token, pooled=False)
    
    def return_client(self, client):
        """Return a client to the pool"""
        if hasattr(client, 'pooled') and client.pooled:
            try:
                self._pool.put_nowait(client)
            except queue.Full:
                client.close()
                self._active_connections -= 1
        else:
            client.close()
    
    def close_all(self):
        """Close all connections"""
        while not self._pool.empty():
            try:
                client = self._pool.get_nowait()
                client.close()
                self._active_connections -= 1
            except:
                pass
    
    def get_stats(self):
        """Get pool statistics"""
        return {
            'active': self._active_connections,
            'pool_size': self._pool.qsize(),
            'created_total': self._created_count,
            'max_connections': self.max_connections
        }


class TursoClient:
    """HTTP client for Turso database with connection pooling support"""
    
    def __init__(self, database_url: str, auth_token: str, pooled: bool = True):
        # Parse the libsql URL to get the HTTP endpoint
        parsed = urlparse(database_url)
        # Convert libsql:// to https://
        self.base_url = f"https://{parsed.netloc}"
        self.auth_token = auth_token
        self.database = parsed.path.strip('/')
        self.pooled = pooled
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        })
        
        # Metrics
        self.read_count = 0
        self.write_count = 0
        self.error_count = 0
        self.last_used = datetime.now()
        
    def _extract_value(self, cell):
        """Extract actual value from Turso response cell"""
        if cell['type'] == 'integer':
            return int(cell['value'])
        elif cell['type'] == 'text':
            return cell['value']
        elif cell['type'] == 'float':
            return float(cell['value'])
        elif cell['type'] == 'blob':
            return cell['value']  # You might need base64 decode
        elif cell['type'] == 'null':
            return None
        return cell['value']
    
    def _parse_rows(self, result):
        """Parse rows from Turso response"""
        rows = []
        if result and 'results' in result and len(result['results']) > 0:
            for res in result['results']:
                if res.get('type') == 'ok' and 'response' in res:
                    response = res['response']
                    if 'result' in response and 'rows' in response['result']:
                        for row in response['result']['rows']:
                            parsed_row = [self._extract_value(cell) for cell in row]
                            rows.append(parsed_row)
        return rows
    
    def execute(self, sql: str, params: List[Any] = None):
        """Execute a SQL query synchronously"""
        url = f"{self.base_url}/v2/pipeline"
        
        # Track read/write
        sql_upper = sql.strip().upper()
        if sql_upper.startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
            self.write_count += 1
        else:
            self.read_count += 1
        
        stmt = {
            "sql": sql,
            "params": params or []
        }
        
        payload = {
            "requests": [
                {"type": "execute", "stmt": stmt}
            ]
        }
        
        self.last_used = datetime.now()
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code != 200:
                self.error_count += 1
                logger.error(f"Turso error: {response.status_code} - {response.text}")
                try:
                    error_data = response.json()
                    raise Exception(f"Database error: {error_data.get('error', response.text)}")
                except:
                    raise Exception(f"Database error: {response.status_code}")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            self.error_count += 1
            logger.error(f"Turso timeout for query: {sql[:100]}")
            raise Exception("Database timeout")
        except Exception as e:
            self.error_count += 1
            logger.error(f"Execute error: {e}")
            raise

    def query(self, sql: str, params: List[Any] = None):
        """Execute a query and return parsed results"""
        result = self.execute(sql, params)
        return self._parse_rows(result)

    def query_one(self, sql: str, params: List[Any] = None):
        """Execute a query and return first row"""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def query_value(self, sql: str, params: List[Any] = None):
        """Execute a query and return first value of first row"""
        row = self.query_one(sql, params)
        return row[0] if row else None

    def execute_batch(self, statements: List[Tuple[str, List[Any]]]):
        """Execute multiple statements in a transaction"""
        url = f"{self.base_url}/v2/pipeline"
        
        requests_list = []
        for sql, params in statements:
            sql_upper = sql.strip().upper()
            if sql_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
                self.write_count += 1
            else:
                self.read_count += 1
                
            requests_list.append({
                "type": "execute",
                "stmt": {"sql": sql, "params": params or []}
            })
        
        payload = {"requests": requests_list}
        
        try:
            response = self.session.post(url, json=payload, timeout=60)
            if response.status_code != 200:
                raise Exception(f"Database error: {response.status_code}")
            return response.json()
        except Exception as e:
            self.error_count += 1
            logger.error(f"Batch execute error: {e}")
            raise
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def get_stats(self):
        """Get client statistics"""
        return {
            'reads': self.read_count,
            'writes': self.write_count,
            'errors': self.error_count,
            'last_used': self.last_used.isoformat(),
            'pooled': self.pooled
        }


# Global connection pool
_pool = None
_pool_lock = Lock()

def init_pool(database_url: str, auth_token: str, max_connections: int = 5):
    """Initialize the global connection pool"""
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = ConnectionPool(database_url, auth_token, max_connections)
            logger.info(f"Initialized Turso connection pool with {max_connections} connections")
    return _pool

def get_client():
    """Get a client from the global pool"""
    global _pool
    if _pool is None:
        raise Exception("Connection pool not initialized. Call init_pool first.")
    return _pool.get_client()

def return_client(client):
    """Return a client to the global pool"""
    global _pool
    if _pool is not None:
        _pool.return_client(client)

def close_pool():
    """Close all connections in the pool"""
    global _pool
    if _pool is not None:
        _pool.close_all()
        _pool = None

def get_pool_stats():
    """Get pool statistics"""
    global _pool
    if _pool is not None:
        return _pool.get_stats()
    return None