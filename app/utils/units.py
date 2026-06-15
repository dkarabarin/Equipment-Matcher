"""
Конвертация единиц измерения для приведения к единому формату
"""

import re
from typing import Optional, Tuple

class UnitConverter:
    """Конвертер единиц измерения"""
    
    # Константы для перевода
    MM_TO_M = 0.001
    CM_TO_MM = 10
    M_TO_MM = 1000
    INCH_TO_MM = 25.4
    
    W_TO_KW = 0.001
    KW_TO_W = 1000
    
    LM_TO_KLN = 0.001
    KLN_TO_LM = 1000
    
    C_TO_K = 273.15
    F_TO_C = lambda f: (f - 32) * 5/9
    F_TO_K = lambda f: (f - 32) * 5/9 + 273.15
    
    @classmethod
    def normalize_length(cls, value: float, unit: str) -> float:
        """Нормализация длины в миллиметры"""
        unit = unit.lower().strip()
        
        if unit in ['мм', 'mm', 'millimeter', 'миллиметр']:
            return value
        elif unit in ['см', 'cm', 'centimeter', 'сантиметр']:
            return value * cls.CM_TO_MM
        elif unit in ['м', 'm', 'meter', 'метр']:
            return value * cls.M_TO_MM
        elif unit in ['дюйм', 'inch', 'in', '"']:
            return value * cls.INCH_TO_MM
        else:
            # Если единица не указана, предполагаем, что значение в мм
            return value
    
    @classmethod
    def normalize_power(cls, value: float, unit: str) -> float:
        """Нормализация мощности в ватты"""
        unit = unit.lower().strip()
        
        if unit in ['вт', 'w', 'watt', 'ватт']:
            return value
        elif unit in ['квт', 'kw', 'kilowatt', 'киловатт']:
            return value * cls.KW_TO_W
        else:
            return value
    
    @classmethod
    def normalize_temperature(cls, value: float, unit: str) -> float:
        """Нормализация температуры в Кельвины"""
        unit = unit.lower().strip()
        
        if unit in ['к', 'k', 'kelvin', 'кельвин']:
            return value
        elif unit in ['°c', 'c', 'celsius', 'градус цельсия', 'град']:
            return value + cls.C_TO_K
        elif unit in ['°f', 'f', 'fahrenheit', 'фарингейт']:
            return cls.F_TO_K(value)
        else:
            # Предполагаем, что это Кельвины
            return value
    
    @classmethod
    def normalize_luminous_flux(cls, value: float, unit: str) -> float:
        """Нормализация светового потока в люмены"""
        unit = unit.lower().strip()
        
        if unit in ['лм', 'lm', 'lumen', 'люмен']:
            return value
        elif unit in ['клм', 'klm', 'kilolumen', 'килолюмен']:
            return value * cls.KLN_TO_LM
        else:
            return value
    
    @classmethod
    def parse_dimension_string(cls, dim_str: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Парсинг строки с размерами формата '500x200x100' или '500*200*100'"""
        
        # Ищем паттерн с разделителями x, *, х
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*[хx*]\s*(\d+(?:[.,]\d+)?)\s*[хx*]\s*(\d+(?:[.,]\d+)?)',
            r'(\d+(?:[.,]\d+)?)\s*[хx*]\s*(\d+(?:[.,]\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, dim_str, re.IGNORECASE)
            if match:
                groups = match.groups()
                length = float(groups[0].replace(',', '.'))
                width = float(groups[1].replace(',', '.'))
                height = float(groups[2].replace(',', '.')) if len(groups) > 2 else None
                return length, width, height
        
        return None, None, None
    
    @classmethod
    def parse_power_string(cls, power_str: str) -> Optional[float]:
        """Парсинг строки с мощностью '40Вт', '40 W', '0.04kW'"""
        
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*[Вв]т',
            r'(\d+(?:[.,]\d+)?)\s*w',
            r'(\d+(?:[.,]\d+)?)\s*квт',
            r'(\d+(?:[.,]\d+)?)\s*kw',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, power_str, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', '.'))
                # Определяем единицу
                if 'квт' in power_str.lower() or 'kw' in power_str.lower():
                    return cls.normalize_power(value, 'kw')
                else:
                    return cls.normalize_power(value, 'w')
        
        return None