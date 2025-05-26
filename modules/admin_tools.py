#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для инструментов администратора.
Обеспечивает управление пользователями, стендами и мерчем.
"""

from typing import Dict, List, Optional, Any
import datetime
import uuid
from utils.db_connector import DBConnector

class AdminTools:
    """Класс для инструментов администратора."""
    
    def __init__(self, db: DBConnector, admin_code: str):
        """Инициализация инструментов администратора."""
        self.db = db
        self.admin_code = admin_code
    
    def verify_admin_code(self, code: str) -> bool:
        """Проверяет код администратора."""
        return code == self.admin_code
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает список всех пользователей."""
        return self.db.get_all_users()
    
    def change_user_role(self, user_id: int, new_role: str) -> bool:
        """Изменяет роль пользователя."""
        valid_roles = ['guest', 'standist', 'hr', 'admin']
        if new_role not in valid_roles:
            return False
        
        return self.db.update_user_role(user_id, new_role)
    
    def block_user(self, user_id: int) -> bool:
        """Блокирует пользователя."""
        return self.db.block_user(user_id, True)
    
    def unblock_user(self, user_id: int) -> bool:
        """Разблокирует пользователя."""
        return self.db.block_user(user_id, False)
    
    def create_stand(self, name: str, description: str, location: str, owner_id: int) -> str:
        """Создает новый стенд."""
        stand_id = f"stand_{uuid.uuid4().hex[:8]}"
        
        # Генерируем QR-код для стенда
        qr_code = f"https://example.com/qr/stand/{stand_id}.png"
        
        stand_data = {
            'stand_id': stand_id,
            'name': name,
            'description': description,
            'location': location,
            'qr_code': qr_code,
            'visits': 0,
            'owner_id': owner_id
        }
        
        return self.db.create_stand(stand_data)
    
    def update_stand(self, stand_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет информацию о стенде."""
        return self.db.update_stand(stand_id, update_data)
    
    def delete_stand(self, stand_id: str) -> bool:
        """Удаляет стенд."""
        # Проверяем, существует ли стенд
        stand = self.db.get_stand(stand_id)
        if not stand:
            return False
        
        # Удаляем стенд из базы данных
        result = self.db.stands.delete_one({'stand_id': stand_id})
        return result.deleted_count > 0
    
    def create_merch(self, name: str, description: str, image_url: str, 
                    points_cost: int, quantity_total: int) -> str:
        """Создает новый мерч."""
        merch_id = f"merch_{uuid.uuid4().hex[:8]}"
        
        merch_data = {
            'merch_id': merch_id,
            'name': name,
            'description': description,
            'image_url': image_url,
            'points_cost': points_cost,
            'quantity_total': quantity_total,
            'quantity_left': quantity_total
        }
        
        return self.db.create_merch(merch_data)
    
    def update_merch(self, merch_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет информацию о мерче."""
        return self.db.update_merch(merch_id, update_data)
    
    def delete_merch(self, merch_id: str) -> bool:
        """Удаляет мерч."""
        # Проверяем, существует ли мерч
        merch = self.db.get_merch(merch_id)
        if not merch:
            return False
        
        # Удаляем мерч из базы данных
        result = self.db.merch.delete_one({'merch_id': merch_id})
        return result.deleted_count > 0
    
    def add_points_to_user(self, user_id: int, points: int, reason: str = 'admin_adjustment') -> bool:
        """Добавляет баллы пользователю."""
        if points <= 0:
            return False
        
        # Обновляем баланс пользователя
        if not self.db.update_user_points(user_id, points):
            return False
        
        # Создаем транзакцию
        transaction_data = {
            'user_id': user_id,
            'amount': points,
            'type': 'earn',
            'reason': reason,
            'reference_id': None
        }
        
        self.db.create_points_transaction(transaction_data)
        return True
    
    def subtract_points_from_user(self, user_id: int, points: int, reason: str = 'admin_adjustment') -> bool:
        """Списывает баллы у пользователя."""
        if points <= 0:
            return False
        
        # Проверяем, достаточно ли баллов у пользователя
        user = self.db.get_user(user_id)
        if not user or user.get('points', 0) < points:
            return False
        
        # Обновляем баланс пользователя
        if not self.db.update_user_points(user_id, -points):
            return False
        
        # Создаем транзакцию
        transaction_data = {
            'user_id': user_id,
            'amount': points,
            'type': 'spend',
            'reason': reason,
            'reference_id': None
        }
        
        self.db.create_points_transaction(transaction_data)
        return True
    
    def get_error_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает список последних ошибок."""
        return self.db.get_recent_errors(limit)
    
    def mark_error_resolved(self, error_id: str) -> bool:
        """Отмечает ошибку как решенную."""
        return self.db.mark_error_resolved(error_id)
    
    def create_event(self, title: str, description: str, location: str, 
                    start_time: datetime.datetime, end_time: datetime.datetime, 
                    max_participants: int, points_reward: int) -> str:
        """Создает новое событие."""
        event_data = {
            'title': title,
            'description': description,
            'location': location,
            'start_time': start_time,
            'end_time': end_time,
            'max_participants': max_participants,
            'current_participants': 0,
            'points_reward': points_reward
        }
        
        return self.db.create_event(event_data)
    
    def update_event(self, event_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет информацию о событии."""
        return self.db.update_event(event_id, update_data)
    
    def delete_event(self, event_id: str) -> bool:
        """Удаляет событие."""
        # Проверяем, существует ли событие
        event = self.db.get_event(event_id)
        if not event:
            return False
        
        # Удаляем событие из базы данных
        result = self.db.events.delete_one({'event_id': event_id})
        return result.deleted_count > 0
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Получает статистику системы."""
        # Получаем количество пользователей по ролям
        all_users = self.db.get_all_users()
        roles = {}
        for user in all_users:
            role = user.get('role', 'guest')
            if role not in roles:
                roles[role] = 0
            roles[role] += 1
        
        # Получаем количество стендов
        all_stands = self.db.get_all_stands()
        
        # Получаем количество мерча
        all_merch = self.db.get_all_merch()
        
        # Получаем количество транзакций
        points_transactions = list(self.db.points_transactions.find())
        merch_transactions = list(self.db.merch_transactions.find())
        
        # Получаем количество ошибок
        errors = list(self.db.error_logs.find())
        unresolved_errors = len([err for err in errors if not err.get('resolved', False)])
        
        return {
            'users': {
                'total': len(all_users),
                'by_role': roles
            },
            'stands': {
                'total': len(all_stands),
                'total_visits': sum(stand.get('visits', 0) for stand in all_stands)
            },
            'merch': {
                'total': len(all_merch),
                'total_quantity': sum(item.get('quantity_total', 0) for item in all_merch),
                'available_quantity': sum(item.get('quantity_left', 0) for item in all_merch)
            },
            'transactions': {
                'points': len(points_transactions),
                'merch': len(merch_transactions)
            },
            'errors': {
                'total': len(errors),
                'unresolved': unresolved_errors
            }
        }
