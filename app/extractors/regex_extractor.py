import re
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegexExtractor:
    @staticmethod
    def extract_products(text: str) -> List[Dict]:
        products = []
        
        patterns = [
            r'(?:№?\s*\d+[\.)]?\s*)?([^\n]{10,150}?(?:светильник|прожектор|светодиодный)[^\n]{0,200})',
            r'(\d+)\s*[xх]\s*(\d+)\s*(?:штук|шт\.?|штуки)',
        ]
        
        lines = text.split('\n')
        current_product = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if any(word in line.lower() for word in ['светильник', 'прожектор', 'светодиодный']):
                if current_product:
                    products.append(current_product)
                
                power = RegexExtractor._extract_power(line)
                color_temp = RegexExtractor._extract_color_temp(line)
                quantity = RegexExtractor._extract_quantity(line)
                
                current_product = {
                    'name': line[:150],
                    'quantity': quantity if quantity else 1,
                    'power_watt': power,
                    'color_temp_kelvin': color_temp,
                    'luminous_flux_lm': RegexExtractor._extract_luminous_flux(line),
                    'raw_characteristics': line
                }
            elif current_product:
                current_product['raw_characteristics'] += " " + line
                
                if not current_product['power_watt']:
                    current_product['power_watt'] = RegexExtractor._extract_power(line)
                if not current_product['color_temp_kelvin']:
                    current_product['color_temp_kelvin'] = RegexExtractor._extract_color_temp(line)
        
        if current_product:
            products.append(current_product)
        
        if not products:
            products.append({
                'name': 'Светильник из технического задания',
                'quantity': 1,
                'power_watt': None,
                'color_temp_kelvin': None,
                'luminous_flux_lm': None,
                'raw_characteristics': text[:500]
            })
        
        logger.info(f"Extracted {len(products)} products using regex")
        return products
    
    @staticmethod
    def _extract_power(text: str) -> float:
        patterns = [r'мощность\D*(\d+(?:[.,]\d+)?)\s*[Вв]т', r'(\d+(?:[.,]\d+)?)\s*[Вв]т']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', '.'))
        return None
    
    @staticmethod
    def _extract_color_temp(text: str) -> int:
        patterns = [r'температур[аы]\D*(\d+)\s*[Кк]', r'(\d+)\s*К\b']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None
    
    @staticmethod
    def _extract_luminous_flux(text: str) -> int:
        match = re.search(r'световой\s+поток\D*(\d+(?:[.,]\d+)?)\s*лм', text, re.IGNORECASE)
        if match:
            return int(float(match.group(1).replace(',', '.')))
        return None
    
    @staticmethod
    def _extract_quantity(text: str) -> int:
        patterns = [
            r'количество\D*(\d+)\s*шт',
            r'кол-во\D*(\d+)\s*шт',
            r'(\d+)\s*штук',
            r'(\d+)\s*шт\.?'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 1