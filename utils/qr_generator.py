#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для генерации и обработки QR-кодов.
Обеспечивает создание QR-кодов для пользователей и стендов, а также их декодирование.
"""

import os
import qrcode
from PIL import Image
from typing import Optional
import uuid
from pyzbar.pyzbar import decode

class QRGenerator:
    """Класс для генерации и обработки QR-кодов."""
    
    def __init__(self):
        """Инициализация генератора QR-кодов."""
        # Создаем директорию для хранения QR-кодов, если её нет
        os.makedirs('data/qr_codes', exist_ok=True)
    
    def generate_user_qr(self, user_id: int) -> str:
        """Генерирует QR-код для пользователя."""
        # Создаем QR-код с ID пользователя
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(user_id))
        qr.make(fit=True)
        
        # Создаем изображение QR-кода
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем изображение
        file_path = f"data/qr_codes/user_{user_id}.png"
        img.save(file_path)
        
        return file_path
    
    def generate_stand_qr(self, stand_id: str) -> str:
        """Генерирует QR-код для стенда."""
        # Создаем QR-код с ID стенда
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(stand_id)
        qr.make(fit=True)
        
        # Создаем изображение QR-кода
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем изображение
        file_path = f"data/qr_codes/stand_{stand_id}.png"
        img.save(file_path)
        
        return file_path
    
    def generate_merch_qr(self, merch_id: str) -> str:
        """Генерирует QR-код для мерча."""
        # Создаем QR-код с ID мерча
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"merch:{merch_id}")
        qr.make(fit=True)
        
        # Создаем изображение QR-кода
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем изображение
        file_path = f"data/qr_codes/merch_{merch_id}.png"
        img.save(file_path)
        
        return file_path
    
    def generate_event_qr(self, event_id: str) -> str:
        """Генерирует QR-код для события."""
        # Создаем QR-код с ID события
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"event:{event_id}")
        qr.make(fit=True)
        
        # Создаем изображение QR-кода
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем изображение
        file_path = f"data/qr_codes/event_{event_id}.png"
        img.save(file_path)
        
        return file_path
    
    def decode_qr(self, image_path: str) -> Optional[str]:
        """Декодирует QR-код из изображения."""
        try:
            # Открываем изображение
            img = Image.open(image_path)
            
            # Декодируем QR-код
            decoded_objects = decode(img)
            
            if decoded_objects:
                # Возвращаем данные из первого найденного QR-кода
                return decoded_objects[0].data.decode('utf-8')
            
            return None
        except Exception as e:
            print(f"Error decoding QR code: {e}")
            return None
    
    def generate_custom_qr(self, data: str, file_name: str = None) -> str:
        """Генерирует QR-код с произвольными данными."""
        # Создаем QR-код с указанными данными
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Создаем изображение QR-кода
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Генерируем имя файла, если не указано
        if not file_name:
            file_name = f"custom_{uuid.uuid4().hex[:8]}.png"
        
        # Сохраняем изображение
        file_path = f"data/qr_codes/{file_name}"
        img.save(file_path)
        
        return file_path
