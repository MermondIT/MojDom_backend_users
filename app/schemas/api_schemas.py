"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any, Union
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import app.exceptions.custom_exceptions as exceptions
from enum import IntEnum

class LoadAdvertsDirection(IntEnum):
    """Load adverts direction"""
    Prev = 1
    Next = 2
    Latest = 3


# Base response models
class ApiResponse(BaseModel):
    """Base API response model"""
    data: Optional[Any] = None
    statusCode: int = 200
    statusMessage: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))
    


class SuccessApiResponse(ApiResponse):
    """Success response without data"""
    data: Optional[Any] = None


class PingResponse(ApiResponse):
    """Ping response with timestamp"""
    data: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))


# User models
class UserModel(BaseModel):
    """User model for API responses"""
    
    uniqueId: UUID
    platform: int
    buildNumber: int
    createdAt: Optional[int] = None
    updatedAt: Optional[int] = None


class UserRegisterRequest(BaseModel):
    """User registration request"""
    FirebaseToken: str
    platform: Optional[int] = None
    buildNumber: Optional[int] = None


    def ThrowIfInvalid(self):
        """Throw exception if request is invalid"""
        if not self.FirebaseToken or self.FirebaseToken == "error":
            raise exceptions.ValidationRequiredParameter("Invalid Firebase token")

    
    class Config:
        json_schema_extra = {
            "example": {
                "FirebaseToken": "772ce730-9bb6-11f0-81d8-e190ec038244",
                "platform": 1,
                "buildNumber": 100
            }
        }


class UserRegisterRequest2(BaseModel):
    """Extended user registration request"""
    firebaseToken: str
    platform: int
    buildNumber: int
    languageCode: str
    regionId: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "firebaseToken": "firebase_token_here",
                "platform": 1,
                "buildNumber": 100,
                "languageCode": "pl",
                "regionId": 1
            }
        }

    def ThrowIfInvalid(self):
        """Throw exception if request is invalid"""
        if not self.FirebaseToken or self.FirebaseToken == "error":
            raise exceptions.ValidationRequiredParameter("Invalid Firebase token")
        if not self.Platform:
            raise exceptions.ValidationRequiredParameter("Platform is required")
        if not self.BuildNumber:
            raise exceptions.ValidationRequiredParameter("Build number is required")        
        if not self.LanguageCode:
            raise exceptions.ValidationRequiredParameter("Language code is required")
        if not self.RegionId:
            raise exceptions.ValidationRequiredParameter("Region ID is required")   

class UserSaveDeviceInfoRequest(BaseModel):
    """Save device info request"""
    Platform: int
    BuildNumber: int

    def ThrowIfInvalid(self):
        """Throw exception if request is invalid"""
        if not self.Platform:
            raise exceptions.ValidationRequiredParameter("Platform is required")
        if not self.BuildNumber:
            raise exceptions.ValidationRequiredParameter("Build number is required")


class UserSettingsModel(BaseModel):
    """User settings model"""
    lastViewId: Optional[int] = None
    isNotificationEnabled: bool = True
    languageCode: str = "pl"
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# Advert models
class AdvertModel(BaseModel):
    """Advert model for API responses"""
    id: int
    sourceId: int
    typeId: int
    url: str
    regionId: int
    region: str
    district: Optional[str]
    title: str
    photos: List[str] = []
    rooms: Optional[int] = None
    area: Optional[float] = None
    price: Optional[float] = None
    currency: str = "zl"
    extPrice: Optional[str] = None
    agency: bool = False
    date: Optional[int] = None
    createdAt: Optional[int] = None 
    validTo: Optional[int] = None


class ReadAdvertsRequest(BaseModel):
    """Read adverts request"""
    AdvertId: Optional[int] = None
    Direction: int  # LoadAdvertsDirection enum
    LastViewId: Optional[int] = None


class ReadAdvertsResponse(ApiResponse):
    """Read adverts response"""
    data: Optional[List[AdvertModel]] = "MojDom Test"
    missed: int = 0


# Filter models
class RangeModel(BaseModel):
    """Range model for filters"""
    from_: Optional[int] = Field(0, alias="from")
    to:   Optional[int] = Field(2**31 - 1, alias="to")

    model_config = {
        "populate_by_name": True, 
    }



class FilterModel(BaseModel):
    """Filter model"""
    CountryId: int
    RegionId: int
    Districts: Optional[List[int]] = None
    Types: Optional[List[int]] = None
    Rooms: Optional[List[int]] = None
    Agency: bool = False
    Area: Optional[RangeModel] = None
    Price: Optional[RangeModel] = None


class SaveFilterRequest(FilterModel):
    """Save filter request"""
    def ThrowIfInvalid(self):
        """Throw exception if request is invalid"""
        if not self.CountryId:
            raise exceptions.ValidationRequiredParameter("Country ID is required")
        if not self.RegionId:
            raise exceptions.ValidationRequiredParameter("Region ID is required")
        if self.Districts:
            if any(district < 0 for district in self.Districts):
                raise exceptions.ValidationRequiredParameter("Districts item value is invalid range")
        if self.Types:
            if any(type <= 0 for type in self.Types):
                raise exceptions.ValidationRequiredParameter("Types item value is invalid range")
        if self.Rooms:
            if any(room <= 0 for room in self.Rooms):
                raise exceptions.ValidationRequiredParameter("Rooms item value is invalid range")
        if self.Area:
            if self.Area.from_ is not None and self.Area.from_ < 0:
                raise exceptions.ValidationRequiredParameter("Area.From is invalid range")
        if self.Price:
            if self.Price.from_ is not None and self.Price.from_ < 0:
                raise exceptions.ValidationRequiredParameter("Price.From is invalid range")
            if self.Price.to is not None and self.Price.to < 0:
                raise exceptions.ValidationRequiredParameter("Price.To is invalid range")


# District models
class DistrictModel(BaseModel):
    """District model"""
    id: int
    name: str
    regionId: int
    # choose: bool = True




class ReadDistrictsResponse(ApiResponse):
    """Read districts response"""
    data: Optional[List[DistrictModel]] = None

class ReadDistrictsRequest(BaseModel):
    """Read districts request"""
    pass


# File models
class FileModel(BaseModel):
    """File model"""
    id: UUID
    name: str
    type: str
    base64: str
    createdAt: datetime


class ReadFilesRequest(BaseModel):
    """Read files request"""
    ids: List[UUID]


class ReadFilesResponse(ApiResponse):
    """Read files response"""
    data: Optional[List[FileModel]] = None


# Partner models
class PartnerAdvertMetaModel(BaseModel):
    """Partner advert meta model"""
    pass  # Define based on actual JSON structure


class PartnerAdvertModel(BaseModel):
    """Partner advert model"""
    id: int
    partner_id: int
    partner_name: str
    partner_type_id: int
    banner_id: UUID
    region_id: int
    endpoint: str
    meta: Optional[PartnerAdvertMetaModel] = None
    created_at: datetime


class ReadPartnerAdvertsRequest(BaseModel):
    """Read partner adverts request"""
    region_id: Optional[int] = None


class ReadPartnerAdvertsResponseData(BaseModel):
    """Read partner adverts response data"""
    region_id: int
    adverts: Optional[List[PartnerAdvertModel]] = None


class ReadPartnerAdvertsResponse(ApiResponse):
    """Read partner adverts response"""
    data: Optional[ReadPartnerAdvertsResponseData] = None


# SMS models
class PhoneVerificationProviderModel(BaseModel):
    """Phone verification provider model"""
    providerType: int  # VerificationPhoneProviderType enum
    count_digits: int


class PhoneVerificationProviderCountryModel(BaseModel):
    """Phone verification provider country model"""
    id: int
    phoneProviderId: int
    phoneProviderType: int
    countryId: int


class SmsCodeModel(BaseModel):
    """SMS code model"""
    phoneProvider: Optional[PhoneVerificationProviderModel] = None
    phone: str
    checkCount: int
    completedAt: Optional[datetime] = None
    checkedAt: Optional[datetime] = None
    createdAt: datetime
    status: bool


class GenerateSmsCodeRequest(BaseModel):
    """Generate SMS code request"""
    partnerAdvertId: int
    phoneCountryId: int
    phone: str


class GenerateSmsCodeResponse(ApiResponse):
    """Generate SMS code response"""
    data: Optional[SmsCodeModel] = None


class CheckSmsCodeRequest(BaseModel):
    """Check SMS code request"""
    partnerAdvertId: int
    code: int


class CheckSmsCodeResponse(ApiResponse):
    """Check SMS code response"""
    data: bool


class SendPartnerLeadRequest(BaseModel):
    """Send partner lead request"""
    partnerAdvertId: int
    code: str
    phone: str
    rooms: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    addressIn: Optional[str] = None
    addressOut: Optional[str] = None
    
    @property
    def phoneNumber(self) -> str:
        """Combined phone number"""
        return f"{self.code}{self.phone}"

    async def ThrowIfInvalidAsync(self, db: AsyncSession):
        from app.pg_data_acces import PgDataAccess
        from app.models.db_models import DbPartnerAdvert
        
        if self.partnerAdvertId <= 0:
            raise exceptions.ValidationRequiredParameter("partnerAdvertId");
        
        if not self.code or self.code.strip() == "":
            raise exceptions.ValidationRequiredParameter("code");
        
        if not self.phone or self.phone.strip() == "":
            raise exceptions.ValidationRequiredParameter("phone");
        
        partnerAdvert = await PgDataAccess.read_one(db, DbPartnerAdvert, "obj_partner_adverts_get", {"id": self.partnerAdvertId})
        if partnerAdvert is None:
            raise exceptions.ValidationException("partnerAdvert not found")
        
        if partnerAdvert.PartnerTypeId == 1:
        
            if not self.rooms or self.rooms.strip() == "":
                raise exceptions.ValidationRequiredParameter("rooms")
            
            if not self.name or self.name.strip() == "":
                raise exceptions.ValidationRequiredParameter("name")
            
            if not self.description or self.description.strip() == "":
                raise exceptions.ValidationRequiredParameter("description")
            
        
        if partnerAdvert.PartnerTypeId == 2:
            if not self.name or self.name.strip() == "":
                raise exceptions.ValidationRequiredParameter("name")
            
            if not self.description or self.description.strip() == "":
                raise exceptions.ValidationRequiredParameter("description")

            if not self.addressIn or self.addressIn.strip() == "":
                raise exceptions.ValidationRequiredParameter("addressIn")
            
            if not self.addressOut or self.addressOut.strip() == "":
                raise exceptions.ValidationRequiredParameter("addressOut")


class SendPartnerLeadResponse(ApiResponse):
    """Send partner lead response"""
    data: bool


# Other models
class SaveFirebaseTokenRequest(BaseModel):
    """Save Firebase token request"""
    token: str

    def ThrowIfInvalid(self):
        """Throw exception if request is invalid"""
        if not self.token or self.token.isspace():
            raise exceptions.ValidationRequiredParameter("Token is required")


class SaveLatestViewAdvertIdRequest(BaseModel):
    """Save latest view advert ID request"""
    advertId: int

    def ThrowIfInvalid(self):
        """Throw exception if request is invalid"""
        if not self.AdvertId or self.AdvertId <= 0:
            raise exceptions.ValidationRequiredParameter("AdvertId")



class SaveIsNotificationEnabledRequest(BaseModel):
    """Save notification enabled request"""
    enable: bool
    def ThrowIfInvalid(self):
        """Throw exception if request is invalid"""
        if self.enable is None:
            raise exceptions.ValidationRequiredParameter("enable")


class SaveSettingsRequest(UserSettingsModel):
    """Save settings request"""
    def ThrowIfInvalid(self):
        """Throw exception if request is invalid"""
        pass


class SendMessageRequest(BaseModel):
    """Send message request"""
    subject: str
    message: str


class ReportLogRequest(BaseModel):
    """Report log request"""
    level: int
    message: str


# Registration response models
class UserRegisterResponseData(BaseModel):
    """User registration response data"""
    user: ApiResponse
    partnerAdverts: ReadPartnerAdvertsResponse
    districts: ReadDistrictsResponse


class UserRegisterResponse(ApiResponse):
    """User registration response"""
    data: Optional[UserRegisterResponseData] = None

