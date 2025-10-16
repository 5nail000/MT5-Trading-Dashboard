#!/usr/bin/env python3
"""
Быстрые команды для Linear
"""

import sys
from dotenv import load_dotenv
from linear_integration import LinearIntegration

load_dotenv()

def quick_status(task_id, status):
    """Быстрое изменение статуса"""
    linear = LinearIntegration()
    
    status_map = {
        'todo': 'Todo',
        'progress': 'In Progress',
        'done': 'Done',
        'cancel': 'Canceled'
    }
    
    linear_status = status_map.get(status.lower())
    if not linear_status:
        print(f"❌ Статус должен быть: todo, progress, done, cancel")
        return
    
    result = linear.update_issue(task_id, state={'name': linear_status})
    
    if result.get('data', {}).get('issueUpdate', {}).get('success'):
        print(f"✅ {task_id} → {linear_status}")
    else:
        print(f"❌ Ошибка обновления {task_id}")

def quick_create(title):
    """Быстрое создание задачи"""
    linear = LinearIntegration()
    result = linear.create_issue(title)
    
    if result.get('data', {}).get('issueCreate', {}).get('success'):
        issue = result['data']['issueCreate']['issue']
        print(f"✅ Создана: {issue['identifier']} - {issue['title']}")
        print(f"🔗 {issue['url']}")
    else:
        print("❌ Ошибка создания задачи")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
🎯 Быстрые команды Linear:

Статус задачи:
  python quick.py MT5-5 done
  python quick.py MT5-6 progress

Создать задачу:
  python quick.py create "Название задачи"
        """)
    elif sys.argv[1] == "create":
        if len(sys.argv) < 3:
            print("❌ Использование: python quick.py create \"Название\"")
        else:
            quick_create(sys.argv[2])
    else:
        if len(sys.argv) < 3:
            print("❌ Использование: python quick.py MT5-5 done")
        else:
            quick_status(sys.argv[1], sys.argv[2])
