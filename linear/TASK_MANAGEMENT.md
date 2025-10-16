# 🎯 Управление задачами Linear

Два скрипта для быстрого и удобного управления задачами в Linear.

## 📋 manage_tasks.py - Полный менеджер задач

### Основные команды:

#### 1. **Показать все задачи**
```bash
python linear/manage_tasks.py list
```
**Результат:**
```
📋 Все задачи в Linear:
--------------------------------------------------
📝 TD-8: Architecture. History through a database
   Статус: Todo
   URL: https://linear.app/mt5-trading-dashboard/issue/TD-8/...

🔄 TD-7: Design. Dashboard Page Structure
   Статус: In Progress
   URL: https://linear.app/mt5-trading-dashboard/issue/TD-7/...

✅ TD-1: Get familiar with Linear (1)
   Статус: Done
   URL: https://linear.app/mt5-trading-dashboard/issue/TD-1/...
```

#### 2. **Изменить статус задачи**
```bash
python linear/manage_tasks.py status TD-5 done
python linear/manage_tasks.py status TD-6 progress
python linear/manage_tasks.py status TD-7 todo
python linear/manage_tasks.py status TD-8 cancel
```

**Доступные статусы:**
- `todo` → Todo (К выполнению)
- `progress` → In Progress (В работе)
- `done` → Done (Выполнено)
- `cancel` → Canceled (Отменено)

#### 3. **Создать новую задачу**
```bash
python linear/manage_tasks.py create "Добавить экспорт данных в Excel"
python linear/manage_tasks.py create "Исправить баг с расчетом" "Подробное описание бага"
```

#### 4. **Справка**
```bash
python linear/manage_tasks.py help
```

---

## ⚡ quick.py - Быстрые команды

Для тех, кто хочет максимально быстро управлять задачами.

### Изменение статуса задачи:
```bash
python linear/quick.py TD-5 done
python linear/quick.py TD-6 progress
python linear/quick.py TD-7 todo
python linear/quick.py TD-8 cancel
```

**Результат:**
```
✅ TD-5 → Done
```

### Создание новой задачи:
```bash
python linear/quick.py create "Новая функция: Автообновление"
```

**Результат:**
```
✅ Создана: TD-9 - Новая функция: Автообновление
🔗 https://linear.app/mt5-trading-dashboard/issue/TD-9/...
```

### Справка:
```bash
python linear/quick.py
```

---

## 🔄 Типичный workflow

### **Начало работы над задачей:**
```bash
# 1. Посмотреть все задачи
python linear/manage_tasks.py list

# 2. Взять задачу в работу
python linear/quick.py TD-6 progress
```

### **Завершение задачи:**
```bash
# 1. Закоммитить изменения
git add .
git commit -m "complete TD-6: реализовал расчет DrawDown"
git push

# 2. Отметить задачу как выполненную
python linear/quick.py TD-6 done
```

### **Создание новой задачи:**
```bash
# Создать задачу для новой функции
python linear/quick.py create "Добавить график прибыли по времени"
```

---

## 🎯 Примеры использования

### **Сценарий 1: Ежедневная работа**
```bash
# Утром - посмотреть задачи
python linear/manage_tasks.py list

# Взять задачу в работу
python linear/quick.py TD-7 progress

# Вечером - завершить задачу
python linear/quick.py TD-7 done
```

### **Сценарий 2: Планирование спринта**
```bash
# Создать несколько задач
python linear/quick.py create "Реализовать фильтрацию по символам"
python linear/quick.py create "Добавить экспорт в PDF"
python linear/quick.py create "Оптимизировать производительность"

# Посмотреть все задачи
python linear/manage_tasks.py list
```

### **Сценарий 3: Отмена задачи**
```bash
# Если задача больше не актуальна
python linear/quick.py TD-8 cancel
```

---

## 🚀 Преимущества

### **manage_tasks.py:**
- ✅ Полная информация о задачах
- ✅ Подробные описания
- ✅ Справка и помощь
- ✅ Создание задач с описанием

### **quick.py:**
- ⚡ Максимальная скорость
- ⚡ Короткие команды
- ⚡ Быстрое изменение статусов
- ⚡ Минимум текста

---

## 🔧 Настройка

Убедитесь, что в `.env` файле правильно настроены:
```env
LINEAR_API_KEY=lin_api_ваш_ключ
LINEAR_TEAM_ID=ваш_team_id
```

---

## 💡 Советы

1. **Используйте `quick.py`** для ежедневной работы
2. **Используйте `manage_tasks.py`** для планирования и обзора
3. **Комбинируйте с Git:** сначала коммит, потом обновление статуса
4. **Создавайте задачи** перед началом работы над новой функцией

---

## 🆘 Решение проблем

### **Ошибка "Issue not found":**
- Проверьте правильность номера задачи (TD-5, TD-6, etc.)
- Убедитесь, что задача существует в Linear

### **Ошибка авторизации:**
- Проверьте `LINEAR_API_KEY` в `.env` файле
- Убедитесь, что API ключ активен

### **Ошибка "Team not found":**
- Проверьте `LINEAR_TEAM_ID` в `.env` файле
- Запустите `python test_linear.py` для получения правильного ID
