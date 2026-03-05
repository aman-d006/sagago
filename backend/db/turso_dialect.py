# db/turso_dialect.py
from sqlalchemy.engine import Dialect
from sqlalchemy import exc
import logging
from .turso_client import TursoClient

logger = logging.getLogger(__name__)

class TursoDialect(Dialect):
    """SQLAlchemy dialect for Turso"""
    
    name = "turso"
    driver = "http"
    supports_statement_cache = True
    supports_alter = False
    supports_pk_autoincrement = True
    supports_default_values = True
    supports_empty_insert = False
    supports_multivalues_insert = True
    supports_native_enum = False
    supports_native_boolean = False
    supports_sane_rowcount = True
    supports_sane_multi_rowcount = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        
    def initialize(self, connection):
        super().initialize(connection)
        
    def create_connect_args(self, url):
        """Return connection arguments"""
        opts = url.translate_connect_args()
        if 'host' in opts:
            opts['database_url'] = f"libsql://{opts['host']}"
        if 'query' in url.query and 'authToken' in url.query:
            opts['auth_token'] = url.query['authToken']
        return ([], opts)
    
    def connect(self, *cargs, **cparams):
        """Create a connection"""
        database_url = cparams.get('database_url')
        auth_token = cparams.get('auth_token')
        
        if not database_url or not auth_token:
            raise exc.ArgumentError("database_url and auth_token required")
        
        self.client = TursoClient(database_url, auth_token)
        return self._Connection(self.client)
    
    class _Connection:
        def __init__(self, client):
            self.client = client
            
        def execute(self, sql, params=None):
            """Execute SQL synchronously"""
            if params is None:
                params = []
                
            # Convert params to list if needed
            if isinstance(params, dict):
                params = list(params.values())
                
            try:
                result = self.client.execute(sql, params)
                return self._TursoResult(result)
            except Exception as e:
                logger.error(f"Execute error: {e}")
                raise exc.DBAPIError(None, None, e)
        
        def close(self):
            self.client.close()
            
        class _TursoResult:
            def __init__(self, result):
                self.result = result
                
            def fetchall(self):
                rows = []
                if self.result and 'results' in self.result:
                    for res in self.result['results']:
                        if 'response' in res and 'result' in res['response']:
                            rows.extend(res['response']['result'].get('rows', []))
                return rows
                
            def fetchone(self):
                rows = self.fetchall()
                return rows[0] if rows else None
                
            def rowcount(self):
                return len(self.fetchall())
    
    def get_isolation_level(self, connection):
        return "AUTOCOMMIT"
    
    def set_isolation_level(self, connection, level):
        pass
    
    def get_columns(self, connection, table_name, schema=None, **kw):
        return []
    
    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        return {"constrained_columns": [], "name": None}
    
    def get_foreign_keys(self, connection, table_name, schema=None, **kw):
        return []
    
    def get_table_names(self, connection, schema=None, **kw):
        return []
    
    def get_view_names(self, connection, schema=None, **kw):
        return []
    
    def get_indexes(self, connection, table_name, schema=None, **kw):
        return []
    
    def has_table(self, connection, table_name, schema=None, **kw):
        return False