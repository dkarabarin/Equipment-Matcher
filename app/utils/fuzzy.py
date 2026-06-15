"""
Fuzzy matching для сравнения названий и характеристик
"""

from thefuzz import fuzz, process
from typing import List, Tuple, Optional
import re

class FuzzyMatcher:
    """Класс для нечеткого сравнения строк"""
    
    @staticmethod
    def match_name(query: str, candidates: List[str], threshold: int = 70) -> List[Tuple[str, int]]:
        """
        Поиск похожих названий
        threshold: минимальный процент совпадения
        """
        if not query or not candidates:
            return []
        
        # Очищаем строки для сравнения
        query_clean = FuzzyMatcher._normalize_name(query)
        candidates_clean = [FuzzyMatcher._normalize_name(c) for c in candidates]
        
        # Ищем лучшие совпадения
        results = process.extract(query_clean, candidates_clean, scorer=fuzz.token_sort_ratio, limit=5)
        
        # Фильтруем по порогу и возвращаем оригинальные названия
        matches = []
        for candidate_clean, score in results:
            if score >= threshold:
                # Находим оригинальное название
                for orig, clean in zip(candidates, candidates_clean):
                    if clean == candidate_clean:
                        matches.append((orig, score))
                        break
        
        return matches
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """Нормализация названия для сравнения"""
        # Приводим к нижнему регистру
        name = name.lower()
        
        # Удаляем специальные символы
        name = re.sub(r'[^\w\s]', ' ', name)
        
        # Удаляем лишние пробелы
        name = ' '.join(name.split())
        
        return name
    
    @staticmethod
    def compare_characteristics(req: dict, catalog: dict) -> float:
        """
        Сравнение характеристик и возврат процента совпадения
        """
        scores = []
        weights = {
            'power_watt': 0.3,
            'color_temp_kelvin': 0.2,
            'luminous_flux_lm': 0.3,
            'dimensions': 0.2
        }
        
        # Сравнение мощности
        if req.get('power_watt') and catalog.get('power_watt'):
            power_dev = abs(req['power_watt'] - catalog['power_watt']) / req['power_watt']
            power_score = max(0, 100 - power_dev * 100)
            scores.append(power_score * weights['power_watt'])
        
        # Сравнение цветовой температуры
        if req.get('color_temp_kelvin') and catalog.get('color_temp_kelvin'):
            temp_dev = abs(req['color_temp_kelvin'] - catalog['color_temp_kelvin']) / req['color_temp_kelvin']
            temp_score = max(0, 100 - temp_dev * 100)
            scores.append(temp_score * weights['color_temp_kelvin'])
        
        # Сравнение светового потока
        if req.get('luminous_flux_lm') and catalog.get('luminous_flux_lm'):
            flux_dev = abs(req['luminous_flux_lm'] - catalog['luminous_flux_lm']) / req['luminous_flux_lm']
            flux_score = max(0, 100 - flux_dev * 100)
            scores.append(flux_score * weights['luminous_flux_lm'])
        
        # Сравнение размеров
        dimensions_score = FuzzyMatcher._compare_dimensions(req, catalog)
        scores.append(dimensions_score * weights['dimensions'])
        
        return sum(scores) if scores else 0
    
    @staticmethod
    def _compare_dimensions(req: dict, catalog: dict) -> float:
        """Сравнение размеров"""
        scores = []
        
        # Сравниваем каждый доступный размер
        for dim in ['length_mm', 'width_mm', 'height_mm']:
            if req.get(dim) and catalog.get(dim):
                deviation = abs(req[dim] - catalog[dim]) / req[dim]
                score = max(0, 100 - deviation * 100)
                scores.append(score)
        
        if scores:
            return sum(scores) / len(scores)
        return 50  # Если нет данных о размерах, даем среднюю оценку
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Удаляем стоп-слова
        stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'из', 'для', 'от', 'до', 'не', 'да', 'нет', 'или', 'при'}
        
        # Разбиваем на слова
        words = re.findall(r'\b[а-яa-z0-9]+\b', text.lower())
        
        # Фильтруем стоп-слова и короткие слова
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return list(set(keywords))  # Уникальные ключевые слова
    
    @staticmethod
    def keyword_match_score(text1: str, text2: str) -> float:
        """Оценка совпадения по ключевым словам"""
        keywords1 = set(FuzzyMatcher.extract_keywords(text1))
        keywords2 = set(FuzzyMatcher.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0
        
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) * 100