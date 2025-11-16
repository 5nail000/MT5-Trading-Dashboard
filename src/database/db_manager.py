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
        """Initialize database tables and migrate if needed"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Initialize all tables
            for table_name, table_config in DatabaseConfig.TABLES.items():
                cursor.execute(table_config["schema"])
            
            # Migrate account_settings table if needed (add leverage and server columns)
            try:
                cursor.execute("ALTER TABLE account_settings ADD COLUMN leverage INTEGER")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE account_settings ADD COLUMN server TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
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
    
    def get_account_title(self, account_id: str) -> Optional[str]:
        """Get account title"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT account_title FROM account_settings WHERE account_id=?",
                (account_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def set_account_title(self, account_id: str, title: str):
        """Set account title (preserves leverage and server)"""
        self.set_account_settings(account_id, title=title)
    
    def get_account_settings(self, account_id: str) -> Dict[str, Any]:
        """Get all account settings (title, leverage, server)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT account_title, leverage, server FROM account_settings WHERE account_id=?",
                (account_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "account_title": result[0],
                    "leverage": result[1],
                    "server": result[2]
                }
            return {
                "account_title": None,
                "leverage": None,
                "server": None
            }
    
    def set_account_settings(self, account_id: str, title: str = None, 
                           leverage: int = None, server: str = None):
        """Set account settings (title, leverage, server)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Получаем текущие значения
            current = self.get_account_settings(account_id)
            
            # Используем переданные значения или текущие
            final_title = title if title is not None else current.get("account_title")
            final_leverage = leverage if leverage is not None else current.get("leverage")
            final_server = server if server is not None else current.get("server")
            
            cursor.execute(
                """INSERT OR REPLACE INTO account_settings 
                   (account_id, account_title, leverage, server) VALUES (?, ?, ?, ?)""",
                (account_id, final_title, final_leverage, final_server)
            )
            conn.commit()
    
    def get_account_leverage(self, account_id: str) -> Optional[int]:
        """Get account leverage"""
        settings = self.get_account_settings(account_id)
        return settings.get("leverage")
    
    def set_account_leverage(self, account_id: str, leverage: int):
        """Set account leverage"""
        self.set_account_settings(account_id, leverage=leverage)
    
    def get_account_server(self, account_id: str) -> Optional[str]:
        """Get account server"""
        settings = self.get_account_settings(account_id)
        return settings.get("server")
    
    def set_account_server(self, account_id: str, server: str):
        """Set account server"""
        self.set_account_settings(account_id, server=server)
    
    def create_magic_group(self, account_id: str, group_name: str) -> int:
        """Create a new magic group and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO magic_groups (account_id, name) VALUES (?, ?)",
                (account_id, group_name)
            )
            conn.commit()
            return cursor.lastrowid
    
    def add_magic_to_group(self, account_id: str, group_id: int, magic: int):
        """Add a magic number to a group"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO magic_group_assignments (account_id, group_id, magic) VALUES (?, ?, ?)",
                (account_id, group_id, magic)
            )
            conn.commit()
    
    def remove_magic_from_group(self, account_id: str, group_id: int, magic: int):
        """Remove a magic number from a group"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM magic_group_assignments WHERE account_id=? AND group_id=? AND magic=?",
                (account_id, group_id, magic)
            )
            conn.commit()
    
    def get_magic_groups(self, account_id: str) -> Dict[int, Dict]:
        """Get all magic groups for an account with their magics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get all groups
            cursor.execute(
                "SELECT id, name FROM magic_groups WHERE account_id=?",
                (account_id,)
            )
            groups = cursor.fetchall()
            
            result = {}
            for group_id, group_name in groups:
                # Get magics for this group
                cursor.execute(
                    "SELECT magic FROM magic_group_assignments WHERE account_id=? AND group_id=?",
                    (account_id, group_id)
                )
                magics = [row[0] for row in cursor.fetchall()]
                result[group_id] = {
                    "name": group_name,
                    "magics": magics
                }
            return result
    
    def get_magics_by_group(self, account_id: str) -> Dict[int, int]:
        """Get mapping of magic -> group_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT magic, group_id FROM magic_group_assignments WHERE account_id=?",
                (account_id,)
            )
            return dict(cursor.fetchall())
    
    def delete_magic_group(self, account_id: str, group_id: int):
        """Delete a magic group and all its assignments"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Delete assignments first
            cursor.execute(
                "DELETE FROM magic_group_assignments WHERE account_id=? AND group_id=?",
                (account_id, group_id)
            )
            # Delete group
            cursor.execute(
                "DELETE FROM magic_groups WHERE account_id=? AND id=?",
                (account_id, group_id)
            )
            conn.commit()
    
    def update_magic_group_name(self, account_id: str, group_id: int, new_name: str):
        """Update magic group name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE magic_groups SET name=? WHERE account_id=? AND id=?",
                (new_name, account_id, group_id)
            )
            conn.commit()
    
    def get_view_mode(self, account_id: str) -> str:
        """Get view mode (individual or grouped)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT view_mode FROM view_settings WHERE account_id=?",
                (account_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else "individual"
    
    def set_view_mode(self, account_id: str, mode: str):
        """Set view mode (individual or grouped)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO view_settings (account_id, view_mode) VALUES (?, ?)",
                (account_id, mode)
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
