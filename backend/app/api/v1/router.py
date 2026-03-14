from fastapi import APIRouter

from app.api.v1 import auth, dicom, studies, inference, reports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(dicom.router, prefix="/dicom", tags=["DICOM"])
api_router.include_router(studies.router, prefix="/studies", tags=["Studies"])
api_router.include_router(inference.router, prefix="/inference", tags=["Inference"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "alpcan-api"}
