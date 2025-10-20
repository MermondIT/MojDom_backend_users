"""
District mapping service for converting district IDs to names
"""

from ast import Tuple
from typing import Dict, List, Optional
from sqlalchemy import distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db_models import DbDistrict
import logging

from app.schemas.api_schemas import DistrictModel
from app.pg_data_acces import PgDataAccess

logger = logging.getLogger(__name__)


class DistrictMappingService:
    """Service for mapping district IDs to names"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._district_cache: Dict[int, str] = {}
        self._cache_loaded = False
        self._api_models: List[DistrictModel] = []


    async def get_distincts_api_models(self):
        if not self._cache_loaded:
            await self._load_district_cache()
        
        return self._api_models
    
    async def get_district_name(self, district_id: int) -> Optional[str]:
        """Get district name by ID"""
        if not self._cache_loaded:
            await self._load_district_cache()
        
        return self._district_cache.get(district_id)
    
    async def get_district_names(self, district_ids: List[int]) -> List[str]:
        """Get district names by IDs"""
        if not self._cache_loaded:
            await self._load_district_cache()
        
        names = []
        for district_id in district_ids:
            name = self._district_cache.get(district_id)
            if name:
                names.append(name)
        
        return names
    
    async def _load_district_cache(self):
        """Load district mapping from database"""
        try:
            districts = await PgDataAccess.read_list(self.db, DbDistrict, "dic_region_districts_load")
            district_models = []
            for district in districts:
                self._district_cache[district.id] = district.name
                district_model = DistrictModel(id=district.id, name=district.name, regionId=district.region_id)
                district_models.append(district_model)
            
            self._api_models = district_models
            self._cache_loaded = True
            logger.info(f"Loaded {len(self._district_cache)} districts into cache")
            
        except Exception as e:
            logger.error(f"Error loading district cache: {e}")
            self._cache_loaded = True  # Mark as loaded to avoid repeated attempts
    
    async def refresh_cache(self):
        """Refresh district cache"""
        self._cache_loaded = False
        self._district_cache.clear()
        await self._load_district_cache()
