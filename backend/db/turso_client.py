import requests
import json
import logging
from typing import Any, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class TursoClient:
    def __init__(self, database_url: str, auth_token: str):
        parsed = urlparse(database_url)
        self.base_url = f"https://{parsed.netloc}"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        })
        
    def execute(self, sql: str, params: List[Any] = None):
        url = f"{self.base_url}/v2/pipeline"
        
        logger.info(f"Raw params in execute: {params}")
        
        formatted_params = []
        if params:
            for i, param in enumerate(params):
                logger.info(f"Param {i}: {param} (type: {type(param)})")
                if isinstance(param, str):
                    formatted_params.append({"type": "text", "value": param})
                elif isinstance(param, int):
                    formatted_params.append({"type": "integer", "value": str(param)})
                elif param is None:
                    formatted_params.append({"type": "null", "value": None})
                else:
                    formatted_params.append({"type": "text", "value": str(param)})
        
        logger.info(f"Formatted params: {formatted_params}")
        
        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql,
                        "params": formatted_params
                    }
                }
            ]
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            if response.status_code != 200:
                raise Exception(f"Database error: {response.status_code}")
            
            result = response.json()
            
            if 'results' in result and result['results']:
                if result['results'][0].get('type') == 'error':
                    error_msg = result['results'][0]['error']['message']
                    raise Exception(f"SQL error: {error_msg}")
            
            return result
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise
        
    def query(self, sql: str, params: List[Any] = None):
        result = self.execute(sql, params)
        rows = []
        if result and 'results' in result:
            for res in result['results']:
                if res.get('type') == 'ok' and 'response' in res:
                    response = res['response']
                    if 'result' in response and 'rows' in response['result']:
                        rows.extend(response['result']['rows'])
        return rows

    def query_one(self, sql: str, params: List[Any] = None):
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def close(self):
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False