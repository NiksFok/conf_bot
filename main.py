#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Основной модуль Telegram-бота для конференции.
Обрабатывает входящие сообщения и маршрутизирует их к соответствующим обработчикам.
"""

import os
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, CallbackQueryHandler,
    Filters, CallbackContext, ConversationHandler
)
from pymongo.errors import ConnectionFailure

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
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
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
        if not self.token:
            raise ValueError("Не указан токен Telegram бота в .env файле")
            
        self.admin_code = os.getenv("ADMIN_CODE")
        if not self.admin_code:
            raise ValueError("Не указан пароль админа БД бота в .env файле")
        
        # Проверка подключения к базе данных
        try:
            # Инициализация подключения к базе данных
            self.db = DBConnector()
            # Проверка соединения
            self.db.client.admin.command('ping')
            logger.info("Успешное подключение к MongoDB")
        except ConnectionFailure:
            logger.error("Не удалось подключиться к MongoDB")
            raise ConnectionError("Не удалось подключиться к MongoDB. Проверьте настройки подключения.")
        
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
        self.dispatcher.add_handler(CommandHandler("test", self.test_command))
        
        # Обработчик регистрации
        registration_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.registration_start, pattern='^register$')],
            states={
                REGISTRATION: [MessageHandler(Filters.text & ~Filters.command, self.registration_name)],
                OCCUPATION: [MessageHandler(Filters.text & ~Filters.command, self.registration_occupation)],
                LEVEL: [CallbackQueryHandler(self.registration_level, pattern='^level_')],
                COMPANY: [MessageHandler(Filters.text & ~Filters.command, self.registration_company)],
                CONSENT: [CallbackQueryHandler(self.registration_consent, pattern='^consent_')]
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
        
        logger.info(f"Команда /start от пользователя {user_id}")
        
        if user:
            # Пользователь уже зарегистрирован
            role = user.get('role', 'guest')
            self._show_role_menu(update, context, role)
        else:
            # Новый пользователь, предлагаем регистрацию
            keyboard = [
                [InlineKeyboardButton("✨ Зарегистрироваться ✨", callback_data="register")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                "👋 Привет! Добро пожаловать в Лабораторию Т-Банка на Aha'25! 🎉\n\n"
                "Я ваш персональный помощник, который сделает ваше участие максимально комфортным и интересным. "
                "Для начала работы, пожалуйста, пройдите быструю регистрацию.",
                reply_markup=reply_markup
            )
    
    def help_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /help."""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            update.message.reply_text(
                "🔍 Для начала работы с ботом используйте команду /start и пройдите быструю регистрацию. "
                "Это займет всего минуту! 😊"
            )
            return
        
        role = user.get('role', 'guest')
        help_text = self._get_help_text(role)
        
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    def test_command(self, update: Update, context: CallbackContext):
        """Тестовая команда для проверки работоспособности бота."""
        logger.info("Получена команда /test")
        update.message.reply_text("✅ Отлично! Бот работает и готов помогать вам на конференции! 🚀")
        logger.info("Тестовое сообщение отправлено")
    
    def admin_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /admin."""
        update.message.reply_text(
            "🔐 Пожалуйста, введите код администратора для доступа к панели управления:"
        )
        return ADMIN_MENU
    
    def registration_start(self, update: Update, context: CallbackContext):
        """Начало процесса регистрации."""
        query = update.callback_query
        query.answer()
        
        # Проверяем, не зарегистрирован ли уже пользователь
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if user:
            role = user.get('role', 'guest')
            query.edit_message_text(
                f"✅ Вы уже зарегистрированы как {self.role_manager.get_role_name(role)}. "
                f"Используйте меню ниже для навигации по функциям бота."
            )
            self._show_role_menu(update, context, role)
            return ConversationHandler.END
        
        query.edit_message_text(
            "👤 Давайте познакомимся! Пожалуйста, введите ваше имя и фамилию:"
        )
        return REGISTRATION
    
    def registration_name(self, update: Update, context: CallbackContext):
        """Обработка ввода имени и фамилии."""
        full_name = update.message.text.strip()
        if len(full_name.split()) < 2:
            update.message.reply_text(
                "🙏 Пожалуйста, введите и имя, и фамилию, разделенные пробелом: "
            )
            return REGISTRATION
        
        # Сохраняем имя и фамилию в контексте
        name_parts = full_name.split(maxsplit=1)
        context.user_data['first_name'] = name_parts[0]
        context.user_data['last_name'] = name_parts[1]
        
        logger.info(f"Регистрация: получено имя и фамилия: {full_name}")
        
        update.message.reply_text(
            f"👍 Отлично, {name_parts[0]}! Теперь укажите вашу должность:"
        )
        return OCCUPATION
    
    def registration_occupation(self, update: Update, context: CallbackContext):
        """Обработка ввода должности."""
        occupation = update.message.text.strip()
        context.user_data['occupation'] = occupation
        
        logger.info(f"Регистрация: получена должность: {occupation}")
        
        # Предлагаем выбрать уровень
        keyboard = [
            [InlineKeyboardButton("🌱 Junior", callback_data="level_junior")],
            [InlineKeyboardButton("🌿 Middle", callback_data="level_middle")],
            [InlineKeyboardButton("🌲 Senior", callback_data="level_senior")],
            [InlineKeyboardButton("🌳 Lead", callback_data="level_lead")],
            [InlineKeyboardButton("🔄 Другое", callback_data="level_other")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "📊 Выберите ваш профессиональный уровень:",
            reply_markup=reply_markup
        )
        return LEVEL
    
    def registration_level(self, update: Update, context: CallbackContext):
        """Обработка выбора уровня."""
        query = update.callback_query
        query.answer()
        
        level = query.data.replace("level_", "")
        context.user_data['level'] = level
        
        logger.info(f"Регистрация: выбран уровень: {level}")
        
        query.edit_message_text(
            "🏢 Укажите название вашей компании:"
        )
        return COMPANY
    
    def registration_company(self, update: Update, context: CallbackContext):
        """Обработка ввода компании."""
        company = update.message.text.strip()
        context.user_data['company'] = company
        
        logger.info(f"Регистрация: указана компания: {company}")
        
        # Запрашиваем согласие на обработку данных
        keyboard = [
            [InlineKeyboardButton("✅ Согласен", callback_data="consent_yes")],
            [InlineKeyboardButton("❌ Не согласен", callback_data="consent_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "📝 Для завершения регистрации необходимо ваше согласие на обработку персональных данных.",
            reply_markup=reply_markup
        )
        return CONSENT
    
    def registration_consent(self, update: Update, context: CallbackContext):
        """Обработка согласия на обработку данных."""
        query = update.callback_query
        query.answer()
        
        if query.data == "consent_no":
            query.edit_message_text(
                "😔 К сожалению, без согласия на обработку данных регистрация невозможна. "
                "Вы можете начать регистрацию заново с помощью команды /start, когда будете готовы."
                "Либо вы можете подойти к стойке регистрации и получить бумажный бланк для участия в наших активностях"
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
            'is_candidate': False,
            'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            self.db.create_user(user_data)
            logger.info(f"Пользователь {update.effective_user.id} успешно зарегистрирован")
            
            # Начисляем баллы за регистрацию
            self.points_system.add_points(
                update.effective_user.id, 
                10, 
                'registration', 
                f"reg_{update.effective_user.id}"
            )
            
            # Генерируем QR-код для пользователя
            qr_path = self.qr_generator.generate_user_qr(update.effective_user.id)
            
            query.edit_message_text(
                f"🎉 Поздравляем! Регистрация успешно завершена! 🎉\n\n"
                f"Ваша роль: ✨ Гость ✨\n\n"
                f"🎁 Вам начислено 10 бонусных баллов за регистрацию! Вы можете получать дополнительные баллы "
                f"за посещение стендов и участие в активностях конференции.\n\n"
                f"Используйте меню ниже для навигации по всем возможностям бота."
            )
            
            # Отправляем QR-код пользователю
            with open(qr_path, 'rb') as qr_file:
                context.bot.send_photo(
                    chat_id=update.effective_user.id,
                    photo=qr_file,
                    caption="🔑 Ваш персональный QR-код. Покажите его стендистам для получения баллов и доступа к специальным предложениям!"
                )
            
            # Показываем меню гостя
            self._show_guest_menu(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя: {e}")
            query.edit_message_text(
                "😓 Произошла небольшая техническая заминка при регистрации. Пожалуйста, попробуйте позже или обратитесь к ребятам на стенде регистрации зала Лаборатории Т."
            )
        
        return ConversationHandler.END
    
    def cancel_registration(self, update: Update, context: CallbackContext):
        """Отмена процесса регистрации."""
        update.message.reply_text(
            "🔄 Регистрация отменена. Вы можете начать заново с помощью команды /start в любое удобное время."
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
                "👋 Для начала работы с ботом необходимо зарегистрироваться. Используйте команду /start."
            )
            return
        
        # Проверяем, не заблокирован ли пользователь
        if user.get('is_blocked', False):
            query.edit_message_text(
                "⛔ Ваш аккаунт временно заблокирован. Пожалуйста, обратитесь к niksfok для разблокировки."
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
            elif callback_data == "view_program":
                self._show_program(update, context)
            elif callback_data == "subscribe":
                self._show_subscription_options(update, context)
            elif callback_data.startswith("subscribe_to_"):
                subscription_type = callback_data.replace("subscribe_to_", "")
                self._subscribe_to(update, context, subscription_type)
            elif callback_data.startswith("unsubscribe_from_"):
                subscription_type = callback_data.replace("unsubscribe_from_", "")
                self._unsubscribe_from(update, context, subscription_type)
            elif callback_data.startswith("view_stand_"):
                stand_id = callback_data.replace("view_stand_", "")
                self._show_stand_details(update, context, stand_id)
        
        # Действия для стендистов
        elif role == 'standist':
            if callback_data == "scan_qr":
                self._prompt_qr_scan(update, context)
            elif callback_data == "view_stand_stats":
                self._show_stand_statistics(update, context)
            elif callback_data == "view_my_stand":
                self._show_my_stand(update, context)
            elif callback_data == "view_points":
                self._show_points_balance(update, context)
            elif callback_data == "view_merch":
                self._show_merch_catalog(update, context)
            elif callback_data.startswith("order_merch_"):
                merch_id = callback_data.replace("order_merch_", "")
                self._order_merch(update, context, merch_id)
            elif callback_data == "edit_stand":
                self._edit_stand_prompt(update, context)
            elif callback_data == "view_visitors":
                self._show_stand_visitors(update, context)
        
        # Действия для HR
        elif role == 'hr':
            if callback_data == "mark_candidate":
                self._prompt_candidate_scan(update, context)
            elif callback_data == "view_candidates":
                self._show_candidates_list(update, context)
            elif callback_data == "export_candidates":
                self._export_candidates(update, context)
            elif callback_data == "view_points":
                self._show_points_balance(update, context)
            elif callback_data == "view_merch":
                self._show_merch_catalog(update, context)
            elif callback_data.startswith("order_merch_"):
                merch_id = callback_data.replace("order_merch_", "")
                self._order_merch(update, context, merch_id)
            elif callback_data.startswith("view_candidate_"):
                candidate_id = callback_data.replace("view_candidate_", "")
                self._show_candidate_details(update, context, candidate_id)
            elif callback_data.startswith("add_note_"):
                candidate_id = callback_data.replace("add_note_", "")
                self._prompt_candidate_note(update, context, candidate_id)
        
        # Действия для администраторов
        elif role == 'admin':
            if callback_data == "manage_users":
                self._show_users_management(update, context)
            elif callback_data == "manage_stands":
                self._show_stands_management(update, context)
            elif callback_data == "manage_merch":
                self._show_merch_management(update, context)
            elif callback_data == "view_statistics":
                self._show_statistics(update, context)
            elif callback_data == "broadcast_message":
                self._prompt_broadcast_message(update, context)
            elif callback_data == "confirm_broadcast":
                self._confirm_broadcast(update, context)
            elif callback_data == "cancel_broadcast":
                self._cancel_broadcast(update, context)
            elif callback_data.startswith("change_role_"):
                parts = callback_data.replace("change_role_", "").split("_")
                user_id = int(parts[0])
                new_role = parts[1]
                self._change_user_role(update, context, user_id, new_role)
            elif callback_data.startswith("block_user_"):
                user_id = int(callback_data.replace("block_user_", ""))
                self._block_user(update, context, user_id)
            elif callback_data.startswith("unblock_user_"):
                user_id = int(callback_data.replace("unblock_user_", ""))
                self._unblock_user(update, context, user_id)
            elif callback_data.startswith("delete_user_"):
                user_id = int(callback_data.replace("delete_user_", ""))
                self._delete_user(update, context, user_id)
            elif callback_data == "add_stand":
                self._add_stand_prompt(update, context)
            elif callback_data.startswith("edit_stand_"):
                stand_id = callback_data.replace("edit_stand_", "")
                self._edit_stand_prompt(update, context, stand_id)
            elif callback_data.startswith("delete_stand_"):
                stand_id = callback_data.replace("delete_stand_", "")
                self._delete_stand(update, context, stand_id)
            elif callback_data == "add_merch":
                self._add_merch_prompt(update, context)
            elif callback_data.startswith("edit_merch_"):
                merch_id = callback_data.replace("edit_merch_", "")
                self._edit_merch_prompt(update, context, merch_id)
            elif callback_data.startswith("delete_merch_"):
                merch_id = callback_data.replace("delete_merch_", "")
                self._delete_merch(update, context, merch_id)
    
    def handle_photo(self, update: Update, context: CallbackContext):
        """Обработка фотографий (сканирование QR-кодов)."""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            update.message.reply_text(
                "👋 Для начала работы с ботом необходимо зарегистрироваться. Используйте команду /start."
            )
            return
        
        # Проверяем, не заблокирован ли пользователь
        if user.get('is_blocked', False):
            update.message.reply_text(
                "⛔ Ваш аккаунт временно заблокирован. Пожалуйста, обратитесь к организаторам конференции для разблокировки."
            )
            return
        
        # Получаем роль пользователя
        role = user.get('role', 'guest')
        
        # Обновляем время последней активности пользователя
        self.db.update_user(user_id, {'last_activity': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        
        # Получаем фото с наилучшим качеством
        photo_file = update.message.photo[-1].get_file()
        photo_path = f"temp/{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        
        try:
            # Скачиваем фото
            photo_file.download(photo_path)
            
            # Сканируем QR-код
            qr_data = self.qr_generator.scan_qr_code(photo_path)
            
            # Удаляем временный файл
            os.remove(photo_path)
            
            if not qr_data:
                update.message.reply_text(
                    "🔍 QR-код не обнаружен на изображении. Пожалуйста, убедитесь, что QR-код хорошо виден и попробуйте снова."
                )
                return
            
            logger.info(f"Отсканирован QR-код: {qr_data}")
            
            # Обработка QR-кода в зависимости от роли пользователя
            if role == 'standist':
                # Стендист сканирует QR-код посетителя для начисления баллов
                try:
                    scanned_user_id = int(qr_data)
                    scanned_user = self.db.get_user(scanned_user_id)
                    
                    if not scanned_user:
                        update.message.reply_text(
                            "❓ Пользователь не найден. Возможно, QR-код недействителен или посетитель не зарегистрирован в системе."
                        )
                        return
                    
                    # Получаем стенд стендиста
                    stand = self.db.get_stand_by_owner(user_id)
                    
                    if not stand:
                        update.message.reply_text(
                            "⚠️ У вас нет привязанного стенда. Пожалуйста, обратитесь к администратору."
                        )
                        return
                    
                    stand_id = stand.get('stand_id')
                    
                    # Проверяем, посещал ли пользователь этот стенд ранее
                    if self.points_system.check_stand_visit(scanned_user_id, stand_id):
                        update.message.reply_text(
                            f"ℹ️ Пользователь {scanned_user.get('first_name')} {scanned_user.get('last_name')} "
                            f"уже посещал ваш стенд и получил баллы ранее."
                        )
                        return
                    
                    # Начисляем баллы за посещение стенда
                    points = stand.get('points_reward', 10)
                    if self.points_system.add_points(scanned_user_id, points, 'stand_visit', stand_id):
                        # Увеличиваем счетчик посещений стенда
                        self.db.increment_stand_visits(stand_id)
                        
                        update.message.reply_text(
                            f"🎉 Отлично! Пользователю {scanned_user.get('first_name')} {scanned_user.get('last_name')} "
                            f"успешно начислено {points} баллов за посещение вашего стенда!"
                        )
                    else:
                        update.message.reply_text(
                            "😓 Не удалось начислить баллы. Пожалуйста, попробуйте позже или обратитесь к администратору."
                        )

                    # Отмечаем пользователя как перспективного кандидата для дальнейшей проработки
                    if self.candidate_manager.mark_as_candidate(scanned_user_id, user_id):
                        update.message.reply_text(
                            f"✅ Отлично! Пользователь {scanned_user.get('first_name')} {scanned_user.get('last_name')} "
                            f"успешно отмечен как перспективный кандидат"
                        )
                        
                        # Предлагаем добавить заметку о кандидате
                        keyboard = [
                            [InlineKeyboardButton("📝 Добавить заметку", callback_data=f"add_note_{scanned_user_id}")],
                            [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        update.message.reply_text(
                            "Хотите добавить заметку о госте?",
                            reply_markup=reply_markup
                        )
                    else:
                        update.message.reply_text(
                            "😓 Не удалось отметить пользователя как кандидата. Пожалуйста, попробуйте позже или обратитесь к администратору"
                        )
                
                except ValueError:
                    update.message.reply_text(
                        "⚠️ Недействительный QR-код. QR-код должен содержать ID пользователя."
                    )
            
            elif role == 'hr':
                # HR сканирует QR-код кандидата для отметки
                try:
                    scanned_user_id = int(qr_data)
                    scanned_user = self.db.get_user(scanned_user_id)
                    
                    if not scanned_user:
                        update.message.reply_text(
                            "❓ Пользователь не найден. Возможно, QR-код недействителен или посетитель не зарегистрирован в системе."
                        )
                        return
                    
                    # Отмечаем пользователя как кандидата
                    if self.candidate_manager.mark_as_candidate(scanned_user_id, user_id):
                        update.message.reply_text(
                            f"✅ Отлично! Пользователь {scanned_user.get('first_name')} {scanned_user.get('last_name')} "
                            f"успешно отмечен как потенциальный кандидат."
                        )
                        
                        # Предлагаем добавить заметку о кандидате
                        keyboard = [
                            [InlineKeyboardButton("📝 Добавить заметку", callback_data=f"add_note_{scanned_user_id}")],
                            [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        update.message.reply_text(
                            "Хотите добавить заметку о кандидате?",
                            reply_markup=reply_markup
                        )
                    else:
                        update.message.reply_text(
                            "😓 Не удалось отметить пользователя как кандидата. Пожалуйста, попробуйте позже или обратитесь к администратору"
                        )
                
                except ValueError:
                    update.message.reply_text(
                        "⚠️ Недействительный QR-код. QR-код должен содержать ID пользователя."
                    )
            
            else:
                # Обычный пользователь сканирует QR-код
                if qr_data.startswith("stand:"):
                    # QR-код стенда
                    stand_id = qr_data.replace("stand:", "")
                    stand = self.db.get_stand(stand_id)
                    
                    if not stand:
                        update.message.reply_text(
                            "❓ Стенд не найден. Возможно, QR-код недействителен или устарел."
                        )
                        return
                    
                    update.message.reply_text(
                        f"🎯 Вы отсканировали QR-код стенда: {stand.get('name')}\n\n"
                        f"{stand.get('description')}\n\n"
                        f"📱 Покажите свой персональный QR-код стендисту для получения бонусных баллов!"
                    )
                
                elif qr_data.startswith("merch:"):
                    # QR-код мерча
                    merch_id = qr_data.replace("merch:", "")
                    merch = self.db.get_merch(merch_id)
                    
                    if not merch:
                        update.message.reply_text(
                            "❓ Мерч не найден. Возможно, QR-код недействителен или устарел."
                        )
                        return
                    
                    # Показываем информацию о мерче
                    keyboard = [
                        [InlineKeyboardButton("🛍️ Заказать", callback_data=f"order_merch_{merch_id}")],
                        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    update.message.reply_text(
                        f"🎁 Вы отсканировали QR-код мерча: {merch.get('name')}\n\n"
                        f"{merch.get('description')}\n\n"
                        f"💰 Стоимость: {merch.get('points_cost')} баллов\n"
                        f"📦 Осталось: {merch.get('quantity_left')} шт.",
                        reply_markup=reply_markup
                    )
                
                elif qr_data.startswith("event:"):
                    # QR-код события
                    event_id = qr_data.replace("event:", "")
                    event = self.db.get_event(event_id)
                    
                    if not event:
                        update.message.reply_text(
                            "❓ Событие не найдено. Возможно, QR-код недействителен или устарел."
                        )
                        return
                    
                    update.message.reply_text(
                        f"📅 Вы отсканировали QR-код события: {event.get('name')}\n\n"
                        f"{event.get('description')}\n\n"
                        f"⏰ Время: {event.get('start_time')} - {event.get('end_time')}\n"
                        f"📍 Место: {event.get('location')}"
                    )
                
                else:
                    # Неизвестный формат QR-кода
                    update.message.reply_text(
                        "❓ Неизвестный формат QR-кода. Пожалуйста, убедитесь, что вы сканируете правильный QR-код"
                    )
        
        except Exception as e:
            logger.error(f"Ошибка при обработке фото: {e}")
            update.message.reply_text(
                "😓 Произошла ошибка при обработке фотографии. Пожалуйста, попробуйте еще раз или обратитесь к технической поддержке."
            )
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Обработка текстовых сообщений."""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            update.message.reply_text(
                "👋 Для начала работы с ботом необходимо зарегистрироваться. Используйте команду /start."
            )
            return
        
        # Проверяем, не заблокирован ли пользователь
        if user.get('is_blocked', False):
            update.message.reply_text(
                "⛔ Ваш аккаунт временно заблокирован. Пожалуйста, обратитесь к администратору для разблокировки."
            )
            return
        
        # Обновляем время последней активности пользователя
        self.db.update_user(user_id, {'last_activity': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        
        # Обработка сообщений в зависимости от текущего состояния
        if context.user_data.get('state') == 'waiting_broadcast_text':
            # Администратор вводит текст для рассылки
            broadcast_text = update.message.text
            
            # Запрашиваем подтверждение
            keyboard = [
                [InlineKeyboardButton("✅ Отправить", callback_data="confirm_broadcast")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            context.user_data['broadcast_text'] = broadcast_text
            
            update.message.reply_text(
                f"📢 Текст сообщения для рассылки:\n\n{broadcast_text}\n\nПодтвердите отправку:",
                reply_markup=reply_markup
            )
            
            context.user_data['state'] = 'waiting_broadcast_confirmation'
        
        elif context.user_data.get('state') == 'waiting_candidate_note':
            # HR вводит заметку о кандидате
            note_text = update.message.text
            candidate_id = context.user_data.get('candidate_id')
            
            if not candidate_id:
                update.message.reply_text(
                    "😓 Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь к технической поддержке."
                )
                return
            
            # Добавляем заметку о кандидате
            if self.candidate_manager.add_note(int(candidate_id), user_id, note_text):
                update.message.reply_text(
                    "✅ Заметка о кандидате успешно добавлена!"
                )
            else:
                update.message.reply_text(
                    "😓 Не удалось добавить заметку. Пожалуйста, попробуйте позже или обратитесь к технической поддержке."
                )
            
            # Сбрасываем состояние
            context.user_data.pop('state', None)
            context.user_data.pop('candidate_id', None)
            
            # Показываем меню HR
            self._show_role_menu(update, context, 'hr')
        
        else:
            # Обычное сообщение, показываем меню в зависимости от роли
            role = user.get('role', 'guest')
            self._show_role_menu(update, context, role)
    
    def unknown_command(self, update: Update, context: CallbackContext):
        """Обработчик неизвестных команд."""
        update.message.reply_text(
            "🤔 Я не знаю такой команды. Используйте /help для получения списка доступных команд или меню для навигации."
        )
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработчик ошибок."""
        logger.error(f"Произошла ошибка: {context.error}")
        
        # Логируем ошибку в базу данных
        error_data = {
            'error_message': str(context.error),
            'traceback': traceback.format_exc(),
            'update': update.to_dict() if update else None
        }
        
        self.db.log_error(error_data)
        
        # Отправляем сообщение пользователю
        if update and update.effective_chat:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="😓 Произошла небольшая техническая заминка. Наши специалисты уже работают над решением. Пожалуйста, попробуйте позже."
            )
    
    def _show_role_menu(self, update: Update, context: CallbackContext):
        """Показывает меню в зависимости от роли пользователя."""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            if update.callback_query:
                update.callback_query.edit_message_text(
                    "👋 Для начала работы с ботом необходимо зарегистрироваться. Используйте команду /start."
                )
            else:
                update.message.reply_text(
                    "👋 Для начала работы с ботом необходимо зарегистрироваться. Используйте команду /start."
                )
            return
        
        role = user.get('role', 'guest')
        
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
            [InlineKeyboardButton("📅 Программа конференции", callback_data="view_program")],
            [InlineKeyboardButton("💰 Мои баллы", callback_data="view_points")],
            # [InlineKeyboardButton("🎁 Каталог мерча", callback_data="view_merch")],
            [InlineKeyboardButton("🏢 Список стендов", callback_data="view_stands")],
            [InlineKeyboardButton("🔔 Подписаться на обновления", callback_data="subscribe")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = "🌟 Главное меню гостя зала Т-Лаборатории 🌟\n\nВыберите интересующий вас раздел:"
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup
            )
    
    def _show_standist_menu(self, update: Update, context: CallbackContext):
        """Показывает меню стендиста."""
        keyboard = [
            [InlineKeyboardButton("📷 Сканировать QR-код", callback_data="scan_qr")],
            [InlineKeyboardButton("👤 Отметить гостя", callback_data="mark_candidate")],
            [InlineKeyboardButton("📊 Статистика стенда", callback_data="view_stand_stats")],
            [InlineKeyboardButton("🏢 Мой стенд", callback_data="view_my_stand")]
            #[InlineKeyboardButton("💰 Мои баллы", callback_data="view_points")],
            #[InlineKeyboardButton("🎁 Каталог мерча", callback_data="view_merch")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = "🌟 Главное меню стендиста 🌟\n\nВыберите интересующий вас раздел:"
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup
            )
    
    def _show_hr_menu(self, update: Update, context: CallbackContext):
        """Показывает меню HR."""
        keyboard = [
            [InlineKeyboardButton("👤 Отметить кандидата", callback_data="mark_candidate")],
            [InlineKeyboardButton("📋 Список кандидатов", callback_data="view_candidates")]
            # [InlineKeyboardButton("📤 Экспорт данных", callback_data="export_candidates")],
            # [InlineKeyboardButton("💰 Мои баллы", callback_data="view_points")],
            # [InlineKeyboardButton("🎁 Каталог мерча", callback_data="view_merch")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = "🌟 Главное меню HR-специалиста 🌟\n\nВыберите интересующий вас раздел:"
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup
            )
    
    def _show_admin_menu(self, update: Update, context: CallbackContext):
        """Показывает меню администратора."""
        keyboard = [
            [InlineKeyboardButton("👥 Управление пользователями", callback_data="manage_users")],
            [InlineKeyboardButton("🏢 Управление стендами", callback_data="manage_stands")],
            [InlineKeyboardButton("🎁 Управление мерчем", callback_data="manage_merch")],
            [InlineKeyboardButton("📊 Статистика и аналитика", callback_data="view_statistics")],
            [InlineKeyboardButton("📢 Рассылка сообщений", callback_data="broadcast_message")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = "🌟 Панель администратора 🌟\n\nВыберите раздел для управления:"
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup
            )
    
    def _get_help_text(self, role):
        """Возвращает текст справки в зависимости от роли пользователя."""
        if role == 'guest':
            return (
                "🌟 *Справка по использованию бота* 🌟\n\n"
                "Вы зарегистрированы как *посетитель Т-Лаборатории*.\n\n"
                "Доступные команды:\n"
                "• /help - Эта справка\n\n"
                "Возможности бота:\n"
                "• 📅 Просмотр программу зала\n"
                "• 💰 Проверка баланса баллов\n"
                "• 🏢 Просмотр информации о стендах\n"
                "• 🔔 Подписка на обновления\n\n"
                "Как получать баллы:\n"
                "• ✅ За регистрацию в боте\n"
                "• 📝 За участие в активностях (покажите свой QR-код стендисту)\n\n"
                "Если у вас возникли вопросы, обратитесь на стойку регистрации у входа в наш зал"
            )
        elif role == 'standist':
            return (
                "🌟 *Справка по использованию бота* 🌟\n\n"
                "Вы зарегистрированы как *Стендист*.\n\n"
                "Доступные команды:\n"
                "• /help - Эта справка\n\n"
                "Возможности бота:\n"
                "• 📷 Сканирование QR-кодов посетителей для начисления баллов\n"
                "• 👤 Отмечайте перспективных ребят\n"
                "• 📝 Добавление заметок о кандидатах\n"
                "• 📊 Просмотр статистики посещений вашего стенда\n"
                "• 🏢 Управление информацией о вашем стенде\n\n"
                "Как начислять баллы посетителям:\n"
                "1. Выберите 'Сканировать QR-код'\n"
                "2. Отсканируйте QR-код посетителя\n"
                "3. Введите сумму баллов, где 1 наклейка = 10 баллов\n"
                "3. Баллы будут начислены автоматически\n\n"
                "Если у вас возникли вопросы, обратитесь к админу - niksfok"
            )
        elif role == 'hr':
            return (
                "🌟 *Справка по использованию бота* 🌟\n\n"
                "Вы зарегистрированы как *HR-специалист*.\n\n"
                "Доступные команды:\n"
                "• /start - Главное меню\n"
                "• /help - Эта справка\n\n"
                "Возможности бота:\n"
                "• 👤 Отметка потенциальных кандидатов\n"
                "• 📋 Просмотр списка отмеченных кандидатов\n"
                "• 📝 Добавление заметок о кандидатах\n"
                "• 📤 Экспорт данных о кандидатах\n"
                "• 💰 Проверка баланса баллов\n"
                "• 🎁 Заказ мерча за баллы\n\n"
                "Как отметить кандидата:\n"
                "1. Выберите 'Отметить кандидата'\n"
                "2. Отсканируйте QR-код участника\n"
                "3. Добавьте заметку о кандидате\n\n"
                "Если у вас возникли вопросы, обратитесь к админу - niksfok"
            )
        elif role == 'admin':
            return (
                "🌟 *Справка по использованию бота* 🌟\n\n"
                "Вы зарегистрированы как *Администратор*.\n\n"
                "Доступные команды:\n"
                "• /start - Главное меню\n"
                "• /help - Эта справка\n"
                "• /admin - Панель администратора\n\n"
                "Возможности бота:\n"
                "• 👥 Управление пользователями (изменение ролей, блокировка)\n"
                "• 🏢 Управление стендами (добавление, редактирование, удаление)\n"
                "• 🎁 Управление мерчем (добавление, редактирование, удаление)\n"
                "• 📊 Просмотр статистики и аналитики\n"
                "• 📢 Рассылка сообщений пользователям\n\n"
                "Если у вас возникли вопросы - молись)))"
            )
        else:
            return (
                "🌟 *Справка по использованию бота* 🌟\n\n"
                "Доступные команды:\n"
                "• /start - Главное меню\n"
                "• /help - Эта справка\n\n"
                "Если у вас возникли вопросы, обратитесь на стойку регистрации у входа в наш зал"
            )
    
    def run_bot(self):
        """Запускает бота в режиме long polling."""
        logger.info("Запуск бота...")
        self.updater.start_polling()
        self.updater.idle()
        logger.info("Бот остановлен")

# Точка входа
if __name__ == "__main__":
    try:
        bot = ConferenceBot()
        bot.run_bot()
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        print(f"Критическая ошибка при запуске бота: {e}")
