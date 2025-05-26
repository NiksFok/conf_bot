#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для управления подписками на уведомления.
Обеспечивает подписку и отписку от различных типов уведомлений.
"""

from typing import Dict, List, Optional, Any
import datetime
import uuid
from utils.db_connector import DBConnector

class SubscriptionManager:
    """Класс для управления подписками на уведомления."""
    
    # Типы подписок
    SUBSCRIPTION_TYPES = {
        'announcements': 'Анонсы и объявления',
        'workshops': 'Мастер-классы и воркшопы',
        'job_offers': 'Вакансии и предложения работы',
        'merch_updates': 'Обновления мерча',
        'special_offers': 'Специальные предложения'
    }
    
    def __init__(self, db: DBConnector):
        """Инициализация менеджера подписок."""
        self.db = db
    
    def subscribe(self, user_id: int, subscription_type: str) -> bool:
        """Подписывает пользователя на указанный тип уведомлений."""
        if subscription_type not in self.SUBSCRIPTION_TYPES:
            return False
        
        # Проверяем, существует ли уже такая подписка
        existing = self.db.subscriptions.find_one({
            'user_id': user_id,
            'type': subscription_type
        })
        
        if existing:
            # Если подписка существует, но неактивна, активируем её
            if not existing.get('is_active', True):
                return self.db.update_subscription(existing.get('subscription_id'), True)
            return True  # Подписка уже существует и активна
        
        # Создаем новую подписку
        subscription_data = {
            'user_id': user_id,
            'type': subscription_type,
            'is_active': True
        }
        
        self.db.create_subscription(subscription_data)
        return True
    
    def unsubscribe(self, user_id: int, subscription_type: str) -> bool:
        """Отписывает пользователя от указанного типа уведомлений."""
        # Находим подписку
        subscription = self.db.subscriptions.find_one({
            'user_id': user_id,
            'type': subscription_type,
            'is_active': True
        })
        
        if not subscription:
            return False  # Подписка не найдена или уже неактивна
        
        # Деактивируем подписку
        return self.db.update_subscription(subscription.get('subscription_id'), False)
    
    def get_user_subscriptions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список активных подписок пользователя."""
        subscriptions = self.db.get_user_subscriptions(user_id)
        
        # Добавляем названия типов подписок
        for sub in subscriptions:
            sub_type = sub.get('type')
            sub['type_name'] = self.SUBSCRIPTION_TYPES.get(sub_type, sub_type)
        
        return subscriptions
    
    def get_all_subscription_types(self) -> Dict[str, str]:
        """Возвращает словарь всех доступных типов подписок."""
        return self.SUBSCRIPTION_TYPES.copy()
    
    def get_subscribers(self, subscription_type: str) -> List[Dict[str, Any]]:
        """Получает список пользователей, подписанных на указанный тип уведомлений."""
        if subscription_type not in self.SUBSCRIPTION_TYPES:
            return []
        
        return self.db.get_subscribers_by_type(subscription_type)
    
    def send_notification(self, bot, subscription_type: str, message: str) -> Dict[str, Any]:
        """Отправляет уведомление всем подписчикам указанного типа."""
        if subscription_type not in self.SUBSCRIPTION_TYPES:
            return {'success': False, 'error': 'Invalid subscription type'}
        
        subscribers = self.get_subscribers(subscription_type)
        
        sent_count = 0
        failed_count = 0
        
        for subscriber in subscribers:
            try:
                bot.send_message(
                    chat_id=subscriber.get('user_id'),
                    text=f"📢 *{self.SUBSCRIPTION_TYPES.get(subscription_type)}*\n\n{message}",
                    parse_mode='Markdown'
                )
                sent_count += 1
            except Exception as e:
                failed_count += 1
                # Логируем ошибку
                self.db.log_error({
                    'user_id': subscriber.get('user_id'),
                    'error_type': 'notification_send_failed',
                    'error_message': str(e),
                    'resolved': False
                })
        
        return {
            'success': True,
            'subscription_type': subscription_type,
            'total_subscribers': len(subscribers),
            'sent_count': sent_count,
            'failed_count': failed_count
        }
