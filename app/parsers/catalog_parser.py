import pandas as pd
import re
from typing import List, Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CatalogParser:
    def __init__(self, catalog_path: str):
        self.catalog_path = catalog_path
        self.products = []
    
    def parse(self) -> List[Dict]:
        try:
            excel_file = pd.ExcelFile(self.catalog_path)
            all_products = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(self.catalog_path, sheet_name=sheet_name)
                
                for idx, row in df.iterrows():
                    if pd.isna(row.iloc[0]):
                        continue
                    
                    name = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else ""
                    if not name or name == "nan" or len(name) < 3:
                        continue
                    
                    characteristics = ""
                    if len(row) > 2 and not pd.isna(row.iloc[2]):
                        characteristics += str(row.iloc[2])
                    if len(row) > 3 and not pd.isna(row.iloc[3]):
                        characteristics += " " + str(row.iloc[3])
                    
                    power = self._extract_power(characteristics)
                    color_temp = self._extract_color_temp(characteristics)
                    luminous_flux = self._extract_luminous_flux(characteristics)
                    dimensions = self._extract_dimensions(characteristics)
                    
                    product = {
                        'name': name,
                        'power_watt': power,
                        'color_temp_kelvin': color_temp,
                        'luminous_flux_lm': luminous_flux,
                        'length_mm': dimensions.get('length'),
                        'width_mm': dimensions.get('width'),
                        'height_mm': dimensions.get('height'),
                        'full_characteristics': characteristics[:1000],
                        'sheet_name': sheet_name
                    }
                    all_products.append(product)
            
            self.products = all_products
            logger.info(f"Loaded {len(all_products)} products from catalog")
            return all_products
        except FileNotFoundError:
            logger.error(f"Catalog file not found: {self.catalog_path}")
            return []
        except Exception as e:
            logger.error(f"Failed to parse catalog: {e}")
            return []
    
    def _extract_power(self, text: str) -> Optional[float]:
        patterns = [
            r'Мощность:\s*(\d+(?:\.\d+)?)\s*Вт',
            r'мощность\D*(\d+(?:\.\d+)?)\s*вт',
            r'(\d+(?:\.\d+)?)\s*[Вв]т'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_color_temp(self, text: str) -> Optional[int]:
        patterns = [
            r'Цветовая температура[^:]*:\s*(\d+)\s*К',
            r'температура[^:]*:\s*(\d+)\s*К',
            r'(\d+)\s*К\b'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None
    
    def _extract_luminous_flux(self, text: str) -> Optional[int]:
        patterns = [
            r'Световой поток[^:]*:\s*(\d+(?:[.,]\d+)?)\s*лм',
            r'(\d+(?:[.,]\d+)?)\s*лм'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(float(match.group(1).replace(',', '.')))
        return None
    
    def _extract_dimensions(self, text: str) -> dict:
        dimensions = {'length': None, 'width': None, 'height': None}
        
        patterns = [
            r'габарит[ыа]\D*(\d+(?:[.,]\d+)?)\D*(\d+(?:[.,]\d+)?)\D*(\d+(?:[.,]\d+)?)',
            r'размер[ы]\D*(\d+(?:[.,]\d+)?)\D*(\d+(?:[.,]\d+)?)\D*(\d+(?:[.,]\d+)?)',
            r'(\d+(?:[.,]\d+)?)\s*[хx*]\s*(\d+(?:[.,]\d+)?)\s*[хx*]\s*(\d+(?:[.,]\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dimensions['length'] = float(match.group(1).replace(',', '.'))
                dimensions['width'] = float(match.group(2).replace(',', '.'))
                dimensions['height'] = float(match.group(3).replace(',', '.'))
                break
        
        return dimensions