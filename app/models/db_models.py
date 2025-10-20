"""
SQLAlchemy database models
Based on the C# DbUser, DbAdvert, etc. classes
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ARRAY, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
from datetime import datetime
from typing import Optional, List

from app.schemas.api_schemas import FileModel, FilterModel, PartnerAdvertModel, RangeModel, SaveFilterRequest, SaveFirebaseTokenRequest, UserModel, UserRegisterRequest2, UserSaveDeviceInfoRequest, UserSettingsModel 
from app.exceptions.custom_exceptions import ApiException
from app.pg_data_acces import PgDataAccess
from app.schemas.api_schemas import UserRegisterRequest

class DbUser(Base):
    """Users table - obj_users"""
    __tablename__ = "obj_users"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    platform = Column(Integer, nullable=False)
    build_number = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    
    def ToApiModel(self):
        """Convert to API model"""
        ts_created = int(self.created_at.timestamp() * 1000) if self.created_at else None
        ts_updated = int(self.updated_at.timestamp() * 1000) if self.updated_at else None

        return UserModel(
            uniqueId=self.unique_id,
            platform=self.platform,
            createdAt=ts_created,
            buildNumber=self.build_number,
            updatedAt=ts_updated)
            
    @staticmethod
    async def Register(db: AsyncSession, model: UserRegisterRequest):
        """Register user"""
        user = await PgDataAccess.read_first_or_default(db, DbUser, "obj_users_register2",
            {"unique_id": uuid.uuid4(),
            "token": model.FirebaseToken,
            "platform": model.platform or 0,
            "build_number": model.buildNumber or 0}
        )

        if user is None:
            raise ApiException("There was an error while creating the user")

        await db.commit()
        return user

    @staticmethod
    async def Register2(db: AsyncSession, model: UserRegisterRequest2):
        """Register user"""
        user = await PgDataAccess.read_first_or_default(db, DbUser, "obj_users_register3",
            {"unique_id": uuid.uuid4(),
            "token": model.firebaseToken or "error",   
            "platform": model.platform or 0,
            "build_number": model.buildNumber or 0,
            "language_code": model.languageCode or "pl",
            "region_id": model.regionId or 0}
        )
        if user is None:
            raise ApiException("There was an error while creating the user")
        await db.commit()
        return user

    @staticmethod
    async def SaveDeviceInfo(db: AsyncSession, unique_id: UUID, model: UserSaveDeviceInfoRequest):
        """Save device info"""
        user = await PgDataAccess.read_first_or_default(db, DbUser, "obj_users_save_device_info",
            {"unique_id": unique_id,
            "platform": model.Platform or 0,
            "build_number": model.BuildNumber or 0}
        )
        if user is None:
            raise ApiException("There was an error while creating the user")

        await db.commit()
        return user

    @staticmethod
    async def GetUser(db: AsyncSession, unique_id: UUID):
        """Get user"""
        user = await PgDataAccess.read_first_or_default(db, DbUser, "obj_users_get", {"unique_id": unique_id})
        if user is None:
            raise ApiException("User not found")
        return user

class DbAdvert(Base):
    """Adverts table - obj_adverts"""
    __tablename__ = "obj_adverts"
    
    rn = Column(Integer)  # Row number for pagination
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, nullable=False)
    type_id = Column(Integer, nullable=False)
    url = Column(String, nullable=False)
    url_hash = Column(Integer, nullable=False)
    region_id = Column(Integer, nullable=False)
    region = Column(String, nullable=False)
    district = Column(String, nullable=False)
    title = Column(String, nullable=False)
    photos = Column(ARRAY(String))  # PostgreSQL array
    photo = Column(String)
    rooms = Column(Integer, nullable=False)
    area = Column(Numeric)
    price = Column(Numeric)
    currency_id = Column(Integer, nullable=False)
    ext_price = Column(String)
    agency = Column(Boolean, nullable=False, default=False)
    date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_to = Column(DateTime(timezone=True))


class DbUserSettings(Base):
    """User settings table - obj_users_settings"""
    __tablename__ = "obj_users_settings"
    
    user_id = Column(Integer, ForeignKey("obj_users.id"), primary_key=True)
    latest_view_advert_id = Column(Integer)
    is_notification_enabled = Column(Boolean, nullable=False, default=True)
    language_code = Column(String(10), nullable=False, default="pl")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # user = relationship("DbUser", back_populates="settings")
    
    def ToApiModel(self):
        """Convert to API model"""
        return UserSettingsModel(
            lastViewId=self.latest_view_advert_id,
            isNotificationEnabled=self.is_notification_enabled,
            languageCode=self.language_code)
    
    @staticmethod
    async def Save(db: AsyncSession, unique_id: UUID, model: UserSettingsModel):
        """Save user settings"""
        params = {
            "unique_id": unique_id,
            "latest_view_advert_id": model.lastViewId or None,
            "is_notification_enabled": model.isNotificationEnabled,
            "language_code": model.languageCode or "pl"
        }
        settings = await PgDataAccess.read_first_or_default(db, DbUserSettings, "obj_users_settings_update", params)
        if settings is None:
            raise ApiException("There was an error while saving the user settings")
        await db.commit()
        return settings
    
    @staticmethod
    async def Read(db: AsyncSession, unique_id: UUID):
        """Read user settings"""
        settings = await PgDataAccess.read_first_or_default(db, DbUserSettings, "obj_users_settings_read", {"unique_id": unique_id})
        if settings is None:
            raise ApiException("There was an error while reading the user settings")
        return settings

class DbFilter(Base):
    """User filters table - obj_users_filter"""
    __tablename__ = "obj_users_filter"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("obj_users.id"), nullable=False)
    country_id = Column(Integer, nullable=False)
    region_id = Column(Integer, nullable=False)
    districts = Column(ARRAY(Integer))  # PostgreSQL array
    types = Column(ARRAY(Integer))  # PostgreSQL array
    rooms = Column(ARRAY(Integer))  # PostgreSQL array
    agency = Column(Boolean, nullable=False, default=False)
    area_from = Column(Integer, nullable=False, default=0)
    area_to = Column(Integer, nullable=False, default=2147483647)  # int.MaxValue
    price_from = Column(Integer, nullable=False, default=0)
    price_to = Column(Integer, nullable=False, default=2147483647)  # int.MaxValue
    
    # Relationships
    # user = relationship("DbUser", back_populates="filters")
    
    def ToApiModel(self):
        """Convert to API model"""
        return FilterModel(
            CountryId=self.country_id,
            RegionId=self.region_id,
            Districts=self.districts,
            Types=self.types,
            Rooms=self.rooms,
            Agency=self.agency,
            Area=RangeModel(from_=self.area_from, to=self.area_to),
            Price=RangeModel(from_=self.price_from, to=self.price_to))
            

    @staticmethod
    async def Save(db: AsyncSession, unique_id: UUID, model: SaveFilterRequest):
        """Save filter"""
        filter = await PgDataAccess.read_mapping_first_or_default(db, "obj_users_filter_save2",
            {"unique_id": unique_id,
            "country_id": model.CountryId,
            "region_id": model.RegionId,
            "districts": model.Districts or [],
            "types": model.Types or [],
            "rooms": model.Rooms or [],
            "agency": model.Agency,
            "area_from": model.Area.from_ if model.Area and model.Area.from_ is not None else 0,
            "area_to":   model.Area.to   if model.Area and model.Area.to   is not None else 2147483647,
            "price_from": model.Price.from_ if model.Price and model.Price.from_ is not None else 0,
            "price_to":   model.Price.to   if model.Price and model.Price.to   is not None else 2147483647}
            

            # "area_from": model.Area is not null a model.Area.From is not null && model.Area.From > 0 ? model.Area.From : 0,
            # "area_to": model.Area is not null && model.Area.To is not null && model.Area.To > 0 ? model.Area.To : int.MaxValue,
            # "price_from": model.Price is not null && model.Price.From is not null && model.Price.From > 0 ? model.Price.From : 0,
            # "price_to": model.Price is not null && model.Price.To is not null && model.Price.To > 0 ? model.Price.To : int.MaxValue
        )
        
        if filter is None:
            raise ApiException("There was an error while saving the filter")
        await db.commit()

        return filter

    @staticmethod
    async def Read(db: AsyncSession, unique_id: UUID):
        """Read filter"""
        row = await PgDataAccess.read_mapping_first_or_default(
    db, "obj_users_filter_get", {"unique_id": unique_id}
)
        if row is None:
            raise ApiException("There was an error while reading the filter")

        filter_model = FilterModel(
        CountryId=row["country_id"],
        RegionId=row["region_id"],
        Districts=row.get("districts") or [],
        Types=row.get("types") or [],
        Rooms=row.get("rooms") or [],
        Agency=row["agency"],
        Area=RangeModel(from_=row["area_from"], to=row["area_to"]),
        Price=RangeModel(from_=row["price_from"], to=row["price_to"]))
        return filter_model

class DbFirebaseToken(Base):
    """Firebase tokens table - obj_firebase_tokens"""
    __tablename__ = "obj_firebase_tokens"
    


    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("obj_users.id"), nullable=False)
    token = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # user = relationship("DbUser", back_populates="firebase_tokens")

    @staticmethod
    async def Save(db: AsyncSession, unique_id: UUID, model: SaveFirebaseTokenRequest):
        """Save firebase token"""
        firebase_token = await PgDataAccess.read_first_or_default(db, DbFirebaseToken, "obj_firebase_tokens_add",
            {"unique_id": unique_id,
            "token": model.token}
        )
        if firebase_token is None:
            raise ApiException("There was an error while add new user token")
        await db.commit()
        return firebase_token


class DbSmsCode(Base):
    """SMS codes table - obj_sms_codes"""
    __tablename__ = "obj_sms_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, nullable=False)
    phone_provider_id = Column(Integer, nullable=False)
    partner_advert_id = Column(Integer)
    sms_code = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("obj_users.id"), nullable=False)
    check_count = Column(Integer, nullable=False, default=0)
    checked_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    #  user = relationship("DbUser", back_populates="sms_codes")


class DbFile(Base):
    """Files table - obj_files"""
    __tablename__ = "obj_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    base64 = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Boolean, nullable=False, default=True)

    def toApiModel(self):
        return FileModel(
            id= self.id,
            name= self.name,
            type= self.type,
            base64= self.base64,
            created_at=self.created_at)
    
    @staticmethod
    async def ReadList(db: AsyncSession, ids: List[UUID]):
        """Read files list"""
        return await PgDataAccess.read_list(db, DbFile, "obj_files_load", {"ids": ids})



class DbPartnerAdvert(Base):
    """Partner adverts table - obj_partner_adverts"""
    __tablename__ = "obj_partner_adverts"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, nullable=False)
    partner_name = Column(String, nullable=False)
    partner_type_id = Column(Integer, nullable=False)
    banner_id = Column(UUID(as_uuid=True), nullable=False)
    region_id = Column(Integer, nullable=False)
    endpoint = Column(String, nullable=False)
    meta = Column(JSON)  # JSONB in PostgreSQL
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Boolean, nullable=False, default=True)

    def toApiModel(self):
        return PartnerAdvertModel(
            id=self.id,
            partner_id=self.partner_id,
            partner_name=self.partner_name,
            banner_id=self.banner_id,
            region_id=self.region_id,
            endpoint=self.endpoint,
            meta=self.meta,
            created_at=self.created_at)

    @staticmethod
    async def ReadList(db: AsyncSession, unique_id: UUID):
        """Read partner adverts list"""
        return await PgDataAccess.read_list(db, DbPartnerAdvert, "obj_partner_adverts_load2", {"unique_id": unique_id})

class DbDistrict(Base):
    """Districts table - dic_region_districts"""
    __tablename__ = "dic_region_districts"
    
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    names = Column(ARRAY(String))  # PostgreSQL array for multilingual names
    status = Column(Boolean, nullable=False, default=True)

    @staticmethod
    async def ReadList(db: AsyncSession):
        """Read districts list"""
        districts = await PgDataAccess.read_list(db, DbDistrict, "dic_region_districts_load") 
        return districts


class DbRegion(Base):
    """Regions table - dic_regions"""
    __tablename__ = "dic_regions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    names = Column(ARRAY(String))  # PostgreSQL array for multilingual names
    status = Column(Boolean, nullable=False, default=True)

    @staticmethod
    async def ReadList(db: AsyncSession) -> List:
        """Read regions list"""
        regions = await PgDataAccess.read_list(db, DbRegion, "dic_regions_load")
        return regions


class DbPartner(Base):
    """Partners table - dic_partners"""
    __tablename__ = "dic_partners"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    site_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Boolean, nullable=False, default=True)


class DbPartnerType(Base):
    """Partner types table - dic_partner_types"""
    __tablename__ = "dic_partner_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


class DbPhoneVerificationProvider(Base):
    """Phone verification providers table - dic_phone_verification_providers"""
    __tablename__ = "dic_phone_verification_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    system_name = Column(String, nullable=False)
    count_digits = Column(Integer, nullable=False)
    status = Column(Boolean, nullable=False, default=True)


class DbPhoneVerificationProviderCountry(Base):
    """Phone verification provider countries table - obj_phone_verification_provider_countries"""
    __tablename__ = "obj_phone_verification_provider_countries"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_provider_id = Column(Integer, nullable=False)
    country_id = Column(Integer, nullable=False)
    status = Column(Boolean, nullable=False, default=True)
