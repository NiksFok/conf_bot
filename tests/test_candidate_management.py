#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки модуля управления кандидатами.
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
from modules.candidate_management import CandidateManager
from utils.db_connector import DBConnector

class TestCandidateManagement(unittest.TestCase):
    """Тестирование модуля управления кандидатами."""
    
    def setUp(self):
        """Подготовка к тестированию."""
        # Создаем мок для DBConnector
        self.db_mock = MagicMock(spec=DBConnector)
        
        # Создаем моки для коллекций базы данных
        self.db_mock.candidate_notes = MagicMock()
        self.db_mock.users = MagicMock()
        
        # Создаем экземпляр менеджера кандидатов с моком базы данных
        self.candidate_manager = CandidateManager(self.db_mock)
        
        # Настраиваем мок для get_user
        self.user_data = {
            'user_id': 123456789,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'occupation': 'Разработчик',
            'level': 'middle',
            'company': 'ООО Рога и Копыта',
            'is_candidate': False
        }
        self.db_mock.get_user.return_value = self.user_data
        
        # Настраиваем мок для candidate_notes.find_one
        self.db_mock.candidate_notes.find_one.return_value = None
    
    def test_mark_as_candidate(self):
        """Тестирование отметки пользователя как кандидата."""
        # Вызываем метод mark_as_candidate
        result = self.candidate_manager.mark_as_candidate(123456789, 987654321)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что был вызван метод mark_user_as_candidate
        self.db_mock.mark_user_as_candidate.assert_called_once_with(123456789, True)
        
        # Проверяем, что был вызван метод find_one для проверки существующей записи
        self.db_mock.candidate_notes.find_one.assert_called_once()
        
        # Проверяем, что был вызван метод insert_one для создания новой записи
        self.db_mock.candidate_notes.insert_one.assert_called_once()
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_mark_as_candidate_nonexistent_user(self):
        """Тестирование отметки несуществующего пользователя как кандидата."""
        # Настраиваем мок для get_user, чтобы он возвращал None
        self.db_mock.get_user.return_value = None
        
        # Вызываем метод mark_as_candidate
        result = self.candidate_manager.mark_as_candidate(123456789, 987654321)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что не был вызван метод mark_user_as_candidate
        self.db_mock.mark_user_as_candidate.assert_not_called()
        
        # Проверяем, что не был вызван метод find_one
        self.db_mock.candidate_notes.find_one.assert_not_called()
        
        # Проверяем, что не был вызван метод insert_one
        self.db_mock.candidate_notes.insert_one.assert_not_called()
        
        # Проверяем, что метод вернул False
        self.assertFalse(result)
    
    def test_unmark_as_candidate(self):
        """Тестирование снятия отметки пользователя как кандидата."""
        # Вызываем метод unmark_as_candidate
        result = self.candidate_manager.unmark_as_candidate(123456789, 987654321)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что был вызван метод delete_one для удаления записи
        self.db_mock.candidate_notes.delete_one.assert_called_once()
        
        # Проверяем, что был вызван метод find_one для проверки других отметок
        self.db_mock.candidate_notes.find_one.assert_called_once()
        
        # Проверяем, что был вызван метод mark_user_as_candidate для снятия флага
        self.db_mock.mark_user_as_candidate.assert_called_once_with(123456789, False)
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_unmark_as_candidate_with_other_marks(self):
        """Тестирование снятия отметки пользователя как кандидата при наличии других отметок."""
        # Настраиваем мок для candidate_notes.find_one, чтобы он возвращал другую отметку
        self.db_mock.candidate_notes.find_one.return_value = {
            'candidate_id': 123456789,
            'hr_id': 111111111,
            'is_marked': True
        }
        
        # Вызываем метод unmark_as_candidate
        result = self.candidate_manager.unmark_as_candidate(123456789, 987654321)
        
        # Проверяем, что был вызван метод get_user
        self.db_mock.get_user.assert_called_once_with(123456789)
        
        # Проверяем, что был вызван метод delete_one для удаления записи
        self.db_mock.candidate_notes.delete_one.assert_called_once()
        
        # Проверяем, что был вызван метод find_one для проверки других отметок
        self.db_mock.candidate_notes.find_one.assert_called_once()
        
        # Проверяем, что не был вызван метод mark_user_as_candidate
        self.db_mock.mark_user_as_candidate.assert_not_called()
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_add_note(self):
        """Тестирование добавления заметки о кандидате."""
        # Сбрасываем счетчик вызовов get_user перед тестом
        self.db_mock.get_user.reset_mock()
        
        # Вызываем метод add_note
        result = self.candidate_manager.add_note(123456789, 987654321, "Отличный кандидат", 5)
        
        # Проверяем, что был вызван метод get_user хотя бы один раз
        self.db_mock.get_user.assert_called_with(123456789)
        
        # Проверяем, что был вызван метод create_candidate_note с правильными данными
        self.db_mock.create_candidate_note.assert_called_once()
        args, kwargs = self.db_mock.create_candidate_note.call_args
        note_data = args[0]
        self.assertEqual(note_data['candidate_id'], 123456789)
        self.assertEqual(note_data['hr_id'], 987654321)
        self.assertEqual(note_data['text'], "Отличный кандидат")
        self.assertEqual(note_data['rating'], 5)
        
        # Проверяем, что был вызван метод mark_as_candidate
        # Для этого мы должны замокать метод mark_as_candidate
        with patch.object(self.candidate_manager, 'mark_as_candidate') as mock_mark:
            # Сбрасываем счетчик вызовов get_user перед тестом
            self.db_mock.get_user.reset_mock()
            
            # Вызываем метод add_note снова
            self.candidate_manager.add_note(123456789, 987654321, "Отличный кандидат", 5)
            
            # Проверяем, что был вызван метод mark_as_candidate
            mock_mark.assert_called_once_with(123456789, 987654321)
        
        # Проверяем, что метод вернул True
        self.assertTrue(result)
    
    def test_get_candidate_notes(self):
        """Тестирование получения заметок о кандидате."""
        # Настраиваем мок для get_candidate_notes
        notes = [
            {
                'note_id': 'note123',
                'candidate_id': 123456789,
                'hr_id': 987654321,
                'text': "Отличный кандидат",
                'rating': 5,
                'created_at': datetime.datetime.utcnow()
            }
        ]
        self.db_mock.get_candidate_notes.return_value = notes
        
        # Вызываем метод get_candidate_notes
        result = self.candidate_manager.get_candidate_notes(123456789, 987654321)
        
        # Проверяем, что был вызван метод get_candidate_notes с правильными параметрами
        self.db_mock.get_candidate_notes.assert_called_once_with(123456789, 987654321)
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(result, notes)
    
    def test_get_hr_candidates(self):
        """Тестирование получения списка кандидатов, отмеченных HR."""
        # Настраиваем мок для candidate_notes.find
        marked_records = [
            {
                'candidate_id': 123456789,
                'hr_id': 987654321,
                'is_marked': True
            },
            {
                'candidate_id': 123456790,
                'hr_id': 987654321,
                'is_marked': True
            }
        ]
        self.db_mock.candidate_notes.find.return_value = marked_records
        
        # Настраиваем мок для get_user для второго кандидата
        user_data2 = {
            'user_id': 123456790,
            'first_name': 'Петр',
            'last_name': 'Петров',
            'occupation': 'Дизайнер',
            'level': 'senior',
            'company': 'ООО Дизайн Про',
            'is_candidate': True
        }
        
        # Настраиваем мок для get_candidate_notes
        notes1 = [
            {
                'note_id': 'note123',
                'candidate_id': 123456789,
                'hr_id': 987654321,
                'text': "Отличный кандидат",
                'rating': 5,
                'created_at': datetime.datetime.utcnow()
            }
        ]
        notes2 = [
            {
                'note_id': 'note456',
                'candidate_id': 123456790,
                'hr_id': 987654321,
                'text': "Хороший дизайнер",
                'rating': 4,
                'created_at': datetime.datetime.utcnow()
            }
        ]
        
        # Настраиваем мок для get_user, чтобы он возвращал разных пользователей
        self.db_mock.get_user.side_effect = lambda user_id: self.user_data if user_id == 123456789 else user_data2
        
        # Настраиваем мок для get_candidate_notes, чтобы он возвращал разные заметки
        self.db_mock.get_candidate_notes.side_effect = lambda candidate_id, hr_id: notes1 if candidate_id == 123456789 else notes2
        
        # Вызываем метод get_hr_candidates
        result = self.candidate_manager.get_hr_candidates(987654321)
        
        # Проверяем, что был вызван метод find с правильными параметрами
        self.db_mock.candidate_notes.find.assert_called_once()
        
        # Проверяем, что метод вернул правильные данные
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['candidate_id'], 123456789)
        self.assertEqual(result[0]['first_name'], 'Иван')
        self.assertEqual(result[0]['notes'], notes1)
        self.assertEqual(result[1]['candidate_id'], 123456790)
        self.assertEqual(result[1]['first_name'], 'Петр')
        self.assertEqual(result[1]['notes'], notes2)

if __name__ == '__main__':
    unittest.main()
