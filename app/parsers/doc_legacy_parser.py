"""
Специальный парсер для старых .doc файлов
"""

import re
import struct
import logging
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocLegacyParser:
    """Парсер для старых .doc файлов с поврежденной кодировкой"""
    
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """Извлечение текста из бинарного .doc файла"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            text_parts = []
            
            # Способ 1: Поиск русских текстовых блоков
            russian_blocks = DocLegacyParser._find_russian_text_blocks(data)
            if russian_blocks:
                text_parts.extend(russian_blocks)
            
            # Способ 2: Поиск таблиц в бинарных данных
            table_text = DocLegacyParser._extract_tables_from_binary(data)
            if table_text:
                text_parts.append(table_text)
            
            # Способ 3: Декодирование как cp1251
            try:
                decoded = data.decode('cp1251', errors='replace')
                # Очищаем от нечитаемых символов
                decoded = re.sub(r'[^\x20-\x7E\x80-\xFF\n\r\t]', ' ', decoded)
                decoded = re.sub(r'\s+', ' ', decoded)
                if len(decoded) > 100:
                    text_parts.append(decoded)
            except:
                pass
            
            if text_parts:
                result = '\n'.join(text_parts)
                # Очищаем результат
                result = re.sub(r'[^\w\s\.\,\-\:\;\?\*\(\)\[\]\{\}\<\>\/\\\|\"\'\`\~\@\#\$\%\^\&\=\+\n\r\tа-яА-Я]', ' ', result)
                result = re.sub(r'\s+', ' ', result)
                logger.info(f"Extracted {len(result)} characters from legacy .doc")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse legacy .doc: {e}")
            return None
    
    @staticmethod
    def _find_russian_text_blocks(data: bytes) -> List[str]:
        """Поиск блоков с русским текстом в бинарных данных"""
        blocks = []
        
        # Ищем последовательности байт, которые могут быть русским текстом
        i = 0
        current_block = []
        
        while i < len(data):
            byte = data[i]
            
            # Диапазоны для русских букв в CP1251
            # А-Я: 192-223, а-я: 224-255
            is_russian = (192 <= byte <= 255)
            is_latin = (65 <= byte <= 90) or (97 <= byte <= 122)
            is_digit = (48 <= byte <= 57)
            is_space = (byte == 32)
            is_punctuation = byte in (46, 44, 59, 58, 33, 63, 40, 41, 45, 95)
            
            if is_russian or is_latin or is_digit or is_space or is_punctuation:
                current_block.append(byte)
            else:
                if len(current_block) > 20:  # Минимальная длина блока
                    try:
                        block_bytes = bytes(current_block)
                        # Пробуем декодировать
                        for encoding in ['cp1251', 'utf-8', 'cp866', 'koi8-r']:
                            try:
                                text = block_bytes.decode(encoding, errors='ignore')
                                # Проверяем, есть ли русские буквы
                                if re.search(r'[а-яА-Я]', text):
                                    # Очищаем блок
                                    text = re.sub(r'[^\w\s\.\,\-\:\;\?\(\)]', ' ', text)
                                    text = re.sub(r'\s+', ' ', text)
                                    if len(text) > 30:
                                        blocks.append(text)
                                        break
                            except:
                                continue
                    except:
                        pass
                current_block = []
            
            i += 1
        
        return blocks
    
    @staticmethod
    def _extract_tables_from_binary(data: bytes) -> Optional[str]:
        """Извлечение таблиц из бинарных данных"""
        table_lines = []
        
        # Ищем паттерны таблиц (последовательности байт с разделителями)
        lines = data.split(b'\r\n')
        
        for line in lines:
            if len(line) < 20:
                continue
            
            # Проверяем, есть ли в строке признаки таблицы
            has_pipe = b'|' in line
            has_tab = b'\t' in line
            has_spaces = line.count(b' ') > 3
            
            if has_pipe or has_tab or has_spaces:
                try:
                    decoded = line.decode('cp1251', errors='ignore')
                    # Очищаем
                    decoded = re.sub(r'[^\w\s\.\,\-\:\|\t]', ' ', decoded)
                    decoded = re.sub(r'\s+', ' ', decoded)
                    if len(decoded) > 10:
                        table_lines.append(decoded)
                except:
                    continue
        
        if table_lines:
            return '\n'.join(table_lines)
        return None


class DocParser:
    """Основной парсер документов Word (DOCX и DOC)"""
    
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """Извлечение текста из DOCX или DOC файла"""
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.docx':
            return DocParser._extract_from_docx(file_path)
        elif file_ext == '.doc':
            # Пробуем разные методы
            text = DocParser._extract_from_doc(file_path)
            if not text or len(text) < 100:
                # Используем специальный парсер для легаси .doc
                text = DocLegacyParser.extract_text(file_path)
            return text
        else:
            logger.warning(f"Unsupported format: {file_ext}")
            return None
    
    @staticmethod
    def _extract_from_docx(file_path: str) -> Optional[str]:
        """Извлечение текста из DOCX"""
        import zipfile
        import xml.etree.ElementTree as ET
        
        try:
            text_parts = []
            
            with zipfile.ZipFile(file_path, 'r') as docx_zip:
                if 'word/document.xml' in docx_zip.namelist():
                    xml_content = docx_zip.read('word/document.xml')
                    root = ET.fromstring(xml_content)
                    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    
                    for para in root.findall('.//w:p', namespaces):
                        para_text = []
                        for text in para.findall('.//w:t', namespaces):
                            if text.text:
                                para_text.append(text.text)
                        if para_text:
                            text_parts.append(' '.join(para_text))
                    
                    for table in root.findall('.//w:tbl', namespaces):
                        for row in table.findall('.//w:tr', namespaces):
                            row_text = []
                            for cell in row.findall('.//w:tc', namespaces):
                                cell_text = []
                                for text in cell.findall('.//w:t', namespaces):
                                    if text.text:
                                        cell_text.append(text.text)
                                if cell_text:
                                    row_text.append(' '.join(cell_text))
                            if row_text:
                                text_parts.append(' | '.join(row_text))
            
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {e}")
            return None
    
    @staticmethod
    def _extract_from_doc(file_path: str) -> Optional[str]:
        """Извлечение текста из .doc через внешние утилиты"""
        import subprocess
        
        # Попытка через antiword
        try:
            result = subprocess.run(
                ['antiword', '-f', file_path],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                text = result.stdout.decode('cp1251', errors='replace')
                if len(text) > 100:
                    logger.info("Extracted text using antiword")
                    return text
        except:
            pass
        
        # Попытка через catdoc
        try:
            result = subprocess.run(
                ['catdoc', '-s', 'cp1251', file_path],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                text = result.stdout.decode('cp1251', errors='replace')
                if len(text) > 100:
                    logger.info("Extracted text using catdoc")
                    return text
        except:
            pass
        
        return None


# Импорт os для работы с путями
import os