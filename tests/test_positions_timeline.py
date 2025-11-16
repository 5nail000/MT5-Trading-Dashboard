"""
Тест функции get_positions_timeline
"""

import sys
import os
from datetime import datetime

# Добавляем корневую папку проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mt5.mt5_client import mt5_data_provider, mt5_calculator


def main_test():
    """Основной тест функции get_positions_timeline"""
    
    print("🧮 ТЕСТ ФУНКЦИИ get_positions_timeline")
    print("=" * 70)
    
    # Параметры теста
    from_date = datetime(2025, 11, 9)
    to_date = datetime(2025, 11, 16)
    magics = [444300, 444152, 444010, 444310, 444230]
    magics = [444700]
    
    print(f"📅 Период: {from_date.strftime('%d.%m.%Y')} - {to_date.strftime('%d.%m.%Y')}")
    print(f"🔢 Мэджики: {magics}")
    print()
    
    # Получаем данные (нужно получить данные с начала истории для корректного восстановления позиций)
    print("🔄 Получение данных...")
    deals, account_info = mt5_data_provider.get_history(
        from_date=datetime(2020, 1, 1),  # С начала истории
        to_date=to_date
    )
    
    if deals is None:
        print("❌ Не удалось получить данные")
        return
    
    print(f"✅ Получено сделок: {len(deals)}")
    
    if account_info:
        print(f"🏦 Аккаунт: {account_info.login}")
        print(f"📈 Текущий баланс MT5: {account_info.balance:.2f}")
    
    print()
    print("=" * 70)
    print()
    
    # Вызываем функцию
    print("🔍 Вызов функции get_positions_timeline...")
    timeline = mt5_calculator.get_positions_timeline(
        from_date=from_date,
        to_date=to_date,
        magics=magics,
        deals=deals
    )
    
    if not timeline:
        print("⚠️  Timeline пуст - нет позиций в указанном периоде")
        return
    
    print(f"✅ Получено промежутков: {len(timeline)}")
    print()
    
    # Выводим результаты
    print("📊 РЕЗУЛЬТАТЫ:")
    print("=" * 70)
    
    for i, period in enumerate(timeline, 1):
        time_in = period['time_in']
        time_out = period['time_out']
        balance = period['balance']
        positions = period['positions']
        
        print(f"\n🔹 Промежуток #{i}:")
        print(f"   ⏰ Время IN:  {time_in.strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"   ⏰ Время OUT: {time_out.strftime('%d.%m.%Y %H:%M:%S') if time_out else 'N/A'}")
        print(f"   💰 Баланс:    {balance:.2f}")
        print(f"   📈 Позиций:   {len(positions)}")
        
        if positions:
            print(f"   📋 Детали позиций:")
            for j, pos in enumerate(positions, 1):
                magic = pos.get('magic', 'N/A')
                print(f"      {j}. {pos['symbol']} | {pos['direction']:4s} | "
                      f"Объем: {pos['volume']:.2f} | Цена: {pos['price_open']:.5f} | "
                      f"Мэджик: {magic}")
        else:
            print(f"   📋 Нет открытых позиций")
    
    print()
    print("=" * 70)
    
    # Статистика
    print("\n📈 СТАТИСТИКА:")
    print("-" * 70)
    total_periods = len(timeline)
    periods_with_positions = sum(1 for p in timeline if len(p['positions']) > 0)
    periods_without_positions = total_periods - periods_with_positions
    
    print(f"Всего промежутков: {total_periods}")
    print(f"С позициями: {periods_with_positions}")
    print(f"Без позиций: {periods_without_positions}")
    
    # Уникальные символы
    all_symbols = set()
    for period in timeline:
        for pos in period['positions']:
            all_symbols.add(pos['symbol'])
    
    if all_symbols:
        print(f"\nУникальные символы: {sorted(all_symbols)}")
    
    # Общий объем позиций по символам
    symbol_volumes = {}
    for period in timeline:
        for pos in period['positions']:
            symbol = pos['symbol']
            if symbol not in symbol_volumes:
                symbol_volumes[symbol] = {'buy': 0.0, 'sell': 0.0}
            direction = pos['direction'].lower()
            if direction in symbol_volumes[symbol]:
                symbol_volumes[symbol][direction] += pos['volume']
    
    if symbol_volumes:
        print(f"\nОбщие объемы по символам:")
        for symbol, volumes in sorted(symbol_volumes.items()):
            print(f"  {symbol}: Buy={volumes['buy']:.2f}, Sell={volumes['sell']:.2f}")
    
    print()
    print("=" * 70)
    print("✅ Тест завершен!")


if __name__ == "__main__":
    try:
        main_test()
    except KeyboardInterrupt:
        print("\n👋 Тест прерван")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

