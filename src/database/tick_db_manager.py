"""
Database operations for tick data storage (uncompressed)
Stores ticks directly, one DB file per server
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from ..config.settings import Config


class TickDatabaseManager:
    """Manages uncompressed tick data database operations"""
    
    def __init__(self, data_dir: str = "ticks_data"):
        self.data_dir = data_dir
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_db_path(self, server: str) -> str:
        """Get database file path for a server"""
        # Sanitize server name for filename
        safe_server_name = server.replace('/', '_').replace('\\', '_').replace(':', '_')
        return os.path.join(self.data_dir, f"{safe_server_name}.db")
    
    @contextmanager
    def get_connection(self, server: str):
        """Context manager for database connections"""
        db_path = self.get_db_path(server)
        conn = sqlite3.connect(db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self, server: str):
        """Initialize tick database tables for a server"""
        with self.get_connection(server) as conn:
            cursor = conn.cursor()
            
            # Table for storing tick data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticks
                (
                    symbol TEXT NOT NULL,
                    time INTEGER NOT NULL,
                    bid REAL NOT NULL,
                    ask REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    flags INTEGER,
                    PRIMARY KEY(symbol, time)
                )
            """)
            
            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time
                ON ticks(symbol, time)
            """)
            
            # Table for tracking available data ranges per symbol
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tick_ranges
                (
                    symbol TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    first_tick_time INTEGER,
                    last_tick_time INTEGER,
                    tick_count INTEGER DEFAULT 0,
                    PRIMARY KEY(symbol, year, month)
                )
            """)
            
            # Index for range queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ranges_symbol
                ON tick_ranges(symbol, year, month)
            """)
            
            conn.commit()
    
    def save_ticks(self, server: str, symbol: str, ticks: List[Any]):
        """
        Save ticks to database
        ticks: list of MT5 tick objects (with time, bid, ask, volume, flags attributes)
        """
        if not ticks:
            return
        
        # Initialize database if needed
        self.init_database(server)
        
        with self.get_connection(server) as conn:
            cursor = conn.cursor()
            
            # Prepare data for bulk insert
            tick_data = []
            months_data = {}  # Track data per month for ranges
            
            for tick in ticks:
                # Extract tick data
                try:
                    if hasattr(tick, 'dtype') and tick.dtype.names:
                        tick_time = int(tick['time'])
                        tick_bid = float(tick['bid'])
                        tick_ask = float(tick['ask'])
                        tick_volume = int(tick['volume'])
                        tick_flags = int(tick['flags'] if 'flags' in tick.dtype.names else 0)
                    elif isinstance(tick, dict):
                        tick_time = int(tick['time'])
                        tick_bid = float(tick['bid'])
                        tick_ask = float(tick['ask'])
                        tick_volume = int(tick.get('volume', 0))
                        tick_flags = int(tick.get('flags', 0))
                    elif hasattr(tick, 'time'):
                        tick_time = int(tick.time)
                        tick_bid = float(tick.bid)
                        tick_ask = float(tick.ask)
                        tick_volume = int(tick.volume)
                        tick_flags = int(getattr(tick, 'flags', 0))
                    else:
                        tick_time = int(tick[0])
                        tick_bid = float(tick[1])
                        tick_ask = float(tick[2])
                        tick_volume = int(tick[3])
                        tick_flags = int(tick[4] if len(tick) > 4 else 0)
                except (AttributeError, KeyError, IndexError, TypeError) as e:
                    print(f"⚠️ Ошибка доступа к полям тика: {e}, тип: {type(tick)}")
                    continue
                
                tick_dt = datetime.fromtimestamp(tick_time)
                year = tick_dt.year
                month = tick_dt.month
                
                # Store tick data
                tick_data.append((
                    symbol,
                    tick_time,
                    tick_bid,
                    tick_ask,
                    tick_volume,
                    tick_flags
                ))
                
                # Track month ranges
                month_key = (year, month)
                if month_key not in months_data:
                    months_data[month_key] = {
                        'first_time': tick_time,
                        'last_time': tick_time,
                        'count': 0
                    }
                else:
                    months_data[month_key]['first_time'] = min(
                        months_data[month_key]['first_time'], tick_time
                    )
                    months_data[month_key]['last_time'] = max(
                        months_data[month_key]['last_time'], tick_time
                    )
                months_data[month_key]['count'] += 1
            
            # Bulk insert ticks (ignore duplicates)
            cursor.executemany("""
                INSERT OR IGNORE INTO ticks 
                (symbol, time, bid, ask, volume, flags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, tick_data)
            
            # Update month ranges
            for (year, month), data in months_data.items():
                cursor.execute("""
                    SELECT first_tick_time, last_tick_time, tick_count FROM tick_ranges
                    WHERE symbol=? AND year=? AND month=?
                """, (symbol, year, month))
                existing = cursor.fetchone()
                
                if existing:
                    existing_first = existing[0]
                    existing_last = existing[1]
                    existing_count = existing[2]
                    
                    final_first = min(existing_first, data['first_time']) if existing_first else data['first_time']
                    final_last = max(existing_last, data['last_time']) if existing_last else data['last_time']
                    final_count = existing_count + data['count']
                else:
                    final_first = data['first_time']
                    final_last = data['last_time']
                    final_count = data['count']
                
                cursor.execute("""
                    INSERT OR REPLACE INTO tick_ranges
                    (symbol, year, month, first_tick_time, last_tick_time, tick_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (symbol, year, month, final_first, final_last, final_count))
            
            conn.commit()
    
    def get_ticks(self, server: str, symbol: str, 
                  from_time: datetime, to_time: datetime) -> List[Dict[str, Any]]:
        """Get ticks from database"""
        self.init_database(server)
        
        from_timestamp = int((from_time - timedelta(hours=Config.LOCAL_TIMESHIFT)).timestamp())
        to_timestamp = int((to_time - timedelta(hours=Config.LOCAL_TIMESHIFT)).timestamp())
        
        with self.get_connection(server) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT time, bid, ask, volume, flags FROM ticks
                WHERE symbol = ? AND time BETWEEN ? AND ?
                ORDER BY time
            """, (symbol, from_timestamp, to_timestamp))
            
            results = cursor.fetchall()
            return [
                {
                    "time": row[0],
                    "bid": row[1],
                    "ask": row[2],
                    "volume": row[3],
                    "flags": row[4]
                }
                for row in results
            ]
    
    def get_available_ranges(self, server: str, symbol: str) -> List[Dict[str, Any]]:
        """Get available data ranges for symbol"""
        self.init_database(server)
        
        with self.get_connection(server) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT year, month, first_tick_time, last_tick_time, tick_count
                FROM tick_ranges
                WHERE symbol = ?
                ORDER BY year, month
            """, (symbol,))
            
            results = cursor.fetchall()
            return [
                {
                    "year": row[0],
                    "month": row[1],
                    "first_tick_time": row[2],
                    "last_tick_time": row[3],
                    "tick_count": row[4]
                }
                for row in results
            ]
    
    def get_missing_months(self, server: str, symbol: str, 
                          from_date: datetime, to_date: datetime) -> List[Tuple[int, int]]:
        """
        Get list of missing months (year, month) for the given date range
        Also checks if current month needs update (has data but not up to requested date)
        """
        self.init_database(server)
        
        # Get all months in the range
        required_months = set()
        current = datetime(from_date.year, from_date.month, 1)
        end = datetime(to_date.year, to_date.month, 1)
        
        while current <= end:
            required_months.add((current.year, current.month))
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
        
        # Get available months from DB with their last tick times
        available_ranges = self.get_available_ranges(server, symbol)
        available_months = {}
        for r in available_ranges:
            key = (r["year"], r["month"])
            if key not in available_months:
                available_months[key] = r
        
        # Check each required month
        missing = []
        now = datetime.now()
        
        for year, month in required_months:
            month_key = (year, month)
            
            if month_key not in available_months:
                # Month completely missing
                missing.append((year, month))
            else:
                # Month exists, but check if we need more data
                range_info = available_months[month_key]
                last_tick_time = range_info.get('last_tick_time')
                
                if last_tick_time:
                    last_tick_dt = datetime.fromtimestamp(last_tick_time)
                    # Convert to local time for comparison
                    last_tick_dt_local = last_tick_dt + timedelta(hours=Config.LOCAL_TIMESHIFT)
                    
                    # If we need data beyond what we have
                    # For current or future months, always check if we need update
                    if (year == now.year and month == now.month):
                        # Current month - check if we need data after the last tick
                        if to_date > last_tick_dt_local:
                            missing.append((year, month))  # Need to update current month
                    elif (year > now.year) or (year == now.year and month > now.month):
                        # Future month - should not happen, but include it
                        missing.append((year, month))
                    # For past months, if to_date is beyond last_tick, we need more data
                    elif to_date > last_tick_dt_local:
                        missing.append((year, month))
                else:
                    # Month exists but has no data
                    missing.append((year, month))
        
        return sorted(list(set(missing)))
    
    def get_first_available_month(self, server: str, symbol: str) -> Optional[Tuple[int, int]]:
        """Get first available month (year, month) for symbol"""
        ranges = self.get_available_ranges(server, symbol)
        if not ranges:
            return None
        
        earliest = min(ranges, key=lambda x: (x["year"], x["month"]))
        return (earliest["year"], earliest["month"])
    
    def recalculate_ranges(self, server: str, symbol: str = None):
        """
        Пересчитать диапазоны на основе реальных данных в ticks
        
        Args:
            server: Сервер для пересчета
            symbol: Если указан, пересчитать только для этого символа
        """
        self.init_database(server)
        
        with self.get_connection(server) as conn:
            cursor = conn.cursor()
            
            # Удалить существующие диапазоны
            if symbol:
                cursor.execute("DELETE FROM tick_ranges WHERE symbol=?", (symbol,))
            else:
                cursor.execute("DELETE FROM tick_ranges")
            
            # Пересчитать диапазоны на основе тиков
            if symbol:
                query = """
                    SELECT 
                        symbol,
                        CAST(strftime('%Y', datetime(time, 'unixepoch')) AS INTEGER) as year,
                        CAST(strftime('%m', datetime(time, 'unixepoch')) AS INTEGER) as month,
                        MIN(time) as first_tick_time,
                        MAX(time) as last_tick_time,
                        COUNT(*) as tick_count
                    FROM ticks
                    WHERE symbol = ?
                    GROUP BY symbol, year, month
                """
                cursor.execute(query, (symbol,))
            else:
                query = """
                    SELECT 
                        symbol,
                        CAST(strftime('%Y', datetime(time, 'unixepoch')) AS INTEGER) as year,
                        CAST(strftime('%m', datetime(time, 'unixepoch')) AS INTEGER) as month,
                        MIN(time) as first_tick_time,
                        MAX(time) as last_tick_time,
                        COUNT(*) as tick_count
                    FROM ticks
                    GROUP BY symbol, year, month
                """
                cursor.execute(query)
            
            ranges = cursor.fetchall()
            
            # Вставить пересчитанные диапазоны
            for sym, yr, mn, first_time, last_time, count in ranges:
                cursor.execute("""
                    INSERT INTO tick_ranges
                    (symbol, year, month, first_tick_time, last_tick_time, tick_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sym, yr, mn, int(first_time), int(last_time), count))
            
            conn.commit()
            print(f"✅ Пересчитано диапазонов: {len(ranges)}")
    
    def get_statistics(self, server: str) -> Dict[str, Any]:
        """Get database statistics for a server"""
        self.init_database(server)
        
        with self.get_connection(server) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM ticks")
            total_ticks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ticks")
            unique_symbols = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tick_ranges")
            total_ranges = cursor.fetchone()[0]
            
            db_path = self.get_db_path(server)
            size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            
            return {
                "server": server,
                "total_ticks": total_ticks,
                "unique_symbols": unique_symbols,
                "total_month_ranges": total_ranges,
                "database_path": db_path,
                "database_size_mb": size_bytes / (1024 * 1024) if size_bytes > 0 else 0
            }


# Global uncompressed tick database manager instance
tick_db_manager = TickDatabaseManager()

