#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки модуля системы баллов.
Эмулирует взаимодействие с модулем для проверки корректности работы.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import datetime

# Настройка пути для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт тестируемого модуля
from modules.points_system import PointsSystem
from utils.db_connector import DBConnector

class TestPointsSystem(unittest.TestCase):
    """Тестирование модуля системы баллов."""
    
    def setUp(self):
        """Подготовка к тестированию."""
        # Создаем мок для DBConnector
        self.db_mock = MagicMock(spec=DBConnector)
        
        # Создаем моки для коллекций базы данных
        self.db_mock.points_transactions = MagicMock()
        
        # Создаем экземпляр системы баллов с моком базы данных
        self.points_system = PointsSystem(self.db_mock)
        
        # Настраиваем тестовые данные
        self.test_user_id = 123456789
        self.test_transaction_id = "tx_12345678"
        
        # Настраиваем мок для get_user
        self.user_data = {
            'user_id': self.test_user_id,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'points': 100
        }
        self.db_mock.get_user.return_value = self.user_data
        
        # Настраиваем мок для get_points_transaction
        self.transaction_data = {
            'transaction_id': self.test_transaction_id,
            'user_id': self.test_user_id,
            'amount': 50,
            'type': 'earn',
            'reason': 'stand_visit',
            'reference_id': 'stand_123',
            'created_at': datetime.datetime.utcnow()
        }
        self.db_mock.get_points_transaction.return_value = self.transaction_data
    
    def test_add_points(self):
        """Тестирование начисления баллов пользователю."""
        # Настраиваем мок для update_user_points
        self.db_mock.update_user_points.return_value = True
        
        # Вызываем метод add_points
        result = self.points_system.add_points(
            user_id=self.test_user_id,
            amount=50,
            reason='stand_visit',
            reference_id='stand_123'
        )
        
        # Проверяем, что был вызван метод update_user_points с правильными параметрами
        self.db_mock.update_user_points.assert_called_once_with(self.test_user_id, 50)
        
        # Проверяем, что был вызван метод create_points_transaction с правильными данными
        self.db_mock.create_points_transaction.assert_called_once()
        args, kwargs = self.db_mock.create_points_transaction.call_args
        transaction_data = args[0]
        self.assertEqual(transaction_data['user_id'], self.test_user_id)
        self.assertEqual(transaction_data['amount'], 50)
        self.assertEqual(transaction_data['type'], 'earn')
        self.assertEqual(transaction_data['reason'], 'stand_visit')
        self.assertEqual(transaction_data['reference_id'], 'stand_123')
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_add_points_invalid_amount(self):
        """Тестирование начисления некорректного количества баллов."""
        # Вызываем метод add_points с отрицательным количеством баллов
        result = self.points_system.add_points(
            user_id=self.test_user_id,
            amount=-50,
            reason='stand_visit'
        )
        
        # Проверяем, что не был вызван метод update_user_points
        self.db_mock.update_user_points.assert_not_called()
        
        # Проверяем, что не был вызван метод create_points_transaction
        self.db_mock.create_points_transaction.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
        
        # Вызываем метод add_points с нулевым количеством баллов
        result = self.points_system.add_points(
            user_id=self.test_user_id,
            amount=0,
            reason='stand_visit'
        )
        
        # Проверяем, что не был вызван метод update_user_points
        self.db_mock.update_user_points.assert_not_called()
        
        # Проверяем, что не был вызван метод create_points_transaction
        self.db_mock.create_points_transaction.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_subtract_points(self):
        """Тестирование списания баллов у пользователя."""
        # Настраиваем мок для update_user_points
        self.db_mock.update_user_points.return_value = True
        
        # Вызываем метод subtract_points
        result = self.points_system.subtract_points(
            user_id=self.test_user_id,
            amount=50,
            reason='merch_order',
            reference_id='merch_123'
        )
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что был вызван метод update_user_points с правильными параметрами
        self.db_mock.update_user_points.assert_called_once_with(self.test_user_id, -50)
        
        # Проверяем, что был вызван метод create_points_transaction с правильными данными
        self.db_mock.create_points_transaction.assert_called_once()
        args, kwargs = self.db_mock.create_points_transaction.call_args
        transaction_data = args[0]
        self.assertEqual(transaction_data['user_id'], self.test_user_id)
        self.assertEqual(transaction_data['amount'], 50)
        self.assertEqual(transaction_data['type'], 'spend')
        self.assertEqual(transaction_data['reason'], 'merch_order')
        self.assertEqual(transaction_data['reference_id'], 'merch_123')
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_subtract_points_invalid_amount(self):
        """Тестирование списания некорректного количества баллов."""
        # Вызываем метод subtract_points с отрицательным количеством баллов
        result = self.points_system.subtract_points(
            user_id=self.test_user_id,
            amount=-50,
            reason='merch_order'
        )
        
        # Проверяем, что не был вызван метод get_user
        self.db_mock.get_user.assert_not_called()
        
        # Проверяем, что не был вызван метод update_user_points
        self.db_mock.update_user_points.assert_not_called()
        
        # Проверяем, что не был вызван метод create_points_transaction
        self.db_mock.create_points_transaction.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
        
        # Вызываем метод subtract_points с нулевым количеством баллов
        result = self.points_system.subtract_points(
            user_id=self.test_user_id,
            amount=0,
            reason='merch_order'
        )
        
        # Проверяем, что не был вызван метод get_user
        self.db_mock.get_user.assert_not_called()
        
        # Проверяем, что не был вызван метод update_user_points
        self.db_mock.update_user_points.assert_not_called()
        
        # Проверяем, что не был вызван метод create_points_transaction
        self.db_mock.create_points_transaction.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_subtract_points_not_enough_balance(self):
        """Тестирование списания баллов при недостаточном балансе."""
        # Настраиваем мок для get_user, чтобы он возвращал пользователя с недостаточным количеством баллов
        user_with_few_points = self.user_data.copy()
        user_with_few_points['points'] = 30
        self.db_mock.get_user.return_value = user_with_few_points
        
        # Вызываем метод subtract_points
        result = self.points_system.subtract_points(
            user_id=self.test_user_id,
            amount=50,
            reason='merch_order'
        )
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что не был вызван метод update_user_points
        self.db_mock.update_user_points.assert_not_called()
        
        # Проверяем, что не был вызван метод create_points_transaction
        self.db_mock.create_points_transaction.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_get_user_balance(self):
        """Тестирование получения текущего баланса баллов пользователя."""
        # Вызываем метод get_user_balance
        result = self.points_system.get_user_balance(self.test_user_id)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что метод вернул правильное количество баллов
        self.assertEqual(result, 100)
    
    def test_get_user_balance_nonexistent_user(self):
        """Тестирование получения баланса несуществующего пользователя."""
        # Настраиваем мок для get_user, чтобы он возвращал None
        self.db_mock.get_user.return_value = None
        
        # Вызываем метод get_user_balance
        result = self.points_system.get_user_balance(self.test_user_id)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что метод вернул 0
        self.assertEqual(result, 0)
    
    def test_get_user_transactions(self):
        """Тестирование получения истории транзакций пользователя."""
        # Настраиваем мок для get_user_points_transactions
        transactions = [self.transaction_data]
        self.db_mock.get_user_points_transactions.return_value = transactions
        
        # Вызываем метод get_user_transactions
        result = self.points_system.get_user_transactions(self.test_user_id)
        
        # Проверяем, что был вызван метод get_user_points_transactions с правильными параметрами
        self.db_mock.get_user_points_transactions.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result, transactions)
    
    def test_check_stand_visit(self):
        """Тестирование проверки посещения стенда пользователем."""
        # Настраиваем мок для points_transactions.count_documents
        self.db_mock.points_transactions.count_documents.return_value = 1
        
        # Вызываем метод check_stand_visit
        result = self.points_system.check_stand_visit(self.test_user_id, 'stand_123')
        
        # Проверяем, что был вызван метод count_documents с правильными параметрами
        self.db_mock.points_transactions.count_documents.assert_called_once()
        args, kwargs = self.db_mock.points_transactions.count_documents.call_args
        query = args[0]
        self.assertEqual(query['user_id'], self.test_user_id)
        self.assertEqual(query['reason'], 'stand_visit')
        self.assertEqual(query['reference_id'], 'stand_123')
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_check_stand_visit_not_visited(self):
        """Тестирование проверки непосещенного стенда."""
        # Настраиваем мок для points_transactions.count_documents
        self.db_mock.points_transactions.count_documents.return_value = 0
        
        # Вызываем метод check_stand_visit
        result = self.points_system.check_stand_visit(self.test_user_id, 'stand_123')
        
        # Проверяем, что был вызван метод count_documents с правильными параметрами
        self.db_mock.points_transactions.count_documents.assert_called_once()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_cancel_transaction(self):
        """Тестирование отмены транзакции баллов."""
        # Настраиваем мок для update_user_points
        self.db_mock.update_user_points.return_value = True
        
        # Настраиваем мок для update_points_transaction_status
        self.db_mock.update_points_transaction_status.return_value = True
        
        # Вызываем метод cancel_transaction
        result = self.points_system.cancel_transaction(self.test_transaction_id)
        
        # Проверяем, что был вызван метод get_points_transaction
        self.db_mock.get_points_transaction.assert_called_once_with(self.test_transaction_id)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что был вызван метод update_user_points с правильными параметрами
        self.db_mock.update_user_points.assert_called_once_with(self.test_user_id, -50)
        
        # Проверяем, что был вызван метод create_points_transaction с правильными данными
        self.db_mock.create_points_transaction.assert_called_once()
        args, kwargs = self.db_mock.create_points_transaction.call_args
        transaction_data = args[0]
        self.assertEqual(transaction_data['user_id'], self.test_user_id)
        self.assertEqual(transaction_data['amount'], 50)
        self.assertEqual(transaction_data['type'], 'spend')
        self.assertEqual(transaction_data['reason'], 'cancel_stand_visit')
        self.assertEqual(transaction_data['reference_id'], self.test_transaction_id)
        
        # Проверяем, что был вызван метод update_points_transaction_status с правильными параметрами
        self.db_mock.update_points_transaction_status.assert_called_once_with(self.test_transaction_id, 'cancelled')
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_cancel_transaction_spend(self):
        """Тестирование отмены транзакции списания баллов."""
        # Настраиваем мок для get_points_transaction, чтобы он возвращал транзакцию списания
        spend_transaction = self.transaction_data.copy()
        spend_transaction['type'] = 'spend'
        self.db_mock.get_points_transaction.return_value = spend_transaction
        
        # Настраиваем мок для update_user_points
        self.db_mock.update_user_points.return_value = True
        
        # Настраиваем мок для update_points_transaction_status
        self.db_mock.update_points_transaction_status.return_value = True
        
        # Вызываем метод cancel_transaction
        result = self.points_system.cancel_transaction(self.test_transaction_id)
        
        # Проверяем, что был вызван метод get_points_transaction
        self.db_mock.get_points_transaction.assert_called_once_with(self.test_transaction_id)
        
        # Проверяем, что не был вызван метод get_user
        self.db_mock.get_user.assert_not_called()
        
        # Проверяем, что был вызван метод update_user_points с правильными параметрами
        self.db_mock.update_user_points.assert_called_once_with(self.test_user_id, 50)
        
        # Проверяем, что был вызван метод create_points_transaction с правильными данными
        self.db_mock.create_points_transaction.assert_called_once()
        args, kwargs = self.db_mock.create_points_transaction.call_args
        transaction_data = args[0]
        self.assertEqual(transaction_data['type'], 'earn')
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_cancel_transaction_not_enough_points(self):
        """Тестирование отмены транзакции при недостаточном балансе."""
        # Настраиваем мок для get_user, чтобы он возвращал пользователя с недостаточным количеством баллов
        user_with_few_points = self.user_data.copy()
        user_with_few_points['points'] = 30
        self.db_mock.get_user.return_value = user_with_few_points
        
        # Вызываем метод cancel_transaction
        result = self.points_system.cancel_transaction(self.test_transaction_id)
        
        # Проверяем, что был вызван метод get_points_transaction
        self.db_mock.get_points_transaction.assert_called_once_with(self.test_transaction_id)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что не был вызван метод update_user_points
        self.db_mock.update_user_points.assert_not_called()
        
        # Проверяем, что не был вызван метод create_points_transaction
        self.db_mock.create_points_transaction.assert_not_called()
        
        # Проверяем, что не был вызван метод update_points_transaction_status
        self.db_mock.update_points_transaction_status.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_get_points_statistics(self):
        """Тестирование получения статистики по баллам."""
        # Настраиваем мок для get_all_users
        all_users = [
            {
                'user_id': self.test_user_id,
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'points': 100
            },
            {
                'user_id': 987654321,
                'first_name': 'Петр',
                'last_name': 'Петров',
                'points': 150
            }
        ]
        self.db_mock.get_all_users.return_value = all_users
        
        # Настраиваем мок для points_transactions.find
        all_transactions = [
            {
                'transaction_id': self.test_transaction_id,
                'user_id': self.test_user_id,
                'amount': 50,
                'type': 'earn',
                'reason': 'stand_visit',
                'reference_id': 'stand_123'
            },
            {
                'transaction_id': 'tx_87654321',
                'user_id': 987654321,
                'amount': 100,
                'type': 'earn',
                'reason': 'registration'
            },
            {
                'transaction_id': 'tx_11111111',
                'user_id': self.test_user_id,
                'amount': 30,
                'type': 'spend',
                'reason': 'merch_order',
                'reference_id': 'merch_123'
            }
        ]
        self.db_mock.points_transactions.find.return_value = all_transactions
        
        # Вызываем метод get_points_statistics
        result = self.points_system.get_points_statistics()
        
        # Проверяем, что были вызваны нужные методы
        self.db_mock.get_all_users.assert_called_once()
        self.db_mock.points_transactions.find.assert_called_once()
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result['total_points_earned'], 150)
        self.assertEqual(result['total_points_spent'], 30)
        self.assertEqual(result['total_points_balance'], 250)
        
        # Проверяем статистику по причинам начисления
        self.assertEqual(result['earn_reasons']['stand_visit'], 50)
        self.assertEqual(result['earn_reasons']['registration'], 100)
        
        # Проверяем статистику по причинам списания
        self.assertEqual(result['spend_reasons']['merch_order'], 30)
        
        # Проверяем список пользователей с наибольшим количеством баллов
        self.assertEqual(len(result['top_users']), 2)
        self.assertEqual(result['top_users'][0]['user_id'], 987654321)
        self.assertEqual(result['top_users'][0]['points'], 150)
        self.assertEqual(result['top_users'][1]['user_id'], self.test_user_id)
        self.assertEqual(result['top_users'][1]['points'], 100)

if __name__ == '__main__':
    unittest.main()
