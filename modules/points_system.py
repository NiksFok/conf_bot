#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для управления системой баллов.
Обеспечивает начисление и списание баллов, а также учет транзакций.
"""

from typing import Dict, List, Optional, Any
import datetime
from utils.db_connector import DBConnector

class PointsSystem:
    """Класс для управления системой баллов."""
    
    # Типы транзакций
    TRANSACTION_TYPES = {
        'earn': 'Начисление',
        'spend': 'Списание'
    }
    
    # Причины транзакций
    TRANSACTION_REASONS = {
        'stand_visit': 'Посещение стенда',
        'merch_order': 'Заказ мерча',
        'workshop_attendance': 'Посещение мастер-класса',
        'registration': 'Регистрация',
        'admin_adjustment': 'Корректировка администратором',
        'other': 'Другое'
    }
    
    def __init__(self, db: DBConnector):
        """Инициализация системы баллов."""
        self.db = db
    
    def add_points(self, user_id: int, amount: int, reason: str, reference_id: str = None) -> bool:
        """Начисляет баллы пользователю."""
        if amount <= 0:
            return False
        
        # Обновляем баланс пользователя
        if not self.db.update_user_points(user_id, amount):
            return False
        
        # Создаем транзакцию
        transaction_data = {
            'user_id': user_id,
            'amount': amount,
            'type': 'earn',
            'reason': reason,
            'reference_id': reference_id
        }
        
        self.db.create_points_transaction(transaction_data)
        return True
    
    def subtract_points(self, user_id: int, amount: int, reason: str, reference_id: str = None) -> bool:
        """Списывает баллы у пользователя."""
        if amount <= 0:
            return False
        
        # Проверяем, достаточно ли баллов у пользователя
        user = self.db.get_user(user_id)
        if not user or user.get('points', 0) < amount:
            return False
        
        # Обновляем баланс пользователя
        if not self.db.update_user_points(user_id, -amount):
            return False
        
        # Создаем транзакцию
        transaction_data = {
            'user_id': user_id,
            'amount': amount,
            'type': 'spend',
            'reason': reason,
            'reference_id': reference_id
        }
        
        self.db.create_points_transaction(transaction_data)
        return True
    
    def get_user_balance(self, user_id: int) -> int:
        """Получает текущий баланс баллов пользователя."""
        user = self.db.get_user(user_id)
        return user.get('points', 0) if user else 0
    
    def get_user_transactions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает историю транзакций пользователя."""
        return self.db.get_user_points_transactions(user_id)
    
    def check_stand_visit(self, user_id: int, stand_id: str) -> bool:
        """Проверяет, посещал ли пользователь указанный стенд ранее."""
        transactions = self.db.points_transactions.find({
            'user_id': user_id,
            'reason': 'stand_visit',
            'reference_id': stand_id
        })
        
        return transactions.count() > 0
    
    def get_points_statistics(self) -> Dict[str, Any]:
        """Получает статистику по баллам."""
        all_users = self.db.get_all_users()
        all_transactions = list(self.db.points_transactions.find())
        
        total_points_earned = sum(tx.get('amount', 0) for tx in all_transactions if tx.get('type') == 'earn')
        total_points_spent = sum(tx.get('amount', 0) for tx in all_transactions if tx.get('type') == 'spend')
        total_points_balance = sum(user.get('points', 0) for user in all_users)
        
        # Статистика по причинам начисления
        earn_reasons = {}
        for tx in all_transactions:
            if tx.get('type') == 'earn':
                reason = tx.get('reason', 'other')
                if reason not in earn_reasons:
                    earn_reasons[reason] = 0
                earn_reasons[reason] += tx.get('amount', 0)
        
        # Статистика по причинам списания
        spend_reasons = {}
        for tx in all_transactions:
            if tx.get('type') == 'spend':
                reason = tx.get('reason', 'other')
                if reason not in spend_reasons:
                    spend_reasons[reason] = 0
                spend_reasons[reason] += tx.get('amount', 0)
        
        # Пользователи с наибольшим количеством баллов
        top_users = sorted(all_users, key=lambda x: x.get('points', 0), reverse=True)[:10]
        top_users_data = []
        for user in top_users:
            top_users_data.append({
                'user_id': user.get('user_id'),
                'name': f"{user.get('first_name', '')} {user.get('last_name', '')}",
                'points': user.get('points', 0)
            })
        
        return {
            'total_points_earned': total_points_earned,
            'total_points_spent': total_points_spent,
            'total_points_balance': total_points_balance,
            'earn_reasons': earn_reasons,
            'spend_reasons': spend_reasons,
            'top_users': top_users_data
        }
