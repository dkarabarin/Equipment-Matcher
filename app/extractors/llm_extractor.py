import aiohttp
import json
import re
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMExtractor:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.ollama_url = ollama_url
        self.model = model
        self.use_llm = True
    
    async def extract_products(self, text: str) -> List[Dict]:
        """Извлечение позиций из текста с помощью Ollama"""
        
        # Если текст слишком длинный, обрезаем
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        prompt = self._build_prompt(text)
        
        try:
            response = await self._call_ollama(prompt)
            products = self._parse_response(response)
            
            if products:
                logger.info(f"LLM extracted {len(products)} products")
                return products
            else:
                logger.warning("LLM returned no products, falling back to regex")
                from .regex_extractor import RegexExtractor
                return RegexExtractor.extract_products(text)
                
        except Exception as e:
            logger.error(f"Ollama extraction failed: {e}, falling back to regex")
            from .regex_extractor import RegexExtractor
            return RegexExtractor.extract_products(text)
    
    def _build_prompt(self, text: str) -> str:
        """Построение промпта для Ollama"""
        return f"""Ты - специалист по извлечению данных из документов о закупках светотехнического оборудования.

Извлеки из текста все позиции, связанные со светильниками, прожекторами, опорами освещения.

Для каждой позиции определи:
1. Наименование товара
2. Количество (штуки)
3. Мощность в Вт
4. Цветовая температура в К
5. Световой поток в лм

Верни ответ ТОЛЬКО в формате JSON без лишнего текста:
{{
  "products": [
    {{
      "name": "название товара",
      "quantity": число,
      "power_watt": число или null,
      "color_temp_kelvin": число или null,
      "luminous_flux_lm": число или null,
      "raw_characteristics": "краткое описание характеристик"
    }}
  ]
}}

Текст документа:
{text}

Извлеки ВСЕ позиции. Если параметр не указан, поставь null.
Важно: верни ТОЛЬКО JSON, без пояснений."""
    
    async def _call_ollama(self, prompt: str) -> str:
        """Вызов Ollama API"""
        timeout = aiohttp.ClientTimeout(total=120)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 4096,
                    "top_p": 0.9
                }
            }
            
            logger.info(f"Calling Ollama with model: {self.model}")
            
            async with session.post(f"{self.ollama_url}/api/generate", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    response_text = result.get("response", "")
                    logger.info(f"Ollama response length: {len(response_text)}")
                    return response_text
                else:
                    error_text = await resp.text()
                    raise Exception(f"Ollama API error {resp.status}: {error_text}")
    
    def _parse_response(self, response: str) -> List[Dict]:
        """Парсинг JSON ответа Ollama"""
        try:
            # Находим JSON в ответе
            json_match = re.search(r'\{[^{}]*"products"\s*:\s*\[.*?\][^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                products = data.get("products", [])
                
                # Валидация и очистка
                for product in products:
                    if not product.get("name"):
                        product["name"] = "Неизвестный светильник"
                    if not product.get("quantity"):
                        product["quantity"] = 1
                    if product.get("power_watt") == "":
                        product["power_watt"] = None
                    if product.get("color_temp_kelvin") == "":
                        product["color_temp_kelvin"] = None
                    if product.get("luminous_flux_lm") == "":
                        product["luminous_flux_lm"] = None
                
                return products
            
            # Если не нашли JSON, пробуем найти список
            list_match = re.search(r'"products"\s*:\s*(\[.*?\])', response, re.DOTALL)
            if list_match:
                products_list = json.loads(list_match.group(1))
                return products_list
            
            logger.warning(f"Could not parse JSON from Ollama response")
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response as JSON: {e}")
            logger.debug(f"Response: {response[:500]}")
            return []
    
    async def check_ollama_health(self) -> bool:
        """Проверка доступности Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = data.get("models", [])
                        available_models = [m.get("name", "") for m in models]
                        logger.info(f"Available Ollama models: {available_models}")
                        
                        # Проверяем, есть ли нужная модель
                        model_available = any(self.model in m for m in available_models)
                        if not model_available:
                            logger.warning(f"Model {self.model} not found. Available: {available_models}")
                        return True
                    return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False