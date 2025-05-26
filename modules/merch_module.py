#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для управления мерчем.
Обеспечивает работу с каталогом мерча и обработку заказов.
"""

from typing import Dict, List, Optional, Any
import datetime
import uuid
from utils.db_connector import DBConnector

class MerchManager:
    """Класс для управления мерчем."""
    
    def __init__(self, db: DBConnector):
        """Инициализация менеджера мерча."""
        self.db = db
    
    def create_merch(self, name: str, description: str, image_url: str, 
                    points_cost: int, quantity_total: int) -> str:
        """Создает новый мерч в каталоге."""
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
    
    def get_merch(self, merch_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о мерче по его ID."""
        return self.db.get_merch(merch_id)
    
    def update_merch(self, merch_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет информацию о мерче."""
        return self.db.update_merch(merch_id, update_data)
    
    def get_all_merch(self) -> List[Dict[str, Any]]:
        """Получает список всего доступного мерча."""
        return self.db.get_all_merch()
    
    def get_available_merch(self) -> List[Dict[str, Any]]:
        """Получает список мерча, доступного для заказа."""
        all_merch = self.db.get_all_merch()
        return [item for item in all_merch if item.get('quantity_left', 0) > 0]
    
    def create_order(self, user_id: int, merch_id: str) -> bool:
        """Создает заказ на мерч."""
        # Получаем информацию о мерче
        merch = self.db.get_merch(merch_id)
        if not merch or merch.get('quantity_left', 0) <= 0:
            return False
        
        # Получаем информацию о пользователе
        user = self.db.get_user(user_id)
        if not user or user.get('points', 0) < merch.get('points_cost', 0):
            return False
        
        # Уменьшаем количество доступного мерча
        if not self.db.decrement_merch_quantity(merch_id):
            return False
        
        # Создаем транзакцию мерча
        transaction_data = {
            'user_id': user_id,
            'merch_id': merch_id,
            'points_spent': merch.get('points_cost', 0),
            'status': 'pending'
        }
        
        self.db.create_merch_transaction(transaction_data)
        return True
    
    def complete_order(self, transaction_id: str) -> bool:
        """Отмечает заказ как выполненный."""
        return self.db.update_merch_transaction_status(transaction_id, 'completed')
    
    def cancel_order(self, transaction_id: str) -> bool:
        """Отменяет заказ."""
        # Получаем информацию о транзакции
        transaction = self.db.merch_transactions.find_one({'transaction_id': transaction_id})
        if not transaction or transaction.get('status') != 'pending':
            return False
        
        # Возвращаем мерч в наличие
        merch_id = transaction.get('merch_id')
        self.db.merch.update_one(
            {'merch_id': merch_id},
            {'$inc': {'quantity_left': 1}}
        )
        
        # Обновляем статус транзакции
        return self.db.update_merch_transaction_status(transaction_id, 'cancelled')
    
    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список заказов пользователя."""
        transactions = self.db.get_user_merch_transactions(user_id)
        
        # Добавляем информацию о мерче к каждой транзакции
        for tx in transactions:
            merch = self.db.get_merch(tx.get('merch_id'))
            if merch:
                tx['merch_name'] = merch.get('name')
                tx['merch_description'] = merch.get('description')
        
        return transactions
    
    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Получает список ожидающих выполнения заказов."""
        pending_transactions = list(self.db.merch_transactions.find({'status': 'pending'}).sort('created_at', 1))
        
        # Добавляем информацию о пользователе и мерче к каждой транзакции
        for tx in pending_transactions:
            user = self.db.get_user(tx.get('user_id'))
            merch = self.db.get_merch(tx.get('merch_id'))
            
            if user:
                tx['user_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
            
            if merch:
                tx['merch_name'] = merch.get('name')
        
        return pending_transactions
    
    def get_merch_statistics(self) -> Dict[str, Any]:
        """Получает статистику по мерчу."""
        all_merch = self.db.get_all_merch()
        all_transactions = list(self.db.merch_transactions.find())
        
        total_merch = len(all_merch)
        total_quantity = sum(item.get('quantity_total', 0) for item in all_merch)
        available_quantity = sum(item.get('quantity_left', 0) for item in all_merch)
        ordered_quantity = total_quantity - available_quantity
        
        completed_orders = len([tx for tx in all_transactions if tx.get('status') == 'completed'])
        pending_orders = len([tx for tx in all_transactions if tx.get('status') == 'pending'])
        cancelled_orders = len([tx for tx in all_transactions if tx.get('status') == 'cancelled'])
        
        # Популярность мерча
        merch_popularity = {}
        for tx in all_transactions:
            merch_id = tx.get('merch_id')
            if merch_id not in merch_popularity:
                merch_popularity[merch_id] = 0
            merch_popularity[merch_id] += 1
        
        # Сортируем по популярности
        popular_merch = []
        for merch_id, count in sorted(merch_popularity.items(), key=lambda x: x[1], reverse=True):
            merch = self.db.get_merch(merch_id)
            if merch:
                popular_merch.append({
                    'merch_id': merch_id,
                    'name': merch.get('name'),
                    'orders_count': count
                })
        
        return {
            'total_merch': total_merch,
            'total_quantity': total_quantity,
            'available_quantity': available_quantity,
            'ordered_quantity': ordered_quantity,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'cancelled_orders': cancelled_orders,
            'popular_merch': popular_merch
        }
