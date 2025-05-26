#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для управления кандидатами.
Обеспечивает отметку пользователей как кандидатов и работу с заметками о них.
"""

from typing import Dict, List, Optional, Any
import datetime
import pandas as pd
from utils.db_connector import DBConnector

class CandidateManager:
    """Класс для управления кандидатами."""
    
    def __init__(self, db: DBConnector):
        """Инициализация менеджера кандидатов."""
        self.db = db
    
    def mark_as_candidate(self, user_id: int, hr_id: int) -> bool:
        """Отмечает пользователя как потенциального кандидата."""
        # Проверяем, существует ли пользователь
        user = self.db.get_user(user_id)
        if not user:
            return False
        
        # Отмечаем пользователя как кандидата
        self.db.mark_user_as_candidate(user_id, True)
        
        # Создаем запись в коллекции кандидатов, если её ещё нет
        existing = self.db.candidate_notes.find_one({
            'candidate_id': user_id,
            'hr_id': hr_id,
            'is_marked': True
        })
        
        if not existing:
            self.db.candidate_notes.insert_one({
                'candidate_id': user_id,
                'hr_id': hr_id,
                'is_marked': True,
                'created_at': datetime.datetime.utcnow(),
                'updated_at': datetime.datetime.utcnow()
            })
        
        return True
    
    def unmark_as_candidate(self, user_id: int, hr_id: int) -> bool:
        """Снимает отметку пользователя как потенциального кандидата."""
        # Проверяем, существует ли пользователь
        user = self.db.get_user(user_id)
        if not user:
            return False
        
        # Удаляем запись из коллекции кандидатов
        self.db.candidate_notes.delete_one({
            'candidate_id': user_id,
            'hr_id': hr_id,
            'is_marked': True
        })
        
        # Проверяем, остались ли другие HR, отметившие этого пользователя
        other_marks = self.db.candidate_notes.find_one({
            'candidate_id': user_id,
            'is_marked': True
        })
        
        # Если нет других отметок, снимаем флаг кандидата с пользователя
        if not other_marks:
            self.db.mark_user_as_candidate(user_id, False)
        
        return True
    
    def add_note(self, candidate_id: int, hr_id: int, text: str, rating: int = None) -> bool:
        """Добавляет заметку о кандидате."""
        # Проверяем, существует ли пользователь и отмечен ли он как кандидат
        user = self.db.get_user(candidate_id)
        if not user:
            return False
        
        # Создаем заметку
        note_data = {
            'candidate_id': candidate_id,
            'hr_id': hr_id,
            'text': text,
            'rating': rating
        }
        
        self.db.create_candidate_note(note_data)
        
        # Отмечаем пользователя как кандидата, если он ещё не отмечен
        if not user.get('is_candidate', False):
            self.mark_as_candidate(candidate_id, hr_id)
        
        return True
    
    def get_candidate_notes(self, candidate_id: int, hr_id: int = None) -> List[Dict[str, Any]]:
        """Получает список заметок о кандидате."""
        return self.db.get_candidate_notes(candidate_id, hr_id)
    
    def get_hr_candidates(self, hr_id: int) -> List[Dict[str, Any]]:
        """Получает список кандидатов, отмеченных указанным HR."""
        # Получаем все записи с отметками от этого HR
        marked_records = list(self.db.candidate_notes.find({
            'hr_id': hr_id,
            'is_marked': True
        }))
        
        # Получаем уникальные ID кандидатов
        candidate_ids = set(record['candidate_id'] for record in marked_records)
        
        # Получаем информацию о каждом кандидате
        candidates = []
        for candidate_id in candidate_ids:
            user = self.db.get_user(candidate_id)
            if user:
                # Получаем заметки об этом кандидате от этого HR
                notes = self.get_candidate_notes(candidate_id, hr_id)
                
                candidates.append({
                    'candidate_id': candidate_id,
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'occupation': user.get('occupation', ''),
                    'level': user.get('level', ''),
                    'company': user.get('company', ''),
                    'notes': notes
                })
        
        return candidates
    
    def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Получает список всех кандидатов."""
        # Получаем всех пользователей, отмеченных как кандидаты
        users = list(self.db.users.find({'is_candidate': True}))
        
        candidates = []
        for user in users:
            # Получаем все заметки об этом кандидате
            notes = self.get_candidate_notes(user.get('user_id'))
            
            # Получаем список HR, отметивших этого кандидата
            hr_ids = set(note.get('hr_id') for note in notes if note.get('is_marked', False))
            hrs = []
            
            for hr_id in hr_ids:
                hr = self.db.get_user(hr_id)
                if hr:
                    hrs.append({
                        'hr_id': hr_id,
                        'name': f"{hr.get('first_name', '')} {hr.get('last_name', '')}"
                    })
            
            candidates.append({
                'candidate_id': user.get('user_id'),
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'occupation': user.get('occupation', ''),
                'level': user.get('level', ''),
                'company': user.get('company', ''),
                'notes': notes,
                'hrs': hrs
            })
        
        return candidates
    
    def export_candidates_to_excel(self, hr_id: int = None, file_path: str = 'candidates_export.xlsx') -> str:
        """Экспортирует данные о кандидатах в Excel-файл."""
        if hr_id:
            # Экспорт кандидатов конкретного HR
            candidates = self.get_hr_candidates(hr_id)
        else:
            # Экспорт всех кандидатов
            candidates = self.get_all_candidates()
        
        # Подготовка данных для экспорта
        export_data = []
        for candidate in candidates:
            # Объединяем все заметки в одну строку
            notes_text = '; '.join([note.get('text', '') for note in candidate.get('notes', []) if 'text' in note])
            
            export_data.append({
                'ID': candidate.get('candidate_id'),
                'Имя': candidate.get('first_name', ''),
                'Фамилия': candidate.get('last_name', ''),
                'Должность': candidate.get('occupation', ''),
                'Уровень': candidate.get('level', ''),
                'Компания': candidate.get('company', ''),
                'Заметки': notes_text
            })
        
        # Создаем DataFrame и экспортируем в Excel
        df = pd.DataFrame(export_data)
        df.to_excel(file_path, index=False)
        
        return file_path
    
    def get_candidate_statistics(self) -> Dict[str, Any]:
        """Получает статистику по кандидатам."""
        all_candidates = self.get_all_candidates()
        all_notes = list(self.db.candidate_notes.find())
        
        total_candidates = len(all_candidates)
        total_notes = len(all_notes)
        
        # Статистика по уровням кандидатов
        level_stats = {}
        for candidate in all_candidates:
            level = candidate.get('level', 'Не указан')
            if level not in level_stats:
                level_stats[level] = 0
            level_stats[level] += 1
        
        # Статистика по компаниям кандидатов
        company_stats = {}
        for candidate in all_candidates:
            company = candidate.get('company', 'Не указана')
            if company not in company_stats:
                company_stats[company] = 0
            company_stats[company] += 1
        
        # HR с наибольшим количеством отмеченных кандидатов
        hr_stats = {}
        for note in all_notes:
            if note.get('is_marked', False):
                hr_id = note.get('hr_id')
                if hr_id not in hr_stats:
                    hr_stats[hr_id] = 0
                hr_stats[hr_id] += 1
        
        top_hrs = []
        for hr_id, count in sorted(hr_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            hr = self.db.get_user(hr_id)
            if hr:
                top_hrs.append({
                    'hr_id': hr_id,
                    'name': f"{hr.get('first_name', '')} {hr.get('last_name', '')}",
                    'candidates_count': count
                })
        
        return {
            'total_candidates': total_candidates,
            'total_notes': total_notes,
            'level_stats': level_stats,
            'company_stats': company_stats,
            'top_hrs': top_hrs
        }
