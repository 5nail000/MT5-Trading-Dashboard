"""
MT5 Tick Data Provider
Handles downloading and storing tick data from MetaTrader 5
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from ..config.settings import Config
from ..database.tick_db_manager import tick_db_manager
from .mt5_client import MT5Connection


class MT5TickProvider:
    """Provides tick data from MetaTrader 5"""
    
    def __init__(self):
        self.connection = MT5Connection()
    
    def get_ticks_from_mt5(self, symbol: str, from_date: datetime, 
                          to_date: datetime, account: Dict[str, Any] = None) -> Optional[List]:
        """
        Get ticks from MT5 terminal for the specified symbol and date range
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            from_date: Start date (local time)
            to_date: End date (local time)
            account: Account info dict (optional)
            
        Returns:
            List of tick objects or None if error
        """
        if not self.connection.initialize(account):
            print(f"❌ Не удалось инициализировать подключение к MT5")
            return None
        
        # Convert local time to UTC for MT5 API
        from_date_utc = from_date - timedelta(hours=Config.LOCAL_TIMESHIFT)
        to_date_utc = to_date - timedelta(hours=Config.LOCAL_TIMESHIFT)
        
        print(f"   Запрос тиков: {from_date_utc.strftime('%Y-%m-%d %H:%M:%S')} - {to_date_utc.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
        
        # Check if symbol is available
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ Символ {symbol} не найден в MT5")
            self.connection.shutdown()
            return None
        
        if not symbol_info.visible:
            print(f"⚠️ Символ {symbol} не видим в Market Watch. Попытка добавить...")
            if not mt5.symbol_select(symbol, True):
                print(f"❌ Не удалось добавить символ {symbol} в Market Watch")
                self.connection.shutdown()
                return None
        
        # Get ticks from MT5
        ticks = mt5.copy_ticks_range(
            symbol,
            from_date_utc,
            to_date_utc,
            mt5.COPY_TICKS_ALL
        )
        
        error_code = mt5.last_error()
        # Check if it's actually an error (not success)
        # In MT5: code 0 or 1 with 'Success' message means success
        # Only show error if code > 1 or message is not 'Success'
        if error_code[0] > 1 or (error_code[0] != 0 and error_code[1] != 'Success'):
            print(f"⚠️ Ошибка MT5 при получении тиков: {error_code}")
        
        self.connection.shutdown()
        
        if ticks is None:
            print(f"❌ MT5 вернул None для тиков")
            return None
        
        ticks_list = list(ticks)
        if len(ticks_list) == 0:
            print(f"⚠️ MT5 вернул пустой список тиков")
        
        return ticks_list
    
    def get_server_name(self, account: Dict[str, Any] = None) -> Optional[str]:
        """Get server name from account info"""
        if not self.connection.initialize(account):
            return None
        
        account_info = self.connection.get_account_info()
        self.connection.shutdown()
        
        if account_info:
            return getattr(account_info, 'server', None)
        return None
    
    def download_and_save_ticks(self, symbol: str, from_date: datetime, 
                                to_date: datetime, account: Dict[str, Any] = None,
                                auto_fill_months: bool = True) -> Dict[str, Any]:
        """
        Download ticks from MT5 and save to database
        
        Args:
            symbol: Trading symbol
            from_date: Start date (local time)
            to_date: End date (local time)
            account: Account info dict (optional)
            auto_fill_months: If True, automatically download missing months
            
        Returns:
            Dict with download statistics
        """
        # Get server name
        server = self.get_server_name(account)
        if not server:
            # Try to get from account dict
            server = account.get('server', 'unknown') if account else 'unknown'
        
        # Initialize database if needed
        tick_db_manager.init_database(server)
        
        result = {
            "server": server,
            "symbol": symbol,
            "from_date": from_date,
            "to_date": to_date,
            "ticks_downloaded": 0,
            "months_processed": [],
            "errors": []
        }
        
        if auto_fill_months:
            # Get missing months in requested range
            missing_months = tick_db_manager.get_missing_months(
                server, symbol, from_date, to_date
            )
            
            if missing_months:
                # Determine download range for continuous data:
                # - If no data exists: download from first missing month to current moment
                # - If data exists: download from first missing month to first available month
                #   (to fill gaps and ensure continuous series)
                first_missing = missing_months[0]
                first_missing_date = datetime(first_missing[0], first_missing[1], 1)
                
                # Check if we have any data
                first_available = tick_db_manager.get_first_available_month(server, symbol)
                
                if first_available is None:
                    # No data exists - download from first missing month to current moment
                    download_to = datetime.now()
                    print(f"📥 Нет данных в БД. Загрузка от {first_missing_date.strftime('%Y-%m')} до текущего момента")
                else:
                    # Data exists - download from first missing month to first available month
                    # This ensures continuous series without gaps
                    first_available_date = datetime(first_available[0], first_available[1], 1)
                    download_to = first_available_date - timedelta(seconds=1)
                    print(f"📥 Данные есть в БД. Загрузка от {first_missing_date.strftime('%Y-%m')} до {first_available_date.strftime('%Y-%m')} для непрерывной серии")
                
                # Generate all months from first missing to download_to
                months_to_download = []
                current = first_missing_date
                while current <= download_to:
                    months_to_download.append((current.year, current.month))
                    # Move to next month
                    if current.month == 12:
                        current = datetime(current.year + 1, 1, 1)
                    else:
                        current = datetime(current.year, current.month + 1, 1)
                
                # Download data for each month
                # For new months: load full month
                # For existing months (current month update): load from last tick to now
                for year, month in months_to_download:
                    try:
                        # Check if this month already exists in DB (needs update, not full load)
                        month_key = (year, month)
                        available_ranges = tick_db_manager.get_available_ranges(server, symbol)
                        existing_range = next((r for r in available_ranges 
                                             if r["year"] == year and r["month"] == month), None)
                        
                        now = datetime.now()
                        is_current_month = (year == now.year and month == now.month)
                        
                        if existing_range and existing_range.get('last_tick_time'):
                            # Month exists - load only missing data
                            last_tick_dt = datetime.fromtimestamp(existing_range['last_tick_time'])
                            last_tick_dt_local = last_tick_dt + timedelta(hours=Config.LOCAL_TIMESHIFT)
                            
                            if is_current_month:
                                # Current month - load from last tick to now
                                month_start = last_tick_dt_local + timedelta(seconds=1)  # Start from next second after last tick
                                month_end = datetime.now()
                            else:
                                # Past month - load from last tick to end of month
                                month_start = last_tick_dt_local + timedelta(seconds=1)
                                if month == 12:
                                    month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
                                else:
                                    month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
                            
                            # Don't load if no time has passed
                            if month_start >= month_end:
                                print(f"⏭️ Месяц {year}-{month:02d} уже актуален (последний тик: {last_tick_dt_local.strftime('%Y-%m-%d %H:%M:%S')})")
                                continue
                            
                            print(f"🔄 Обновление месяца {year}-{month:02d} для {symbol} на сервере {server}: {month_start.strftime('%Y-%m-%d %H:%M:%S')} - {month_end.strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            # New month - load full month
                            month_start = datetime(year, month, 1)
                            # Last day of month (23:59:59)
                            if month == 12:
                                month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
                            else:
                                month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
                            
                            # For the last month, don't go beyond current moment
                            if month_end > datetime.now():
                                month_end = datetime.now()
                            
                            print(f"📥 Загрузка тиков для {symbol} на сервере {server}: весь месяц {month_start.strftime('%Y-%m')} ({month_start.strftime('%Y-%m-%d')} - {month_end.strftime('%Y-%m-%d')})")
                        
                        ticks = self.get_ticks_from_mt5(symbol, month_start, month_end, account)
                        
                        if ticks:
                            tick_db_manager.save_ticks(server, symbol, ticks)
                            result["ticks_downloaded"] += len(ticks)
                            result["months_processed"].append({
                                "year": year,
                                "month": month,
                                "ticks": len(ticks)
                            })
                            print(f"✅ Загружено {len(ticks)} тиков за {month_start.strftime('%Y-%m')}")
                        else:
                            result["errors"].append(f"No ticks for {year}-{month:02d}")
                            print(f"⚠️ Тики не найдены для {year}-{month:02d}")
                    except Exception as e:
                        error_msg = f"Error loading {year}-{month:02d}: {str(e)}"
                        result["errors"].append(error_msg)
                        print(f"❌ {error_msg}")
                        import traceback
                        traceback.print_exc()
        else:
            # Download only for the specified range
            ticks = self.get_ticks_from_mt5(symbol, from_date, to_date, account)
            if ticks:
                tick_db_manager.save_ticks(server, symbol, ticks)
                result["ticks_downloaded"] = len(ticks)
        
        return result
    
    def get_ticks_from_db(self, symbol: str, from_date: datetime, 
                         to_date: datetime, server: str = None,
                         account: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get ticks from database (with auto-download if missing)
        
        Args:
            symbol: Trading symbol
            from_date: Start date (local time)
            to_date: End date (local time)
            server: Server name (optional, will be detected if not provided)
            account: Account info dict (optional)
            
        Returns:
            List of tick dictionaries
        """
        # Get server name if not provided
        if not server:
            server = self.get_server_name(account)
            if not server:
                server = account.get('server', 'unknown') if account else 'unknown'
        
        # Initialize database for this server
        tick_db_manager.init_database(server)
        
        # Check for missing data and download if needed
        # For continuous series, we need to ensure all months in the requested range are loaded
        missing_months = tick_db_manager.get_missing_months(server, symbol, from_date, to_date)
        if missing_months:
            print(f"⚠️ Обнаружены недостающие месяцы для {symbol} на {server}: {missing_months}")
            print("📥 Начинаю загрузку недостающих данных (полные месяцы для непрерывной серии)...")
            
            # Calculate the range: from first missing month to last missing month
            first_missing = missing_months[0]
            last_missing = missing_months[-1]
            
            # Start from the beginning of the first missing month
            download_from = datetime(first_missing[0], first_missing[1], 1)
            
            # End at the end of the last missing month (or current moment if it's the current month)
            if last_missing[1] == 12:
                download_to = datetime(last_missing[0] + 1, 1, 1) - timedelta(seconds=1)
            else:
                download_to = datetime(last_missing[0], last_missing[1] + 1, 1) - timedelta(seconds=1)
            
            # Don't go beyond current moment
            if download_to > datetime.now():
                download_to = datetime.now()
            
            # Download full months to ensure continuous series
            self.download_and_save_ticks(symbol, download_from, download_to, account, auto_fill_months=True)
        
        # Get ticks from database
        return tick_db_manager.get_ticks(server, symbol, from_date, to_date)
    
    def get_high_low_prices(self, symbol: str, from_date: datetime, 
                           to_date: datetime, server: str = None,
                           account: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Get HIGH and LOW prices from tick data for the specified period
        
        Args:
            symbol: Trading symbol
            from_date: Start date (local time)
            to_date: End date (local time)
            server: Server name (optional, will be detected from account if not provided)
            account: Account info dict (optional)
            
        Returns:
            Dict with 'high' and 'low' prices (using ask for high, bid for low)
        """
        # Ensure server is determined
        if not server:
            server = self.get_server_name(account)
            if not server:
                server = account.get('server', None) if account else None
                if not server:
                    raise ValueError("Server must be provided or determined from account info")
        
        ticks = self.get_ticks_from_db(symbol, from_date, to_date, server=server, account=account)
        
        if not ticks:
            return {"high": None, "low": None}
        
        # Find highest ask and lowest bid
        high = max(tick["ask"] for tick in ticks)
        low = min(tick["bid"] for tick in ticks)
        
        return {"high": high, "low": low}


# Global tick provider instance
mt5_tick_provider = MT5TickProvider()

