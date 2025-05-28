#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для генерации тестовых данных для демонстрации бота.
Создает тестовых пользователей с разными ролями, стенды, мерч и транзакции.
"""

import os
import sys
import random
import datetime
from dotenv import load_dotenv

# Настройка пути для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Загрузка переменных окружения
load_dotenv()

# Импорт модулей бота
from utils.db_connector import DBConnector
from modules.role_management import RoleManager
from modules.merch_module import MerchManager
from modules.points_system import PointsSystem
from modules.candidate_management import CandidateManager
from utils.qr_generator import QRGenerator

def generate_demo_data():
    """Генерирует тестовые данные для демонстрации бота."""
    print("Начинаем генерацию тестовых данных...")
    
    # Подключение к базе данных
    db = DBConnector()
    
    # Очистка существующих данных
    print("Очистка существующих данных...")
    db.users.delete_many({})
    db.stands.delete_many({})
    db.merch.delete_many({})
    db.points_transactions.delete_many({})
    db.merch_transactions.delete_many({})
    db.candidates.delete_many({})
    db.daily_statistics.delete_many({})
    
    # Создание тестовых пользователей
    print("Создание тестовых пользователей...")
    
    # Администратор
    admin_id = 111111111
    admin_data = {
        'user_id': admin_id,
        'first_name': 'Админ',
        'last_name': 'Администраторов',
        'username': 'admin_demo',
        'role': 'admin',
        'company': 'Организатор конференции',
        'position': 'Главный организатор',
        'level': 'Senior',
        'points': 1000,
        'registered_at': datetime.datetime.utcnow() - datetime.timedelta(days=10),
        'last_activity': datetime.datetime.utcnow(),
        'is_active': True
    }
    db.users.insert_one(admin_data)
    
    # HR-специалист
    hr_id = 222222222
    hr_data = {
        'user_id': hr_id,
        'first_name': 'Елена',
        'last_name': 'Кадрова',
        'username': 'hr_demo',
        'role': 'hr',
        'company': 'HR Solutions',
        'position': 'HR-менеджер',
        'level': 'Middle',
        'points': 500,
        'registered_at': datetime.datetime.utcnow() - datetime.timedelta(days=7),
        'last_activity': datetime.datetime.utcnow() - datetime.timedelta(hours=2),
        'is_active': True
    }
    db.users.insert_one(hr_data)
    
    # Стендисты
    stand_owners = []
    for i in range(1, 4):
        stand_owner_id = 300000000 + i
        stand_owner_data = {
            'user_id': stand_owner_id,
            'first_name': f'Стендист{i}',
            'last_name': f'Демонстрационный{i}',
            'username': f'stand_owner{i}_demo',
            'role': 'stand_owner',
            'company': f'Компания {i}',
            'position': 'Менеджер стенда',
            'level': 'Middle',
            'points': 300,
            'registered_at': datetime.datetime.utcnow() - datetime.timedelta(days=5),
            'last_activity': datetime.datetime.utcnow() - datetime.timedelta(hours=i),
            'is_active': True
        }
        db.users.insert_one(stand_owner_data)
        stand_owners.append(stand_owner_id)
    
    # Обычные участники
    participants = []
    companies = ['ООО Технологии', 'ЗАО Инновации', 'ИП Разработка', 'ООО Дизайн Про', 'ЗАО Консалтинг']
    positions = ['Разработчик', 'Дизайнер', 'Менеджер', 'Аналитик', 'Тестировщик']
    levels = ['Junior', 'Middle', 'Senior', 'Lead']
    
    for i in range(1, 11):
        participant_id = 400000000 + i
        participant_data = {
            'user_id': participant_id,
            'first_name': f'Участник{i}',
            'last_name': f'Тестовый{i}',
            'username': f'participant{i}_demo',
            'role': 'participant',
            'company': random.choice(companies),
            'position': random.choice(positions),
            'level': random.choice(levels),
            'points': random.randint(50, 200),
            'registered_at': datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 5)),
            'last_activity': datetime.datetime.utcnow() - datetime.timedelta(hours=random.randint(1, 12)),
            'is_active': True
        }
        db.users.insert_one(participant_data)
        participants.append(participant_id)
    
    # Создание тестовых стендов
    print("Создание тестовых стендов...")
    stands = []
    stand_descriptions = [
        'Демонстрация инновационных технологий в области искусственного интеллекта',
        'Презентация новых решений для бизнеса',
        'Облачные технологии и их применение в современном мире'
    ]
    
    for i, owner_id in enumerate(stand_owners):
        stand_id = f'stand_{i+1}'
        stand_data = {
            'stand_id': stand_id,
            'name': f'Стенд компании {i+1}',
            'description': stand_descriptions[i],
            'owner_id': owner_id,
            'visits': random.randint(5, 20),
            'created_at': datetime.datetime.utcnow() - datetime.timedelta(days=5)
        }
        db.stands.insert_one(stand_data)
        stands.append(stand_id)
    
    # Создание тестового мерча
    print("Создание тестового мерча...")
    merch_items = [
        {
            'merch_id': 'merch_1',
            'name': 'Футболка с логотипом',
            'description': 'Хлопковая футболка с логотипом конференции',
            'points_cost': 100,
            'available': 50,
            'image_url': 'https://example.com/tshirt.jpg',
            'created_at': datetime.datetime.utcnow() - datetime.timedelta(days=5)
        },
        {
            'merch_id': 'merch_2',
            'name': 'Кружка',
            'description': 'Керамическая кружка с логотипом конференции',
            'points_cost': 50,
            'available': 100,
            'image_url': 'https://example.com/mug.jpg',
            'created_at': datetime.datetime.utcnow() - datetime.timedelta(days=5)
        },
        {
            'merch_id': 'merch_3',
            'name': 'Блокнот',
            'description': 'Блокнот для записей с логотипом конференции',
            'points_cost': 30,
            'available': 200,
            'image_url': 'https://example.com/notebook.jpg',
            'created_at': datetime.datetime.utcnow() - datetime.timedelta(days=5)
        },
        {
            'merch_id': 'merch_4',
            'name': 'Рюкзак',
            'description': 'Рюкзак с логотипом конференции',
            'points_cost': 200,
            'available': 20,
            'image_url': 'https://example.com/backpack.jpg',
            'created_at': datetime.datetime.utcnow() - datetime.timedelta(days=5)
        },
        {
            'merch_id': 'merch_5',
            'name': 'Наклейки',
            'description': 'Набор наклеек с логотипами технологий',
            'points_cost': 20,
            'available': 300,
            'image_url': 'https://example.com/stickers.jpg',
            'created_at': datetime.datetime.utcnow() - datetime.timedelta(days=5)
        }
    ]
    
    for merch in merch_items:
        db.merch.insert_one(merch)
    
    # Создание тестовых транзакций баллов
    print("Создание тестовых транзакций баллов...")
    
    # Транзакции за регистрацию
    for participant_id in participants:
        registration_tx = {
            'transaction_id': f'tx_reg_{participant_id}',
            'user_id': participant_id,
            'amount': 100,
            'type': 'earn',
            'reason': 'registration',
            'created_at': db.get_user(participant_id)['registered_at']
        }
        db.points_transactions.insert_one(registration_tx)
    
    # Транзакции за посещение стендов
    for participant_id in participants:
        for stand_id in random.sample(stands, random.randint(1, len(stands))):
            visit_tx = {
                'transaction_id': f'tx_visit_{participant_id}_{stand_id}',
                'user_id': participant_id,
                'amount': 50,
                'type': 'earn',
                'reason': 'stand_visit',
                'reference_id': stand_id,
                'created_at': datetime.datetime.utcnow() - datetime.timedelta(hours=random.randint(1, 24))
            }
            db.points_transactions.insert_one(visit_tx)
    
    # Транзакции за заказ мерча
    for participant_id in random.sample(participants, 5):
        merch_id = random.choice(['merch_1', 'merch_2', 'merch_3', 'merch_4', 'merch_5'])
        merch_item = db.merch.find_one({'merch_id': merch_id})
        
        merch_tx = {
            'transaction_id': f'tx_merch_{participant_id}_{merch_id}',
            'user_id': participant_id,
            'amount': merch_item['points_cost'],
            'type': 'spend',
            'reason': 'merch_order',
            'reference_id': merch_id,
            'created_at': datetime.datetime.utcnow() - datetime.timedelta(hours=random.randint(1, 12))
        }
        db.points_transactions.insert_one(merch_tx)
        
        # Создание заказа мерча
        merch_order = {
            'transaction_id': f'mtx_{participant_id}_{merch_id}',
            'user_id': participant_id,
            'merch_id': merch_id,
            'points_spent': merch_item['points_cost'],
            'status': random.choice(['pending', 'completed']),
            'created_at': merch_tx['created_at']
        }
        db.merch_transactions.insert_one(merch_order)
    
    # Создание тестовых кандидатов для HR
    print("Создание тестовых кандидатов для HR...")
    for participant_id in random.sample(participants, 3):
        candidate_data = {
            'candidate_id': f'cand_{participant_id}',
            'user_id': participant_id,
            'hr_id': hr_id,
            'notes': f'Потенциальный кандидат на позицию {random.choice(positions)}',
            'status': random.choice(['new', 'contacted', 'interested']),
            'created_at': datetime.datetime.utcnow() - datetime.timedelta(hours=random.randint(1, 24)),
            'updated_at': datetime.datetime.utcnow() - datetime.timedelta(hours=random.randint(0, 12))
        }
        db.candidates.insert_one(candidate_data)
    
    # Генерация QR-кодов для тестовых пользователей
    print("Генерация QR-кодов для тестовых пользователей...")
    qr_generator = QRGenerator()
    
    # Создание директории для QR-кодов, если она не существует
    os.makedirs('data/qr_codes', exist_ok=True)
    
    # Генерация QR-кодов для всех пользователей
    all_users = [admin_id, hr_id] + stand_owners + participants
    for user_id in all_users:
        qr_data = f"user:{user_id}"
        qr_path = f"data/qr_codes/user_{user_id}.png"
        qr_generator.generate_qr_code(qr_data, qr_path)
    
    print("Генерация тестовых данных завершена успешно!")
    print(f"Создано пользователей: {len(all_users)}")
    print(f"Создано стендов: {len(stands)}")
    print(f"Создано позиций мерча: {len(merch_items)}")
    print("QR-коды сохранены в директории data/qr_codes/")
    
    # Вывод учетных данных для тестовых аккаунтов
    print("\nУчетные данные для тестовых аккаунтов:")
    print(f"Администратор: ID {admin_id}, username: admin_demo")
    print(f"HR-специалист: ID {hr_id}, username: hr_demo")
    for i, owner_id in enumerate(stand_owners):
        print(f"Стендист {i+1}: ID {owner_id}, username: stand_owner{i+1}_demo")
    print("Обычные участники:")
    for i, participant_id in enumerate(participants):
        print(f"Участник {i+1}: ID {participant_id}, username: participant{i+1}_demo")

if __name__ == "__main__":
    generate_demo_data()
