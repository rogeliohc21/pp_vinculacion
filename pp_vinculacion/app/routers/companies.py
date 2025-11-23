"""
Router de Empresas con endpoint de verificación corregido
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.company import (
    CompanyCreate,
    CompanyInDB,
    CompanyResponse,
    CompanyUpdate
)
from app.models.user import UserInDB
from app.database import get_companies_collection
from app.routers.auth import get_current_user

router = APIRouter()


# ============= FUNCIÓN DE DEPENDENCIA =============

async def get_current_company(current_user: UserInDB = Depends(get_current_user)) -> CompanyInDB:
    """
    Obtener empresa del usuario actual (solo empresas)
    """
    if current_user.role != "empresa":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company users can access this endpoint"
        )
    
    companies = await get_companies_collection()
    
    # Buscar empresa asociada al user_id
    company = await companies.find_one({"user_id": ObjectId(current_user.id)})
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found. Please create your company profile first."
        )
    
    return CompanyInDB(**company)


# ============= ENDPOINTS =============

@router.post("/profile", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company_profile(
    company_data: CompanyCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Crear perfil de empresa (solo usuarios empresa)
    """
    if current_user.role != "empresa":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company users can create company profiles"
        )
    
    companies = await get_companies_collection()
    
    # Verificar si ya existe perfil para este usuario
    existing = await companies.find_one({"user_id": ObjectId(current_user.id)})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company profile already exists"
        )
    
    # Crear documento
    company_dict = company_data.dict()
    company_dict.update({
        "user_id": ObjectId(current_user.id),
        "verificada": False,
        "fecha_registro": datetime.utcnow(),
        "fecha_actualizacion": datetime.utcnow()
    })
    
    result = await companies.insert_one(company_dict)
    created_company = await companies.find_one({"_id": result.inserted_id})
    
    # Convertir ObjectIds a string
    created_company["_id"] = str(created_company["_id"])
    created_company["user_id"] = str(created_company["user_id"])
    
    return CompanyResponse(**created_company)


@router.get("/profile", response_model=CompanyResponse)
async def get_company_profile(current_company: CompanyInDB = Depends(get_current_company)):
    """
    Obtener perfil de la empresa actual
    """
    company_dict = current_company.dict()
    company_dict["_id"] = str(current_company.id)
    company_dict["user_id"] = str(current_company.user_id)
    return CompanyResponse(**company_dict)


@router.put("/profile", response_model=CompanyResponse)
async def update_company_profile(
    update_data: CompanyUpdate,
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Actualizar perfil de empresa
    """
    companies = await get_companies_collection()
    
    # Preparar datos de actualización (solo campos no nulos)
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["fecha_actualizacion"] = datetime.utcnow()
    
    await companies.update_one(
        {"_id": ObjectId(current_company.id)},
        {"$set": update_dict}
    )
    
    updated_company = await companies.find_one({"_id": ObjectId(current_company.id)})
    
    # Convertir ObjectIds a string
    updated_company["_id"] = str(updated_company["_id"])
    updated_company["user_id"] = str(updated_company["user_id"])
    
    return CompanyResponse(**updated_company)


# ============= ENDPOINTS ADMIN =============

@router.get("/admin/all", response_model=List[CompanyResponse])
async def get_all_companies(
    skip: int = 0,
    limit: int = 100,
    verified: Optional[bool] = Query(None, description="Filtrar por verificadas"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Listar todas las empresas (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    companies = await get_companies_collection()
    
    filters = {}
    if verified is not None:
        filters["verificada"] = verified
    
    company_list = await companies.find(filters).skip(skip).limit(limit).to_list(length=limit)
    
    # Convertir ObjectId a string antes de crear CompanyResponse
    result = []
    for company in company_list:
        company["_id"] = str(company["_id"])
        company["user_id"] = str(company["user_id"])
        result.append(CompanyResponse(**company))
    
    return result


@router.put("/{company_id}/verify", response_model=CompanyResponse)
async def verify_company(
    company_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Verificar empresa (solo admin)
    
    CORREGIDO: Valida ObjectId antes de buscar
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can verify companies"
        )
    
    # ⭐ VALIDAR que el ID sea válido ANTES de buscar
    if not ObjectId.is_valid(company_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid company ID format: {company_id}"
        )
    
    companies = await get_companies_collection()
    
    # Buscar empresa
    company = await companies.find_one({"_id": ObjectId(company_id)})
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )
    
    # Actualizar verificación
    await companies.update_one(
        {"_id": ObjectId(company_id)},
        {"$set": {
            "verificada": True,
            "fecha_verificacion": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }}
    )
    
    # Obtener empresa actualizada
    updated_company = await companies.find_one({"_id": ObjectId(company_id)})
    
    # Convertir ObjectIds a string
    updated_company["_id"] = str(updated_company["_id"])
    updated_company["user_id"] = str(updated_company["user_id"])
    
    return CompanyResponse(**updated_company)


@router.put("/{company_id}/unverify", response_model=CompanyResponse)
async def unverify_company(
    company_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Desverificar empresa (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can unverify companies"
        )
    
    # ⭐ VALIDAR ObjectId
    if not ObjectId.is_valid(company_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid company ID format: {company_id}"
        )
    
    companies = await get_companies_collection()
    
    company = await companies.find_one({"_id": ObjectId(company_id)})
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )
    
    await companies.update_one(
        {"_id": ObjectId(company_id)},
        {"$set": {
            "verificada": False,
            "fecha_verificacion": None,
            "fecha_actualizacion": datetime.utcnow()
        }}
    )
    
    updated_company = await companies.find_one({"_id": ObjectId(company_id)})
    
    # Convertir ObjectIds a string
    updated_company["_id"] = str(updated_company["_id"])
    updated_company["user_id"] = str(updated_company["user_id"])
    
    return CompanyResponse(**updated_company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Eliminar empresa (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete companies"
        )
    
    # ⭐ VALIDAR ObjectId
    if not ObjectId.is_valid(company_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid company ID format: {company_id}"
        )
    
    companies = await get_companies_collection()
    
    result = await companies.delete_one({"_id": ObjectId(company_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )
    
    return None


@router.get("/admin/stats", response_model=dict)
async def get_company_stats(current_user: UserInDB = Depends(get_current_user)):
    """
    Estadísticas de empresas (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    companies = await get_companies_collection()
    
    total = await companies.count_documents({})
    verified = await companies.count_documents({"verificada": True})
    pending = await companies.count_documents({"verificada": False})
    
    return {
        "total_companies": total,
        "verified": verified,
        "pending_verification": pending
    }