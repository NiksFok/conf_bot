#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для подключения к базе данных MongoDB.
Обеспечивает взаимодействие с коллекциями базы данных.
"""

import os
import datetime
from typing import Dict, List, Optional, Any, Union
from pymongo import MongoClient
from bson.objectid import ObjectId

class DBConnector:
    """Класс для подключения к базе данных MongoDB."""
    
    def __init__(self):
        """Инициализация подключения к базе данных."""
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/conference_bot")
        self.client = MongoClient(mongo_uri)
        self.db = self.client.get_database()
        
        # Инициализация коллекций
        self.users = self.db.users
        self.stands = self.db.stands
        self.merch = self.db.merch
        self.points_transactions = self.db.points_transactions
        self.merch_transactions = self.db.merch_transactions
        self.candidate_notes = self.db.candidate_notes
        self.bot_statistics = self.db.bot_statistics
        self.error_logs = self.db.error_logs
        self.events = self.db.events
        self.subscriptions = self.db.subscriptions
    
    # Методы для работы с пользователями
    
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """Создает нового пользователя в базе данных."""
        user_data['registered_at'] = datetime.datetime.utcnow()
        user_data['last_activity'] = datetime.datetime.utcnow()
        
        result = self.users.insert_one(user_data)
        return str(result.inserted_id)
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о пользователе по его ID."""
        return self.users.find_one({'user_id': user_id})
    
    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Обновляет информацию о пользователе."""
        update_data['last_activity'] = datetime.datetime.utcnow()
        
        result = self.users.update_one(
            {'user_id': user_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает список всех пользователей."""
        return list(self.users.find())
    
    def update_user_points(self, user_id: int, points: int) -> bool:
        """Обновляет количество баллов пользователя."""
        result = self.users.update_one(
            {'user_id': user_id},
            {
                '$set': {'last_activity': datetime.datetime.utcnow()},
                '$inc': {'points': points}
            }
        )
        
        return result.modified_count > 0
    
    def update_user_role(self, user_id: int, role: str) -> bool:
        """Обновляет роль пользователя."""
        result = self.users.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'role': role,
                    'last_activity': datetime.datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    def block_user(self, user_id: int, block: bool = True) -> bool:
        """Блокирует или разблокирует пользователя."""
        result = self.users.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'is_blocked': block,
                    'last_activity': datetime.datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    def mark_user_as_candidate(self, user_id: int, is_candidate: bool = True) -> bool:
        """Отмечает пользователя как кандидата."""
        result = self.users.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'is_candidate': is_candidate,
                    'last_activity': datetime.datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Получает список пользователей с указанной ролью."""
        return list(self.users.find({'role': role}))
    
    def get_active_users(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получает список активных пользователей за последние N часов."""
        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
        
        return list(self.users.find({
            'last_activity': {'$gte': cutoff_time}
        }))
    
    # Методы для работы со стендами
    
    def create_stand(self, stand_data: Dict[str, Any]) -> str:
        """Создает новый стенд в базе данных."""
        stand_data['created_at'] = datetime.datetime.utcnow()
        stand_data['updated_at'] = datetime.datetime.utcnow()
        stand_data['visits'] = 0
        
        result = self.stands.insert_one(stand_data)
        return str(result.inserted_id)
    
    def get_stand(self, stand_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о стенде по его ID."""
        return self.stands.find_one({'stand_id': stand_id})
    
    def update_stand(self, stand_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет информацию о стенде."""
        update_data['updated_at'] = datetime.datetime.utcnow()
        
        result = self.stands.update_one(
            {'stand_id': stand_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    def get_all_stands(self) -> List[Dict[str, Any]]:
        """Получает список всех стендов."""
        return list(self.stands.find())
    
    def get_stand_by_owner(self, owner_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о стенде по ID владельца."""
        return self.stands.find_one({'owner_id': owner_id})
    
    def increment_stand_visits(self, stand_id: str) -> bool:
        """Увеличивает счетчик посещений стенда."""
        result = self.stands.update_one(
            {'stand_id': stand_id},
            {
                '$inc': {'visits': 1},
                '$set': {'updated_at': datetime.datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    # Методы для работы с мерчем
    
    def create_merch(self, merch_data: Dict[str, Any]) -> str:
        """Создает новый мерч в базе данных."""
        merch_data['created_at'] = datetime.datetime.utcnow()
        merch_data['updated_at'] = datetime.datetime.utcnow()
        merch_data['quantity_left'] = merch_data.get('quantity_total', 0)
        
        result = self.merch.insert_one(merch_data)
        return str(result.inserted_id)
    
    def get_merch(self, merch_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о мерче по его ID."""
        return self.merch.find_one({'merch_id': merch_id})
    
    def update_merch(self, merch_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет информацию о мерче."""
        update_data['updated_at'] = datetime.datetime.utcnow()
        
        result = self.merch.update_one(
            {'merch_id': merch_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    def get_all_merch(self) -> List[Dict[str, Any]]:
        """Получает список всего мерча."""
        return list(self.merch.find())
    
    def decrement_merch_quantity(self, merch_id: str) -> bool:
        """Уменьшает количество доступного мерча."""
        result = self.merch.update_one(
            {
                'merch_id': merch_id,
                'quantity_left': {'$gt': 0}
            },
            {
                '$inc': {'quantity_left': -1},
                '$set': {'updated_at': datetime.datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    # Методы для работы с транзакциями баллов
    
    def create_points_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Создает новую транзакцию баллов."""
        transaction_data['created_at'] = datetime.datetime.utcnow()
        transaction_data['transaction_id'] = f"tr{ObjectId()}"
        
        result = self.points_transactions.insert_one(transaction_data)
        return str(result.inserted_id)
    
    def get_user_points_transactions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список транзакций баллов пользователя."""
        return list(self.points_transactions.find(
            {'user_id': user_id}
        ).sort('created_at', -1))
    
    # Методы для работы с транзакциями мерча
    
    def create_merch_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Создает новую транзакцию мерча."""
        transaction_data['created_at'] = datetime.datetime.utcnow()
        transaction_data['updated_at'] = datetime.datetime.utcnow()
        transaction_data['completed_at'] = None
        transaction_data['transaction_id'] = f"mtr{ObjectId()}"
        
        result = self.merch_transactions.insert_one(transaction_data)
        return str(result.inserted_id)
    
    def get_user_merch_transactions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список транзакций мерча пользователя."""
        return list(self.merch_transactions.find(
            {'user_id': user_id}
        ).sort('created_at', -1))
    
    def update_merch_transaction_status(self, transaction_id: str, status: str) -> bool:
        """Обновляет статус транзакции мерча."""
        update_data = {
            'status': status,
            'updated_at': datetime.datetime.utcnow()
        }
        
        if status == 'completed':
            update_data['completed_at'] = datetime.datetime.utcnow()
        
        result = self.merch_transactions.update_one(
            {'transaction_id': transaction_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    # Методы для работы с заметками о кандидатах
    
    def create_candidate_note(self, note_data: Dict[str, Any]) -> str:
        """Создает новую заметку о кандидате."""
        note_data['created_at'] = datetime.datetime.utcnow()
        note_data['updated_at'] = datetime.datetime.utcnow()
        note_data['note_id'] = f"note{ObjectId()}"
        
        result = self.candidate_notes.insert_one(note_data)
        return str(result.inserted_id)
    
    def get_candidate_notes(self, candidate_id: int, hr_id: int = None) -> List[Dict[str, Any]]:
        """Получает список заметок о кандидате."""
        query = {'candidate_id': candidate_id}
        
        if hr_id is not None:
            query['hr_id'] = hr_id
        
        return list(self.candidate_notes.find(query).sort('created_at', -1))
    
    def update_candidate_note(self, note_id: str, text: str) -> bool:
        """Обновляет текст заметки о кандидате."""
        result = self.candidate_notes.update_one(
            {'note_id': note_id},
            {
                '$set': {
                    'text': text,
                    'updated_at': datetime.datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    # Методы для работы со статистикой
    
    def update_daily_statistics(self, stat_data: Dict[str, Any]) -> bool:
        """Обновляет ежедневную статистику."""
        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        
        result = self.bot_statistics.update_one(
            {'date': today},
            {'$set': stat_data},
            upsert=True
        )
        
        return result.modified_count > 0 or result.upserted_id is not None
    
    def get_daily_statistics(self, date: str = None) -> Optional[Dict[str, Any]]:
        """Получает ежедневную статистику."""
        if date is None:
            date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        
        return self.bot_statistics.find_one({'date': date})
    
    def get_statistics_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Получает статистику за указанный период."""
        return list(self.bot_statistics.find({
            'date': {'$gte': start_date, '$lte': end_date}
        }).sort('date', 1))
    
    # Методы для работы с логами ошибок
    
    def log_error(self, error_data: Dict[str, Any]) -> str:
        """Логирует ошибку в базу данных."""
        error_data['timestamp'] = datetime.datetime.utcnow()
        error_data['error_id'] = f"err{ObjectId()}"
        
        result = self.error_logs.insert_one(error_data)
        return str(result.inserted_id)
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает список последних ошибок."""
        return list(self.error_logs.find().sort('timestamp', -1).limit(limit))
    
    def mark_error_resolved(self, error_id: str) -> bool:
        """Отмечает ошибку как решенную."""
        result = self.error_logs.update_one(
            {'error_id': error_id},
            {'$set': {'resolved': True}}
        )
        
        return result.modified_count > 0
    
    # Методы для работы с событиями
    
    def create_event(self, event_data: Dict[str, Any]) -> str:
        """Создает новое событие в базе данных."""
        event_data['created_at'] = datetime.datetime.utcnow()
        event_data['updated_at'] = datetime.datetime.utcnow()
        event_data['event_id'] = f"event{ObjectId()}"
        
        result = self.events.insert_one(event_data)
        return str(result.inserted_id)
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о событии по его ID."""
        return self.events.find_one({'event_id': event_id})
    
    def update_event(self, event_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет информацию о событии."""
        update_data['updated_at'] = datetime.datetime.utcnow()
        
        result = self.events.update_one(
            {'event_id': event_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    def get_upcoming_events(self) -> List[Dict[str, Any]]:
        """Получает список предстоящих событий."""
        now = datetime.datetime.utcnow()
        
        return list(self.events.find({
            'start_time': {'$gt': now}
        }).sort('start_time', 1))
    
    # Методы для работы с подписками
    
    def create_subscription(self, subscription_data: Dict[str, Any]) -> str:
        """Создает новую подписку в базе данных."""
        subscription_data['created_at'] = datetime.datetime.utcnow()
        subscription_data['updated_at'] = datetime.datetime.utcnow()
        subscription_data['subscription_id'] = f"sub{ObjectId()}"
        
        result = self.subscriptions.insert_one(subscription_data)
        return str(result.inserted_id)
    
    def get_user_subscriptions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список подписок пользователя."""
        return list(self.subscriptions.find({
            'user_id': user_id,
            'is_active': True
        }))
    
    def update_subscription(self, subscription_id: str, is_active: bool) -> bool:
        """Обновляет статус подписки."""
        result = self.subscriptions.update_one(
            {'subscription_id': subscription_id},
            {
                '$set': {
                    'is_active': is_active,
                    'updated_at': datetime.datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    def get_subscribers_by_type(self, subscription_type: str) -> List[Dict[str, Any]]:
        """Получает список пользователей, подписанных на указанный тип уведомлений."""
        subscriptions = list(self.subscriptions.find({
            'type': subscription_type,
            'is_active': True
        }))
        
        user_ids = [sub['user_id'] for sub in subscriptions]
        
        return list(self.users.find({
            'user_id': {'$in': user_ids},
            'is_blocked': False
        }))
