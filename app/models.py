from pydantic import BaseModel
from typing import Optional, List, Dict

class ProductCharacteristics(BaseModel):
    name: str
    quantity: int
    power_watt: Optional[float] = None
    color_temp_kelvin: Optional[int] = None
    luminous_flux_lm: Optional[int] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    ip_rating: Optional[str] = None
    raw_description: str = ""
    raw_characteristics: str = ""

class CatalogProduct(BaseModel):
    name: str
    power_watt: Optional[float] = None
    color_temp_kelvin: Optional[int] = None
    luminous_flux_lm: Optional[int] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    full_characteristics: str
    sheet_name: str = ""

class MatchResult(BaseModel):
    product_name: str
    required_quantity: int
    required_characteristics: str
    matched_product_name: Optional[str] = None
    matched_characteristics: Optional[str] = None
    comment: str
    match_score: float
    deviations: Dict[str, str] = {}