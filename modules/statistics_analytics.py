#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для сбора и анализа статистики.
Обеспечивает генерацию отчетов и визуализацию данных.
"""

from typing import Dict, List, Optional, Any
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import os
from utils.db_connector import DBConnector

class StatisticsManager:
    """Класс для управления статистикой и аналитикой."""
    
    def __init__(self, db: DBConnector):
        """Инициализация менеджера статистики."""
        self.db = db
        
        # Создаем директорию для сохранения графиков, если её нет
        os.makedirs('data/statistics', exist_ok=True)
    
    def get_general_statistics(self) -> Dict[str, Any]:
        """Получает общую статистику по боту."""
        # Получаем всех пользователей
        all_users = self.db.get_all_users()
        
        # Получаем активных пользователей за сегодня
        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        active_users_today = self.db.users.count_documents({
            'last_activity': {'$gte': today}
        })
        
        # Получаем новых пользователей за сегодня
        new_registrations_today = self.db.users.count_documents({
            'registered_at': {'$gte': today}
        })
        
        # Получаем статистику по стендам
        all_stands = self.db.get_all_stands()
        total_stand_visits = sum(stand.get('visits', 0) for stand in all_stands)
        
        # Получаем статистику по мерчу
        all_merch_transactions = list(self.db.merch_transactions.find())
        total_merch_orders = len(all_merch_transactions)
        
        # Получаем статистику по баллам
        all_points_transactions = list(self.db.points_transactions.find())
        total_points_earned = sum(tx.get('amount', 0) for tx in all_points_transactions if tx.get('type') == 'earn')
        total_points_spent = sum(tx.get('amount', 0) for tx in all_points_transactions if tx.get('type') == 'spend')
        
        return {
            'total_users': len(all_users),
            'active_users_today': active_users_today,
            'new_registrations_today': new_registrations_today,
            'total_stand_visits': total_stand_visits,
            'total_merch_orders': total_merch_orders,
            'total_points_earned': total_points_earned,
            'total_points_spent': total_points_spent,
            # Добавляем эмодзи для улучшения UX в отчетах
            'stats_with_emoji': {
                '👥 Всего пользователей': len(all_users),
                '🔆 Активных пользователей сегодня': active_users_today,
                '✨ Новых регистраций сегодня': new_registrations_today,
                '🏢 Всего посещений стендов': total_stand_visits,
                '🛍️ Всего заказов мерча': total_merch_orders,
                '⬆️ Всего начислено баллов': total_points_earned,
                '⬇️ Всего потрачено баллов': total_points_spent
            }
        }
    
    def get_stand_visitors(self, stand_id: str) -> List[Dict[str, Any]]:
        """Получает список посетителей стенда."""
        # Получаем транзакции баллов за посещение этого стенда
        transactions = list(self.db.points_transactions.find({
            'reason': 'stand_visit',
            'reference_id': stand_id
        }).sort('created_at', -1))
        
        visitors = []
        for tx in transactions:
            user_id = tx.get('user_id')
            user = self.db.get_user(user_id)
            
            if user:
                visitors.append({
                    'user_id': user_id,
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'company': user.get('company', ''),
                    'visit_time': tx.get('created_at'),
                    # Добавляем форматированное время для улучшения UX
                    'visit_time_display': tx.get('created_at').strftime('%d.%m.%Y %H:%M') if tx.get('created_at') else ''
                })
        
        return visitors
    
    def get_stand_statistics(self, stand_id: str = None) -> Dict[str, Any]:
        """Получает статистику по стенду или всем стендам."""
        if stand_id:
            # Статистика по конкретному стенду
            stand = self.db.get_stand(stand_id)
            if not stand:
                return {}
            
            visitors = self.get_stand_visitors(stand_id)
            
            return {
                'stand_id': stand_id,
                'name': stand.get('name', ''),
                'visits': stand.get('visits', 0),
                'visitors': visitors,
                # Добавляем эмодзи для улучшения UX
                'stats_with_emoji': {
                    '🏢 Название стенда': stand.get('name', ''),
                    '👣 Количество посещений': stand.get('visits', 0),
                    '👥 Количество уникальных посетителей': len(visitors)
                }
            }
        else:
            # Статистика по всем стендам
            all_stands = self.db.get_all_stands()
            
            stands_data = []
            for stand in all_stands:
                stand_id = stand.get('stand_id')
                visitors_count = self.db.points_transactions.count_documents({
                    'reason': 'stand_visit',
                    'reference_id': stand_id
                })
                
                # Добавляем эмодзи для популярности стенда
                popularity_emoji = '🔥' if stand.get('visits', 0) > 20 else ('⭐' if stand.get('visits', 0) > 10 else '📊')
                
                stands_data.append({
                    'stand_id': stand_id,
                    'name': stand.get('name', ''),
                    'visits': stand.get('visits', 0),
                    'visitors_count': visitors_count,
                    'popularity': popularity_emoji
                })
            
            # Сортируем по количеству посещений
            stands_data.sort(key=lambda x: x.get('visits', 0), reverse=True)
            
            return {
                'total_stands': len(all_stands),
                'total_visits': sum(stand.get('visits', 0) for stand in all_stands),
                'stands': stands_data,
                # Добавляем эмодзи для улучшения UX
                'stats_with_emoji': {
                    '🏢 Всего стендов': len(all_stands),
                    '👣 Всего посещений': sum(stand.get('visits', 0) for stand in all_stands)
                }
            }
    
    def get_user_activity_statistics(self) -> Dict[str, Any]:
        """Получает статистику активности пользователей."""
        # Получаем всех пользователей
        all_users = self.db.get_all_users()
        
        # Группируем пользователей по ролям
        roles = {}
        for user in all_users:
            role = user.get('role', 'guest')
            if role not in roles:
                roles[role] = 0
            roles[role] += 1
        
        # Добавляем эмодзи к ролям
        roles_with_emoji = {}
        for role, count in roles.items():
            if role == 'admin':
                roles_with_emoji['🛡️ Администратор'] = count
            elif role == 'organizer':
                roles_with_emoji['🎯 Организатор'] = count
            elif role == 'exhibitor':
                roles_with_emoji['🏢 Экспонент'] = count
            elif role == 'hr':
                roles_with_emoji['👔 HR'] = count
            elif role == 'participant':
                roles_with_emoji['👤 Участник'] = count
            else:
                roles_with_emoji['👋 ' + role.capitalize()] = count
        
        # Получаем статистику по времени регистрации
        registrations_by_day = {}
        for user in all_users:
            reg_date = user.get('registered_at')
            if reg_date:
                day = reg_date.strftime('%Y-%m-%d')
                if day not in registrations_by_day:
                    registrations_by_day[day] = 0
                registrations_by_day[day] += 1
        
        # Получаем статистику по времени последней активности
        activity_by_day = {}
        for user in all_users:
            last_activity = user.get('last_activity')
            if last_activity:
                day = last_activity.strftime('%Y-%m-%d')
                if day not in activity_by_day:
                    activity_by_day[day] = 0
                activity_by_day[day] += 1
        
        # Получаем статистику по компаниям
        companies = {}
        for user in all_users:
            company = user.get('company', 'Не указана')
            if company not in companies:
                companies[company] = 0
            companies[company] += 1
        
        # Сортируем компании по количеству пользователей
        companies = dict(sorted(companies.items(), key=lambda x: x[1], reverse=True))
        
        # Добавляем эмодзи к топ-компаниям
        companies_with_emoji = {}
        for i, (company, count) in enumerate(companies.items()):
            if i < 3:
                emoji = '🥇' if i == 0 else ('🥈' if i == 1 else '🥉')
            else:
                emoji = '🏢'
            companies_with_emoji[f"{emoji} {company}"] = count
        
        return {
            'total_users': len(all_users),
            'roles': roles,
            'roles_with_emoji': roles_with_emoji,
            'registrations_by_day': registrations_by_day,
            'activity_by_day': activity_by_day,
            'companies': companies,
            'companies_with_emoji': companies_with_emoji,
            # Добавляем эмодзи для улучшения UX в общей статистике
            'stats_with_emoji': {
                '👥 Всего пользователей': len(all_users),
                '🔄 Активных за последние 24 часа': self.db.users.count_documents({
                    'last_activity': {'$gte': datetime.datetime.utcnow() - datetime.timedelta(hours=24)}
                })
            }
        }
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Генерирует ежедневный отчет по активности бота."""
        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        
        # Получаем общую статистику
        general_stats = self.get_general_statistics()
        
        # Получаем статистику по стендам
        stand_stats = self.get_stand_statistics()
        
        # Получаем статистику по активности пользователей
        user_stats = self.get_user_activity_statistics()
        
        # Формируем отчет
        report = {
            'date': today,
            'general_stats': general_stats,
            'stand_stats': stand_stats,
            'user_stats': user_stats,
            # Добавляем дружелюбное сообщение для отчета
            'report_title': f"📊 Ежедневный отчет за {today}",
            'report_message': f"✨ Отчет успешно сгенерирован! Ниже представлена статистика активности бота за {today}."
        }
        
        # Сохраняем отчет в базу данных
        self.db.update_daily_statistics(report)
        
        return report
    
    def generate_stand_visits_chart(self, file_path: str = 'data/statistics/stand_visits.png') -> str:
        """Генерирует график посещаемости стендов."""
        # Получаем статистику по стендам
        stand_stats = self.get_stand_statistics()
        
        # Подготавливаем данные для графика
        stands = stand_stats.get('stands', [])
        names = [stand.get('name', '') for stand in stands[:10]]  # Берем только топ-10 стендов
        visits = [stand.get('visits', 0) for stand in stands[:10]]
        
        # Создаем график с улучшенным дизайном
        plt.figure(figsize=(12, 6))
        bars = plt.bar(names, visits, color='#4CAF50')
        
        # Добавляем значения над столбцами
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.xlabel('Стенды', fontsize=12)
        plt.ylabel('Количество посещений', fontsize=12)
        plt.title('🏆 Топ-10 стендов по посещаемости', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Сохраняем график
        plt.savefig(file_path)
        plt.close()
        
        return file_path
    
    def generate_user_registrations_chart(self, file_path: str = 'data/statistics/user_registrations.png') -> str:
        """Генерирует график регистраций пользователей по дням."""
        # Получаем статистику по активности пользователей
        user_stats = self.get_user_activity_statistics()
        
        # Подготавливаем данные для графика
        registrations = user_stats.get('registrations_by_day', {})
        
        # Сортируем по датам
        dates = sorted(registrations.keys())
        counts = [registrations[date] for date in dates]
        
        # Создаем график с улучшенным дизайном
        plt.figure(figsize=(12, 6))
        plt.plot(dates, counts, marker='o', color='#2196F3', linewidth=2, markersize=8)
        
        # Добавляем значения над точками
        for i, count in enumerate(counts):
            plt.text(i, count + 0.5, f'{count}', ha='center')
        
        plt.xlabel('Дата', fontsize=12)
        plt.ylabel('Количество регистраций', fontsize=12)
        plt.title('📈 Динамика регистраций пользователей', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.grid(linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Сохраняем график
        plt.savefig(file_path)
        plt.close()
        
        return file_path
    
    def generate_roles_distribution_chart(self, file_path: str = 'data/statistics/roles_distribution.png') -> str:
        """Генерирует круговую диаграмму распределения ролей пользователей."""
        # Получаем статистику по активности пользователей
        user_stats = self.get_user_activity_statistics()
        
        # Подготавливаем данные для графика с эмодзи
        roles = user_stats.get('roles_with_emoji', {})
        
        # Создаем график с улучшенным дизайном
        plt.figure(figsize=(10, 10))
        colors = ['#4CAF50', '#2196F3', '#FFC107', '#9C27B0', '#F44336', '#607D8B']
        
        plt.pie(roles.values(), labels=roles.keys(), autopct='%1.1f%%', 
                startangle=90, colors=colors, shadow=True)
        plt.axis('equal')
        plt.title('👥 Распределение пользователей по ролям', fontsize=14)
        
        # Сохраняем график
        plt.savefig(file_path)
        plt.close()
        
        return file_path
    
    def export_statistics_to_excel(self, file_path: str = 'data/statistics/statistics_export.xlsx') -> str:
        """Экспортирует статистику в Excel-файл."""
        # Получаем все необходимые данные
        general_stats = self.get_general_statistics()
        stand_stats = self.get_stand_statistics()
        user_stats = self.get_user_activity_statistics()
        
        # Создаем Excel-файл с несколькими листами
        with pd.ExcelWriter(file_path) as writer:
            # Лист с общей статистикой (используем версию с эмодзи)
            general_df = pd.DataFrame({
                'Показатель': general_stats.get('stats_with_emoji', {}).keys(),
                'Значение': general_stats.get('stats_with_emoji', {}).values()
            })
            general_df.to_excel(writer, sheet_name='Общая статистика', index=False)
            
            # Лист со статистикой по стендам
            stands_df = pd.DataFrame(stand_stats.get('stands', []))
            if not stands_df.empty:
                stands_df.to_excel(writer, sheet_name='Статистика стендов', index=False)
            
            # Лист с распределением по ролям (используем версию с эмодзи)
            roles_df = pd.DataFrame({
                'Роль': user_stats.get('roles_with_emoji', {}).keys(),
                'Количество': user_stats.get('roles_with_emoji', {}).values()
            })
            roles_df.to_excel(writer, sheet_name='Распределение ролей', index=False)
            
            # Лист с регистрациями по дням
            registrations_df = pd.DataFrame({
                'Дата': user_stats.get('registrations_by_day', {}).keys(),
                'Количество': user_stats.get('registrations_by_day', {}).values()
            })
            registrations_df.to_excel(writer, sheet_name='Регистрации по дням', index=False)
            
            # Лист с компаниями (используем версию с эмодзи)
            companies_df = pd.DataFrame({
                'Компания': user_stats.get('companies_with_emoji', {}).keys(),
                'Количество': user_stats.get('companies_with_emoji', {}).values()
            })
            companies_df.to_excel(writer, sheet_name='Компании', index=False)
        
        return file_path
