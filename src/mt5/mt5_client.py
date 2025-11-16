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
            to_date = datetime.now()
        
        # Convert local time to UTC for MT5 API
        from_date_utc = from_date - timedelta(hours=Config.LOCAL_TIMESHIFT)
        to_date_utc = to_date - timedelta(hours=Config.LOCAL_TIMESHIFT)
        
        if not self.connection.initialize(account):
            return None, None
        
        account_info = self.connection.get_account_info()
        if account_info is None:
            self.connection.shutdown()
            return None, None
        
        deals = mt5.history_deals_get(from_date_utc, to_date_utc)
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
    def calculate_balance_at_date(target_date: datetime, deals: List, 
                                 initial_balance: float = None, 
                                 end_of_day: bool = False,
                                 use_exact_time: bool = False) -> float:
        """
        Вычисляет баланс на указанную дату
        
        Args:
            target_date: Дата и время, на которые нужно вычислить баланс
            deals: Список всех сделок из истории
            initial_balance: Начальный баланс (если None, используется 0)
            end_of_day: Если True - баланс на конец дня (23:59:59), 
                       если False - баланс на начало дня (00:00:00)
            use_exact_time: Если True - использует точное время из target_date,
                          если False - использует начало/конец дня
            
        Returns:
            Баланс на указанную дату и время
        """
        
        if not deals:
            return initial_balance or 0.0
        
        # Если initial_balance не указан, используем 0 (начинаем с самого начала)
        if initial_balance is None:
            initial_balance = 0.0
        
        # Конвертируем местное время в UTC для сравнения с данными MT5
        if use_exact_time:
            # Используем точное время из target_date
            target_date_time = target_date
        elif end_of_day:
            # Используем конец дня (23:59:59) в местном времени
            target_date_time = target_date.replace(hour=23, minute=59, second=59)
        else:
            # Используем начало дня (00:00:00) в местном времени
            target_date_time = target_date.replace(hour=0, minute=0, second=0)
        
        target_date_utc = target_date_time + timedelta(hours=Config.LOCAL_TIMESHIFT)
        target_timestamp = target_date_utc.timestamp()
        
        # Сортируем сделки по времени
        sorted_deals = sorted(deals, key=lambda x: x.time)
        
        # Начинаем с начального баланса и добавляем сделки до указанной даты
        balance = initial_balance
        
        for deal in sorted_deals:
            # Пропускаем сделки после целевой даты
            if deal.time > target_timestamp:
                break
            
            # Учитываем только сделки изменения баланса (type == 2)
            if deal.type == 2:
                balance += deal.profit
            else:
                # Для обычных сделок добавляем прибыль/убыток
                balance += deal.profit + deal.commission + deal.swap
        
        return balance
    
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
                          to_date: datetime = None,
                          magic_groups: Optional[Dict[int, List[int]]] = None) -> Dict[str, Any]:
        """Calculate profits grouped by magic numbers or groups"""
        magic_profits = {}
        magics_summ = 0
        magic_total_sums = {}
        
        # Create reverse mapping: magic -> group_id (if grouped)
        magic_to_group = {}
        if magic_groups:
            for group_id, magics in magic_groups.items():
                for magic in magics:
                    magic_to_group[magic] = group_id
        
        for deal in deals:
            deal_time = datetime.fromtimestamp(deal.time) - timedelta(hours=Config.LOCAL_TIMESHIFT)
            if deal.type == 2:  # Balance changes
                continue
            if from_date and deal_time < from_date:
                continue
            if to_date and deal_time > to_date:
                continue
            
            magic_key = deal.magic
            if magic_key == 0:
                for d in deals:
                    if d.position_id == deal.position_id and d.magic != 0:
                        magic_key = d.magic
                        break
            
            # If grouping is enabled, use group_id instead of magic_key
            display_key = magic_key
            if magic_groups and magic_key in magic_to_group:
                display_key = magic_to_group[magic_key]
            
            symbol_key = deal.symbol if symbol is None else symbol
            key = (display_key, symbol_key)
            
            if key not in magic_profits:
                magic_profits[key] = 0.0
            
            deal_profit = deal.profit + deal.commission + deal.swap
            magic_profits[key] += deal_profit
            magics_summ += deal_profit
            
            if display_key not in magic_total_sums:
                magic_total_sums[display_key] = 0.0
            magic_total_sums[display_key] += deal_profit
        
        magic_profits["Summ"] = magics_summ
        if magic_total_sums and magic_total_sums.get(0) is not None:
            magic_profits["Summ only magics"] = magics_summ - magic_total_sums[0]
        magic_profits["Total by Magic"] = magic_total_sums
        
        return magic_profits
    
    @staticmethod
    def get_positions_timeline(from_date: datetime, to_date: datetime, 
                               magics: List[int], deals: List,
                               account: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Получает серию временных промежутков с пулом позиций
        
        Args:
            from_date: Время начала среза (IN)
            to_date: Время конца среза (OUT)
            magics: Список мэджиков для фильтрации
            deals: Список всех сделок из истории (должен включать период до from_date)
            account: Информация об аккаунте (опционально, для получения баланса)
            
        Returns:
            Список словарей, каждый содержит:
            - 'positions': список позиций (каждая с symbol, direction, volume, price_open, magic)
            - 'time_in': время начала промежутка
            - 'time_out': время конца промежутка
            - 'balance': баланс на начало промежутка
                * Для первого промежутка баланс рассчитывается через calculate_balance_at_date
                * Для последующих промежутков баланс накапливается: начальный + все изменения
                  (SWAP, комиссии, прибыль при закрытии позиций)
                * При закрытии позиции учитывается двойная комиссия (открытие + закрытие)
        """
        # Конвертируем даты в UTC timestamp
        from_date_utc = from_date - timedelta(hours=Config.LOCAL_TIMESHIFT)
        to_date_utc = to_date - timedelta(hours=Config.LOCAL_TIMESHIFT)
        from_timestamp = from_date_utc.timestamp()
        to_timestamp = to_date_utc.timestamp()
        
        # Фильтруем сделки (исключаем изменения баланса)
        trading_deals = [d for d in deals if d.type != 2]
        
        # Создаем маппинг position_id -> magic (для связи позиций с нулевым мэджиком)
        position_id_to_magic = {}
        for deal in trading_deals:
            if deal.position_id != 0 and deal.magic != 0:
                position_id_to_magic[deal.position_id] = deal.magic
        
        # Находим релевантные position_id (позиции с нужными мэджиками)
        relevant_position_ids = set()
        for deal in trading_deals:
            deal_magic = deal.magic
            position_id = deal.position_id
            
            # Определяем мэджик позиции
            if deal_magic in magics:
                relevant_position_ids.add(position_id)
            elif position_id != 0 and position_id in position_id_to_magic:
                if position_id_to_magic[position_id] in magics:
                    relevant_position_ids.add(position_id)
        
        # Получаем ВСЕ сделки для релевантных позиций (включая открытие до from_date)
        all_relevant_deals = []
        for deal in trading_deals:
            if deal.position_id in relevant_position_ids:
                all_relevant_deals.append(deal)
        
        # Сортируем сделки по времени и deal номеру
        all_relevant_deals.sort(key=lambda x: (x.time, x.deal if hasattr(x, 'deal') else 0))
        
        # Восстанавливаем состояние позиций на начало периода
        # Позиция считается открытой, если есть сделки открытия до from_timestamp
        # и нет сделок закрытия до from_timestamp
        positions_at_start = {}  # position_id -> позиция
        
        for deal in all_relevant_deals:
            if deal.time >= from_timestamp:
                break
            
            position_id = deal.position_id
            if position_id == 0:
                continue
            
            entry = deal.entry  # 0 = in (открытие), 1 = out (закрытие)
            
            if entry == 0:  # Сделка открытия
                if position_id not in positions_at_start:
                    # Определяем мэджик для позиции
                    magic = deal.magic
                    if magic == 0 and position_id in position_id_to_magic:
                        magic = position_id_to_magic[position_id]
                    
                    positions_at_start[position_id] = {
                        'position_id': position_id,
                        'symbol': deal.symbol,
                        'direction': 'Buy' if deal.type == 0 else 'Sell',
                        'volume': abs(deal.volume),
                        'price_open': deal.price,
                        'magic': magic,
                        'total_volume': abs(deal.volume),
                        'total_price_volume': deal.price * abs(deal.volume)  # Для расчета средней цены
                    }
                else:
                    # Добавляем объем к существующей позиции
                    pos = positions_at_start[position_id]
                    pos['total_volume'] += abs(deal.volume)
                    pos['total_price_volume'] += deal.price * abs(deal.volume)
                    pos['price_open'] = pos['total_price_volume'] / pos['total_volume']
            elif entry == 1:  # Сделка закрытия
                if position_id in positions_at_start:
                    # Уменьшаем объем или удаляем позицию
                    close_volume = abs(deal.volume)
                    pos = positions_at_start[position_id]
                    pos['total_volume'] -= close_volume
                    if pos['total_volume'] <= 0:
                        del positions_at_start[position_id]
                    else:
                        # Пересчитываем среднюю цену (упрощенно, без учета закрытого объема)
                        # В реальности нужно учитывать FIFO или другую логику
                        pass
        
        # Теперь проходим по сделкам в периоде и отслеживаем изменения
        timeline = []
        current_positions = {}
        for pid, pos in positions_at_start.items():
            current_positions[pid] = {
                'position_id': pos['position_id'],
                'symbol': pos['symbol'],
                'direction': pos['direction'],
                'volume': pos['total_volume'],
                'price_open': pos['price_open'],
                'magic': pos['magic'],
                'total_volume': pos['total_volume'],
                'total_price_volume': pos['total_price_volume']
            }
        
        # Добавляем начальное состояние
        # Баланс для первого промежутка рассчитывается через calculate_balance_at_date
        initial_balance = MT5Calculator.calculate_balance_at_date(
            from_date, deals, use_exact_time=True
        )
        
        timeline.append({
            'positions': [{
                'symbol': pos['symbol'],
                'direction': pos['direction'],
                'volume': pos['total_volume'],
                'price_open': pos['price_open'],
                'magic': pos['magic']
            } for pos in current_positions.values()],
            'time_in': from_date,
            'time_out': None,  # Будет установлено при следующем изменении
            'balance': initial_balance
        })
        
        # Текущий баланс для накопления изменений
        current_balance = initial_balance
        
        # Обрабатываем сделки в периоде
        for deal in all_relevant_deals:
            if deal.time < from_timestamp:
                continue
            if deal.time > to_timestamp:
                break
            
            position_id = deal.position_id
            if position_id == 0:
                continue
            
            entry = deal.entry
            deal_time_local = datetime.fromtimestamp(deal.time) - timedelta(hours=Config.LOCAL_TIMESHIFT)
            positions_changed = False
            balance_change = 0.0  # Изменение баланса от этой сделки
            
            if entry == 0:  # Сделка открытия
                if position_id not in current_positions:
                    # Новая позиция
                    magic = deal.magic
                    if magic == 0 and position_id in position_id_to_magic:
                        magic = position_id_to_magic[position_id]
                    
                    current_positions[position_id] = {
                        'position_id': position_id,
                        'symbol': deal.symbol,
                        'direction': 'Buy' if deal.type == 0 else 'Sell',
                        'volume': abs(deal.volume),
                        'price_open': deal.price,
                        'magic': magic,
                        'total_volume': abs(deal.volume),
                        'total_price_volume': deal.price * abs(deal.volume)
                    }
                    positions_changed = True
                else:
                    # Добавляем объем к существующей позиции
                    pos = current_positions[position_id]
                    new_volume = abs(deal.volume)
                    pos['total_volume'] += new_volume
                    pos['total_price_volume'] += deal.price * new_volume
                    pos['price_open'] = pos['total_price_volume'] / pos['total_volume']
                    pos['volume'] = pos['total_volume']
                    positions_changed = True
                
                # При открытии учитываем только SWAP (если есть)
                # Комиссия за открытие будет учтена при закрытии
                balance_change = deal.swap if hasattr(deal, 'swap') else 0.0
            
            elif entry == 1:  # Сделка закрытия или SWAP
                close_volume = abs(deal.volume)
                
                if position_id in current_positions:
                    # Позиция существует - это может быть закрытие или SWAP
                    pos = current_positions[position_id]
                    
                    if close_volume > 0:
                        # Это закрытие позиции (полное или частичное)
                        pos['total_volume'] -= close_volume
                        
                        if pos['total_volume'] <= 0:
                            # Позиция полностью закрыта
                            del current_positions[position_id]
                            positions_changed = True
                        else:
                            # Позиция частично закрыта
                            pos['volume'] = pos['total_volume']
                            positions_changed = True
                    
                    # При закрытии учитываем:
                    # - Прибыль/убыток (profit)
                    # - SWAP
                    # - Двойную комиссию (открытие + закрытие), только если это реальное закрытие
                    profit = deal.profit if hasattr(deal, 'profit') else 0.0
                    swap = deal.swap if hasattr(deal, 'swap') else 0.0
                    commission = deal.commission if hasattr(deal, 'commission') else 0.0
                    
                    if close_volume > 0:
                        # Реальное закрытие - двойная комиссия
                        balance_change = profit + swap + (commission * 2)
                    else:
                        # Только SWAP-сделка (volume=0 или очень маленький)
                        balance_change = swap
                else:
                    # Позиция уже закрыта ранее, но есть SWAP или другая сделка
                    # Учитываем только SWAP (комиссия и profit уже были учтены при закрытии)
                    swap = deal.swap if hasattr(deal, 'swap') else 0.0
                    balance_change = swap
            
            # Примечание: В MT5 SWAP обычно включается в сделку закрытия (entry=1)
            # Отдельные SWAP-сделки для открытых позиций также имеют entry=1,
            # но они обрабатываются выше в блоке закрытия
            
            # Накапливаем изменение баланса
            current_balance += balance_change
            
            # Если пул позиций изменился, создаем новый элемент в timeline
            if positions_changed:
                # Закрываем предыдущий промежуток
                if timeline:
                    timeline[-1]['time_out'] = deal_time_local
                
                # Для последующих промежутков используем накопленный баланс
                # Добавляем новый промежуток
                timeline.append({
                    'positions': [{
                        'symbol': pos['symbol'],
                        'direction': pos['direction'],
                        'volume': pos['total_volume'],
                        'price_open': pos['price_open'],
                        'magic': pos['magic']
                    } for pos in current_positions.values()],
                    'time_in': deal_time_local,
                    'time_out': None,  # Будет установлено при следующем изменении
                    'balance': current_balance
                })
            # Если пул не изменился, но баланс изменился (например, SWAP),
            # обновляем баланс в последнем промежутке
            elif balance_change != 0 and timeline:
                timeline[-1]['balance'] = current_balance
        
        # Закрываем последний промежуток
        if timeline:
            timeline[-1]['time_out'] = to_date
        
        return timeline


# Global instances
mt5_data_provider = MT5DataProvider()
mt5_calculator = MT5Calculator()
