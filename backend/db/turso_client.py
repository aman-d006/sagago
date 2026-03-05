# db/turso_client.py
import requests
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class TursoClient:
    """HTTP client for Turso database using their REST API with requests"""
    
    def __init__(self, database_url: str, auth_token: str):
        # Parse the libsql URL to get the HTTP endpoint
        parsed = urlparse(database_url)
        # Convert libsql:// to https://
        self.base_url = f"https://{parsed.netloc}"
        self.auth_token = auth_token
        self.database = parsed.path.strip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        })
        
    def execute(self, sql: str, params: List[Any] = None):
        """Execute a SQL query synchronously"""
        url = f"{self.base_url}/v2/pipeline"
        
        # Format for Turso API
        stmt = {
            "q": sql,
            "params": params or []
        }
        
        payload = {
            "requests": [
                {"type": "execute", "stmt": stmt},
                {"type": "close"}
            ]
        }
        
        try:
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Turso error: {response.status_code} - {response.text}")
                raise Exception(f"Database error: {response.status_code}")
            
            return response.json()
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise

    def query(self, sql: str, params: List[Any] = None):
        """Execute a query and return results"""
        result = self.execute(sql, params)
        if result and 'results' in result and len(result['results']) > 0:
            return result['results'][0].get('response', {}).get('result', {}).get('rows', [])
        return []

    def execute_batch(self, statements: List[tuple]):
        """Execute multiple statements in a transaction"""
        url = f"{self.base_url}/v2/pipeline"
        
        requests_list = []
        for sql, params in statements:
            requests_list.append({
                "type": "execute",
                "stmt": {"q": sql, "params": params or []}
            })
        requests_list.append({"type": "close"})
        
        payload = {"requests": requests_list}
        
        try:
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                raise Exception(f"Database error: {response.status_code}")
            return response.json()
        except Exception as e:
            logger.error(f"Batch execute error: {e}")
            raise
    
    def close(self):
        """Close the session"""
        self.session.close()