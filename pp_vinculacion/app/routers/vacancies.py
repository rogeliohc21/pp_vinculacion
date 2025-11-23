"""
Router de Vacantes
Endpoints para gestión de vacantes laborales
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.vacancy import (
    VacancyCreate,
    VacancyInDB,
    VacancyUpdate,
    VacancyPublic
)
from app.models.user import UserInDB
from app.models.company import CompanyInDB
from app.database import (
    get_vacancies_collection,
    get_companies_collection,
    get_students_collection
)
from app.routers.auth import get_current_user
from app.routers.companies import get_current_company

router = APIRouter()


# ============= FUNCIONES AUXILIARES =============

def vacancy_helper(vacancy) -> dict:
    """Convertir documento de MongoDB a dict"""
    return {
        "_id": str(vacancy["_id"]),
        "company_id": str(vacancy["company_id"]),
        **{k: v for k, v in vacancy.items() if k not in ["_id", "company_id"]}
    }


async def get_vacancy_or_404(vacancy_id: str):
    """Obtener vacante o lanzar 404"""
    if not ObjectId.is_valid(vacancy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID"
        )
    
    vacancies = await get_vacancies_collection()
    vacancy = await vacancies.find_one({"_id": ObjectId(vacancy_id)})
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    return vacancy


# ============= ENDPOINTS PARA EMPRESAS =============

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    vacancy: VacancyCreate,
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Crear nueva vacante
    
    Solo empresas verificadas pueden crear vacantes
    """
    if not current_company.verificada:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company must be verified to create vacancies"
        )
    
    vacancies = await get_vacancies_collection()
    companies = await get_companies_collection()
    
    # Crear vacante
    vacancy_dict = vacancy.dict()
    vacancy_dict["company_id"] = current_company.id
    vacancy_dict["estado"] = "activa"
    vacancy_dict["fecha_publicacion"] = datetime.utcnow()
    vacancy_dict["fecha_actualizacion"] = datetime.utcnow()
    vacancy_dict["num_visualizaciones"] = 0
    vacancy_dict["num_candidatos_matched"] = 0
    vacancy_dict["num_solicitudes_contacto"] = 0
    vacancy_dict["candidatos_contactados"] = []
    vacancy_dict["vacancy_embedding"] = None  # Se generará con IA después
    
    result = await vacancies.insert_one(vacancy_dict)
    
    # Actualizar contador de vacantes de la empresa
    await companies.update_one(
        {"_id": current_company.id},
        {"$inc": {"num_vacantes_publicadas": 1}}
    )
    
    return {
        "message": "Vacancy created successfully",
        "vacancy_id": str(result.inserted_id),
        "estado": "activa"
    }


@router.get("/my-vacancies", response_model=List[dict])
async def get_my_vacancies(
    skip: int = 0,
    limit: int = 50,
    estado: Optional[str] = Query(None, description="activa, cerrada, borrador"),
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Obtener mis vacantes
    
    Filtrar por estado si se proporciona
    """
    vacancies = await get_vacancies_collection()
    
    filters = {"company_id": current_company.id}
    if estado:
        filters["estado"] = estado
    
    vacancy_list = await vacancies.find(filters).skip(skip).limit(limit).to_list(length=limit)
    
    return [vacancy_helper(v) for v in vacancy_list]


@router.get("/{vacancy_id}", response_model=dict)
async def get_vacancy(
    vacancy_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtener detalles de una vacante específica
    
    Empresas solo pueden ver sus propias vacantes
    Estudiantes y admins pueden ver todas
    """
    vacancy = await get_vacancy_or_404(vacancy_id)
    
    # Verificar permisos
    if current_user.role == "empresa":
        companies = await get_companies_collection()
        company = await companies.find_one({"user_id": current_user.id})
        
        if not company or str(vacancy["company_id"]) != str(company["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own vacancies"
            )
    
    # Incrementar contador de visualizaciones (solo para estudiantes)
    if current_user.role == "estudiante":
        vacancies = await get_vacancies_collection()
        await vacancies.update_one(
            {"_id": ObjectId(vacancy_id)},
            {"$inc": {"num_visualizaciones": 1}}
        )
    
    return vacancy_helper(vacancy)


@router.put("/{vacancy_id}", response_model=dict)
async def update_vacancy(
    vacancy_id: str,
    vacancy_update: VacancyUpdate,
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Actualizar vacante
    
    Solo la empresa propietaria puede actualizar
    """
    vacancy = await get_vacancy_or_404(vacancy_id)
    
    # Verificar que la vacante pertenece a la empresa
    if str(vacancy["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own vacancies"
        )
    
    # Obtener solo los campos que no son None
    update_data = {k: v for k, v in vacancy_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Agregar fecha de actualización
    update_data["fecha_actualizacion"] = datetime.utcnow()
    
    # Si se actualiza, regenerar embedding (marcar como None)
    if any(key in update_data for key in ["habilidades_tecnicas_requeridas", "descripcion", "titulo"]):
        update_data["vacancy_embedding"] = None
    
    vacancies = await get_vacancies_collection()
    await vacancies.update_one(
        {"_id": ObjectId(vacancy_id)},
        {"$set": update_data}
    )
    
    return {
        "message": "Vacancy updated successfully",
        "updated_fields": list(update_data.keys())
    }


@router.patch("/{vacancy_id}/estado", response_model=dict)
async def change_vacancy_status(
    vacancy_id: str,
    nuevo_estado: str = Query(..., description="activa, cerrada, borrador"),
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Cambiar estado de la vacante
    """
    vacancy = await get_vacancy_or_404(vacancy_id)
    
    # Verificar que la vacante pertenece a la empresa
    if str(vacancy["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own vacancies"
        )
    
    # Validar estado
    estados_validos = ["activa", "cerrada", "borrador"]
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(estados_validos)}"
        )
    
    vacancies = await get_vacancies_collection()
    await vacancies.update_one(
        {"_id": ObjectId(vacancy_id)},
        {"$set": {
            "estado": nuevo_estado,
            "fecha_actualizacion": datetime.utcnow()
        }}
    )
    
    return {
        "message": f"Vacancy status changed to '{nuevo_estado}'",
        "estado": nuevo_estado
    }


@router.delete("/{vacancy_id}", response_model=dict)
async def delete_vacancy(
    vacancy_id: str,
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Eliminar vacante
    
    Solo la empresa propietaria puede eliminar
    """
    vacancy = await get_vacancy_or_404(vacancy_id)
    
    # Verificar que la vacante pertenece a la empresa
    if str(vacancy["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own vacancies"
        )
    
    vacancies = await get_vacancies_collection()
    await vacancies.delete_one({"_id": ObjectId(vacancy_id)})
    
    return {"message": "Vacancy deleted successfully"}


# ============= ENDPOINTS PÚBLICOS (PARA ESTUDIANTES) =============

@router.get("/public/all", response_model=List[VacancyPublic])
async def get_all_public_vacancies(
    skip: int = 0,
    limit: int = 50,
    tipo_contrato: Optional[str] = None,
    modalidad: Optional[str] = None,
    ciudad: Optional[str] = None,
    area: Optional[str] = None
):
    """
    Obtener todas las vacantes activas
    
    Con filtros opcionales
    """
    vacancies = await get_vacancies_collection()
    companies = await get_companies_collection()
    
    # Construir filtros
    filters = {"estado": "activa"}
    if tipo_contrato:
        filters["tipo_contrato"] = tipo_contrato
    if modalidad:
        filters["modalidad"] = modalidad
    if ciudad:
        filters["ubicacion_ciudad"] = ciudad
    if area:
        filters["area"] = area
    
    vacancy_list = await vacancies.find(filters).skip(skip).limit(limit).to_list(length=limit)
    
    result = []
    for vacancy in vacancy_list:
        # Obtener nombre de la empresa
        company = await companies.find_one({"_id": vacancy["company_id"]})
        empresa_nombre = company.get("nombre_empresa", "Empresa") if company else "Empresa"
        
        # Construir salario string
        salario_visible = not vacancy.get("salario_oculto", False)
        salario_rango = None
        if salario_visible and vacancy.get("salario_minimo") and vacancy.get("salario_maximo"):
            salario_rango = f"${vacancy['salario_minimo']:,.0f} - ${vacancy['salario_maximo']:,.0f}"
        elif salario_visible and vacancy.get("salario_minimo"):
            salario_rango = f"Desde ${vacancy['salario_minimo']:,.0f}"
        
        # Construir ubicación
        ubicacion = None
        if vacancy.get("ubicacion_ciudad") and vacancy.get("ubicacion_estado"):
            ubicacion = f"{vacancy['ubicacion_ciudad']}, {vacancy['ubicacion_estado']}"
        
        result.append(VacancyPublic(
            _id=str(vacancy["_id"]),
            titulo=vacancy.get("titulo", ""),
            area=vacancy.get("area", ""),
            descripcion=vacancy.get("descripcion", ""),
            empresa_nombre=empresa_nombre,
            tipo_contrato=vacancy.get("tipo_contrato", ""),
            modalidad=vacancy.get("modalidad", ""),
            salario_visible=salario_visible,
            salario_rango=salario_rango,
            beneficios=vacancy.get("beneficios", []),
            ubicacion=ubicacion,
            habilidades_requeridas=vacancy.get("habilidades_tecnicas_requeridas", []),
            fecha_publicacion=vacancy.get("fecha_publicacion", datetime.utcnow()),
            num_vacantes=vacancy.get("num_vacantes", 1)
        ))
    
    return result


@router.get("/public/search", response_model=List[VacancyPublic])
async def search_vacancies(
    q: str = Query(..., min_length=3, description="Search query"),
    skip: int = 0,
    limit: int = 50
):
    """
    Buscar vacantes por texto
    
    Busca en título, descripción y área
    """
    vacancies = await get_vacancies_collection()
    companies = await get_companies_collection()
    
    # Búsqueda por texto
    vacancy_list = await vacancies.find({
        "estado": "activa",
        "$or": [
            {"titulo": {"$regex": q, "$options": "i"}},
            {"descripcion": {"$regex": q, "$options": "i"}},
            {"area": {"$regex": q, "$options": "i"}},
            {"habilidades_tecnicas_requeridas": {"$regex": q, "$options": "i"}}
        ]
    }).skip(skip).limit(limit).to_list(length=limit)
    
    result = []
    for vacancy in vacancy_list:
        company = await companies.find_one({"_id": vacancy["company_id"]})
        empresa_nombre = company.get("nombre_empresa", "Empresa") if company else "Empresa"
        
        salario_visible = not vacancy.get("salario_oculto", False)
        salario_rango = None
        if salario_visible and vacancy.get("salario_minimo"):
            salario_rango = f"${vacancy['salario_minimo']:,.0f}"
            if vacancy.get("salario_maximo"):
                salario_rango += f" - ${vacancy['salario_maximo']:,.0f}"
        
        ubicacion = None
        if vacancy.get("ubicacion_ciudad"):
            ubicacion = vacancy["ubicacion_ciudad"]
            if vacancy.get("ubicacion_estado"):
                ubicacion += f", {vacancy['ubicacion_estado']}"
        
        result.append(VacancyPublic(
            _id=str(vacancy["_id"]),
            titulo=vacancy.get("titulo", ""),
            area=vacancy.get("area", ""),
            descripcion=vacancy.get("descripcion", ""),
            empresa_nombre=empresa_nombre,
            tipo_contrato=vacancy.get("tipo_contrato", ""),
            modalidad=vacancy.get("modalidad", ""),
            salario_visible=salario_visible,
            salario_rango=salario_rango,
            beneficios=vacancy.get("beneficios", []),
            ubicacion=ubicacion,
            habilidades_requeridas=vacancy.get("habilidades_tecnicas_requeridas", []),
            fecha_publicacion=vacancy.get("fecha_publicacion", datetime.utcnow()),
            num_vacantes=vacancy.get("num_vacantes", 1)
        ))
    
    return result


# ============= ENDPOINTS ADMIN =============

@router.get("/admin/all", response_model=List[dict])
async def get_all_vacancies_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtener todas las vacantes (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    vacancies = await get_vacancies_collection()
    vacancy_list = await vacancies.find().skip(skip).limit(limit).to_list(length=limit)
    
    return [vacancy_helper(v) for v in vacancy_list]


@router.get("/admin/stats", response_model=dict)
async def get_vacancies_stats(current_user: UserInDB = Depends(get_current_user)):
    """
    Estadísticas de vacantes (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    vacancies = await get_vacancies_collection()
    
    total = await vacancies.count_documents({})
    activas = await vacancies.count_documents({"estado": "activa"})
    cerradas = await vacancies.count_documents({"estado": "cerrada"})
    
    # Vacantes por tipo de contrato
    pipeline = [
        {"$group": {"_id": "$tipo_contrato", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    tipos_contrato = await vacancies.aggregate(pipeline).to_list(length=10)
    
    # Vacantes por modalidad
    pipeline_mod = [
        {"$group": {"_id": "$modalidad", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    modalidades = await vacancies.aggregate(pipeline_mod).to_list(length=10)
    
    # Áreas más demandadas
    pipeline_area = [
        {"$group": {"_id": "$area", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    areas = await vacancies.aggregate(pipeline_area).to_list(length=10)
    
    # Habilidades más solicitadas
    pipeline_skills = [
        {"$unwind": "$habilidades_tecnicas_requeridas"},
        {"$group": {"_id": "$habilidades_tecnicas_requeridas", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    habilidades = await vacancies.aggregate(pipeline_skills).to_list(length=10)
    
    return {
        "total_vacantes": total,
        "vacantes_activas": activas,
        "vacantes_cerradas": cerradas,
        "por_tipo_contrato": [{"tipo": t["_id"], "count": t["count"]} for t in tipos_contrato],
        "por_modalidad": [{"modalidad": m["_id"], "count": m["count"]} for m in modalidades],
        "areas_mas_demandadas": [{"area": a["_id"], "count": a["count"]} for a in areas],
        "habilidades_mas_solicitadas": [{"habilidad": h["_id"], "count": h["count"]} for h in habilidades]
    }


@router.patch("/admin/{vacancy_id}/estado", response_model=dict)
async def admin_change_vacancy_status(
    vacancy_id: str,
    nuevo_estado: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Admin puede cambiar estado de cualquier vacante
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    vacancy = await get_vacancy_or_404(vacancy_id)
    
    estados_validos = ["activa", "cerrada", "borrador"]
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(estados_validos)}"
        )
    
    vacancies = await get_vacancies_collection()
    await vacancies.update_one(
        {"_id": ObjectId(vacancy_id)},
        {"$set": {
            "estado": nuevo_estado,
            "fecha_actualizacion": datetime.utcnow()
        }}
    )
    
    return {
        "message": f"Vacancy status changed to '{nuevo_estado}' by admin",
        "estado": nuevo_estado
    }