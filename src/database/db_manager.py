"""
Database operations for MT5 Trading Dashboard
"""

import sqlite3
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from ..config.settings import DatabaseConfig


class DatabaseManager:
    """Manages database operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DatabaseConfig.DATABASE_PATH
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(DatabaseConfig.TABLES["magic_descriptions"]["schema"])
            conn.commit()
    
    def get_magic_description(self, account: str, magic: int) -> Optional[str]:
        """Get description for a magic number"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT description FROM magic_descriptions WHERE account=? AND magic=?",
                (account, magic)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def set_magic_description(self, account: str, magic: int, description: str):
        """Set description for a magic number"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO magic_descriptions (account, magic, description) VALUES (?, ?, ?)",
                (account, magic, description)
            )
            conn.commit()
    
    def get_all_magic_descriptions(self, account: str) -> Dict[int, str]:
        """Get all magic descriptions for an account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT magic, description FROM magic_descriptions WHERE account=?",
                (account,)
            )
            return dict(cursor.fetchall())
    
    def delete_magic_description(self, account: str, magic: int):
        """Delete magic description"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM magic_descriptions WHERE account=? AND magic=?",
                (account, magic)
            )
            conn.commit()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM magic_descriptions")
            total_descriptions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT account) FROM magic_descriptions")
            unique_accounts = cursor.fetchone()[0]
            
            return {
                "total_descriptions": total_descriptions,
                "unique_accounts": unique_accounts,
                "database_path": self.db_path
            }


# Global database manager instance
db_manager = DatabaseManager()
