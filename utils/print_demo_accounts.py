#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для вывода учетных данных тестовых аккаунтов для демонстрации бота.
"""

import os
import sys
from dotenv import load_dotenv

# Настройка пути для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Загрузка переменных окружения
load_dotenv()

# Импорт модулей бота
from utils.db_connector import DBConnector

def print_demo_accounts():
    """Выводит учетные данные тестовых аккаунтов."""
    print("Получение учетных данных тестовых аккаунтов...")
    
    # Подключение к базе данных
    db = DBConnector()
    
    # Получение всех пользователей
    users = list(db.users.find({}))
    
    if not users:
        print("Тестовые аккаунты не найдены. Сначала запустите скрипт demo_data_generator.py")
        return
    
    # Вывод учетных данных по ролям
    print("\n=== ТЕСТОВЫЕ АККАУНТЫ ДЛЯ ДЕМОНСТРАЦИИ ===\n")
    
    # Администраторы
    admins = [user for user in users if user.get('role') == 'admin']
    if admins:
        print("АДМИНИСТРАТОРЫ:")
        for admin in admins:
            print(f"  ID: {admin['user_id']}")
            print(f"  Имя: {admin.get('first_name', '')} {admin.get('last_name', '')}")
            print(f"  Username: {admin.get('username', 'Нет')}")
            print(f"  Компания: {admin.get('company', 'Не указана')}")
            print(f"  Баллы: {admin.get('points', 0)}")
            print("  ---")
    
    # HR-специалисты
    hrs = [user for user in users if user.get('role') == 'hr']
    if hrs:
        print("\nHR-СПЕЦИАЛИСТЫ:")
        for hr in hrs:
            print(f"  ID: {hr['user_id']}")
            print(f"  Имя: {hr.get('first_name', '')} {hr.get('last_name', '')}")
            print(f"  Username: {hr.get('username', 'Нет')}")
            print(f"  Компания: {hr.get('company', 'Не указана')}")
            print(f"  Баллы: {hr.get('points', 0)}")
            print("  ---")
    
    # Стендисты
    stand_owners = [user for user in users if user.get('role') == 'stand_owner']
    if stand_owners:
        print("\nСТЕНДИСТЫ:")
        for owner in stand_owners:
            print(f"  ID: {owner['user_id']}")
            print(f"  Имя: {owner.get('first_name', '')} {owner.get('last_name', '')}")
            print(f"  Username: {owner.get('username', 'Нет')}")
            print(f"  Компания: {owner.get('company', 'Не указана')}")
            print(f"  Баллы: {owner.get('points', 0)}")
            
            # Получение информации о стенде
            stand = db.stands.find_one({'owner_id': owner['user_id']})
            if stand:
                print(f"  Стенд: {stand.get('name', 'Неизвестно')} (ID: {stand.get('stand_id', 'Неизвестно')})")
            
            print("  ---")
    
    # Обычные участники
    participants = [user for user in users if user.get('role') == 'participant']
    if participants:
        print("\nУЧАСТНИКИ:")
        for i, participant in enumerate(participants):
            print(f"  Участник {i+1}:")
            print(f"  ID: {participant['user_id']}")
            print(f"  Имя: {participant.get('first_name', '')} {participant.get('last_name', '')}")
            print(f"  Username: {participant.get('username', 'Нет')}")
            print(f"  Компания: {participant.get('company', 'Не указана')}")
            print(f"  Должность: {participant.get('position', 'Не указана')}")
            print(f"  Уровень: {participant.get('level', 'Не указан')}")
            print(f"  Баллы: {participant.get('points', 0)}")
            
            # Проверка, является ли участник кандидатом
            candidate = db.candidates.find_one({'user_id': participant['user_id']})
            if candidate:
                print(f"  Статус кандидата: {candidate.get('status', 'Неизвестно')}")
            
            print("  ---")
    
    # Информация о QR-кодах
    print("\nQR-КОДЫ:")
    print("  Все QR-коды пользователей сохранены в директории data/qr_codes/")
    print("  Формат имени файла: user_[ID пользователя].png")
    print("  Например: user_111111111.png для администратора")
    
    # Информация о мерче
    merch_items = list(db.merch.find({}))
    if merch_items:
        print("\nДОСТУПНЫЙ МЕРЧ:")
        for merch in merch_items:
            print(f"  {merch.get('name', 'Неизвестно')} (ID: {merch.get('merch_id', 'Неизвестно')})")
            print(f"  Описание: {merch.get('description', 'Нет описания')}")
            print(f"  Стоимость: {merch.get('points_cost', 0)} баллов")
            print(f"  Доступно: {merch.get('available', 0)} шт.")
            print("  ---")
    
    print("\n=== ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ ===")
    print("1. Запустите бота командой: python main.py")
    print("2. Используйте указанные выше ID пользователей для входа в разные аккаунты")
    print("3. Для входа как администратор используйте команду /admin и код из файла .env")
    print("4. QR-коды можно использовать для демонстрации сканирования и других функций")
    print("\nПодробные сценарии демонстрации смотрите в файле PRESENTATION_GUIDE.md")

if __name__ == "__main__":
    print_demo_accounts()
