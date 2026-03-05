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
        
        # Format based on the working test
        # The test showed that 'sql' field might be expected
        stmt = {
            "sql": sql,  # Changed from 'q' to 'sql'
            "params": params or []
        }
        
        payload = {
            "requests": [
                {"type": "execute", "stmt": stmt}
            ]
        }
        
        try:
            logger.debug(f"Executing SQL: {sql[:100]}...")
            logger.debug(f"Payload: {json.dumps(payload)[:200]}")
            
            response = self.session.post(url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Turso error: {response.status_code} - {response.text}")
                try:
                    error_data = response.json()
                    raise Exception(f"Database error: {error_data.get('error', response.text)}")
                except:
                    raise Exception(f"Database error: {response.status_code}")
            
            result = response.json()
            logger.debug(f"Query result: {str(result)[:200]}")
            return result
            
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise

    def query(self, sql: str, params: List[Any] = None):
        """Execute a query and return results"""
        result = self.execute(sql, params)
        
        # Parse the response format
        rows = []
        if result and 'results' in result:
            for res in result['results']:
                if res.get('type') == 'ok' and 'response' in res:
                    response = res['response']
                    if 'result' in response and 'rows' in response['result']:
                        rows.extend(response['result']['rows'])
        
        return rows

    def execute_batch(self, statements: List[tuple]):
        """Execute multiple statements in a transaction"""
        url = f"{self.base_url}/v2/pipeline"
        
        requests_list = []
        for sql, params in statements:
            requests_list.append({
                "type": "execute",
                "stmt": {"sql": sql, "params": params or []}
            })
        
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