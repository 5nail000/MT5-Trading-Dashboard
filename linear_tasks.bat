@echo off
cd /d "D:\Python_projects\009_MT5_Trading_Dashboard"

if "%1"=="list" (
    python linear\manage_tasks.py list
) else if "%1"=="done" (
    python linear\quick.py %2 done
) else if "%1"=="progress" (
    python linear\quick.py %2 progress
) else if "%1"=="todo" (
    python linear\quick.py %2 todo
) else (
    echo.
    echo 🎯 Linear Task Manager
    echo.
    echo Команды:
    echo   linear_tasks.bat list                    - Показать все задачи
    echo   linear_tasks.bat done TD-5              - Завершить задачу
    echo   linear_tasks.bat progress TD-6          - Взять в работу
    echo   linear_tasks.bat todo TD-7              - Вернуть в Todo
    echo.
)

pause
