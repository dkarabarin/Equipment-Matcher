from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductMatcher:
    def __init__(self, catalog_products: List[Dict], max_deviation: float = 20.0):
        self.catalog = catalog_products
        self.max_deviation = max_deviation
    
    def match(self, requirement: Dict) -> Dict:
        candidates = []
        
        for product in self.catalog:
            score, deviations = self._calculate_score(requirement, product)
            if score > 0:
                candidates.append((score, deviations, product))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        if not candidates:
            return {
                'product_name': requirement.get('name', ''),
                'required_quantity': requirement.get('quantity', 1),
                'required_characteristics': requirement.get('raw_characteristics', ''),
                'matched_product_name': None,
                'matched_characteristics': None,
                'comment': "❌ Аналогов в каталоге не найдено",
                'match_score': 0,
                'deviations': {}
            }
        
        best_score, deviations, best_product = candidates[0]
        comment = self._build_comment(best_product, requirement, deviations, best_score)
        
        return {
            'product_name': requirement.get('name', ''),
            'required_quantity': requirement.get('quantity', 1),
            'required_characteristics': requirement.get('raw_characteristics', ''),
            'matched_product_name': best_product.get('name'),
            'matched_characteristics': best_product.get('full_characteristics', ''),
            'comment': comment,
            'match_score': best_score,
            'deviations': deviations
        }
    
    def _calculate_score(self, req: Dict, cat: Dict) -> Tuple[float, Dict]:
        deviations = {}
        scores = []
        
        if req.get('power_watt') and cat.get('power_watt'):
            deviation = abs(req['power_watt'] - cat['power_watt']) / req['power_watt'] * 100
            deviations['power'] = f"требуется {req['power_watt']}Вт, в каталоге {cat['power_watt']}Вт (отклонение {deviation:.1f}%)"
            score = max(0, 100 - deviation) * 0.4
            scores.append(score)
        
        if req.get('color_temp_kelvin') and cat.get('color_temp_kelvin'):
            deviation = abs(req['color_temp_kelvin'] - cat['color_temp_kelvin']) / req['color_temp_kelvin'] * 100
            deviations['color_temp'] = f"требуется {req['color_temp_kelvin']}К, в каталоге {cat['color_temp_kelvin']}К (отклонение {deviation:.1f}%)"
            score = max(0, 100 - deviation) * 0.3
            scores.append(score)
        
        if req.get('luminous_flux_lm') and cat.get('luminous_flux_lm'):
            deviation = abs(req['luminous_flux_lm'] - cat['luminous_flux_lm']) / req['luminous_flux_lm'] * 100
            deviations['luminous_flux'] = f"требуется {req['luminous_flux_lm']}лм, в каталоге {cat['luminous_flux_lm']}лм (отклонение {deviation:.1f}%)"
            score = max(0, 100 - deviation) * 0.3
            scores.append(score)
        
        total_score = sum(scores) if scores else 0
        return total_score, deviations
    
    def _build_comment(self, product: Dict, req: Dict, deviations: Dict, score: float) -> str:
        if score >= 80:
            title = f"✅ ХОРОШЕЕ СООТВЕТСТВИЕ (score: {score:.0f}%)"
        elif score >= 60:
            title = f"⚠️ БЛИЗКИЙ АНАЛОГ (score: {score:.0f}%)"
        elif score >= 40:
            title = f"⚠️ ЧАСТИЧНОЕ СООТВЕТСТВИЕ (score: {score:.0f}%)"
        else:
            title = f"❌ СЛАБОЕ СООТВЕТСТВИЕ (score: {score:.0f}%)"
        
        comment = f"{title}\n\nНайденный аналог: {product.get('name', '')}\n"
        
        if deviations:
            comment += "\nСравнение параметров:\n"
            for key, dev in deviations.items():
                comment += f"  • {dev}\n"
        
        return comment