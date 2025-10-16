# 🚀 Шпаргалка по Linear задачам

## ⚡ Быстрые команды (quick.py)

```bash
# Изменить статус
python linear/quick.py TD-5 done
python linear/quick.py TD-6 progress
python linear/quick.py TD-7 todo

# Создать задачу
python linear/quick.py create "Название задачи"

# Справка
python linear/quick.py
```

## 📋 Полный менеджер (manage_tasks.py)

```bash
# Показать все задачи
python linear/manage_tasks.py list

# Изменить статус
python linear/manage_tasks.py status TD-5 done

# Создать задачу
python linear/manage_tasks.py create "Название" "Описание"

# Справка
python linear/manage_tasks.py help
```

## 🎯 Статусы задач

- `todo` → Todo (К выполнению)
- `progress` → In Progress (В работе)  
- `done` → Done (Выполнено)
- `cancel` → Canceled (Отменено)

## 🔄 Типичный workflow

```bash
# 1. Взять задачу в работу
python linear/quick.py TD-6 progress

# 2. Закоммитить изменения
git linear/commit -m "complete TD-6: реализовал функцию"

# 3. Отметить как выполненную
python linear/quick.py TD-6 done
```

## 📊 Ваши текущие задачи

- TD-8: Architecture. History through a database (Todo)
- TD-7: Design. Dashboard Page Structure (Todo)
- TD-6: Calculations. DrawDown (Todo)
- TD-5: Calculations. Start Balance (Done ✅)
- TD-4: Import your data (Todo)
- TD-3: Connect your tools (Todo)
- TD-2: Set up your teams (Done ✅)
- TD-1: Get familiar with Linear (Done ✅)
