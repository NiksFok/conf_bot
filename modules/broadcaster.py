#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для рассылки сообщений.
Обеспечивает массовую рассылку сообщений и планирование рассылок.
"""

from typing import Dict, List, Optional, Any
import datetime
import schedule
import time
import threading
import sys
from utils.db_connector import DBConnector

class Broadcaster:
    """Класс для рассылки сообщений."""
    
    def __init__(self, db: DBConnector):
        """Инициализация модуля рассылки."""
        self.db = db
    
    def send_broadcast(self, bot, message: str, target_role: str = None) -> Dict[str, Any]:
        """Отправляет сообщение всем пользователям или пользователям с указанной ролью."""
        if target_role:
            # Получаем пользователей с указанной ролью
            users = self.db.get_users_by_role(target_role)
        else:
            # Получаем всех пользователей
            users = self.db.get_all_users()
        
        # Фильтруем заблокированных пользователей
        users = [user for user in users if not user.get('is_blocked', False)]
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                bot.send_message(
                    chat_id=user.get('user_id'),
                    text=message
                )
                sent_count += 1
            except Exception as e:
                failed_count += 1
                # Логируем ошибку
                self.db.log_error({
                    'user_id': user.get('user_id'),
                    'error_type': 'broadcast_send_failed',
                    'error_message': str(e),
                    'resolved': False
                })
        
        # Логируем информацию о рассылке
        broadcast_info = {
            'timestamp': datetime.datetime.utcnow(),
            'message': message,
            'target_role': target_role,
            'total_users': len(users),
            'sent_count': sent_count,
            'failed_count': failed_count
        }
        
        # Сохраняем информацию о рассылке в базу данных
        self.db.bot_statistics.update_one(
            {'date': datetime.datetime.utcnow().strftime('%Y-%m-%d')},
            {'$push': {'broadcasts': broadcast_info}},
            upsert=True
        )
        
        return {
            'success': True,
            'total_users': len(users),
            'sent_count': sent_count,
            'failed_count': failed_count
        }
    
    def schedule_broadcast(self, bot, message: str, schedule_time: datetime.datetime, target_role: str = None) -> Dict[str, Any]:
        """Планирует рассылку сообщения на указанное время."""
        # Создаем запись о запланированной рассылке
        scheduled_broadcast = {
            'message': message,
            'schedule_time': schedule_time,
            'target_role': target_role,
            'created_at': datetime.datetime.utcnow(),
            'status': 'scheduled'
        }
        
        # Сохраняем информацию о запланированной рассылке в базу данных
        result = self.db.bot_statistics.update_one(
            {'date': datetime.datetime.utcnow().strftime('%Y-%m-%d')},
            {'$push': {'scheduled_broadcasts': scheduled_broadcast}},
            upsert=True
        )
        
        # Планируем рассылку
        def send_scheduled_broadcast():
            self.send_broadcast(bot, message, target_role)
            
            # Обновляем статус рассылки
            self.db.bot_statistics.update_one(
                {'date': datetime.datetime.utcnow().strftime('%Y-%m-%d'), 'scheduled_broadcasts.schedule_time': schedule_time},
                {'$set': {'scheduled_broadcasts.$.status': 'sent'}}
            )
        
        # Вычисляем время до запланированной рассылки
        now = datetime.datetime.utcnow()
        if schedule_time > now:
            delay = (schedule_time - now).total_seconds()
            threading.Timer(delay, send_scheduled_broadcast).start()
        
        return {
            'success': True,
            'message': message,
            'schedule_time': schedule_time,
            'target_role': target_role
        }
    
    def get_scheduled_broadcasts(self) -> List[Dict[str, Any]]:
        """Получает список запланированных рассылок."""
        # Получаем все записи о запланированных рассылках
        stats = list(self.db.bot_statistics.find())
        
        scheduled_broadcasts = []
        for stat in stats:
            if 'scheduled_broadcasts' in stat:
                for broadcast in stat['scheduled_broadcasts']:
                    if broadcast.get('status') == 'scheduled':
                        scheduled_broadcasts.append(broadcast)
        
        return scheduled_broadcasts
    
    def cancel_scheduled_broadcast(self, schedule_time: datetime.datetime) -> bool:
        """Отменяет запланированную рассылку."""
        # Обновляем статус рассылки
        result = self.db.bot_statistics.update_one(
            {'scheduled_broadcasts.schedule_time': schedule_time},
            {'$set': {'scheduled_broadcasts.$.status': 'cancelled'}}
        )
        
        return result.modified_count > 0
    
    def run_scheduler(self):
        """Запускает планировщик рассылок."""
        # Получаем бота из основного модуля
        sys.path.append('..')
        from main import ConferenceBot
        bot = ConferenceBot().updater.bot
        
        # Функция для проверки и отправки запланированных рассылок
        def check_scheduled_broadcasts():
            now = datetime.datetime.utcnow()
            
            # Получаем все запланированные рассылки
            scheduled_broadcasts = self.get_scheduled_broadcasts()
            
            for broadcast in scheduled_broadcasts:
                schedule_time = broadcast.get('schedule_time')
                
                # Если время рассылки наступило или прошло
                if schedule_time and schedule_time <= now:
                    # Отправляем рассылку
                    self.send_broadcast(
                        bot,
                        broadcast.get('message', ''),
                        broadcast.get('target_role')
                    )
                    
                    # Обновляем статус рассылки
                    self.db.bot_statistics.update_one(
                        {'scheduled_broadcasts.schedule_time': schedule_time},
                        {'$set': {'scheduled_broadcasts.$.status': 'sent'}}
                    )
        
        # Планируем проверку каждую минуту
        schedule.every(1).minutes.do(check_scheduled_broadcasts)
        
        # Запускаем планировщик
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    # Если модуль запущен напрямую, запускаем планировщик
    if len(sys.argv) > 1 and sys.argv[1] == 'run_scheduler':
        from dotenv import load_dotenv
        load_dotenv()
        
        db = DBConnector()
        broadcaster = Broadcaster(db)
        broadcaster.run_scheduler()
