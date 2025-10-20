"""
External listings service for integration with new real estate API
"""

import asyncio
from uuid import UUID
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from sqlalchemy import false
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.exceptions.custom_exceptions import ApiException
from app.schemas.api_schemas import FilterModel, LoadAdvertsDirection, ReadAdvertsRequest, AdvertModel
from app.services.district_mapping_service import DistrictMappingService
from app.models.db_models import DbRegion
from app.pg_data_acces import PgDataAccess
from enum import Enum


logger = logging.getLogger(__name__)

class BuildingType(str, Enum):
    BLOCK = "BLOCK"
    APARTMENT_BUILDING = "APARTMENT_BUILDING"
    TENEMENT = "TENEMENT"
    HOUSE = "HOUSE"
    INFILL = "INFILL"
    RIBBON = "RIBBON"
    LOFT = "LOFT"
    WOLNOSTOJACY = "WOLNOSTOJACY"
    OTHER = "OTHER"

class ExternalListingsService:
    """Service for external listings API integration"""
    
    def __init__(self, db: AsyncSession):
        self.base_url = settings.external_listings_url
        self.endpoint = settings.external_listings_endpoint
        self.timeout = settings.external_listings_timeout
        # Mapping dictionaries
        self.source_mapping = {
            "olx": 1,
            "otodom": 2,
            "gratka": 5,
            "domiporta": 4,
            "morizon": 3,
            "gumtree": 6
        }
        
        self.type_mapping = {
            "RENT": 1,
            "SALE": 2
        }
        self.db = db
        self.district_mapper = DistrictMappingService(db)

      
        self.building_types = {1: "Room", 2: "Apartment", 3: "House"}

        self.building_type_mapping = {
            BuildingType.BLOCK: 2,            # "BLOCK" -> "Apartment"
            BuildingType.APARTMENT_BUILDING: 2,
            BuildingType.TENEMENT: 3,
            BuildingType.HOUSE: 3,
            BuildingType.INFILL: 2,
            BuildingType.RIBBON: 2,
            BuildingType.LOFT: 2,
            BuildingType.WOLNOSTOJACY: 3,
            BuildingType.OTHER: 2,            # fallback
        }

        self.reverse_building_type_mapping = {
            1: [ # room
                BuildingType.OTHER
            ],
            2: [ # apartment
                BuildingType.BLOCK,
                BuildingType.APARTMENT_BUILDING,
                BuildingType.INFILL,
                BuildingType.RIBBON,
                BuildingType.LOFT
            ],
            3: [ # house
                BuildingType.TENEMENT,
                BuildingType.HOUSE,
                BuildingType.WOLNOSTOJACY
            ]
        }

        
    

    async def get_missed(        
        self, 
        filter_model: FilterModel, 
        pagination: ReadAdvertsRequest,
        user_guid: UUID
    ) -> Dict[str, Any]:
        try:            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params_missed = await self._build_query_params_missed(filter_model, pagination, user_guid)
                try:
                    resp = await client.get(f"{self.base_url}/api/v1/listings/new/count", params=params_missed)

                    if resp.status_code == 200:
                        data = resp.json()
                        total = data.get("total", 0)
                    else:
                        logger.warning(f"External API returned {resp.status_code} for {resp.request.url}")
                        total = 0
                except Exception as e:
                    logger.error(f"Request failed for params {params_missed}: {e}")
                    total = 0

            return total

        except httpx.TimeoutException:
            logger.error("External listings API timeout")
            raise ApiException("External listings API timeout")
        except Exception as e:
            logger.error(f"Unexpected error in external listings service: {e}")
            raise ApiException("Internal error in listings service")
    
    async def get_listings(
        self, 
        filter_model: FilterModel, 
        pagination: ReadAdvertsRequest,
        user_guid: UUID
    ) -> Dict[str, Any]:

        try:
            params_pagination = await self._build_query_params_pagination(filter_model, pagination, user_guid)
            
            data = None
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    resp = await client.get(f"{self.base_url}{self.endpoint}", params=params_pagination)

                    if resp.status_code == 200:
                        data = resp.json()
                        results = data.get("items", [])
                    else:
                        logger.warning(f"External API returned {resp.status_code} for {resp.request.url}")
                        results = []
                except Exception as e:
                    logger.error(f"Request failed for params {params_pagination}: {e}")
                    results = []

            return results

        except httpx.TimeoutException:
            logger.error("External listings API timeout")
            raise ApiException("External listings API timeout")
        except Exception as e:
            logger.error(f"Unexpected error in external listings service: {e}")
            raise ApiException("Internal error in listings service")

    
    async def _build_query_filters(
        self, filter_model: FilterModel, pagination: ReadAdvertsRequest, user_guid: UUID
        ) -> List[Dict[str, Any]]:

         # === filters ===
        params: Dict[str, Any] = {}
        
        params["offer_type"] = "RENT"

        if filter_model.Types:
            params["building_type"] = [
                bt.value
                for t in filter_model.Types
                if t in self.reverse_building_type_mapping
                for bt in self.reverse_building_type_mapping[t]
            ]
        print(params["building_type"])
        # price
        if filter_model.Price:
            if filter_model.Price.from_ is not None:
                params["min_price"] = filter_model.Price.from_
            if filter_model.Price.to is not None:
                params["max_price"] = filter_model.Price.to
      
        if filter_model.Area:
            if filter_model.Area.from_ is not None:
                params["min_area"] = filter_model.Area.from_
            if filter_model.Area.to is not None:
                params["max_area"] = filter_model.Area.to

        # rooms count (list)
        if filter_model.Rooms and len(filter_model.Rooms) > 0:
            params["rooms"] = filter_model.Rooms

        # Agency mapping
        if filter_model.Agency is not None and filter_model.Agency is True:
            params["is_business"] = False

        # districts (list)
        if filter_model.Districts and len(filter_model.Districts) > 0:
            district_names = await self.district_mapper.get_district_names(filter_model.Districts)
            if district_names:
                params["district"] = district_names

        
        if filter_model.RegionId:
            regions = await DbRegion.ReadList(self.db)
            for reg in regions:
                if reg.id == filter_model.RegionId:
                    region_name = reg.names[-1]
                    # base_params["region"] = [region_name]
                    params["city"] = [region_name.capitalize()]
                    
                    break

        return params

    async def _build_query_params_missed(
        self, filter_model: FilterModel, pagination: ReadAdvertsRequest, user_guid: UUID
        ) -> List[Dict[str, Any]]: 

        params: Dict[str, Any] = await self._build_query_filters(filter_model, pagination, user_guid)

        if pagination.LastViewId:
            params["id"] = pagination.LastViewId
        
        return params


    async def _build_query_params_pagination(
        self, filter_model: FilterModel, pagination: ReadAdvertsRequest, user_guid: UUID
    ) -> List[Dict[str, Any]]:
        """
        returns a dict of parameters for request listings to the external API.
        """

        params: Dict[str, Any] = await self._build_query_filters(filter_model, pagination, user_guid)

        # === pagination ===
        params["limit"] = 10
        
        if pagination.AdvertId:
            params["direction"] = "after" if pagination.Direction == LoadAdvertsDirection.Prev else "before"
            params["id"] = pagination.AdvertId
        elif pagination.Direction == LoadAdvertsDirection.Latest:
            params["direction"] = "latest"
           
        return params
    

    
    def map_listing_to_advert(self, listing: Dict[str, Any]) -> AdvertModel:
        """Map external listing to our AdvertModel format"""
        try:
            # Extract photos
            photos = [listing.get("photos_urls", [])[0]] if listing.get("photos_urls") else []
            
            # Convert timestamps
            created_time = self._parse_datetime(listing.get("created_time"))
            valid_to_time = self._parse_datetime(listing.get("valid_to_time"))
            parsed_at = self._parse_datetime(listing.get("parsed_at"))
            # Map source to sourceId
            source = listing.get("source", "unknown")
            source_id = self.source_mapping.get(source, 0)
            
            # Map offer_type to typeId
            offer_type = listing.get("offer_type", "RENT")
            type_id = self.type_mapping.get(offer_type, 1)
            
            return AdvertModel(
                id=listing.get("id", 0),
                sourceId=source_id,
                typeId=type_id,
                url=listing.get("url", ""),
                regionId=listing.get("region_id", 0),
                region= listing.get("city", "") or listing.get("region", ""),
                district=listing.get("district", "") or "",
                title=listing.get("title", ""),
                photos=photos,
                rooms=listing.get("rooms", 0),
                area=listing.get("area_m2"),
                price=listing.get("price"),
                currency=listing.get("currency_code", "zl"),
                extPrice=None,  # Not available in new API
                agency=listing.get("is_business", True),
                date=int(parsed_at.timestamp() * 1000),
                createdAt=int(created_time.timestamp() * 1000),
                validTo=int(valid_to_time.timestamp() * 1000) if valid_to_time else int(created_time.timestamp() * 1000)
            )
            
        except Exception as e:
            logger.error(f"Error mapping listing to advert: {e}")
            return None
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> datetime:
        """Parse datetime string to datetime object"""
        if not datetime_str:
            return datetime.utcnow()
        
        try:
            # Try different datetime formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            logger.warning(f"Could not parse datetime: {datetime_str}")
            return datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error parsing datetime {datetime_str}: {e}")
            return datetime.utcnow()
    
    async def get_listings_mapped(
        self, 
        filter_model: FilterModel, 
        pagination: ReadAdvertsRequest,
        user_guid: UUID
    ) -> List[AdvertModel]:
        """
        Get listings and map them to AdvertModel format
        """
        try:
            # Get raw listings from external API
            listings = await self.get_listings(filter_model, pagination, user_guid)

            # Map each listing to AdvertModel
            mapped_adverts = []
            for listing in listings:
                advert = self.map_listing_to_advert(listing)
                if advert is not None:
                    mapped_adverts.append(advert)
            
            return mapped_adverts
            
        except Exception as e:
            logger.error(f"Error getting mapped listings: {e}")
            # Return empty list on error
            return []
