#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки модуля управления мерчем.
Эмулирует взаимодействие с модулем для проверки корректности работы.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import datetime
import uuid

# Настройка пути для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт тестируемого модуля
from modules.merch_module import MerchManager
from utils.db_connector import DBConnector

class TestMerchManager(unittest.TestCase):
    """Тестирование модуля управления мерчем."""
    
    def setUp(self):
        """Подготовка к тестированию."""
        # Создаем мок для DBConnector
        self.db_mock = MagicMock(spec=DBConnector)
        
        # Создаем экземпляр менеджера мерча с моком базы данных
        self.merch_manager = MerchManager(self.db_mock)
        
        # Настраиваем тестовые данные
        self.test_merch_id = "merch_12345678"
        self.test_user_id = 123456789
        self.test_transaction_id = "tx_12345678"
        
        # Настраиваем мок для get_merch
        self.merch_data = {
            'merch_id': self.test_merch_id,
            'name': 'Футболка с логотипом',
            'description': 'Хлопковая футболка с логотипом конференции',
            'image_url': 'https://example.com/tshirt.jpg',
            'points_cost': 50,
            'quantity_total': 100,
            'quantity_left': 50,
            'created_at': datetime.datetime.utcnow()
        }
        self.db_mock.get_merch.return_value = self.merch_data
        
        # Настраиваем мок для get_user
        self.user_data = {
            'user_id': self.test_user_id,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'points': 100
        }
        self.db_mock.get_user.return_value = self.user_data
        
        # Настраиваем мок для get_merch_transaction
        self.transaction_data = {
            'transaction_id': self.test_transaction_id,
            'user_id': self.test_user_id,
            'merch_id': self.test_merch_id,
            'points_spent': 50,
            'status': 'pending',
            'created_at': datetime.datetime.utcnow()
        }
        self.db_mock.get_merch_transaction.return_value = self.transaction_data
    
    def test_create_merch(self):
        """Тестирование создания нового мерча."""
        # Настраиваем мок для create_merch
        self.db_mock.create_merch.return_value = self.test_merch_id
        
        # Вызываем метод create_merch
        result = self.merch_manager.create_merch(
            name='Футболка с логотипом',
            description='Хлопковая футболка с логотипом конференции',
            image_url='https://example.com/tshirt.jpg',
            points_cost=50,
            quantity_total=100
        )
        
        # Проверяем, что был вызван метод create_merch с правильными данными
        self.db_mock.create_merch.assert_called_once()
        args, kwargs = self.db_mock.create_merch.call_args
        merch_data = args[0]
        self.assertEqual(merch_data['name'], 'Футболка с логотипом')
        self.assertEqual(merch_data['description'], 'Хлопковая футболка с логотипом конференции')
        self.assertEqual(merch_data['image_url'], 'https://example.com/tshirt.jpg')
        self.assertEqual(merch_data['points_cost'], 50)
        self.assertEqual(merch_data['quantity_total'], 100)
        self.assertEqual(merch_data['quantity_left'], 100)
        
        # Проверяем, что метод вернул правильный ID
        self.assertEqual(result, self.test_merch_id)
    
    def test_get_merch(self):
        """Тестирование получения информации о мерче."""
        # Вызываем метод get_merch
        result = self.merch_manager.get_merch(self.test_merch_id)
        
        # Проверяем, что был вызван метод get_merch с правильными параметрами
        self.db_mock.get_merch.assert_called_once_with(self.test_merch_id)
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result, self.merch_data)
    
    def test_update_merch(self):
        """Тестирование обновления информации о мерче."""
        # Настраиваем мок для update_merch
        self.db_mock.update_merch.return_value = True
        
        # Подготавливаем данные для обновления
        update_data = {
            'description': 'Обновленное описание',
            'points_cost': 60
        }
        
        # Вызываем метод update_merch
        result = self.merch_manager.update_merch(self.test_merch_id, update_data)
        
        # Проверяем, что был вызван метод update_merch с правильными параметрами
        self.db_mock.update_merch.assert_called_once_with(self.test_merch_id, update_data)
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_get_all_merch(self):
        """Тестирование получения списка всего мерча."""
        # Настраиваем мок для get_all_merch
        all_merch = [self.merch_data]
        self.db_mock.get_all_merch.return_value = all_merch
        
        # Вызываем метод get_all_merch
        result = self.merch_manager.get_all_merch()
        
        # Проверяем, что был вызван метод get_all_merch
        self.db_mock.get_all_merch.assert_called_once()
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result, all_merch)
    
    def test_get_available_merch(self):
        """Тестирование получения списка доступного мерча."""
        # Настраиваем мок для get_all_merch
        available_merch = self.merch_data.copy()
        unavailable_merch = self.merch_data.copy()
        unavailable_merch['merch_id'] = 'merch_87654321'
        unavailable_merch['quantity_left'] = 0
        
        all_merch = [available_merch, unavailable_merch]
        self.db_mock.get_all_merch.return_value = all_merch
        
        # Вызываем метод get_available_merch
        result = self.merch_manager.get_available_merch()
        
        # Проверяем, что был вызван метод get_all_merch
        self.db_mock.get_all_merch.assert_called_once()
        
        # Проверяем, что метод вернул только доступный мерч
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['merch_id'], self.test_merch_id)
    
    def test_create_order_success(self):
        """Тестирование успешного создания заказа на мерч."""
        # Настраиваем мок для decrement_merch_quantity
        self.db_mock.decrement_merch_quantity.return_value = True
        
        # Вызываем метод create_order
        result = self.merch_manager.create_order(self.test_user_id, self.test_merch_id)
        
        # Проверяем, что были вызваны нужные методы
        self.db_mock.get_merch.assert_called_once_with(self.test_merch_id)
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        self.db_mock.decrement_merch_quantity.assert_called_once_with(self.test_merch_id)
        self.db_mock.create_merch_transaction.assert_called_once()
        
        # Проверяем данные транзакции
        args, kwargs = self.db_mock.create_merch_transaction.call_args
        transaction_data = args[0]
        self.assertEqual(transaction_data['user_id'], self.test_user_id)
        self.assertEqual(transaction_data['merch_id'], self.test_merch_id)
        self.assertEqual(transaction_data['points_spent'], 50)
        self.assertEqual(transaction_data['status'], 'pending')
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_create_order_no_merch(self):
        """Тестирование создания заказа при отсутствии мерча."""
        # Настраиваем мок для get_merch, чтобы он возвращал None
        self.db_mock.get_merch.return_value = None
        
        # Вызываем метод create_order
        result = self.merch_manager.create_order(self.test_user_id, self.test_merch_id)
        
        # Проверяем, что был вызван метод get_merch
        self.db_mock.get_merch.assert_called_once_with(self.test_merch_id)
        
        # Проверяем, что не были вызваны другие методы
        self.db_mock.get_user.assert_not_called()
        self.db_mock.decrement_merch_quantity.assert_not_called()
        self.db_mock.create_merch_transaction.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_create_order_out_of_stock(self):
        """Тестирование создания заказа при отсутствии мерча в наличии."""
        # Настраиваем мок для get_merch, чтобы он возвращал мерч с нулевым количеством
        out_of_stock_merch = self.merch_data.copy()
        out_of_stock_merch['quantity_left'] = 0
        self.db_mock.get_merch.return_value = out_of_stock_merch
        
        # Вызываем метод create_order
        result = self.merch_manager.create_order(self.test_user_id, self.test_merch_id)
        
        # Проверяем, что был вызван метод get_merch
        self.db_mock.get_merch.assert_called_once_with(self.test_merch_id)
        
        # Проверяем, что не были вызваны другие методы
        self.db_mock.get_user.assert_not_called()
        self.db_mock.decrement_merch_quantity.assert_not_called()
        self.db_mock.create_merch_transaction.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_create_order_not_enough_points(self):
        """Тестирование создания заказа при недостатке баллов у пользователя."""
        # Настраиваем мок для get_user, чтобы он возвращал пользователя с недостаточным количеством баллов
        user_with_few_points = self.user_data.copy()
        user_with_few_points['points'] = 10
        self.db_mock.get_user.return_value = user_with_few_points
        
        # Вызываем метод create_order
        result = self.merch_manager.create_order(self.test_user_id, self.test_merch_id)
        
        # Проверяем, что были вызваны нужные методы
        self.db_mock.get_merch.assert_called_once_with(self.test_merch_id)
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что не были вызваны другие методы
        self.db_mock.decrement_merch_quantity.assert_not_called()
        self.db_mock.create_merch_transaction.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_complete_order(self):
        """Тестирование отметки заказа как выполненного."""
        # Настраиваем мок для update_merch_transaction_status
        self.db_mock.update_merch_transaction_status.return_value = True
        
        # Вызываем метод complete_order
        result = self.merch_manager.complete_order(self.test_transaction_id)
        
        # Проверяем, что был вызван метод update_merch_transaction_status с правильными параметрами
        self.db_mock.update_merch_transaction_status.assert_called_once_with(self.test_transaction_id, 'completed')
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_cancel_order(self):
        """Тестирование отмены заказа."""
        # Настраиваем мок для increment_merch_quantity
        self.db_mock.increment_merch_quantity.return_value = True
        
        # Настраиваем мок для update_merch_transaction_status
        self.db_mock.update_merch_transaction_status.return_value = True
        
        # Вызываем метод cancel_order
        result = self.merch_manager.cancel_order(self.test_transaction_id)
        
        # Проверяем, что были вызваны нужные методы
        self.db_mock.get_merch_transaction.assert_called_once_with(self.test_transaction_id)
        self.db_mock.increment_merch_quantity.assert_called_once_with(self.test_merch_id)
        self.db_mock.update_merch_transaction_status.assert_called_once_with(self.test_transaction_id, 'cancelled')
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_cancel_order_not_pending(self):
        """Тестирование отмены заказа, который не находится в статусе ожидания."""
        # Настраиваем мок для get_merch_transaction, чтобы он возвращал транзакцию с другим статусом
        completed_transaction = self.transaction_data.copy()
        completed_transaction['status'] = 'completed'
        self.db_mock.get_merch_transaction.return_value = completed_transaction
        
        # Вызываем метод cancel_order
        result = self.merch_manager.cancel_order(self.test_transaction_id)
        
        # Проверяем, что был вызван метод get_merch_transaction
        self.db_mock.get_merch_transaction.assert_called_once_with(self.test_transaction_id)
        
        # Проверяем, что не были вызваны другие методы
        self.db_mock.increment_merch_quantity.assert_not_called()
        self.db_mock.update_merch_transaction_status.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_get_user_orders(self):
        """Тестирование получения списка заказов пользователя."""
        # Настраиваем мок для get_user_merch_transactions
        transactions = [self.transaction_data]
        self.db_mock.get_user_merch_transactions.return_value = transactions
        
        # Вызываем метод get_user_orders
        result = self.merch_manager.get_user_orders(self.test_user_id)
        
        # Проверяем, что был вызван метод get_user_merch_transactions с правильными параметрами
        self.db_mock.get_user_merch_transactions.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что был вызван метод get_merch для получения информации о мерче
        self.db_mock.get_merch.assert_called_with(self.test_merch_id)
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['transaction_id'], self.test_transaction_id)
        self.assertEqual(result[0]['merch_name'], self.merch_data['name'])
        self.assertEqual(result[0]['merch_description'], self.merch_data['description'])
    
    def test_get_pending_orders(self):
        """Тестирование получения списка ожидающих выполнения заказов."""
        # Настраиваем мок для get_pending_merch_transactions
        pending_transactions = [self.transaction_data]
        self.db_mock.get_pending_merch_transactions.return_value = pending_transactions
        
        # Вызываем метод get_pending_orders
        result = self.merch_manager.get_pending_orders()
        
        # Проверяем, что был вызван метод get_pending_merch_transactions
        self.db_mock.get_pending_merch_transactions.assert_called_once()
        
        # Проверяем, что были вызваны методы get_user и get_merch для получения дополнительной информации
        self.db_mock.get_user.assert_called_with(self.test_user_id)
        self.db_mock.get_merch.assert_called_with(self.test_merch_id)
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['transaction_id'], self.test_transaction_id)
        self.assertEqual(result[0]['user_name'], 'Иван Иванов')
        self.assertEqual(result[0]['merch_name'], self.merch_data['name'])
    
    def test_handle_out_of_stock(self):
        """Тестирование обработки ситуации, когда мерч закончился."""
        # Настраиваем мок для get_merch, чтобы он возвращал мерч с нулевым количеством
        out_of_stock_merch = self.merch_data.copy()
        out_of_stock_merch['quantity_left'] = 0
        self.db_mock.get_merch.return_value = out_of_stock_merch
        
        # Настраиваем мок для update_merch
        self.db_mock.update_merch.return_value = True
        
        # Вызываем метод handle_out_of_stock
        result = self.merch_manager.handle_out_of_stock(self.test_merch_id)
        
        # Проверяем, что был вызван метод get_merch
        self.db_mock.get_merch.assert_called_once_with(self.test_merch_id)
        
        # Проверяем, что был вызван метод create_admin_notification
        self.db_mock.create_admin_notification.assert_called_once()
        
        # Проверяем, что был вызван метод update_merch с правильными параметрами
        self.db_mock.update_merch.assert_called_once()
        args, kwargs = self.db_mock.update_merch.call_args
        self.assertEqual(args[0], self.test_merch_id)
        self.assertFalse(args[1]['is_available'])
        self.assertIn('out_of_stock_at', args[1])
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_handle_out_of_stock_with_stock(self):
        """Тестирование обработки ситуации, когда мерч еще есть в наличии."""
        # Настраиваем мок для get_merch, чтобы он возвращал мерч с положительным количеством
        in_stock_merch = self.merch_data.copy()
        in_stock_merch['quantity_left'] = 10
        self.db_mock.get_merch.return_value = in_stock_merch
        
        # Вызываем метод handle_out_of_stock
        result = self.merch_manager.handle_out_of_stock(self.test_merch_id)
        
        # Проверяем, что был вызван метод get_merch
        self.db_mock.get_merch.assert_called_once_with(self.test_merch_id)
        
        # Проверяем, что не были вызваны другие методы
        self.db_mock.create_admin_notification.assert_not_called()
        self.db_mock.update_merch.assert_not_called()
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_get_merch_statistics(self):
        """Тестирование получения статистики по мерчу."""
        # Настраиваем мок для get_all_merch
        all_merch = [
            {
                'merch_id': self.test_merch_id,
                'name': 'Футболка с логотипом',
                'quantity_total': 100,
                'quantity_left': 50
            },
            {
                'merch_id': 'merch_87654321',
                'name': 'Кружка с логотипом',
                'quantity_total': 50,
                'quantity_left': 20
            }
        ]
        self.db_mock.get_all_merch.return_value = all_merch
        
        # Настраиваем мок для get_all_merch_transactions
        all_transactions = [
            {
                'transaction_id': self.test_transaction_id,
                'merch_id': self.test_merch_id,
                'status': 'completed'
            },
            {
                'transaction_id': 'tx_87654321',
                'merch_id': self.test_merch_id,
                'status': 'pending'
            },
            {
                'transaction_id': 'tx_11111111',
                'merch_id': 'merch_87654321',
                'status': 'completed'
            },
            {
                'transaction_id': 'tx_22222222',
                'merch_id': 'merch_87654321',
                'status': 'cancelled'
            }
        ]
        self.db_mock.get_all_merch_transactions.return_value = all_transactions
        
        # Вызываем метод get_merch_statistics
        result = self.merch_manager.get_merch_statistics()
        
        # Проверяем, что были вызваны нужные методы
        self.db_mock.get_all_merch.assert_called_once()
        self.db_mock.get_all_merch_transactions.assert_called_once()
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result['total_merch'], 2)
        self.assertEqual(result['total_quantity'], 150)
        self.assertEqual(result['available_quantity'], 70)
        self.assertEqual(result['ordered_quantity'], 80)
        self.assertEqual(result['completed_orders'], 2)
        self.assertEqual(result['pending_orders'], 1)
        self.assertEqual(result['cancelled_orders'], 1)
        
        # Проверяем популярность мерча
        self.assertEqual(len(result['popular_merch']), 2)
        self.assertEqual(result['popular_merch'][0]['merch_id'], self.test_merch_id)
        self.assertEqual(result['popular_merch'][0]['orders_count'], 2)
        self.assertEqual(result['popular_merch'][1]['merch_id'], 'merch_87654321')
        self.assertEqual(result['popular_merch'][1]['orders_count'], 2)

if __name__ == '__main__':
    unittest.main()
