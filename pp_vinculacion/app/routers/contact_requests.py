"""
Router de Solicitudes de Contacto
Sistema para que empresas soliciten información de contacto de estudiantes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.contact_request import (
    ContactRequestCreate,
    ContactRequestInDB,
    ContactRequestUpdate,
    ContactRequestResponse,
    ContactRequestList,
    StudentContactInfo
)
from app.models.user import UserInDB
from app.models.company import CompanyInDB
from app.database import (
    get_contact_requests_collection,
    get_matches_collection,
    get_students_collection,
    get_vacancies_collection,
    get_companies_collection
)
from app.routers.auth import get_current_user
from app.routers.companies import get_current_company

router = APIRouter()


# ============= ENDPOINTS PARA EMPRESAS =============

@router.post("/request", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_contact_request(
    request_data: ContactRequestCreate,
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Solicitar contacto con un estudiante
    
    La empresa debe enviar:
    - vacancy_id: ID de la vacante
    - student_matricula: Matrícula del estudiante
    - motivo: Razón de la solicitud (opcional)
    """
    contact_requests = await get_contact_requests_collection()
    matches = await get_matches_collection()
    students = await get_students_collection()
    vacancies = await get_vacancies_collection()
    
    # Verificar que la vacante existe y pertenece a la empresa
    if not ObjectId.is_valid(request_data.vacancy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID"
        )
    
    vacancy = await vacancies.find_one({"_id": ObjectId(request_data.vacancy_id)})
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if str(vacancy["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only request contact for your own vacancies"
        )
    
    # Verificar que existe un match entre la vacante y el estudiante
    match = await matches.find_one({
        "vacancy_id": ObjectId(request_data.vacancy_id),
        "student_matricula": request_data.student_matricula
    })
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No match found between this vacancy and student"
        )
    
    # Verificar que el estudiante existe
    student = await students.find_one({"matricula": request_data.student_matricula})
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Verificar que no existe una solicitud previa
    existing_request = await contact_requests.find_one({
        "vacancy_id": ObjectId(request_data.vacancy_id),
        "student_matricula": request_data.student_matricula,
        "company_id": current_company.id
    })
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contact request already exists with status: {existing_request['estado']}"
        )
    
    # Crear solicitud
    request_doc = {
        "vacancy_id": ObjectId(request_data.vacancy_id),
        "company_id": current_company.id,
        "student_matricula": request_data.student_matricula,
        "motivo": request_data.motivo,
        "estado": "pendiente",
        "fecha_solicitud": datetime.utcnow(),
        "fecha_respuesta": None,
        "respondido_por": None,
        "comentario_admin": None,
        "motivo_rechazo": None
    }
    
    result = await contact_requests.insert_one(request_doc)
    
    # Actualizar contador en la vacante
    await vacancies.update_one(
        {"_id": ObjectId(request_data.vacancy_id)},
        {"$inc": {"num_solicitudes_contacto": 1}}
    )
    
    return {
        "message": "Contact request created successfully",
        "request_id": str(result.inserted_id),
        "estado": "pendiente",
        "note": "An administrator will review your request"
    }


@router.get("/my-requests", response_model=ContactRequestList)
async def get_my_contact_requests(
    skip: int = 0,
    limit: int = 50,
    estado: Optional[str] = Query(None, description="pendiente, aprobada, rechazada"),
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Obtener mis solicitudes de contacto
    """
    contact_requests = await get_contact_requests_collection()
    vacancies = await get_vacancies_collection()
    
    # Filtros
    filters = {"company_id": current_company.id}
    if estado:
        filters["estado"] = estado
    
    # Obtener solicitudes
    requests_list = await contact_requests.find(filters).sort(
        "fecha_solicitud", -1
    ).skip(skip).limit(limit).to_list(length=limit)
    
    # Construir respuesta
    result = []
    for req in requests_list:
        vacancy = await vacancies.find_one({"_id": req["vacancy_id"]})
        
        result.append(ContactRequestResponse(
            _id=str(req["_id"]),
            vacancy_titulo=vacancy.get("titulo", "Vacante") if vacancy else "Vacante",
            company_nombre=current_company.nombre_empresa,
            student_matricula=req["student_matricula"],
            estado=req["estado"],
            fecha_solicitud=req["fecha_solicitud"],
            fecha_respuesta=req.get("fecha_respuesta"),
            motivo=req.get("motivo"),
            comentario_admin=req.get("comentario_admin")
        ))
    
    # Contadores
    total = await contact_requests.count_documents({"company_id": current_company.id})
    pendientes = await contact_requests.count_documents({"company_id": current_company.id, "estado": "pendiente"})
    aprobadas = await contact_requests.count_documents({"company_id": current_company.id, "estado": "aprobada"})
    rechazadas = await contact_requests.count_documents({"company_id": current_company.id, "estado": "rechazada"})
    
    return ContactRequestList(
        total=total,
        pendientes=pendientes,
        aprobadas=aprobadas,
        rechazadas=rechazadas,
        solicitudes=result
    )


@router.get("/student-contact/{request_id}", response_model=StudentContactInfo)
async def get_student_contact_info(
    request_id: str,
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Obtener información de contacto del estudiante
    
    Solo disponible si la solicitud fue aprobada
    """
    contact_requests = await get_contact_requests_collection()
    students = await get_students_collection()
    
    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID"
        )
    
    # Obtener solicitud
    request = await contact_requests.find_one({"_id": ObjectId(request_id)})
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact request not found"
        )
    
    # Verificar que pertenece a la empresa
    if str(request["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Verificar que está aprobada
    if request["estado"] != "aprobada":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Contact request is {request['estado']}. Must be approved to access contact info"
        )
    
    # Obtener información del estudiante
    student = await students.find_one({"matricula": request["student_matricula"]})
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Obtener datos de usuario para email
    from app.database import get_users_collection
    users = await get_users_collection()
    user = await users.find_one({"_id": student["user_id"]})
    
    return StudentContactInfo(
        matricula=student["matricula"],
        nombre_completo=student.get("nombre_completo", ""),
        email=user.get("email", "") if user else "",
        telefono=student.get("telefono", ""),
        carrera=student.get("carrera", ""),
        semestre=student.get("semestre", 0),
        cv_url=f"/uploads/cvs/{student['cv_filename']}" if student.get("cv_filename") else None,
        linkedin=student.get("linkedin"),
        github=student.get("github"),
        portafolio=student.get("portafolio")
    )


# ============= ENDPOINTS ADMIN =============

@router.get("/admin/all", response_model=ContactRequestList)
async def get_all_contact_requests(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = Query(None, description="pendiente, aprobada, rechazada"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtener todas las solicitudes de contacto (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    contact_requests = await get_contact_requests_collection()
    vacancies = await get_vacancies_collection()
    companies = await get_companies_collection()
    
    # Filtros
    filters = {}
    if estado:
        filters["estado"] = estado
    
    # Obtener solicitudes
    requests_list = await contact_requests.find(filters).sort(
        "fecha_solicitud", -1
    ).skip(skip).limit(limit).to_list(length=limit)
    
    # Construir respuesta
    result = []
    for req in requests_list:
        vacancy = await vacancies.find_one({"_id": req["vacancy_id"]})
        company = await companies.find_one({"_id": req["company_id"]})
        
        result.append(ContactRequestResponse(
            _id=str(req["_id"]),
            vacancy_titulo=vacancy.get("titulo", "Vacante") if vacancy else "Vacante",
            company_nombre=company.get("nombre_empresa", "Empresa") if company else "Empresa",
            student_matricula=req["student_matricula"],
            estado=req["estado"],
            fecha_solicitud=req["fecha_solicitud"],
            fecha_respuesta=req.get("fecha_respuesta"),
            motivo=req.get("motivo"),
            comentario_admin=req.get("comentario_admin")
        ))
    
    # Contadores
    total = await contact_requests.count_documents({})
    pendientes = await contact_requests.count_documents({"estado": "pendiente"})
    aprobadas = await contact_requests.count_documents({"estado": "aprobada"})
    rechazadas = await contact_requests.count_documents({"estado": "rechazada"})
    
    return ContactRequestList(
        total=total,
        pendientes=pendientes,
        aprobadas=aprobadas,
        rechazadas=rechazadas,
        solicitudes=result
    )


@router.put("/admin/{request_id}/review", response_model=dict)
async def review_contact_request(
    request_id: str,
    review_data: ContactRequestUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Aprobar o rechazar solicitud de contacto (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can review contact requests"
        )
    
    contact_requests = await get_contact_requests_collection()
    
    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID"
        )
    
    # Obtener solicitud
    request = await contact_requests.find_one({"_id": ObjectId(request_id)})
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact request not found"
        )
    
    # Validar estado
    if review_data.estado not in ["aprobada", "rechazada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado must be 'aprobada' or 'rechazada'"
        )
    
    # Actualizar solicitud
    update_data = {
        "estado": review_data.estado,
        "fecha_respuesta": datetime.utcnow(),
        "respondido_por": current_user.id,
        "comentario_admin": review_data.comentario_admin
    }
    
    if review_data.estado == "rechazada" and review_data.motivo_rechazo:
        update_data["motivo_rechazo"] = review_data.motivo_rechazo
    
    await contact_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": update_data}
    )
    
    # TODO: Enviar notificación a la empresa
    # TODO: Si es aprobada, enviar notificación al estudiante
    
    return {
        "message": f"Contact request {review_data.estado}",
        "request_id": request_id,
        "estado": review_data.estado
    }


@router.get("/admin/stats", response_model=dict)
async def get_contact_request_stats(current_user: UserInDB = Depends(get_current_user)):
    """
    Estadísticas de solicitudes de contacto (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    contact_requests = await get_contact_requests_collection()
    
    total = await contact_requests.count_documents({})
    pendientes = await contact_requests.count_documents({"estado": "pendiente"})
    aprobadas = await contact_requests.count_documents({"estado": "aprobada"})
    rechazadas = await contact_requests.count_documents({"estado": "rechazada"})
    
    # Empresas más activas
    pipeline_companies = [
        {"$group": {"_id": "$company_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    top_companies = await contact_requests.aggregate(pipeline_companies).to_list(length=10)
    
    # Tasa de aprobación
    tasa_aprobacion = (aprobadas / total * 100) if total > 0 else 0
    
    return {
        "total_solicitudes": total,
        "pendientes": pendientes,
        "aprobadas": aprobadas,
        "rechazadas": rechazadas,
        "tasa_aprobacion": round(tasa_aprobacion, 2),
        "empresas_mas_activas": len(top_companies)
    }


@router.delete("/admin/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact_request(
    request_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Eliminar solicitud de contacto (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete contact requests"
        )
    
    contact_requests = await get_contact_requests_collection()
    
    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID"
        )
    
    result = await contact_requests.delete_one({"_id": ObjectId(request_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact request not found"
        )
    
    return None