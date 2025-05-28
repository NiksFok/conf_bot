#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки модуля статистики и аналитики.
Эмулирует взаимодействие с модулем для проверки корректности работы.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import io

# Настройка пути для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт тестируемого модуля
from modules.statistics_analytics import StatisticsManager
from utils.db_connector import DBConnector

class TestStatisticsManager(unittest.TestCase):
    """Тестирование модуля статистики и аналитики."""
    
    def setUp(self):
        """Подготовка к тестированию."""
        # Создаем мок для DBConnector
        self.db_mock = MagicMock(spec=DBConnector)
        
        # Создаем моки для коллекций базы данных
        self.db_mock.users = MagicMock()
        self.db_mock.points_transactions = MagicMock()
        self.db_mock.merch_transactions = MagicMock()
        
        # Создаем экземпляр менеджера статистики с моком базы данных
        self.statistics_manager = StatisticsManager(self.db_mock)
        
        # Настраиваем тестовые данные
        self.test_user_id = 123456789
        self.test_stand_id = "stand_12345678"
        
        # Настраиваем мок для get_all_users
        self.users_data = [
            {
                'user_id': self.test_user_id,
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'role': 'participant',
                'company': 'ООО Рога и Копыта',
                'points': 100,
                'registered_at': datetime.datetime(2025, 5, 25, 10, 0, 0),
                'last_activity': datetime.datetime(2025, 5, 27, 9, 0, 0)
            },
            {
                'user_id': 987654321,
                'first_name': 'Петр',
                'last_name': 'Петров',
                'role': 'hr',
                'company': 'ООО Дизайн Про',
                'points': 150,
                'registered_at': datetime.datetime(2025, 5, 26, 11, 0, 0),
                'last_activity': datetime.datetime(2025, 5, 27, 8, 0, 0)
            }
        ]
        self.db_mock.get_all_users.return_value = self.users_data
        
        # Настраиваем мок для get_all_stands
        self.stands_data = [
            {
                'stand_id': self.test_stand_id,
                'name': 'Стенд компании А',
                'description': 'Описание стенда компании А',
                'visits': 10
            },
            {
                'stand_id': 'stand_87654321',
                'name': 'Стенд компании Б',
                'description': 'Описание стенда компании Б',
                'visits': 5
            }
        ]
        self.db_mock.get_all_stands.return_value = self.stands_data
        
        # Настраиваем мок для get_stand
        self.db_mock.get_stand.return_value = self.stands_data[0]
        
        # Настраиваем мок для get_user
        self.db_mock.get_user.return_value = self.users_data[0]
        
        # Настраиваем мок для users.count_documents
        self.db_mock.users.count_documents.return_value = 1
        
        # Настраиваем мок для points_transactions.find
        self.points_transactions_data = [
            {
                'transaction_id': 'tx_12345678',
                'user_id': self.test_user_id,
                'amount': 50,
                'type': 'earn',
                'reason': 'stand_visit',
                'reference_id': self.test_stand_id,
                'created_at': datetime.datetime(2025, 5, 27, 9, 30, 0)
            },
            {
                'transaction_id': 'tx_87654321',
                'user_id': 987654321,
                'amount': 100,
                'type': 'earn',
                'reason': 'registration',
                'created_at': datetime.datetime(2025, 5, 26, 11, 0, 0)
            },
            {
                'transaction_id': 'tx_11111111',
                'user_id': self.test_user_id,
                'amount': 30,
                'type': 'spend',
                'reason': 'merch_order',
                'reference_id': 'merch_123',
                'created_at': datetime.datetime(2025, 5, 27, 10, 0, 0)
            }
        ]
        
        # Создаем мок для курсора MongoDB с методом sort
        cursor_mock = MagicMock()
        cursor_mock.__iter__.return_value = iter(self.points_transactions_data)
        cursor_mock.sort.return_value = cursor_mock
        self.db_mock.points_transactions.find.return_value = cursor_mock
        
        # Настраиваем мок для merch_transactions.find
        self.merch_transactions_data = [
            {
                'transaction_id': 'mtx_12345678',
                'user_id': self.test_user_id,
                'merch_id': 'merch_123',
                'points_spent': 30,
                'status': 'completed',
                'created_at': datetime.datetime(2025, 5, 27, 10, 0, 0)
            }
        ]
        merch_cursor_mock = MagicMock()
        merch_cursor_mock.__iter__.return_value = iter(self.merch_transactions_data)
        self.db_mock.merch_transactions.find.return_value = merch_cursor_mock
        
        # Настраиваем мок для points_transactions.count_documents
        self.db_mock.points_transactions.count_documents.return_value = 1
        
        # Создаем временную директорию для тестовых файлов
        os.makedirs('data/statistics', exist_ok=True)
    
    def tearDown(self):
        """Очистка после тестирования."""
        # Удаляем тестовые файлы, если они были созданы
        test_files = [
            'data/statistics/stand_visits.png',
            'data/statistics/user_registrations.png',
            'data/statistics/roles_distribution.png',
            'data/statistics/statistics_export.xlsx'
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def test_get_general_statistics(self):
        """Тестирование получения общей статистики."""
        # Вызываем метод get_general_statistics
        result = self.statistics_manager.get_general_statistics()
        
        # Проверяем, что были вызваны нужные методы
        self.db_mock.get_all_users.assert_called_once()
        self.db_mock.get_all_stands.assert_called_once()
        self.db_mock.users.count_documents.assert_called()
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result['total_users'], 2)
        self.assertEqual(result['active_users_today'], 1)
        self.assertEqual(result['new_registrations_today'], 1)
        self.assertEqual(result['total_stand_visits'], 15)
        self.assertEqual(result['total_merch_orders'], 1)
        self.assertEqual(result['total_points_earned'], 150)
        self.assertEqual(result['total_points_spent'], 30)
    
    def test_get_stand_visitors(self):
        """Тестирование получения списка посетителей стенда."""
        # Настраиваем мок для points_transactions.find
        stand_visit_transactions = [self.points_transactions_data[0]]
        cursor_mock = MagicMock()
        cursor_mock.__iter__.return_value = iter(stand_visit_transactions)
        cursor_mock.sort.return_value = cursor_mock
        self.db_mock.points_transactions.find.return_value = cursor_mock
        
        # Вызываем метод get_stand_visitors
        result = self.statistics_manager.get_stand_visitors(self.test_stand_id)
        
        # Проверяем, что был вызван метод find с правильными параметрами
        self.db_mock.points_transactions.find.assert_called_once()
        args, kwargs = self.db_mock.points_transactions.find.call_args
        query = args[0]
        self.assertEqual(query['reason'], 'stand_visit')
        self.assertEqual(query['reference_id'], self.test_stand_id)
        
        # Проверяем, что был вызван метод sort
        cursor_mock.sort.assert_called_once_with('created_at', -1)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(self.test_user_id)
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['user_id'], self.test_user_id)
        self.assertEqual(result[0]['first_name'], 'Иван')
        self.assertEqual(result[0]['last_name'], 'Иванов')
        self.assertEqual(result[0]['company'], 'ООО Рога и Копыта')
    
    def test_get_stand_statistics_specific_stand(self):
        """Тестирование получения статистики по конкретному стенду."""
        # Настраиваем мок для get_stand_visitors
        with patch.object(self.statistics_manager, 'get_stand_visitors') as mock_get_visitors:
            visitors = [
                {
                    'user_id': self.test_user_id,
                    'first_name': 'Иван',
                    'last_name': 'Иванов',
                    'company': 'ООО Рога и Копыта',
                    'visit_time': datetime.datetime(2025, 5, 27, 9, 30, 0)
                }
            ]
            mock_get_visitors.return_value = visitors
            
            # Вызываем метод get_stand_statistics
            result = self.statistics_manager.get_stand_statistics(self.test_stand_id)
            
            # Проверяем, что был вызван метод get_stand
            self.db_mock.get_stand.assert_called_once_with(self.test_stand_id)
            
            # Проверяем, что был вызван метод get_stand_visitors
            mock_get_visitors.assert_called_once_with(self.test_stand_id)
            
            # Проверяем, что метод вернул правильные данные
            self.assertEqual(result['stand_id'], self.test_stand_id)
            self.assertEqual(result['name'], 'Стенд компании А')
            self.assertEqual(result['visits'], 10)
            self.assertEqual(result['visitors'], visitors)
    
    def test_get_stand_statistics_all_stands(self):
        """Тестирование получения статистики по всем стендам."""
        # Вызываем метод get_stand_statistics без указания конкретного стенда
        result = self.statistics_manager.get_stand_statistics()
        
        # Проверяем, что был вызван метод get_all_stands
        self.db_mock.get_all_stands.assert_called_once()
        
        # Проверяем, что был вызван метод count_documents для каждого стенда
        self.db_mock.points_transactions.count_documents.assert_called()
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result['total_stands'], 2)
        self.assertEqual(result['total_visits'], 15)
        self.assertEqual(len(result['stands']), 2)
        self.assertEqual(result['stands'][0]['stand_id'], self.test_stand_id)
        self.assertEqual(result['stands'][0]['name'], 'Стенд компании А')
        self.assertEqual(result['stands'][0]['visits'], 10)
        self.assertEqual(result['stands'][0]['visitors_count'], 1)
    
    def test_get_user_activity_statistics(self):
        """Тестирование получения статистики активности пользователей."""
        # Вызываем метод get_user_activity_statistics
        result = self.statistics_manager.get_user_activity_statistics()
        
        # Проверяем, что был вызван метод get_all_users
        self.db_mock.get_all_users.assert_called_once()
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result['total_users'], 2)
        self.assertEqual(result['roles']['participant'], 1)
        self.assertEqual(result['roles']['hr'], 1)
        self.assertEqual(result['registrations_by_day']['2025-05-25'], 1)
        self.assertEqual(result['registrations_by_day']['2025-05-26'], 1)
        self.assertEqual(result['activity_by_day']['2025-05-27'], 2)
        self.assertEqual(result['companies']['ООО Рога и Копыта'], 1)
        self.assertEqual(result['companies']['ООО Дизайн Про'], 1)
    
    def test_generate_daily_report(self):
        """Тестирование генерации ежедневного отчета."""
        # Настраиваем моки для методов, которые вызываются в generate_daily_report
        with patch.object(self.statistics_manager, 'get_general_statistics') as mock_general_stats, \
             patch.object(self.statistics_manager, 'get_stand_statistics') as mock_stand_stats, \
             patch.object(self.statistics_manager, 'get_user_activity_statistics') as mock_user_stats:
            
            general_stats = {'total_users': 2, 'active_users_today': 1}
            stand_stats = {'total_stands': 2, 'total_visits': 15}
            user_stats = {'total_users': 2, 'roles': {'participant': 1, 'hr': 1}}
            
            mock_general_stats.return_value = general_stats
            mock_stand_stats.return_value = stand_stats
            mock_user_stats.return_value = user_stats
            
            # Вызываем метод generate_daily_report
            result = self.statistics_manager.generate_daily_report()
            
            # Проверяем, что были вызваны нужные методы
            mock_general_stats.assert_called_once()
            mock_stand_stats.assert_called_once()
            mock_user_stats.assert_called_once()
            
            # Проверяем, что был вызван метод update_daily_statistics
            self.db_mock.update_daily_statistics.assert_called_once()
            
            # Проверяем, что метод вернул правильные данные
            self.assertEqual(result['date'], datetime.datetime.utcnow().strftime('%Y-%m-%d'))
            self.assertEqual(result['general_stats'], general_stats)
            self.assertEqual(result['stand_stats'], stand_stats)
            self.assertEqual(result['user_stats'], user_stats)
    
    @patch('matplotlib.pyplot.savefig')
    def test_generate_stand_visits_chart(self, mock_savefig):
        """Тестирование генерации графика посещаемости стендов."""
        # Настраиваем мок для get_stand_statistics
        with patch.object(self.statistics_manager, 'get_stand_statistics') as mock_stand_stats:
            stand_stats = {
                'total_stands': 2,
                'total_visits': 15,
                'stands': [
                    {
                        'stand_id': self.test_stand_id,
                        'name': 'Стенд компании А',
                        'visits': 10
                    },
                    {
                        'stand_id': 'stand_87654321',
                        'name': 'Стенд компании Б',
                        'visits': 5
                    }
                ]
            }
            mock_stand_stats.return_value = stand_stats
            
            # Вызываем метод generate_stand_visits_chart
            file_path = 'data/statistics/test_stand_visits.png'
            result = self.statistics_manager.generate_stand_visits_chart(file_path)
            
            # Проверяем, что был вызван метод get_stand_statistics
            mock_stand_stats.assert_called_once()
            
            # Проверяем, что был вызван метод savefig
            mock_savefig.assert_called_once_with(file_path)
            
            # Проверяем, что метод вернул правильный путь к файлу
            self.assertEqual(result, file_path)
    
    @patch('matplotlib.pyplot.savefig')
    def test_generate_user_registrations_chart(self, mock_savefig):
        """Тестирование генерации графика регистраций пользователей."""
        # Настраиваем мок для get_user_activity_statistics
        with patch.object(self.statistics_manager, 'get_user_activity_statistics') as mock_user_stats:
            user_stats = {
                'total_users': 2,
                'roles': {'participant': 1, 'hr': 1},
                'registrations_by_day': {
                    '2025-05-25': 1,
                    '2025-05-26': 1
                }
            }
            mock_user_stats.return_value = user_stats
            
            # Вызываем метод generate_user_registrations_chart
            file_path = 'data/statistics/test_user_registrations.png'
            result = self.statistics_manager.generate_user_registrations_chart(file_path)
            
            # Проверяем, что был вызван метод get_user_activity_statistics
            mock_user_stats.assert_called_once()
            
            # Проверяем, что был вызван метод savefig
            mock_savefig.assert_called_once_with(file_path)
            
            # Проверяем, что метод вернул правильный путь к файлу
            self.assertEqual(result, file_path)
    
    @patch('matplotlib.pyplot.savefig')
    def test_generate_roles_distribution_chart(self, mock_savefig):
        """Тестирование генерации круговой диаграммы распределения ролей."""
        # Настраиваем мок для get_user_activity_statistics
        with patch.object(self.statistics_manager, 'get_user_activity_statistics') as mock_user_stats:
            user_stats = {
                'total_users': 2,
                'roles': {'participant': 1, 'hr': 1}
            }
            mock_user_stats.return_value = user_stats
            
            # Вызываем метод generate_roles_distribution_chart
            file_path = 'data/statistics/test_roles_distribution.png'
            result = self.statistics_manager.generate_roles_distribution_chart(file_path)
            
            # Проверяем, что был вызван метод get_user_activity_statistics
            mock_user_stats.assert_called_once()
            
            # Проверяем, что был вызван метод savefig
            mock_savefig.assert_called_once_with(file_path)
            
            # Проверяем, что метод вернул правильный путь к файлу
            self.assertEqual(result, file_path)
    
    @patch('pandas.DataFrame.to_excel')
    def test_export_statistics_to_excel(self, mock_to_excel):
        """Тестирование экспорта статистики в Excel-файл."""
        # Настраиваем моки для методов, которые вызываются в export_statistics_to_excel
        with patch.object(self.statistics_manager, 'get_general_statistics') as mock_general_stats, \
             patch.object(self.statistics_manager, 'get_stand_statistics') as mock_stand_stats, \
             patch.object(self.statistics_manager, 'get_user_activity_statistics') as mock_user_stats, \
             patch('pandas.ExcelWriter', autospec=True) as mock_excel_writer, \
             patch('builtins.open', mock_open()) as mock_file:
            
            general_stats = {'total_users': 2, 'active_users_today': 1}
            stand_stats = {
                'total_stands': 2,
                'total_visits': 15,
                'stands': [
                    {
                        'stand_id': self.test_stand_id,
                        'name': 'Стенд компании А',
                        'visits': 10
                    }
                ]
            }
            user_stats = {
                'total_users': 2,
                'roles': {'participant': 1, 'hr': 1},
                'registrations_by_day': {'2025-05-25': 1, '2025-05-26': 1},
                'companies': {'ООО Рога и Копыта': 1, 'ООО Дизайн Про': 1}
            }
            
            mock_general_stats.return_value = general_stats
            mock_stand_stats.return_value = stand_stats
            mock_user_stats.return_value = user_stats
            
            # Настраиваем мок для ExcelWriter как контекстный менеджер
            mock_excel_writer.return_value.__enter__.return_value = mock_excel_writer.return_value
            
            # Вызываем метод export_statistics_to_excel
            file_path = 'data/statistics/test_statistics_export.xlsx'
            result = self.statistics_manager.export_statistics_to_excel(file_path)
            
            # Проверяем, что были вызваны нужные методы
            mock_general_stats.assert_called_once()
            mock_stand_stats.assert_called_once()
            mock_user_stats.assert_called_once()
            
            # Проверяем, что был создан ExcelWriter
            mock_excel_writer.assert_called_once_with(file_path)
            
            # Проверяем, что метод вернул правильный путь к файлу
            self.assertEqual(result, file_path)

if __name__ == '__main__':
    unittest.main()
