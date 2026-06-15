import pdfplumber
import PyPDF2
from typing import Optional
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFParser:
    """Парсер PDF документов с поддержкой таблиц"""
    
    @staticmethod
    def extract_text(file_path: str, method: str = 'pdfplumber') -> Optional[str]:
        """
        Извлечение текста из PDF
        method: 'pdfplumber' (лучше для таблиц) или 'pypdf2' (быстрее)
        """
        
        if method == 'pdfplumber':
            return PDFParser._extract_with_pdfplumber(file_path)
        else:
            return PDFParser._extract_with_pypdf2(file_path)
    
    @staticmethod
    def _extract_with_pdfplumber(file_path: str) -> Optional[str]:
        """Извлечение текста с помощью pdfplumber (лучше сохраняет структуру)"""
        try:
            all_text = []
            all_tables = []
            
            with pdfplumber.open(file_path) as pdf:
                logger.info(f"Processing PDF with {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Извлекаем текст
                    text = page.extract_text()
                    if text:
                        all_text.append(f"--- Page {page_num} ---\n{text}")
                    
                    # Извлекаем таблицы
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            table_text = []
                            for row in table:
                                clean_row = [str(cell).strip() if cell else '' for cell in row]
                                if any(clean_row):
                                    table_text.append(' | '.join(clean_row))
                            if table_text:
                                all_tables.append(table_text)
                                all_text.append("\n".join(table_text))
            
            full_text = '\n'.join(all_text)
            logger.info(f"Extracted {len(full_text)} characters from PDF using pdfplumber, found {len(all_tables)} tables")
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to extract text with pdfplumber: {e}")
            return None
    
    @staticmethod
    def _extract_with_pypdf2(file_path: str) -> Optional[str]:
        """Извлечение текста с помощью PyPDF2 (быстрее, но хуже качество)"""
        try:
            all_text = []
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                logger.info(f"Processing PDF with {len(reader.pages)} pages")
                
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        all_text.append(f"--- Page {page_num} ---\n{text}")
            
            full_text = '\n'.join(all_text)
            logger.info(f"Extracted {len(full_text)} characters from PDF using PyPDF2")
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to extract text with PyPDF2: {e}")
            return None
    
    @staticmethod
    def extract_tables(file_path: str) -> list:
        """Извлечение таблиц из PDF"""
        tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table and len(table) > 1:
                            clean_table = []
                            for row in table:
                                clean_row = [str(cell).strip() if cell else '' for cell in row]
                                if any(clean_row):
                                    clean_table.append(clean_row)
                            if clean_table:
                                tables.append({
                                    'page': page_num,
                                    'data': clean_table
                                })
            
            logger.info(f"Extracted {len(tables)} tables from PDF")
            
        except Exception as e:
            logger.error(f"Failed to extract tables from PDF: {e}")
        
        return tables
    
    @staticmethod
    def extract_metadata(file_path: str) -> dict:
        """Извлечение метаданных PDF"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata
                return {
                    'title': metadata.get('/Title', '') if metadata else '',
                    'author': metadata.get('/Author', '') if metadata else '',
                    'subject': metadata.get('/Subject', '') if metadata else '',
                    'creator': metadata.get('/Creator', '') if metadata else '',
                    'producer': metadata.get('/Producer', '') if metadata else '',
                    'pages': len(reader.pages)
                }
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            return {}