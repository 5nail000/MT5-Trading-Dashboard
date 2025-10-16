# Функция calculate_balance_at_date

Документация по функции расчета баланса на указанную дату из модуля `MT5Calculator`.

## Описание

Функция `calculate_balance_at_date` вычисляет баланс торгового счета на указанную дату, учитывая все сделки из истории торговли.

## Возможности

- ✅ **Начальный баланс = 0** (по умолчанию)
- ✅ **Опция начала/конца дня** (`end_of_day` параметр)
- ✅ **Расчет по точному времени** (`use_exact_time` параметр) 🆕
- ✅ **Правильный учет временной зоны** (`LOCAL_TIMESHIFT = 3`)
- ✅ **Корректная логика расчета** с учетом всех типов сделок

## Параметры функции

```python
def calculate_balance_at_date(
    target_date: datetime,      # Дата и время для расчета баланса
    deals: List,                 # Список всех сделок из истории
    initial_balance: float = None,  # Начальный баланс (по умолчанию 0)
    end_of_day: bool = False,   # True = конец дня, False = начало дня
    use_exact_time: bool = False # True = точное время из target_date 🆕
) -> float:
```

## Использование

### Базовые режимы (как раньше)

```python
# По умолчанию - начало дня (00:00:00)
balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 10),
    deals=deals
)

# Конец дня (23:59:59)
balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 10),
    deals=deals,
    end_of_day=True
)
```

### 🆕 Расчет по точному времени

```python
# Баланс на точное время (14:30:25)
balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 10, 14, 30, 25),
    deals=deals,
    use_exact_time=True
)

# Баланс на другое точное время (18:45:00)
balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 10, 18, 45, 0),
    deals=deals,
    use_exact_time=True
)
```

### Комбинированное использование

```python
# Можно комбинировать параметры
balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 10, 12, 0, 0),
    deals=deals,
    initial_balance=1000.0,  # Начальный баланс
    use_exact_time=True      # Точное время
)
```

## Запуск тестов

### Основной тест
```bash
python tests/balance_calculation/test_balance_function.py
```

### 🆕 Тест точного времени
```bash
python test_balance_time.py
```

### Тест с точным временем (из папки tests)
```bash
python tests/balance_calculation/test_exact_time.py
```

## Результаты теста

Тест проверяет:
- **10 октября 2025** - рабочий день с торговлей
- **27 сентября 2025** - суббота (выходной)
- **28 сентября 2025** - воскресенье (выходной)

Ожидаемые результаты:
- Суббота и воскресенье должны иметь одинаковый баланс (нет торговли)
- Разница между началом и концом дня показывает прибыль/убыток за день

## Логика работы

1. **Временная зона**: Местное время конвертируется в UTC с учетом `LOCAL_TIMESHIFT`
2. **Типы сделок**:
   - `type == 2`: Изменения баланса (депозиты/снятия)
   - Остальные: Торговые сделки (прибыль + комиссия + своп)
3. **Расчет**: Начальный баланс + все сделки до указанной даты
4. **Режимы времени**:
   - `use_exact_time=False`: Использует начало/конец дня
   - `use_exact_time=True`: Использует точное время из `target_date`

## 🎯 Практические примеры использования

### Анализ торгового дня
```python
# Баланс в начале торгового дня
morning_balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 15, 9, 0, 0),
    deals=deals,
    use_exact_time=True
)

# Баланс в середине дня
midday_balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 15, 12, 30, 0),
    deals=deals,
    use_exact_time=True
)

# Баланс в конце торгового дня
evening_balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 15, 18, 0, 0),
    deals=deals,
    use_exact_time=True
)

print(f"Утренний баланс: {morning_balance:.2f}")
print(f"Дневной баланс: {midday_balance:.2f}")
print(f"Вечерний баланс: {evening_balance:.2f}")
print(f"Прибыль за день: {evening_balance - morning_balance:.2f}")
```

### Отслеживание конкретных сделок
```python
# Баланс до конкретной сделки
before_deal = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 15, 14, 25, 30),
    deals=deals,
    use_exact_time=True
)

# Баланс после конкретной сделки
after_deal = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 15, 14, 26, 15),
    deals=deals,
    use_exact_time=True
)

print(f"Баланс до сделки: {before_deal:.2f}")
print(f"Баланс после сделки: {after_deal:.2f}")
print(f"Влияние сделки: {after_deal - before_deal:.2f}")
```

### Сравнение разных периодов
```python
# Баланс на начало недели
week_start = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 13, 0, 0, 0),  # Понедельник
    deals=deals,
    use_exact_time=True
)

# Баланс на конец недели
week_end = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 17, 23, 59, 59),  # Пятница
    deals=deals,
    use_exact_time=True
)

print(f"Баланс на начало недели: {week_start:.2f}")
print(f"Баланс на конец недели: {week_end:.2f}")
print(f"Прибыль за неделю: {week_end - week_start:.2f}")
```

## Примеры вывода

### Основной тест
```
🧮 ТЕСТ ФУНКЦИИ calculate_balance_at_date
==================================================
🔄 Получение данных...
✅ Получено сделок: 3004
🏦 Аккаунт: 25235504
📈 Текущий баланс MT5: 11968.11

📅 10 октября (2025-10-10):
   • 🌅 Начало дня: 10938.49
   • 🌆 Конец дня:  10491.50
   • 📊 Разница:    -446.99
   • 📈 От текущего: +1476.61

📅 Суббота (2025-09-27):
   • 🌅 Начало дня: 6833.09
   • 🌆 Конец дня:  6833.09
   • 📊 Разница:    +0.00
   • 📈 От текущего: +5135.02

📅 Воскресенье (2025-09-28):
   • 🌅 Начало дня: 6833.09
   • 🌆 Конец дня:  6833.09
   • 📊 Разница:    +0.00
   • 📈 От текущего: +5135.02

==================================================
✅ Тест завершен!
```

### 🆕 Тест точного времени
```
🧪 Тестирование расчета баланса по точному времени
============================================================
📊 Получение данных из MT5...
✅ Получено 3004 сделок
📅 Тестируем на дату: 15.10.2025

🌅 Баланс на начало дня (00:00:00): 10938.49
🌙 Баланс на конец дня (23:59:59): 10491.50
⏰ Баланс на точное время (12:00:00): 10715.25
⏰ Баланс на точное время (18:30:45): 10589.30

📈 Анализ:
   Разница начало → конец дня: -446.99
   Разница 12:00 → 18:30: -125.95
✅ Логика корректна: начало ≤ точное время ≤ конец

============================================================
🎯 Тест с пользовательским временем
Введите час (0-23): 14
Введите минуты (0-59): 30
Введите секунды (0-59): 15
💰 Баланс на 14:30:15: 10652.80
```

### Консольный инструмент
Для быстрого расчета баланса на конкретную дату из командной строки:

```bash
# Расчет баланса на начало дня
python tests/balance_calculation/balance_by_date.py --date 2025-09-27

# Расчет баланса на конец дня
python tests/balance_calculation/balance_by_date.py --date 2025-09-27 --end-of-day

# Расчет с пользовательским начальным балансом
python tests/balance_calculation/balance_by_date.py --date 2025-10-10 --initial-balance 1000

# Подробный вывод с информацией о сделках
python tests/balance_calculation/balance_by_date.py --date 2025-09-30 --verbose
```

**Поддерживаемые форматы дат:**
- `2025-09-27` (ISO формат)
- `27-09-2025` (Европейский формат)
- `27/09/2025` (Формат с косой чертой)
- `27.09.2025` (Формат с точкой)

## Примеры вывода

```
🧮 РАСЧЕТ БАЛАНСА НА ДАТУ
==================================================
📅 Целевая дата: 27.09.2025
🕐 Режим: Начало дня

🔄 Получение данных...
✅ Получено сделок: 3004
🏦 Аккаунт: 25235504
📈 Текущий баланс MT5: 11968.11

🧮 РЕЗУЛЬТАТ:
------------------------------
📊 Баланс: 6833.09
📈 От текущего: +5135.02

==================================================
✅ Расчет завершен!
```