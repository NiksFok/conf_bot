#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для управления ролями пользователей.
Обеспечивает проверку прав доступа и изменение ролей.
"""

from typing import Dict, List, Optional, Any
from utils.db_connector import DBConnector

class RoleManager:
    """Класс для управления ролями пользователей."""
    
    # Доступные роли с эмодзи
    ROLES = {
        'guest': '✨ Гость',
        'standist': '🏢 Стендист',
        'hr': '👔 HR-специалист',
        'admin': '🔑 Администратор'
    }
    
    # Права доступа для ролей
    PERMISSIONS = {
        'guest': [
            'view_merch',
            'order_merch',
            'view_points',
            'view_stands',
            'manage_subscriptions'
        ],
        'standist': [
            'view_merch',
            'order_merch',
            'view_points',
            'view_stands',
            'manage_subscriptions',
            'scan_qr',
            'view_stand_stats',
            'view_my_stand'
        ],
        'hr': [
            'view_merch',
            'order_merch',
            'view_points',
            'view_stands',
            'manage_subscriptions',
            'mark_candidate',
            'view_candidates',
            'add_note',
            'export_candidates'
        ],
        'admin': [
            'view_merch',
            'order_merch',
            'view_points',
            'view_stands',
            'manage_subscriptions',
            'scan_qr',
            'view_stand_stats',
            'view_my_stand',
            'mark_candidate',
            'view_candidates',
            'add_note',
            'export_candidates',
            'manage_users',
            'manage_stands',
            'manage_merch',
            'view_statistics',
            'send_broadcast'
        ]
    }
    
    def __init__(self, db: DBConnector):
        """Инициализация менеджера ролей."""
        self.db = db
    
    def get_user_role(self, user_id: int) -> str:
        """Получает роль пользователя."""
        user = self.db.get_user(user_id)
        if user:
            return user.get('role', 'guest')
        return 'guest'
    
    def set_user_role(self, user_id: int, role: str) -> bool:
        """Устанавливает роль пользователя."""
        if role not in self.ROLES:
            return False
        
        return self.db.update_user_role(user_id, role)
    
    def check_permission(self, user_id: int, permission: str) -> bool:
        """Проверяет наличие у пользователя указанного разрешения."""
        role = self.get_user_role(user_id)
        
        # Проверяем, не заблокирован ли пользователь
        user = self.db.get_user(user_id)
        if user and user.get('is_blocked', False):
            return False
        
        return permission in self.PERMISSIONS.get(role, [])
    
    def get_role_name(self, role: str) -> str:
        """Возвращает название роли на русском языке с эмодзи."""
        return self.ROLES.get(role, '❓ Неизвестная роль')
    
    def get_available_permissions(self, role: str) -> List[str]:
        """Возвращает список доступных разрешений для указанной роли."""
        return self.PERMISSIONS.get(role, [])
    
    def get_all_roles(self) -> Dict[str, str]:
        """Возвращает словарь всех доступных ролей."""
        return self.ROLES.copy()
    
    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Возвращает список пользователей с указанной ролью."""
        return self.db.get_users_by_role(role)
    
    def block_user(self, user_id: int) -> bool:
        """Блокирует пользователя."""
        return self.db.block_user(user_id, True)
    
    def unblock_user(self, user_id: int) -> bool:
        """Разблокирует пользователя."""
        return self.db.block_user(user_id, False)
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь."""
        user = self.db.get_user(user_id)
        return user and user.get('is_blocked', False)
