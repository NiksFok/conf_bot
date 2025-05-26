#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Основной модуль Telegram-бота для конференции.
Обрабатывает входящие сообщения и маршрутизирует их к соответствующим обработчикам.
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, CallbackQueryHandler,
    Filters, CallbackContext, ConversationHandler
)

# Импорт модулей бота
from modules.role_management import RoleManager
from modules.merch_module import MerchManager
from modules.points_system import PointsSystem
from modules.candidate_management import CandidateManager
from modules.statistics_analytics import StatisticsManager
from modules.admin_tools import AdminTools
from modules.subscription_feature import SubscriptionManager
from modules.broadcaster import Broadcaster
from utils.qr_generator import QRGenerator
from utils.db_connector import DBConnector

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(
    REGISTRATION, OCCUPATION, LEVEL, COMPANY, CONSENT,
    ADMIN_MENU, MERCH_MENU, STAND_MENU, HR_MENU, GUEST_MENU
) = range(10)

class ConferenceBot:
    """Основной класс Telegram-бота для конференции."""
    
    def __init__(self):
        """Инициализация бота и подключение к базе данных."""
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.admin_code = os.getenv("ADMIN_CODE")
        
        # Инициализация подключения к базе данных
        self.db = DBConnector()
        
        # Инициализация менеджеров
        self.role_manager = RoleManager(self.db)
        self.merch_manager = MerchManager(self.db)
        self.points_system = PointsSystem(self.db)
        self.candidate_manager = CandidateManager(self.db)
        self.statistics_manager = StatisticsManager(self.db)
        self.admin_tools = AdminTools(self.db, self.admin_code)
        self.subscription_manager = SubscriptionManager(self.db)
        self.broadcaster = Broadcaster(self.db)
        self.qr_generator = QRGenerator()
        
        # Создание экземпляра Updater
        self.updater = Updater(self.token)
        self.dispatcher = self.updater.dispatcher
        
        # Регистрация обработчиков
        self._register_handlers()
        
        logger.info("Бот инициализирован")
    
    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений."""
        # Обработчики команд
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("help", self.help_command))
        self.dispatcher.add_handler(CommandHandler("admin", self.admin_command))
        
        # Обработчик регистрации
        registration_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.registration_start, pattern='^register$')],
            states={
                REGISTRATION: [MessageHandler(Filters.text & ~Filters.command, self.registration_name)],
                OCCUPATION: [MessageHandler(Filters.text & ~Filters.command, self.registration_occupation)],
                LEVEL: [MessageHandler(Filters.text & ~Filters.command, self.registration_level)],
                COMPANY: [MessageHandler(Filters.text & ~Filters.command, self.registration_company)],
                CONSENT: [CallbackQueryHandler(self.registration_consent)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_registration)]
        )
        self.dispatcher.add_handler(registration_handler)
        
        # Обработчики меню для разных ролей
        self.dispatcher.add_handler(CallbackQueryHandler(self.handle_menu_callback))
        
        # Обработчик сканирования QR-кодов
        self.dispatcher.add_handler(MessageHandler(Filters.photo, self.handle_photo))
        
        # Обработчик неизвестных команд
        self.dispatcher.add_handler(MessageHandler(Filters.command, self.unknown_command))
        
        # Обработчик текстовых сообщений
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        
        # Обработчик ошибок
        self.dispatcher.add_error_handler(self.error_handler)
    
    def start(self, update: Update, context: CallbackContext):
        """Обработчик команды /start."""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if user:
            # Пользователь уже зарегистрирован
            role = user.get('role', 'guest')
            self._show_role_menu(update, context, role)
        else:
            # Новый пользователь, предлагаем регистрацию
            keyboard = [
                [InlineKeyboardButton("Зарегистрироваться", callback_data="register")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                "Добро пожаловать на конференцию! Для использования бота необходимо зарегистрироваться.",
                reply_markup=reply_markup
            )
    
    def help_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /help."""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            update.message.reply_text(
                "Для начала работы с ботом используйте команду /start и пройдите регистрацию."
            )
            return
        
        role = user.get('role', 'guest')
        help_text = self._get_help_text(role)
        
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    def admin_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /admin."""
        update.message.reply_text(
            "Введите код администратора для доступа к панели управления:"
        )
        return ADMIN_MENU
    
    def registration_start(self, update: Update, context: CallbackContext):
        """Начало процесса регистрации."""
        query = update.callback_query
        query.answer()
        
        query.edit_message_text(
            "Пожалуйста, введите ваше имя и фамилию:"
        )
        return REGISTRATION
    
    def registration_name(self, update: Update, context: CallbackContext):
        """Обработка ввода имени и фамилии."""
        full_name = update.message.text.strip()
        if len(full_name.split()) < 2:
            update.message.reply_text(
                "Пожалуйста, введите и имя, и фамилию, разделенные пробелом:"
            )
            return REGISTRATION
        
        # Сохраняем имя и фамилию в контексте
        name_parts = full_name.split(maxsplit=1)
        context.user_data['first_name'] = name_parts[0]
        context.user_data['last_name'] = name_parts[1]
        
        update.message.reply_text(
            "Спасибо! Теперь укажите вашу должность:"
        )
        return OCCUPATION
    
    def registration_occupation(self, update: Update, context: CallbackContext):
        """Обработка ввода должности."""
        occupation = update.message.text.strip()
        context.user_data['occupation'] = occupation
        
        # Предлагаем выбрать уровень
        keyboard = [
            [InlineKeyboardButton("Junior", callback_data="level_junior")],
            [InlineKeyboardButton("Middle", callback_data="level_middle")],
            [InlineKeyboardButton("Senior", callback_data="level_senior")],
            [InlineKeyboardButton("Lead", callback_data="level_lead")],
            [InlineKeyboardButton("Другое", callback_data="level_other")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "Укажите ваш уровень:",
            reply_markup=reply_markup
        )
        return LEVEL
    
    def registration_level(self, update: Update, context: CallbackContext):
        """Обработка выбора уровня."""
        query = update.callback_query
        query.answer()
        
        level = query.data.replace("level_", "")
        context.user_data['level'] = level
        
        query.edit_message_text(
            "Укажите название вашей компании:"
        )
        return COMPANY
    
    def registration_company(self, update: Update, context: CallbackContext):
        """Обработка ввода компании."""
        company = update.message.text.strip()
        context.user_data['company'] = company
        
        # Запрашиваем согласие на обработку данных
        keyboard = [
            [InlineKeyboardButton("Согласен", callback_data="consent_yes")],
            [InlineKeyboardButton("Не согласен", callback_data="consent_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "Для завершения регистрации необходимо ваше согласие на обработку персональных данных.",
            reply_markup=reply_markup
        )
        return CONSENT
    
    def registration_consent(self, update: Update, context: CallbackContext):
        """Обработка согласия на обработку данных."""
        query = update.callback_query
        query.answer()
        
        if query.data == "consent_no":
            query.edit_message_text(
                "К сожалению, без согласия на обработку данных регистрация невозможна. "
                "Вы можете начать регистрацию заново с помощью команды /start."
            )
            return ConversationHandler.END
        
        # Сохраняем пользователя в базе данных
        user_data = {
            'user_id': update.effective_user.id,
            'first_name': context.user_data.get('first_name'),
            'last_name': context.user_data.get('last_name'),
            'username': update.effective_user.username,
            'occupation': context.user_data.get('occupation'),
            'level': context.user_data.get('level'),
            'company': context.user_data.get('company'),
            'role': 'guest',  # По умолчанию роль "гость"
            'points': 0,
            'consent': True,
            'is_blocked': False,
            'is_candidate': False
        }
        
        self.db.create_user(user_data)
        
        # Генерируем QR-код для пользователя
        qr_path = self.qr_generator.generate_user_qr(update.effective_user.id)
        
        query.edit_message_text(
            f"Регистрация успешно завершена! Ваша роль: Гость\n\n"
            f"Вам начислено 0 баллов. Вы можете получать баллы за посещение стендов и участие в активностях.\n\n"
            f"Используйте меню для навигации по функциям бота."
        )
        
        # Отправляем QR-код пользователю
        with open(qr_path, 'rb') as qr_file:
            context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=qr_file,
                caption="Ваш персональный QR-код. Покажите его стендистам для получения баллов."
            )
        
        # Показываем меню гостя
        self._show_guest_menu(update, context)
        
        return ConversationHandler.END
    
    def cancel_registration(self, update: Update, context: CallbackContext):
        """Отмена процесса регистрации."""
        update.message.reply_text(
            "Регистрация отменена. Вы можете начать заново с помощью команды /start."
        )
        return ConversationHandler.END
    
    def handle_menu_callback(self, update: Update, context: CallbackContext):
        """Обработка нажатий на кнопки меню."""
        query = update.callback_query
        query.answer()
        
        callback_data = query.data
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            query.edit_message_text(
                "Для начала работы с ботом необходимо зарегистрироваться. Используйте команду /start."
            )
            return
        
        # Обработка различных callback_data в зависимости от роли пользователя
        role = user.get('role', 'guest')
        
        # Общие действия для всех ролей
        if callback_data == "main_menu":
            self._show_role_menu(update, context, role)
            return
        
        # Действия для гостей
        if role == 'guest':
            if callback_data == "view_merch":
                self._show_merch_catalog(update, context)
            elif callback_data == "view_points":
                self._show_points_balance(update, context)
            elif callback_data == "view_stands":
                self._show_stands_list(update, context)
            elif callback_data.startswith("order_merch_"):
                merch_id = callback_data.replace("order_merch_", "")
                self._order_merch(update, context, merch_id)
        
        # Действия для стендистов
        elif role == 'standist':
            if callback_data == "scan_qr":
                query.edit_message_text(
                    "Отправьте фотографию QR-кода посетителя для начисления баллов."
                )
            elif callback_data == "view_stand_stats":
                self._show_stand_statistics(update, context)
        
        # Действия для HR
        elif role == 'hr':
            if callback_data == "mark_candidate":
                query.edit_message_text(
                    "Отправьте фотографию QR-кода кандидата для отметки."
                )
            elif callback_data == "view_candidates":
                self._show_candidates_list(update, context)
            elif callback_data.startswith("add_note_"):
                candidate_id = callback_data.replace("add_note_", "")
                context.user_data['candidate_id'] = candidate_id
                query.edit_message_text(
                    "Введите заметку о кандидате:"
                )
                return HR_MENU
        
        # Действия для администраторов
        elif role == 'admin':
            if callback_data == "manage_users":
                self._show_users_list(update, context)
            elif callback_data == "manage_stands":
                self._show_stands_management(update, context)
            elif callback_data == "manage_merch":
                self._show_merch_management(update, context)
            elif callback_data == "view_statistics":
                self._show_admin_statistics(update, context)
            elif callback_data == "send_broadcast":
                query.edit_message_text(
                    "Введите текст сообщения для рассылки всем пользователям:"
                )
                return ADMIN_MENU
    
    def handle_photo(self, update: Update, context: CallbackContext):
        """Обработка фотографий (для сканирования QR-кодов)."""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            update.message.reply_text(
                "Для начала работы с ботом необходимо зарегистрироваться. Используйте команду /start."
            )
            return
        
        role = user.get('role', 'guest')
        
        # Сохраняем фото
        photo_file = update.message.photo[-1].get_file()
        photo_path = f"data/qr_scans/{user_id}_{photo_file.file_id}.jpg"
        photo_file.download(photo_path)
        
        # Пытаемся распознать QR-код
        qr_data = self.qr_generator.decode_qr(photo_path)
        
        if not qr_data:
            update.message.reply_text(
                "QR-код не распознан. Пожалуйста, попробуйте еще раз с более четким изображением."
            )
            return
        
        # Обрабатываем данные QR-кода в зависимости от роли пользователя
        if role == 'standist':
            # Стендист сканирует QR-код посетителя для начисления баллов
            try:
                scanned_user_id = int(qr_data)
                scanned_user = self.db.get_user(scanned_user_id)
                
                if not scanned_user:
                    update.message.reply_text(
                        "Пользователь не найден. QR-код может быть недействительным."
                    )
                    return
                
                # Получаем информацию о стенде
                stand = self.db.get_stand_by_owner(user_id)
                
                if not stand:
                    update.message.reply_text(
                        "У вас нет зарегистрированного стенда. Обратитесь к администратору."
                    )
                    return
                
                # Проверяем, не посещал ли пользователь этот стенд ранее
                if self.points_system.check_stand_visit(scanned_user_id, stand['stand_id']):
                    update.message.reply_text(
                        f"Пользователь {scanned_user['first_name']} {scanned_user['last_name']} "
                        f"уже посещал ваш стенд ранее."
                    )
                    return
                
                # Начисляем баллы за посещение стенда
                points = 10  # Стандартное количество баллов за посещение стенда
                self.points_system.add_points(
                    scanned_user_id, 
                    points, 
                    "stand_visit", 
                    stand['stand_id']
                )
                
                # Увеличиваем счетчик посещений стенда
                self.db.increment_stand_visits(stand['stand_id'])
                
                update.message.reply_text(
                    f"Пользователю {scanned_user['first_name']} {scanned_user['last_name']} "
                    f"начислено {points} баллов за посещение вашего стенда."
                )
                
                # Отправляем уведомление пользователю
                context.bot.send_message(
                    chat_id=scanned_user_id,
                    text=f"Вам начислено {points} баллов за посещение стенда \"{stand['name']}\"."
                )
                
            except ValueError:
                update.message.reply_text(
                    "Некорректный QR-код. Пожалуйста, убедитесь, что сканируете QR-код посетителя."
                )
        
        elif role == 'hr':
            # HR сканирует QR-код для отметки кандидата
            try:
                scanned_user_id = int(qr_data)
                scanned_user = self.db.get_user(scanned_user_id)
                
                if not scanned_user:
                    update.message.reply_text(
                        "Пользователь не найден. QR-код может быть недействительным."
                    )
                    return
                
                # Отмечаем пользователя как кандидата
                self.candidate_manager.mark_as_candidate(scanned_user_id, user_id)
                
                update.message.reply_text(
                    f"Пользователь {scanned_user['first_name']} {scanned_user['last_name']} "
                    f"отмечен как потенциальный кандидат."
                )
                
                # Предлагаем добавить заметку о кандидате
                keyboard = [
                    [InlineKeyboardButton("Добавить заметку", callback_data=f"add_note_{scanned_user_id}")],
                    [InlineKeyboardButton("Вернуться в меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                update.message.reply_text(
                    "Хотите добавить заметку о кандидате?",
                    reply_markup=reply_markup
                )
                
            except ValueError:
                update.message.reply_text(
                    "Некорректный QR-код. Пожалуйста, убедитесь, что сканируете QR-код посетителя."
                )
        
        else:
            # Для других ролей сканирование QR-кодов может иметь другую логику
            update.message.reply_text(
                "Функция сканирования QR-кодов недоступна для вашей роли."
            )
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Обработка текстовых сообщений."""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            update.message.reply_text(
                "Для начала работы с ботом необходимо зарегистрироваться. Используйте команду /start."
            )
            return
        
        # Обработка сообщений в зависимости от текущего состояния и роли пользователя
        if context.user_data.get('state') == 'waiting_for_broadcast_text' and user.get('role') == 'admin':
            # Администратор вводит текст для рассылки
            broadcast_text = update.message.text
            self.broadcaster.send_broadcast(context.bot, broadcast_text)
            
            update.message.reply_text(
                "Сообщение отправлено всем пользователям."
            )
            
            # Сбрасываем состояние
            context.user_data.pop('state', None)
            
            # Возвращаем меню администратора
            self._show_admin_menu(update, context)
            
        elif context.user_data.get('state') == 'waiting_for_candidate_note' and user.get('role') == 'hr':
            # HR вводит заметку о кандидате
            note_text = update.message.text
            candidate_id = context.user_data.get('candidate_id')
            
            if candidate_id:
                self.candidate_manager.add_note(candidate_id, user_id, note_text)
                
                update.message.reply_text(
                    "Заметка о кандидате добавлена."
                )
                
                # Сбрасываем состояние
                context.user_data.pop('state', None)
                context.user_data.pop('candidate_id', None)
                
                # Возвращаем меню HR
                self._show_hr_menu(update, context)
            else:
                update.message.reply_text(
                    "Ошибка: не указан ID кандидата. Пожалуйста, начните процесс заново."
                )
        
        else:
            # Обычное сообщение, показываем меню в зависимости от роли
            role = user.get('role', 'guest')
            self._show_role_menu(update, context, role)
    
    def unknown_command(self, update: Update, context: CallbackContext):
        """Обработка неизвестных команд."""
        update.message.reply_text(
            "Извините, я не знаю такой команды. Используйте /help для получения списка доступных команд."
        )
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработчик ошибок."""
        logger.error(f"Ошибка: {context.error}")
        
        # Логируем ошибку в базу данных
        error_data = {
            'timestamp': context.error,
            'user_id': update.effective_user.id if update else None,
            'error_type': type(context.error).__name__,
            'error_message': str(context.error),
            'resolved': False
        }
        self.db.log_error(error_data)
        
        # Отправляем сообщение пользователю
        if update:
            update.effective_message.reply_text(
                "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
            )
    
    def _show_role_menu(self, update: Update, context: CallbackContext, role: str):
        """Показывает меню в зависимости от роли пользователя."""
        if role == 'guest':
            self._show_guest_menu(update, context)
        elif role == 'standist':
            self._show_standist_menu(update, context)
        elif role == 'hr':
            self._show_hr_menu(update, context)
        elif role == 'admin':
            self._show_admin_menu(update, context)
    
    def _show_guest_menu(self, update: Update, context: CallbackContext):
        """Показывает меню гостя."""
        keyboard = [
            [InlineKeyboardButton("Каталог мерча", callback_data="view_merch")],
            [InlineKeyboardButton("Мои баллы", callback_data="view_points")],
            [InlineKeyboardButton("Список стендов", callback_data="view_stands")],
            [InlineKeyboardButton("Подписки на уведомления", callback_data="manage_subscriptions")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                "Меню гостя. Выберите действие:",
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                "Меню гостя. Выберите действие:",
                reply_markup=reply_markup
            )
    
    def _show_standist_menu(self, update: Update, context: CallbackContext):
        """Показывает меню стендиста."""
        keyboard = [
            [InlineKeyboardButton("Сканировать QR-код посетителя", callback_data="scan_qr")],
            [InlineKeyboardButton("Статистика посещений", callback_data="view_stand_stats")],
            [InlineKeyboardButton("Мой стенд", callback_data="view_my_stand")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                "Меню стендиста. Выберите действие:",
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                "Меню стендиста. Выберите действие:",
                reply_markup=reply_markup
            )
    
    def _show_hr_menu(self, update: Update, context: CallbackContext):
        """Показывает меню HR."""
        keyboard = [
            [InlineKeyboardButton("Отметить кандидата", callback_data="mark_candidate")],
            [InlineKeyboardButton("Список кандидатов", callback_data="view_candidates")],
            [InlineKeyboardButton("Экспорт данных", callback_data="export_candidates")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                "Меню HR. Выберите действие:",
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                "Меню HR. Выберите действие:",
                reply_markup=reply_markup
            )
    
    def _show_admin_menu(self, update: Update, context: CallbackContext):
        """Показывает меню администратора."""
        keyboard = [
            [InlineKeyboardButton("Управление пользователями", callback_data="manage_users")],
            [InlineKeyboardButton("Управление стендами", callback_data="manage_stands")],
            [InlineKeyboardButton("Управление мерчем", callback_data="manage_merch")],
            [InlineKeyboardButton("Статистика", callback_data="view_statistics")],
            [InlineKeyboardButton("Рассылка сообщений", callback_data="send_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                "Меню администратора. Выберите действие:",
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                "Меню администратора. Выберите действие:",
                reply_markup=reply_markup
            )
    
    def _show_merch_catalog(self, update: Update, context: CallbackContext):
        """Показывает каталог мерча."""
        query = update.callback_query
        
        # Получаем список мерча из базы данных
        merch_items = self.merch_manager.get_all_merch()
        
        if not merch_items:
            query.edit_message_text(
                "Каталог мерча пуст.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
            )
            return
        
        # Формируем сообщение с мерчем
        message_text = "Каталог мерча:\n\n"
        keyboard = []
        
        for item in merch_items:
            message_text += f"🎁 *{item['name']}*\n"
            message_text += f"Описание: {item['description']}\n"
            message_text += f"Стоимость: {item['points_cost']} баллов\n"
            message_text += f"Осталось: {item['quantity_left']} шт.\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"Заказать {item['name']} ({item['points_cost']} баллов)",
                callback_data=f"order_merch_{item['merch_id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("Назад", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _show_points_balance(self, update: Update, context: CallbackContext):
        """Показывает баланс баллов пользователя."""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Получаем информацию о пользователе
        user = self.db.get_user(user_id)
        points = user.get('points', 0)
        
        # Получаем историю транзакций
        transactions = self.points_system.get_user_transactions(user_id)
        
        message_text = f"Ваш текущий баланс: *{points} баллов*\n\n"
        
        if transactions:
            message_text += "История транзакций:\n\n"
            for tx in transactions[:5]:  # Показываем только последние 5 транзакций
                if tx['type'] == 'earn':
                    message_text += f"➕ Получено {tx['amount']} баллов - {tx['reason']}\n"
                else:
                    message_text += f"➖ Потрачено {tx['amount']} баллов - {tx['reason']}\n"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _show_stands_list(self, update: Update, context: CallbackContext):
        """Показывает список стендов."""
        query = update.callback_query
        
        # Получаем список стендов из базы данных
        stands = self.db.get_all_stands()
        
        if not stands:
            query.edit_message_text(
                "Список стендов пуст.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
            )
            return
        
        # Формируем сообщение со стендами
        message_text = "Список стендов на конференции:\n\n"
        
        for stand in stands:
            message_text += f"🏢 *{stand['name']}*\n"
            message_text += f"Описание: {stand['description']}\n"
            message_text += f"Расположение: {stand['location']}\n"
            message_text += f"Посещений: {stand['visits']}\n\n"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _order_merch(self, update: Update, context: CallbackContext, merch_id: str):
        """Обрабатывает заказ мерча."""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Получаем информацию о мерче
        merch = self.merch_manager.get_merch(merch_id)
        
        if not merch:
            query.edit_message_text(
                "Товар не найден.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="view_merch")]])
            )
            return
        
        # Проверяем наличие товара
        if merch['quantity_left'] <= 0:
            query.edit_message_text(
                f"К сожалению, товар \"{merch['name']}\" закончился.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="view_merch")]])
            )
            return
        
        # Получаем информацию о пользователе
        user = self.db.get_user(user_id)
        points = user.get('points', 0)
        
        # Проверяем достаточно ли баллов
        if points < merch['points_cost']:
            query.edit_message_text(
                f"У вас недостаточно баллов для заказа \"{merch['name']}\".\n"
                f"Необходимо: {merch['points_cost']} баллов\n"
                f"У вас: {points} баллов",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="view_merch")]])
            )
            return
        
        # Создаем заказ
        order_result = self.merch_manager.create_order(user_id, merch_id)
        
        if order_result:
            # Списываем баллы
            self.points_system.subtract_points(
                user_id,
                merch['points_cost'],
                "merch_order",
                merch_id
            )
            
            query.edit_message_text(
                f"Вы успешно заказали \"{merch['name']}\"!\n"
                f"С вашего счета списано {merch['points_cost']} баллов.\n"
                f"Вы можете получить заказ на стойке выдачи мерча.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
            )
        else:
            query.edit_message_text(
                "Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="view_merch")]])
            )
    
    def _show_stand_statistics(self, update: Update, context: CallbackContext):
        """Показывает статистику посещений стенда."""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Получаем информацию о стенде
        stand = self.db.get_stand_by_owner(user_id)
        
        if not stand:
            query.edit_message_text(
                "У вас нет зарегистрированного стенда. Обратитесь к администратору.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
            )
            return
        
        # Получаем статистику посещений
        visits = stand.get('visits', 0)
        
        # Получаем последних посетителей
        visitors = self.statistics_manager.get_stand_visitors(stand['stand_id'])
        
        message_text = f"Статистика стенда \"{stand['name']}\":\n\n"
        message_text += f"Всего посещений: {visits}\n\n"
        
        if visitors:
            message_text += "Последние посетители:\n"
            for visitor in visitors[:5]:  # Показываем только последних 5 посетителей
                user = self.db.get_user(visitor['user_id'])
                if user:
                    message_text += f"- {user['first_name']} {user['last_name']} ({user['company']})\n"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup
        )
    
    def _show_candidates_list(self, update: Update, context: CallbackContext):
        """Показывает список кандидатов для HR."""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Получаем список кандидатов, отмеченных этим HR
        candidates = self.candidate_manager.get_hr_candidates(user_id)
        
        if not candidates:
            query.edit_message_text(
                "У вас пока нет отмеченных кандидатов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
            )
            return
        
        # Формируем сообщение с кандидатами
        message_text = "Ваши отмеченные кандидаты:\n\n"
        keyboard = []
        
        for candidate in candidates:
            user = self.db.get_user(candidate['candidate_id'])
            if user:
                message_text += f"👤 *{user['first_name']} {user['last_name']}*\n"
                message_text += f"Должность: {user['occupation']}\n"
                message_text += f"Уровень: {user['level']}\n"
                message_text += f"Компания: {user['company']}\n"
                
                # Добавляем заметки, если есть
                notes = self.candidate_manager.get_candidate_notes(candidate['candidate_id'], user_id)
                if notes:
                    message_text += "Заметки:\n"
                    for note in notes:
                        message_text += f"- {note['text']}\n"
                
                message_text += "\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"Добавить заметку о {user['first_name']} {user['last_name']}",
                    callback_data=f"add_note_{candidate['candidate_id']}"
                )])
        
        keyboard.append([InlineKeyboardButton("Назад", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _show_users_list(self, update: Update, context: CallbackContext):
        """Показывает список пользователей для администратора."""
        query = update.callback_query
        
        # Получаем список пользователей
        users = self.db.get_all_users()
        
        if not users:
            query.edit_message_text(
                "Список пользователей пуст.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
            )
            return
        
        # Формируем сообщение с пользователями
        message_text = "Список пользователей:\n\n"
        
        for user in users[:10]:  # Показываем только первых 10 пользователей
            message_text += f"👤 *{user['first_name']} {user['last_name']}*\n"
            message_text += f"Роль: {user['role']}\n"
            message_text += f"Баллы: {user['points']}\n\n"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _show_stands_management(self, update: Update, context: CallbackContext):
        """Показывает управление стендами для администратора."""
        query = update.callback_query
        
        # Получаем список стендов
        stands = self.db.get_all_stands()
        
        # Формируем сообщение со стендами
        message_text = "Управление стендами:\n\n"
        
        if stands:
            for stand in stands:
                message_text += f"🏢 *{stand['name']}*\n"
                message_text += f"Расположение: {stand['location']}\n"
                message_text += f"Посещений: {stand['visits']}\n\n"
        else:
            message_text += "Список стендов пуст.\n\n"
        
        keyboard = [
            [InlineKeyboardButton("Добавить стенд", callback_data="add_stand")],
            [InlineKeyboardButton("Назад", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _show_merch_management(self, update: Update, context: CallbackContext):
        """Показывает управление мерчем для администратора."""
        query = update.callback_query
        
        # Получаем список мерча
        merch_items = self.merch_manager.get_all_merch()
        
        # Формируем сообщение с мерчем
        message_text = "Управление мерчем:\n\n"
        
        if merch_items:
            for item in merch_items:
                message_text += f"🎁 *{item['name']}*\n"
                message_text += f"Стоимость: {item['points_cost']} баллов\n"
                message_text += f"Осталось: {item['quantity_left']} / {item['quantity_total']} шт.\n\n"
        else:
            message_text += "Каталог мерча пуст.\n\n"
        
        keyboard = [
            [InlineKeyboardButton("Добавить мерч", callback_data="add_merch")],
            [InlineKeyboardButton("Назад", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _show_admin_statistics(self, update: Update, context: CallbackContext):
        """Показывает статистику для администратора."""
        query = update.callback_query
        
        # Получаем статистику
        stats = self.statistics_manager.get_general_statistics()
        
        message_text = "Общая статистика:\n\n"
        
        if stats:
            message_text += f"Всего пользователей: {stats.get('total_users', 0)}\n"
            message_text += f"Активных пользователей сегодня: {stats.get('active_users_today', 0)}\n"
            message_text += f"Новых регистраций сегодня: {stats.get('new_registrations_today', 0)}\n"
            message_text += f"Всего посещений стендов: {stats.get('total_stand_visits', 0)}\n"
            message_text += f"Всего заказов мерча: {stats.get('total_merch_orders', 0)}\n"
            message_text += f"Всего начислено баллов: {stats.get('total_points_earned', 0)}\n"
            message_text += f"Всего потрачено баллов: {stats.get('total_points_spent', 0)}\n"
        else:
            message_text += "Статистика недоступна.\n"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message_text,
            reply_markup=reply_markup
        )
    
    def _get_help_text(self, role: str) -> str:
        """Возвращает текст справки в зависимости от роли пользователя."""
        base_help = (
            "Основные команды:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n\n"
        )
        
        if role == 'guest':
            return base_help + (
                "Функции гостя:\n"
                "- Просмотр каталога мерча\n"
                "- Проверка баланса баллов\n"
                "- Заказ мерча за баллы\n"
                "- Просмотр списка стендов\n"
                "- Управление подписками на уведомления\n\n"
                "Для получения баллов посещайте стенды и показывайте свой QR-код стендистам."
            )
        elif role == 'standist':
            return base_help + (
                "Функции стендиста:\n"
                "- Сканирование QR-кодов посетителей для начисления баллов\n"
                "- Просмотр статистики посещений стенда\n"
                "- Управление информацией о стенде\n\n"
                "Для начисления баллов посетителю отсканируйте его QR-код."
            )
        elif role == 'hr':
            return base_help + (
                "Функции HR:\n"
                "- Отметка потенциальных кандидатов\n"
                "- Добавление заметок о кандидатах\n"
                "- Просмотр списка отмеченных кандидатов\n"
                "- Экспорт данных о кандидатах\n\n"
                "Для отметки кандидата отсканируйте его QR-код."
            )
        elif role == 'admin':
            return base_help + (
                "Функции администратора:\n"
                "- Управление пользователями\n"
                "- Управление стендами\n"
                "- Управление мерчем\n"
                "- Просмотр статистики\n"
                "- Рассылка сообщений\n\n"
                "Для доступа к панели администратора используйте команду /admin."
            )
        else:
            return base_help
    
    def run(self):
    """Запускает бота в режиме long polling."""
    self.updater.start_polling()
    self.updater.idle()
    logging.info('Бот запущен в режиме long polling')


if __name__ == "__main__":
    bot = ConferenceBot()
    bot.run()
