import zipfile
import xml.etree.ElementTree as ET
from typing import Optional
import logging
import os
import subprocess
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocParser:
    """Парсер документов Word (DOCX и DOC)"""
    
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """Извлечение текста из DOCX или DOC файла"""
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.docx':
            return DocParser._extract_from_docx(file_path)
        elif file_ext == '.doc':
            return DocParser._extract_from_doc(file_path)
        else:
            logger.warning(f"Unsupported format: {file_ext}")
            return None
    
    @staticmethod
    def _extract_from_docx(file_path: str) -> Optional[str]:
        """Извлечение текста из DOCX"""
        try:
            text_parts = []
            tables_data = []
            
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
                        table_data = []
                        for row in table.findall('.//w:tr', namespaces):
                            row_data = []
                            for cell in row.findall('.//w:tc', namespaces):
                                cell_text = []
                                for text in cell.findall('.//w:t', namespaces):
                                    if text.text:
                                        cell_text.append(text.text)
                                if cell_text:
                                    row_data.append(' '.join(cell_text))
                            if row_data:
                                table_data.append(row_data)
                        if table_data:
                            tables_data.append(table_data)
                            for row in table_data:
                                text_parts.append(' | '.join(row))
            
            result = '\n'.join(text_parts)
            logger.info(f"Extracted {len(result)} characters from DOCX, found {len(tables_data)} tables")
            return result
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {e}")
            return None
    
    @staticmethod
    def _extract_from_doc(file_path: str) -> Optional[str]:
        """Извлечение текста из старого формата .doc с правильной кодировкой"""
        
        # Способ 1: Использование antiword (лучший для .doc)
        antiword_paths = [
            'antiword',
            'C:\\antiword\\antiword.exe',
            'C:\\Program Files\\antiword\\antiword.exe',
            'C:\\Program Files (x86)\\antiword\\antiword.exe'
        ]
        
        for antiword in antiword_paths:
            try:
                result = subprocess.run(
                    [antiword, '-f', file_path],  # -f для форматированного вывода
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0 and result.stdout:
                    # Декодируем в cp1251 для русских символов
                    text = result.stdout.decode('cp1251', errors='replace')
                    if len(text) > 100:
                        logger.info(f"Extracted text using antiword from {file_path}")
                        return text
            except (subprocess.SubprocessError, FileNotFoundError, UnicodeDecodeError):
                continue
        
        # Способ 2: Использование catdoc
        catdoc_paths = ['catdoc', 'C:\\catdoc\\catdoc.exe']
        for catdoc in catdoc_paths:
            try:
                result = subprocess.run(
                    [catdoc, '-s', 'cp1251', file_path],  # -s задает кодировку
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0 and result.stdout:
                    text = result.stdout.decode('cp1251', errors='replace')
                    if len(text) > 100:
                        logger.info(f"Extracted text using catdoc from {file_path}")
                        return text
            except (subprocess.SubprocessError, FileNotFoundError, UnicodeDecodeError):
                continue
        
        # Способ 3: Чтение через olefile (для .doc файлов)
        try:
            import olefile
            if olefile.isOleFile(file_path):
                ole = olefile.OleFileIO(file_path)
                
                # Пробуем извлечь текст из разных потоков
                text_parts = []
                
                # Основной поток WordDocument
                if ole.exists('WordDocument'):
                    data = ole.openstream('WordDocument').read()
                    # Пробуем разные кодировки
                    for encoding in ['cp1251', 'utf-8', 'cp866', 'koi8-r']:
                        try:
                            text = data.decode(encoding, errors='ignore')
                            # Очищаем от бинарных символов
                            text = re.sub(r'[^\x20-\x7F\x80-\xFF\n\r\t]', ' ', text)
                            text = re.sub(r'\s+', ' ', text)
                            if len(text) > 100:
                                text_parts.append(text)
                                break
                        except:
                            continue
                
                # Поток SummaryInformation (может содержать метаданные)
                if ole.exists('\x05SummaryInformation'):
                    data = ole.openstream('\x05SummaryInformation').read()
                    for encoding in ['cp1251', 'utf-16-le', 'utf-8']:
                        try:
                            text = data.decode(encoding, errors='ignore')
                            if len(text) > 50:
                                text_parts.append(text)
                                break
                        except:
                            continue
                
                ole.close()
                
                if text_parts:
                    result = '\n'.join(text_parts)
                    logger.info(f"Extracted {len(result)} characters using olefile")
                    return result
        except ImportError:
            logger.debug("olefile not installed")
        except Exception as e:
            logger.error(f"olefile error: {e}")
        
        # Способ 4: Чтение как бинарного файла с поиском текста
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
                # Ищем текстовые блоки (последовательности читаемых символов)
                text_blocks = []
                current_block = []
                
                for byte in content:
                    # Проверяем, является ли байт читаемым символом
                    if 32 <= byte <= 126 or 192 <= byte <= 255:  # ASCII + русские буквы в CP1251
                        current_block.append(byte)
                    else:
                        if len(current_block) > 10:  # Минимальная длина блока
                            try:
                                # Пробуем декодировать блок в разных кодировках
                                block_bytes = bytes(current_block)
                                for encoding in ['cp1251', 'utf-8', 'cp866']:
                                    try:
                                        text = block_bytes.decode(encoding, errors='ignore')
                                        if re.search(r'[а-яА-Я]', text):  # Есть русские буквы
                                            text_blocks.append(text)
                                            break
                                    except:
                                        continue
                            except:
                                pass
                        current_block = []
                
                if text_blocks:
                    result = '\n'.join(text_blocks)
                    logger.info(f"Extracted {len(result)} characters using binary search")
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to read .doc file as binary: {e}")
        
        logger.warning(f"Could not extract text from .doc file: {file_path}")
        return None
    
    @staticmethod
    def extract_tables(file_path: str) -> list:
        """Извлечение таблиц из документа"""
        tables = []
        
        try:
            if file_path.endswith('.docx'):
                with zipfile.ZipFile(file_path, 'r') as docx_zip:
                    if 'word/document.xml' in docx_zip.namelist():
                        xml_content = docx_zip.read('word/document.xml')
                        root = ET.fromstring(xml_content)
                        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                        
                        for table in root.findall('.//w:tbl', namespaces):
                            table_data = []
                            for row in table.findall('.//w:tr', namespaces):
                                row_data = []
                                for cell in row.findall('.//w:tc', namespaces):
                                    cell_text = []
                                    for text in cell.findall('.//w:t', namespaces):
                                        if text.text:
                                            cell_text.append(text.text)
                                    row_data.append(' '.join(cell_text))
                                if row_data:
                                    table_data.append(row_data)
                            if table_data:
                                tables.append(table_data)
            
            logger.info(f"Extracted {len(tables)} tables from document")
        except Exception as e:
            logger.error(f"Failed to extract tables: {e}")
        
        return tables