from fastapi import APIRouter, Depends
from backend.modeles.schemas import (
    SeedingRateRequest,
    SeedingRateResponse,
    SprayingRequest,
    SprayingResponse,
    FertilizerRequest,
    FertilizerResponse,
)
from backend.services.calculator_service import CalculatorService
from backend.routers.auth import get_current_user

router = APIRouter()

@router.post(
    "/calculator/seeding",
    response_model=SeedingRateResponse,
    summary="Расчет нормы высева (кг/га)",
)
async def calculate_seeding(
    data: SeedingRateRequest,
    current_user: str = Depends(get_current_user),
):
    return CalculatorService.calculate_seeding_rate(data)

@router.post(
    "/calculator/spraying",
    response_model=SprayingResponse,
    summary="Расчет баковых смесей для опрыскивателя",
)
async def calculate_spraying(
    data: SprayingRequest,
    current_user: str = Depends(get_current_user),
):
    return CalculatorService.calculate_spraying(data)

@router.post(
    "/calculator/fertilizer",
    response_model=FertilizerResponse,
    summary="Расчет потребности в удобрениях (NPK) на плановую урожайность",
)
async def calculate_fertilizer(
    data: FertilizerRequest,
    current_user: str = Depends(get_current_user),
):
    return CalculatorService.calculate_fertilizer(data)
