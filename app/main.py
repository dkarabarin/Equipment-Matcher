from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import uuid
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lighting Equipment Matcher")

# Создание необходимых папок
Path("uploads").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

from app.parsers import DocParser, PDFParser, CatalogParser
from app.extractors import LLMExtractor
from app.matcher import ProductMatcher
from app.config import Config

# Загрузка каталога
CATALOG_PATH = Config.CATALOG_PATH
catalog_products = []

if os.path.exists(CATALOG_PATH):
    catalog_parser = CatalogParser(CATALOG_PATH)
    catalog_products = catalog_parser.parse()
    logger.info(f"Loaded {len(catalog_products)} products from catalog")
else:
    logger.warning(f"Catalog not found at {CATALOG_PATH}")

# Инициализация LLM экстрактора
llm_extractor = LLMExtractor(
    ollama_url=Config.OLLAMA_BASE_URL,
    model=Config.OLLAMA_MODEL
)


@app.on_event("startup")
async def startup_event():
    """Проверка Ollama при старте"""
    if Config.USE_LLM:
        is_healthy = await llm_extractor.check_ollama_health()
        if is_healthy:
            logger.info(f"Ollama is available with model: {Config.OLLAMA_MODEL}")
        else:
            logger.warning("Ollama is not available. Will use regex extractor.")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lighting Equipment Matcher</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 900px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 20px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 { 
                color: #333; 
                text-align: center; 
                margin-bottom: 10px;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
            }
            .warning {
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                display: none;
            }
            .warning.show {
                display: block;
            }
            .warning-title {
                color: #856404;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .warning-text {
                color: #856404;
                font-size: 14px;
            }
            .format-badge {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                margin: 0 3px;
            }
            .format-badge.bad {
                background: #dc3545;
            }
            form { 
                border: 2px dashed #ccc; 
                padding: 30px; 
                border-radius: 15px; 
                text-align: center;
                background: #f9f9f9;
                transition: all 0.3s ease;
            }
            form:hover {
                border-color: #667eea;
                background: #f5f5f5;
            }
            input[type="file"] { 
                margin: 20px 0; 
                padding: 10px;
                font-size: 16px;
            }
            button { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                padding: 12px 30px; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 16px;
                font-weight: bold;
                transition: transform 0.2s;
            }
            button:hover { 
                transform: scale(1.02);
                cursor: pointer;
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .status { 
                margin-top: 20px; 
                padding: 12px; 
                border-radius: 8px; 
                text-align: center; 
                display: none;
            }
            .footer { 
                text-align: center; 
                margin-top: 30px; 
                color: #999; 
                font-size: 12px;
            }
            .badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                margin-left: 10px;
            }
            .badge-llm { background: #28a745; color: white; }
            .badge-regex { background: #ffc107; color: #333; }
            .features {
                display: flex;
                justify-content: center;
                gap: 15px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            .feature {
                background: #f0f0f0;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
            }
            hr {
                margin: 20px 0;
                border: none;
                border-top: 1px solid #eee;
            }
            .recommendation {
                background: #e7f3ff;
                border-radius: 10px;
                padding: 15px;
                margin-top: 20px;
                font-size: 13px;
                color: #004085;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Lighting Equipment Matcher</h1>
            <div class="subtitle">Автоматический подбор аналогов светотехнического оборудования</div>
            
            <div class="features">
                <span class="feature">📄 DOC</span>
                <span class="feature">📝 DOCX</span>
                <span class="feature">📑 PDF</span>
                <span class="feature">🤖 LLM (Ollama)</span>
            </div>
            
            <div id="warning" class="warning">
                <div class="warning-title">⚠️ Внимание: Проблемы с .doc файлами</div>
                <div class="warning-text">
                    Файлы в старом формате .doc могут иметь проблемы с кодировкой.<br>
                    <strong>Рекомендация:</strong> Откройте файл в Microsoft Word и сохраните как .docx или .pdf для лучшего результата.
                </div>
            </div>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="fileInput" name="file" accept=".docx,.doc,.pdf" required>
                <br>
                <button type="submit" id="submitBtn">🔍 Начать подбор</button>
            </form>
            
            <div id="status" class="status"></div>
            
            <div class="recommendation">
                <strong>💡 Рекомендации для лучшего результата:</strong><br>
                • Для .doc файлов: сохраните как .docx в Microsoft Word<br>
                • Убедитесь, что файл содержит технические характеристики<br>
                • Поддерживаемые форматы: DOCX, PDF (рекомендуются), DOC (может работать некорректно)
            </div>
            
            <hr>
            
            <div class="footer">
                <strong>Поддерживаемые форматы:</strong> 
                <span class="format-badge">DOCX</span>
                <span class="format-badge">PDF</span>
                <span class="format-badge bad">DOC (ограниченно)</span><br>
                <strong>Статус LLM:</strong> <span id="llmStatus" class="badge">Проверка...</span>
            </div>
        </div>
        
        <script>
            // Проверка статуса LLM
            fetch('/ollama/status')
                .then(res => res.json())
                .then(data => {
                    const badge = document.getElementById('llmStatus');
                    if (data.available) {
                        badge.textContent = '✓ LLM доступен (' + data.model + ')';
                        badge.className = 'badge badge-llm';
                    } else {
                        badge.textContent = '⚠ LLM недоступен, используется regex';
                        badge.className = 'badge badge-regex';
                    }
                })
                .catch(() => {
                    const badge = document.getElementById('llmStatus');
                    badge.textContent = '⚠ LLM недоступен';
                    badge.className = 'badge badge-regex';
                });
            
            // Проверка типа файла
            const fileInput = document.getElementById('fileInput');
            const warningDiv = document.getElementById('warning');
            const submitBtn = document.getElementById('submitBtn');
            
            fileInput.addEventListener('change', function() {
                const file = this.files[0];
                if (file && file.name.toLowerCase().endsWith('.doc')) {
                    warningDiv.classList.add('show');
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🔍 Начать подбор (возможны проблемы с кодировкой)';
                } else {
                    warningDiv.classList.remove('show');
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🔍 Начать подбор';
                }
            });
            
            // Обработка отправки формы
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const statusDiv = document.getElementById('status');
                const submitBtn = document.getElementById('submitBtn');
                
                statusDiv.style.display = 'block';
                statusDiv.style.background = '#fff3cd';
                statusDiv.style.color = '#856404';
                statusDiv.textContent = '⏳ Обработка файла... Это может занять до 30 секунд.';
                submitBtn.disabled = true;
                submitBtn.textContent = '⏳ Обработка...';
                
                try {
                    const response = await fetch('/match', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'result.xlsx';
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);
                        
                        statusDiv.style.background = '#d4edda';
                        statusDiv.style.color = '#155724';
                        statusDiv.textContent = '✅ Файл успешно обработан! Скачивание началось.';
                    } else {
                        const error = await response.json();
                        throw new Error(error.detail || 'Ошибка обработки');
                    }
                } catch (error) {
                    statusDiv.style.background = '#f8d7da';
                    statusDiv.style.color = '#721c24';
                    statusDiv.textContent = '❌ Ошибка: ' + error.message;
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🔍 Начать подбор';
                    setTimeout(() => {
                        statusDiv.style.display = 'none';
                    }, 5000);
                }
            };
        </script>
    </body>
    </html>
    """


@app.get("/ollama/status")
async def ollama_status():
    """Проверка статуса Ollama"""
    is_healthy = await llm_extractor.check_ollama_health()
    return {
        "available": is_healthy,
        "model": Config.OLLAMA_MODEL if is_healthy else None,
        "url": Config.OLLAMA_BASE_URL
    }


@app.post("/match")
async def match_products(file: UploadFile = File(...)):
    """Обработка загруженного файла и подбор соответствий"""
    try:
        file_ext = Path(file.filename).suffix.lower()
        file_id = str(uuid.uuid4())
        file_path = Path("uploads") / f"{file_id}{file_ext}"
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Processing file: {file.filename} with extension: {file_ext}")
        
        # Извлечение текста в зависимости от формата
        text = None
        
        if file_ext == '.docx':
            text = DocParser.extract_text(str(file_path))
        elif file_ext == '.pdf':
            text = PDFParser.extract_text(str(file_path))
        elif file_ext == '.doc':
            # Для .doc файлов показываем предупреждение и пробуем извлечь
            text = DocParser.extract_text(str(file_path))
            if not text or len(text) < 100:
                # Если не удалось извлечь, возвращаем ошибку с рекомендацией
                file_path.unlink()
                raise HTTPException(
                    400, 
                    "Не удалось извлечь текст из .doc файла. "
                    "Рекомендуем: 1) Открыть файл в Microsoft Word, "
                    "2) Сохранить как .docx или .pdf, "
                    "3) Загрузить заново."
                )
        else:
            raise HTTPException(400, f"Unsupported file format: {file_ext}. Please upload DOC, DOCX or PDF")
        
        if not text:
            file_path.unlink()
            raise HTTPException(400, "Could not extract text from file. Please check file format.")
        
        logger.info(f"Extracted {len(text)} characters from file")
        
        # Извлечение позиций через LLM или regex
        extracted_products = await llm_extractor.extract_products(text)
        
        if not extracted_products:
            extracted_products = [{
                'name': Path(file.filename).stem,
                'quantity': 1,
                'power_watt': None,
                'color_temp_kelvin': None,
                'luminous_flux_lm': None,
                'raw_characteristics': text[:500]
            }]
        
        logger.info(f"Extracted {len(extracted_products)} products")
        
        # Матчинг
        matcher = ProductMatcher(catalog_products if catalog_products else [], Config.MAX_DEVIATION_PERCENT)
        results = []
        
        for prod in extracted_products:
            result = matcher.match(prod)
            results.append(result)
            logger.info(f"Matched '{prod.get('name', '')[:50]}' with score: {result['match_score']:.0f}%")
        
        # Создание Excel
        data = []
        for i, r in enumerate(results, 1):
            data.append({
                "№": i,
                "Наименование": r['product_name'][:200] if r['product_name'] else "Неизвестно",
                "Кол-во": r['required_quantity'],
                "Характеристики": r['required_characteristics'][:500] if r['required_characteristics'] else "",
                "Наименование товара из каталога": r['matched_product_name'][:200] if r['matched_product_name'] else "Не найден",
                "Характеристики товара из каталога": (r['matched_characteristics'][:500] if r['matched_characteristics'] else ""),
                "Комментарий": r['comment'][:1000] if r['comment'] else ""
            })
        
        df = pd.DataFrame(data)
        output_path = Path("outputs") / f"{file_id}_result.xlsx"
        df.to_excel(output_path, index=False)
        
        # Очистка временного файла
        file_path.unlink()
        
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="result.xlsx"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}")
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(500, str(e))


@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {
        "status": "ok",
        "catalog_loaded": len(catalog_products) > 0,
        "catalog_count": len(catalog_products),
        "ollama_available": await llm_extractor.check_ollama_health()
    }