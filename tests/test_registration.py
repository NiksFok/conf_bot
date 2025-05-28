#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки регистрации и ролевой системы бота.
Эмулирует взаимодействие пользователя с ботом для проверки корректности работы.
"""

import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch
from telegram import Update, User, Chat, Message, CallbackQuery
from telegram.ext import CallbackContext, ConversationHandler

# Настройка пути для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт основного класса бота
from main import ConferenceBot

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TestRegistrationAndRoles(unittest.TestCase):
    """Тестирование регистрации и ролевой системы бота."""
    
    def setUp(self):
        """Подготовка к тестированию."""
        # Создаем мок для DBConnector
        self.db_patcher = patch('main.DBConnector')
        self.mock_db = self.db_patcher.start()
        
        # Создаем мок для QRGenerator
        self.qr_patcher = patch('main.QRGenerator')
        self.mock_qr = self.qr_patcher.start()
        
        # Настраиваем мок для get_user
        self.mock_db.return_value.get_user.return_value = None
        
        # Настраиваем мок для QRGenerator
        self.mock_qr.return_value.generate_user_qr.return_value = "/tmp/qr_123456789.png"
        
        # Создаем экземпляр бота с моком базы данных
        with patch('main.Updater'), patch('os.path.exists', return_value=True):
            self.bot = ConferenceBot()
        
        # Создаем мок для Update
        self.update = MagicMock(spec=Update)
        self.update.effective_user = MagicMock(spec=User)
        self.update.effective_user.id = 123456789
        self.update.effective_user.username = "test_user"
        self.update.message = MagicMock(spec=Message)
        self.update.message.chat = MagicMock(spec=Chat)
        self.update.message.chat.id = 123456789
        
        # Создаем мок для CallbackContext
        self.context = MagicMock(spec=CallbackContext)
        self.context.user_data = {}
        self.context.bot = MagicMock()
        
        # Создаем мок для CallbackQuery
        self.update.callback_query = MagicMock(spec=CallbackQuery)
        self.update.callback_query.data = "register"
        self.update.callback_query.message = MagicMock(spec=Message)
        self.update.callback_query.message.chat_id = 123456789
    
    def tearDown(self):
        """Завершение тестирования."""
        self.db_patcher.stop()
        self.qr_patcher.stop()
    
    def test_start_command_new_user(self):
        """Тестирование команды /start для нового пользователя."""
        # Вызываем метод start
        self.bot.start(self.update, self.context)
        
        # Проверяем, что был вызван метод get_user
        self.bot.db.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что было отправлено сообщение с предложением регистрации
        self.update.message.reply_text.assert_called_once()
        args, kwargs = self.update.message.reply_text.call_args
        self.assertIn("зарегистрироваться", args[0].lower())
    
    def test_registration_start(self):
        """Тестирование начала процесса регистрации."""
        # Вызываем метод registration_start
        result = self.bot.registration_start(self.update, self.context)
        
        # Проверяем, что был вызван метод get_user
        self.bot.db.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что было отправлено сообщение с запросом имени и фамилии
        self.update.callback_query.edit_message_text.assert_called_once()
        args, kwargs = self.update.callback_query.edit_message_text.call_args
        self.assertIn("имя и фамилию", args[0].lower())
        
        # Проверяем, что возвращено правильное состояние
        self.assertEqual(result, 0)  # REGISTRATION = 0
    
    def test_registration_name(self):
        """Тестирование ввода имени и фамилии."""
        # Устанавливаем текст сообщения
        self.update.message.text = "Иван Иванов"
        
        # Вызываем метод registration_name
        result = self.bot.registration_name(self.update, self.context)
        
        # Проверяем, что имя и фамилия сохранены в контексте
        self.assertEqual(self.context.user_data['first_name'], "Иван")
        self.assertEqual(self.context.user_data['last_name'], "Иванов")
        
        # Проверяем, что было отправлено сообщение с запросом должности
        self.update.message.reply_text.assert_called_once()
        args, kwargs = self.update.message.reply_text.call_args
        self.assertIn("должность", args[0].lower())
        
        # Проверяем, что возвращено правильное состояние
        self.assertEqual(result, 1)  # OCCUPATION = 1
    
    def test_registration_occupation(self):
        """Тестирование ввода должности."""
        # Устанавливаем текст сообщения
        self.update.message.text = "Разработчик"
        
        # Вызываем метод registration_occupation
        result = self.bot.registration_occupation(self.update, self.context)
        
        # Проверяем, что должность сохранена в контексте
        self.assertEqual(self.context.user_data['occupation'], "Разработчик")
        
        # Проверяем, что было отправлено сообщение с запросом уровня
        self.update.message.reply_text.assert_called_once()
        args, kwargs = self.update.message.reply_text.call_args
        self.assertIn("уровень", args[0].lower())
        
        # Проверяем, что возвращено правильное состояние
        self.assertEqual(result, 2)  # LEVEL = 2
    
    def test_registration_level(self):
        """Тестирование выбора уровня."""
        # Устанавливаем данные callback_query
        self.update.callback_query.data = "level_middle"
        
        # Вызываем метод registration_level
        result = self.bot.registration_level(self.update, self.context)
        
        # Проверяем, что уровень сохранен в контексте
        self.assertEqual(self.context.user_data['level'], "middle")
        
        # Проверяем, что было отправлено сообщение с запросом компании
        self.update.callback_query.edit_message_text.assert_called_once()
        args, kwargs = self.update.callback_query.edit_message_text.call_args
        self.assertIn("компани", args[0].lower())
        
        # Проверяем, что возвращено правильное состояние
        self.assertEqual(result, 3)  # COMPANY = 3
    
    def test_registration_company(self):
        """Тестирование ввода компании."""
        # Устанавливаем текст сообщения
        self.update.message.text = "ООО Рога и Копыта"
        
        # Вызываем метод registration_company
        result = self.bot.registration_company(self.update, self.context)
        
        # Проверяем, что компания сохранена в контексте
        self.assertEqual(self.context.user_data['company'], "ООО Рога и Копыта")
        
        # Проверяем, что было отправлено сообщение с запросом согласия
        self.update.message.reply_text.assert_called_once()
        args, kwargs = self.update.message.reply_text.call_args
        self.assertIn("соглас", args[0].lower())
        
        # Проверяем, что возвращено правильное состояние
        self.assertEqual(result, 4)  # CONSENT = 4
    
    def test_registration_consent_yes(self):
        """Тестирование согласия на обработку данных."""
        # Устанавливаем данные callback_query
        self.update.callback_query.data = "consent_yes"
        
        # Настраиваем контекст с данными пользователя
        self.context.user_data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'occupation': 'Разработчик',
            'level': 'middle',
            'company': 'ООО Рога и Копыта'
        }
        
        # Настраиваем мок для create_user
        self.bot.db.create_user.return_value = "user_id"
        
        # Мокаем метод _show_guest_menu
        self.bot._show_guest_menu = MagicMock()
        
        # Патчим метод send_photo, чтобы избежать ошибки с отсутствующим файлом
        with patch.object(self.context.bot, 'send_photo'):
            # Вызываем метод registration_consent
            result = self.bot.registration_consent(self.update, self.context)
        
        # Проверяем, что был вызван метод create_user с правильными данными
        self.bot.db.create_user.assert_called_once()
        args, kwargs = self.bot.db.create_user.call_args
        user_data = args[0]
        self.assertEqual(user_data['first_name'], 'Иван')
        self.assertEqual(user_data['last_name'], 'Иванов')
        self.assertEqual(user_data['occupation'], 'Разработчик')
        self.assertEqual(user_data['level'], 'middle')
        self.assertEqual(user_data['company'], 'ООО Рога и Копыта')
        self.assertEqual(user_data['role'], 'guest')
        
        # Проверяем, что было отправлено сообщение об успешной регистрации
        # Проверяем только первый вызов, так как второй может быть связан с ошибкой QR
        args, kwargs = self.update.callback_query.edit_message_text.call_args_list[0]
        self.assertIn("успешно", args[0].lower())
        
        # Проверяем, что был вызван метод _show_guest_menu
        self.bot._show_guest_menu.assert_called_once()
        
        # Проверяем, что возвращено правильное состояние
        self.assertEqual(result, ConversationHandler.END)
    
    def test_registration_consent_no(self):
        """Тестирование отказа от обработки данных."""
        # Устанавливаем данные callback_query
        self.update.callback_query.data = "consent_no"
        
        # Вызываем метод registration_consent
        result = self.bot.registration_consent(self.update, self.context)
        
        # Проверяем, что не был вызван метод create_user
        self.bot.db.create_user.assert_not_called()
        
        # Проверяем, что было отправлено сообщение о невозможности регистрации
        self.update.callback_query.edit_message_text.assert_called_once()
        args, kwargs = self.update.callback_query.edit_message_text.call_args
        self.assertIn("невозможна", args[0].lower())
        
        # Проверяем, что возвращено правильное состояние
        self.assertEqual(result, ConversationHandler.END)
    
    def test_start_command_existing_user(self):
        """Тестирование команды /start для существующего пользователя."""
        # Настраиваем мок для get_user, чтобы он возвращал существующего пользователя
        user_data = {
            'user_id': 123456789,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'role': 'guest',
            'points': 10
        }
        self.bot.db.get_user.return_value = user_data
        
        # Мокаем метод _show_role_menu
        self.bot._show_role_menu = MagicMock()
        
        # Вызываем метод start
        self.bot.start(self.update, self.context)
        
        # Проверяем, что был вызван метод get_user
        self.bot.db.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что был вызван метод _show_role_menu с правильными параметрами
        self.bot._show_role_menu.assert_called_once_with(self.update, self.context, 'guest')
    
    def test_handle_menu_callback_guest(self):
        """Тестирование обработки нажатий на кнопки меню для гостя."""
        # Настраиваем мок для get_user, чтобы он возвращал существующего пользователя
        user_data = {
            'user_id': 123456789,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'role': 'guest',
            'points': 10,
            'is_blocked': False
        }
        self.bot.db.get_user.return_value = user_data
        
        # Устанавливаем данные callback_query
        self.update.callback_query.data = "view_points"
        
        # Мокаем методы для показа различных меню
        self.bot._show_points_balance = MagicMock()
        
        # Вызываем метод handle_menu_callback
        self.bot.handle_menu_callback(self.update, self.context)
        
        # Проверяем, что был вызван метод get_user
        self.bot.db.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что был вызван метод _show_points_balance
        self.bot._show_points_balance.assert_called_once_with(self.update, self.context)
    
    def test_handle_menu_callback_blocked_user(self):
        """Тестирование обработки нажатий на кнопки меню для заблокированного пользователя."""
        # Настраиваем мок для get_user, чтобы он возвращал заблокированного пользователя
        user_data = {
            'user_id': 123456789,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'role': 'guest',
            'points': 10,
            'is_blocked': True
        }
        self.bot.db.get_user.return_value = user_data
        
        # Устанавливаем данные callback_query
        self.update.callback_query.data = "view_points"
        
        # Вызываем метод handle_menu_callback
        self.bot.handle_menu_callback(self.update, self.context)
        
        # Проверяем, что был вызван метод get_user
        self.bot.db.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что было отправлено сообщение о блокировке
        self.update.callback_query.edit_message_text.assert_called_once()
        args, kwargs = self.update.callback_query.edit_message_text.call_args
        self.assertIn("заблокирован", args[0].lower())

if __name__ == '__main__':
    unittest.main()
