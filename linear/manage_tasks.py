#!/usr/bin/env python3
"""
Linear Task Manager
Быстрое управление задачами в Linear
"""

import sys
import os
from dotenv import load_dotenv
from linear_integration import LinearIntegration

# Load environment variables
load_dotenv()

class TaskManager:
    """Менеджер задач Linear"""
    
    def __init__(self):
        self.linear = LinearIntegration()
    
    def list_tasks(self):
        """Показать все задачи"""
        print("📋 Все задачи в Linear:")
        print("-" * 50)
        
        issues = self.linear.get_issues(limit=20)
        
        if not issues:
            print("❌ Задачи не найдены")
            return
        
        for issue in issues:
            status_emoji = {
                'Todo': '📝',
                'In Progress': '🔄', 
                'Done': '✅',
                'Canceled': '❌'
            }.get(issue['state']['name'], '❓')
            
            print(f"{status_emoji} {issue['identifier']}: {issue['title']}")
            print(f"   Статус: {issue['state']['name']}")
            print(f"   URL: {issue['url']}")
            print()
    
    def update_task_status(self, task_id, new_status):
        """Обновить статус задачи"""
        status_mapping = {
            'todo': 'Todo',
            'progress': 'In Progress', 
            'done': 'Done',
            'cancel': 'Canceled'
        }
        
        linear_status = status_mapping.get(new_status.lower())
        if not linear_status:
            print(f"❌ Неизвестный статус: {new_status}")
            print("Доступные: todo, progress, done, cancel")
            return
        
        result = self.linear.update_issue(task_id, state={'name': linear_status})
        
        if result.get('data', {}).get('issueUpdate', {}).get('success'):
            print(f"✅ Задача {task_id} переведена в статус: {linear_status}")
        else:
            print(f"❌ Ошибка обновления задачи {task_id}")
            print(f"Ответ: {result}")
    
    def create_task(self, title, description=""):
        """Создать новую задачу"""
        result = self.linear.create_issue(title, description)
        
        if result.get('data', {}).get('issueCreate', {}).get('success'):
            issue = result['data']['issueCreate']['issue']
            print(f"✅ Создана задача: {issue['identifier']}")
            print(f"📝 Название: {issue['title']}")
            print(f"🔗 URL: {issue['url']}")
        else:
            print("❌ Ошибка создания задачи")
            print(f"Ответ: {result}")
    
    def show_help(self):
        """Показать справку"""
        print("""
🎯 Linear Task Manager - Справка

Команды:
  python manage_tasks.py list                    - Показать все задачи
  python manage_tasks.py status MT5-5 done      - Изменить статус задачи
  python manage_tasks.py create "Название"       - Создать новую задачу
  python manage_tasks.py help                    - Показать эту справку

Статусы:
  todo      - К выполнению
  progress  - В работе  
  done      - Выполнено
  cancel    - Отменено

Примеры:
  python manage_tasks.py status MT5-5 done
  python manage_tasks.py create "Добавить экспорт в Excel"
  python manage_tasks.py create "Исправить баг" "Описание бага"
        """)

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("❌ Недостаточно аргументов")
        print("Используйте: python manage_tasks.py help")
        return
    
    manager = TaskManager()
    command = sys.argv[1].lower()
    
    if command == "list":
        manager.list_tasks()
    
    elif command == "status":
        if len(sys.argv) < 4:
            print("❌ Использование: python manage_tasks.py status MT5-5 done")
            return
        task_id = sys.argv[2]
        new_status = sys.argv[3]
        manager.update_task_status(task_id, new_status)
    
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Использование: python manage_tasks.py create \"Название задачи\"")
            return
        title = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""
        manager.create_task(title, description)
    
    elif command == "help":
        manager.show_help()
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Используйте: python manage_tasks.py help")

if __name__ == "__main__":
    main()
