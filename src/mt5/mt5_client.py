"""
MetaTrader 5 integration module
"""

import MetaTrader5 as mt5
import psutil
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from ..config.settings import Config


class MT5Connection:
    """Manages MetaTrader 5 connection"""
    
    def __init__(self):
        self.is_initialized = False
    
    def check_mt5_process(self) -> List[psutil.Process]:
        """Check for running MT5 processes"""
        return [proc for proc in psutil.process_iter() if 'terminal64.exe' in proc.name()]
    
    def initialize(self, account: Dict[str, Any] = None) -> bool:
        """Initialize MT5 connection"""
        mt5_processes = self.check_mt5_process()
        all_terminal_exes = False
        
        if mt5_processes:
            all_terminal_exes = [process.exe() for process in mt5_processes]
        
        # Try to initialize with specific terminal path
        if all_terminal_exes and not mt5.initialize(all_terminal_exes[0]):
            mt5.initialize()
        
        if not all_terminal_exes:
            mt5.initialize()
        
        # Login if account provided
        if account:
            authorized = mt5.login(
                account['login'], 
                account['password'], 
                account['server']
            )
            if not authorized:
                mt5.shutdown()
                return False
        
        self.is_initialized = True
        return True
    
    def shutdown(self):
        """Shutdown MT5 connection"""
        if self.is_initialized:
            mt5.shutdown()
            self.is_initialized = False
    
    def get_account_info(self) -> Optional[Any]:
        """Get account information"""
        if not self.is_initialized:
            return None
        return mt5.account_info()


class MT5DataProvider:
    """Provides data from MetaTrader 5"""
    
    def __init__(self):
        self.connection = MT5Connection()
    
    def get_history(self, account: Dict[str, Any] = None, 
                   from_date: datetime = None, 
                   to_date: datetime = None) -> Tuple[Optional[List], Optional[Any]]:
        """Get trading history"""
        if from_date is None:
            from_date = datetime(2020, 1, 1)
        if to_date is None:
            to_date = datetime.now() + timedelta(hours=Config.LOCAL_TIMESHIFT)
        
        if not self.connection.initialize(account):
            return None, None
        
        account_info = self.connection.get_account_info()
        if account_info is None:
            self.connection.shutdown()
            return None, None
        
        deals = mt5.history_deals_get(from_date, to_date)
        self.connection.shutdown()
        
        return deals, account_info
    
    def get_open_positions(self, account: Dict[str, Any] = None) -> Tuple[Optional[List], Optional[Any]]:
        """Get open positions"""
        if not self.connection.initialize(account):
            return None, None
        
        account_info = self.connection.get_account_info()
        if account_info is None:
            self.connection.shutdown()
            return None, None
        
        positions = mt5.positions_get()
        self.connection.shutdown()
        
        return list(positions), account_info


class MT5Calculator:
    """Calculates trading metrics"""
    
    @staticmethod
    def calculate_open_profits_by_magics(positions: List) -> Dict[str, Any]:
        """Calculate open profits grouped by magic numbers"""
        magic_profits = {}
        magics_total = {}
        magic_symbol_type = {}
        
        for pos in positions:
            if pos.type == 0:  # Buy
                type_str = "Buy"
            elif pos.type == 1:  # Sell
                type_str = "Sell"
            else:
                continue
            
            magic_key = pos.magic
            symbol_key = pos.symbol
            full_key = (magic_key, symbol_key, type_str)
            
            # Initialize nested dict
            if magic_key not in magic_symbol_type:
                magic_symbol_type[magic_key] = {}
            if symbol_key not in magic_symbol_type[magic_key]:
                magic_symbol_type[magic_key][symbol_key] = {}
            if type_str not in magic_symbol_type[magic_key][symbol_key]:
                magic_symbol_type[magic_key][symbol_key][type_str] = 0.0
            
            profit = pos.profit + pos.swap
            magic_symbol_type[magic_key][symbol_key][type_str] += profit
            
            # Update totals
            if magic_key not in magics_total:
                magics_total[magic_key] = 0.0
            magics_total[magic_key] += profit
            
            if full_key not in magic_profits:
                magic_profits[full_key] = 0.0
            magic_profits[full_key] += profit
        
        total_floating = sum(magics_total.values())
        return {
            "by_magic": magics_total,
            "total_floating": total_floating,
            "detailed": magic_symbol_type
        }
    
    @staticmethod
    def calculate_by_magics(deals: List, symbol: str = None, 
                          from_date: datetime = None, 
                          to_date: datetime = None) -> Dict[str, Any]:
        """Calculate profits grouped by magic numbers"""
        magic_profits = {}
        magics_summ = 0
        magic_total_sums = {}
        
        for deal in deals:
            if deal.type == 2:  # Balance changes
                continue
            if from_date and deal.time < from_date.timestamp():
                continue
            if to_date and deal.time > to_date.timestamp():
                continue
            
            magic_key = deal.magic
            if magic_key == 0:
                for d in deals:
                    if d.position_id == deal.position_id and d.magic != 0:
                        magic_key = d.magic
                        break
            
            symbol_key = deal.symbol if symbol is None else symbol
            key = (magic_key, symbol_key)
            
            if key not in magic_profits:
                magic_profits[key] = 0.0
            
            deal_profit = deal.profit + deal.commission + deal.swap
            magic_profits[key] += deal_profit
            magics_summ += deal_profit
            
            if magic_key not in magic_total_sums:
                magic_total_sums[magic_key] = 0.0
            magic_total_sums[magic_key] += deal_profit
        
        magic_profits["Summ"] = magics_summ
        if magic_total_sums and magic_total_sums.get(0) is not None:
            magic_profits["Summ only magics"] = magics_summ - magic_total_sums[0]
        magic_profits["Total by Magic"] = magic_total_sums
        
        return magic_profits


# Global instances
mt5_data_provider = MT5DataProvider()
mt5_calculator = MT5Calculator()
