"""
Public API router
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.user_service import PublicUserService
from app.schemas.api_schemas import (
    ApiResponse, PingResponse, ReportLogRequest, UserRegisterResponse,
    UserRegisterRequest2, UserRegisterResponseData, ReadPartnerAdvertsResponse, ReadDistrictsResponse
)
from datetime import datetime
from app.exceptions.custom_exceptions import ApiException, UnauthorizedException
from app.models.db_models import DbDistrict, DbPartnerAdvert, DbUser

router = APIRouter()


def get_public_user_service(request: Request) -> PublicUserService:
    """Dependency to get public user service"""
    return PublicUserService(request)


@router.post("/db")
async def db(
    user_service: PublicUserService = Depends(get_public_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Get database version"""
    user_service.throw_if_unauthorized()
    
    # Execute raw SQL query
    result = await db.execute("SELECT VERSION()")
    version = result.scalar()
    
    return ApiResponse(data=version)


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return PingResponse()


@router.post("/report_log")
async def report_log(
    request: ReportLogRequest,
    user_service: PublicUserService = Depends(get_public_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Report log message"""
    user_service.throw_if_unauthorized()
    
    # maybe deprecated 
    
    return ApiResponse(data=True)


@router.post("/register")
async def register(
    request: UserRegisterRequest2,
    user_service: PublicUserService = Depends(get_public_user_service),
    db: AsyncSession = Depends(get_db)
):
    """Register new user (public endpoint)"""
    user_service.throw_if_unauthorized()
    
    request.throw_if_invalid()
    raise ApiException(message="Not implemented")
    # maybe deprecated
    # pass
    # dbUser = await DbUser.Register2(request)

    # dbDistricts = await DbDistrict.ReadList()
    # dbPartnerAdverts = await DbPartnerAdvert.ReadList(dbUser.UniqueId)



    # _user = dbUser.ToUserModel()
    # _districts = [x.ToApiModel() for x in dbDistricts]
    # _partnerAdverts = [x.ToApiModel() for x in dbPartnerAdverts]


    return UserRegisterResponse()
