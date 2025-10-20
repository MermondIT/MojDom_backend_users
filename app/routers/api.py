"""
Main API router
"""
import urllib.parse
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from uuid import UUID

from app.config import settings
from app.database import get_db
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.schemas.api_schemas import DistrictModel, ReadPartnerAdvertsResponseData

from app.models.db_models import DbDistrict, DbFile, DbFilter, DbFirebaseToken, DbPartnerAdvert, DbRegion, DbUser, DbUserSettings

from app.services.external_listings_service import ExternalListingsService
from app.pg_data_acces import PgDataAccess
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)
from app.schemas.api_schemas import *
from app.exceptions.custom_exceptions import ApiException, UnauthorizedException

router = APIRouter()



def get_user_service(request: Request) -> UserService:
    """Dependency to get user service"""
    return UserService(request)


@router.post("/Register")
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register new user"""
    request.ThrowIfInvalid()
   
    user = await DbUser.Register(db, request)      
    return ApiResponse(data=user.ToApiModel())




@router.post("/SaveDeviceInfo")
async def save_device_info(
    request: UserSaveDeviceInfoRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Save device information"""
    user_service.throw_if_unauthorized()

    request.ThrowIfInvalid() 
    user = await DbUser.SaveDeviceInfo(db, user_service.user_guid, request)
    return ApiResponse(data=user.ToApiModel())



@router.post("/SaveFirebaseToken")
async def save_firebase_token(
    request: SaveFirebaseTokenRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Save Firebase token"""
    user_service.throw_if_unauthorized()
    
    request.ThrowIfInvalid()    

    await DbFirebaseToken.Save(db, user_service.user_guid, request)
    return SuccessApiResponse()



@router.post("/SaveFilter")
async def save_filter(
    request: SaveFilterRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Save user filter"""
    user_service.throw_if_unauthorized()
    
    request.ThrowIfInvalid()      
  
    await DbFilter.Save(db, user_service.user_guid, request) 
    user = await DbUser.GetUser(db, user_service.user_guid)
    await PgDataAccess.execute(
    db,
    "SELECT obj_users_pagination_state_upsert(:_unique_id, :_last_offset, :_last_seen_id)",
    {"_unique_id": user_service.user_guid, "_last_offset": 0, "_last_seen_id": 0})   

    return SuccessApiResponse(data=user.ToApiModel())


@router.post("/ReadFilter")
async def read_filter(
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Read user filter"""
    user_service.throw_if_unauthorized()
    
    filter_model = await DbFilter.Read(db, user_service.user_guid)

    return ApiResponse(data=filter_model)


@router.post("/ReadSettings")
async def read_settings(
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Read user settings"""
    user_service.throw_if_unauthorized()
    
    settings_model = await DbUserSettings.Read(db, user_service.user_guid)  
    return ApiResponse(data=settings_model.ToApiModel())



@router.post("/SaveLatestViewAdvertId")
async def save_latest_view_advert_id(
    request: SaveLatestViewAdvertIdRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Save latest viewed advert ID"""
    user_service.throw_if_unauthorized()
    request.ThrowIfInvalid()

    settings_model = await DbUserSettings.Read(db, user_service.user_guid)
    settings_model.latest_view_advert_id = request.advert_id
    await DbUserSettings.Save(db, user_service.user_guid, settings_model)
    return SuccessApiResponse()


@router.post("/SaveIsNotificationEnabled")
async def save_is_notification_enabled(
    request: SaveIsNotificationEnabledRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Save notification enabled setting"""
    user_service.throw_if_unauthorized()
    request.ThrowIfInvalid()
    settings_model = await DbUserSettings.Read(db, user_service.user_guid)
    settings_model.is_notification_enabled = request.enable
    await DbUserSettings.Save(db, user_service.user_guid, settings_model.ToApiModel())
    user = await DbUser.GetUser(db, user_service.user_guid)
    return SuccessApiResponse(data=user.ToApiModel())
   


@router.post("/SaveSettings")
async def save_settings(
    request: SaveSettingsRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Save user settings"""
    user_service.throw_if_unauthorized()
    request.ThrowIfInvalid()
    await DbUserSettings.Save(db, user_service.user_guid, request)
    
    return SuccessApiResponse()


@router.post("/ReadAdverts")
async def read_adverts(
    request: ReadAdvertsRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Read adverts with pagination from external API"""
    user_service.throw_if_unauthorized()

    filter_model = await DbFilter.Read(db, user_service.user_guid)
        
    # Get external listings
    external_service = ExternalListingsService(db)

    # Get mapped adverts from external API
    try:
        adverts = await external_service.get_listings_mapped(filter_model, request, user_service.user_guid)
        adverts.sort(key=lambda x: x.id, reverse=False)

    except Exception as e:
        logger.warning(f"External API failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Dependent service is unavailable. Please try again later."
        )

    missed = 0
    if request.Direction == LoadAdvertsDirection.Prev or request.Direction == LoadAdvertsDirection.Next:
        missed = await external_service.get_missed(filter_model, request, user_service.user_guid)
    
    return ReadAdvertsResponse(data=adverts, missed=missed)



@router.post("/ReadAdverts2")
async def read_adverts2(
    request: ReadAdvertsRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Read adverts with update banner"""
    user_service.throw_if_unauthorized()
    
    settings_model = await DbUserSettings.Read(db, user_service.user_guid)

    titles = {  "uk": "ОНОВИТИ ↗", "pl" : "AKTUALIZOVAĆ ↗", "en": "UPDATE ↗" }
    title = titles.get(settings_model.language_code, "ОБНОВИТЬ ↗")

    update_model = AdvertModel(
                id=1,
                sourceId=0,
                typeId=0,
                url="https://rentme.onelink.me/3UJa/share",
                regionId=0,
                region="",
                district="",
                title=f"{title}"
  "<style>"
   " #advert-1 {"
   "   position: absolute;"
   "   top: 0;"
   "   right: 0;"
   "   bottom: 0;"
   "   left: 0;"
   "   padding: 18px;"
   " }"
   " #advert-1 .advert-item__content > :not(.advert-item__title) {"
   "   display: none;"
   " }"
   "</style>",
                photos=[f"https://rentme.group/images/update_{settings_model.language_code}.png"],
                rooms=0,
                area=None,
                price=1,
                currency="",
                extPrice=None,  # Not available in new API
                agency=False,
                date=datetime.utcnow,
                createdAt=datetime.utcnow,
                validTo=datetime.utcnow
            )
    
    return ReadAdvertsResponse([update_model], 0)


@router.post("/SendMessage")
async def send_message(
    request: SendMessageRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Send message via email"""
    user_service.throw_if_unauthorized()
    ES = EmailService()
    await ES.send_contact_message(request.subject, request.message)
    return SuccessApiResponse()


@router.post("/ReadDistricts")
async def read_districts(
    request: ReadDistrictsRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Read districts list"""
    user_service.throw_if_unauthorized()
    # request.ThrowIfInvalid()
    districts = await DbDistrict.ReadList(db)
    district_models = []
    for district in districts:
        district_model = DistrictModel(id=district.id, name=district.name, regionId=district.region_id)
        district_models.append(district_model)

    return ReadDistrictsResponse(data=district_models)



@router.post("/ReadFiles")
async def read_files(
    request: ReadFilesRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Read files by IDs"""
    user_service.throw_if_unauthorized()
    
    items = await DbFile.ReadList(db, request.ids)  

    files = []
    for item in items:
        files.append(item.toApiModel())
    
    return ReadFilesResponse(data=files)


@router.post("/ReadPartnerAdverts")
async def read_partner_adverts(
    request: ReadPartnerAdvertsRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Read partner adverts"""
    user_service.throw_if_unauthorized()

    filter = await DbFilter.Read(db, user_service.user_guid)
    adverts = await DbPartnerAdvert.ReadList(db, user_service.user_guid)    

    items = []
    for adv in adverts:
        items.append(adv.toApiModel())

    data = ReadPartnerAdvertsResponseData(regionId=filter.regionId, adverts=items)
    
    return ReadPartnerAdvertsResponse(data)


@router.post("/GenerateSmsCode")
async def generate_sms_code(
    request: GenerateSmsCodeRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Generate SMS verification code"""
    user_service.throw_if_unauthorized()
    
    # maybe deprecated 
    return GenerateSmsCodeResponse()


@router.post("/CheckSmsCode")
async def check_sms_code(
    request: CheckSmsCodeRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Check SMS verification code"""
    user_service.throw_if_unauthorized()
    
    # maybe deprecated 
    return CheckSmsCodeResponse(data=False)


@router.post("/SendPartnerLead")
async def send_partner_lead(
    request: SendPartnerLeadRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Send partner lead"""
    user_service.throw_if_unauthorized()
    
    await request.ThrowIfInvalidAsync(db)

    is_succes = send_lead(db)

    return SendPartnerLeadResponse(data=is_succes)


@router.post("/Messaggio")
async def messaggio_callback(
    request: dict,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Messaggio SMS callback"""
    # maybe deprecated 
    return ApiResponse(data=True)


@router.post("/ReadLatestAdverts")
async def read_latest_adverts(
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Read latest adverts (admin only)"""
    user_service.throw_if_unauthorized()
    if user_service.UserGuid != UUID("BA73FDEC-4028-403F-A110-12FB9B722D64"):
        raise UnauthorizedException();
    # Get external listings
    external_service = ExternalListingsService(db)
    
    # Get mapped adverts from external API
    try:
        adverts = await external_service.get_listings_mapped(None, ReadAdvertsRequest(direction=LoadAdvertsDirection.Latest), user_service.user_guid)

        adverts.sort(key=lambda x: x.id, reverse=False)
        
    except Exception as e:
        logger.warning(f"External API failed: {e}")
    
        
    return ReadAdvertsResponse(data=adverts, missed=0)

async def send_grid(subject: str, plain_text_content: str, html_content: str | None) -> bool:
    email_service = EmailService()

    success = await email_service.send_email(
        to_email="info@rentme.group",
        subject=subject,
        plain_text_content=plain_text_content,
        html_content=html_content
    )

    return success

async def send_lead(db: AsyncSession, model: SendPartnerLeadRequest) -> bool:

    partner_advert = await PgDataAccess.read_one(
        db,
        "DbPartnerAdvert",
        "obj_partner_adverts_get",
        {"id": model.partnerAdvertId},
    )

    if not partner_advert:
        return False

    message = []

    db_region = await PgDataAccess.read_first_or_default(
        db,
        "DbRegion",
        "dic_regions_get",
        {"id": partner_advert.region_id},
    )

    if db_region:
        message.append(f"<b>Region:</b> {db_region.name}")

    if partner_advert.partner_type_id == 1:
        message.append(f"<b>Phone:</b> {model.phone_number}")
        message.append(f"<b>Name:</b> {model.name}")
        message.append(f"<b>Rooms:</b> {model.rooms}")
        message.append(f"<b>Description:</b> {model.description}")

    elif partner_advert.partner_type_id == 2:
        message.append(f"<b>Phone:</b> {model.phone_number}")
        message.append(f"<b>Name:</b> {model.name}")
        message.append(f"<b>Address from:</b> {model.address_in}")
        message.append(f"<b>Address to:</b> {model.address_out}")
        message.append(f"<b>Description:</b> {model.description}")

    text = urllib.parse.quote_plus("\n".join(message))

    if not partner_advert.endpoint or partner_advert.endpoint.strip() == "":
        return await send_grid("New Lead", "\n".join(message))

    url = partner_advert.endpoint.replace("{text}", text)

    headers = {
        "content-type": "application/json; charset=UTF-8",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            json_text = response.text

            if response.status_code == 200 and json_text:
                logger.info("Lead successfully sent via endpoint.")
                return True
            else:
                logger.warning(
                    f"SendLead failed. Status: {response.status_code}, Body: {json_text}"
                )
                return False

    except Exception as e:
        logger.error(f"SendLead error: {e}")
        await PgDataAccess.write_info(f"{{\"error\": \"{str(e)}\"}}")
        return False