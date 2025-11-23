"""
Router de Matching con IA
Motor de inteligencia artificial para emparejar estudiantes con vacantes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict
from datetime import datetime
from bson import ObjectId
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.models.match import (
    MatchCreate,
    MatchInDB,
    MatchResponse,
    MatchListResponse,
    MatchDesglose,
    RadarChartData
)
from app.models.user import UserInDB
from app.models.company import CompanyInDB
from app.database import (
    get_matches_collection,
    get_vacancies_collection,
    get_students_collection,
    get_companies_collection
)
from app.routers.auth import get_current_user
from app.routers.companies import get_current_company
from app.config import settings

router = APIRouter()


# ============= FUNCIONES DE MATCHING =============

def calculate_skills_match(student_skills: List[str], required_skills: List[str]) -> float:
    """
    Calcular compatibilidad de habilidades
    
    Retorna un valor entre 0 y 1
    """
    if not required_skills:
        return 1.0
    
    if not student_skills:
        return 0.0
    
    # Convertir a minúsculas para comparación
    student_skills_lower = [s.lower() for s in student_skills]
    required_skills_lower = [s.lower() for s in required_skills]
    
    # Contar coincidencias
    matches = sum(1 for skill in required_skills_lower if skill in student_skills_lower)
    
    return matches / len(required_skills_lower)


def calculate_language_match(student_langs: List[Dict], required_langs: List[Dict]) -> float:
    """
    Calcular compatibilidad de idiomas
    
    Verifica nivel mínimo requerido
    """
    if not required_langs:
        return 1.0
    
    if not student_langs:
        return 0.0
    
    # Mapeo de niveles
    level_order = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6, "Nativo": 7}
    
    matches = 0
    for req_lang in required_langs:
        req_idioma = req_lang.get("idioma", "").lower()
        req_nivel = req_lang.get("nivel_minimo", "A1")
        req_nivel_num = level_order.get(req_nivel, 0)
        
        # Buscar idioma en estudiante
        for student_lang in student_langs:
            student_idioma = student_lang.get("idioma", "").lower()
            student_nivel = student_lang.get("nivel", "A1")
            student_nivel_num = level_order.get(student_nivel, 0)
            
            if req_idioma == student_idioma and student_nivel_num >= req_nivel_num:
                matches += 1
                break
    
    return matches / len(required_langs)


def calculate_experience_match(student_experience: List[Dict], required_experience: str) -> float:
    """
    Calcular compatibilidad de experiencia
    """
    experience_mapping = {
        "Sin experiencia": 0,
        "Menos de 1 año": 0.5,
        "1-2 años": 1.5,
        "2-3 años": 2.5,
        "3-5 años": 4,
        "Más de 5 años": 6
    }
    
    required_years = experience_mapping.get(required_experience, 0)
    
    # Si no se requiere experiencia
    if required_years == 0:
        return 1.0
    
    # Calcular años de experiencia del estudiante
    student_years = len(student_experience) * 0.5  # Aproximación simple
    
    if student_years >= required_years:
        return 1.0
    elif student_years > 0:
        return student_years / required_years
    else:
        return 0.5  # Dar algo de crédito si no tiene experiencia pero la vacante la requiere


def calculate_career_match(student_career: str, required_careers: List[str]) -> float:
    """
    Calcular compatibilidad de carrera
    """
    if not required_careers or len(required_careers) == 0:
        return 1.0  # Si no especifica carreras, todas son válidas
    
    student_career_lower = student_career.lower()
    required_careers_lower = [c.lower() for c in required_careers]
    
    # Coincidencia exacta
    if student_career_lower in required_careers_lower:
        return 1.0
    
    # Coincidencia parcial (buscar palabras clave)
    for req_career in required_careers_lower:
        if any(word in student_career_lower for word in req_career.split()):
            return 0.7
    
    return 0.3  # Dar algo de crédito aunque no coincida


def calculate_semester_match(student_semester: int, required_semester: int) -> float:
    """
    Calcular compatibilidad de semestre
    """
    if not required_semester or required_semester == 0:
        return 1.0
    
    if student_semester >= required_semester:
        return 1.0
    else:
        # Dar crédito parcial si está cerca
        diff = required_semester - student_semester
        if diff <= 1:
            return 0.8
        elif diff <= 2:
            return 0.6
        else:
            return 0.3


def calculate_modality_match(student_modality: str, vacancy_modality: str) -> float:
    """
    Calcular compatibilidad de modalidad de trabajo
    """
    if not student_modality or not vacancy_modality:
        return 1.0
    
    student_mod = student_modality.lower()
    vacancy_mod = vacancy_modality.lower()
    
    if student_mod == vacancy_mod:
        return 1.0
    
    # Híbrido es compatible con presencial y remoto
    if "híbrido" in student_mod or "hibrido" in student_mod:
        return 0.9
    if "híbrido" in vacancy_mod or "hibrido" in vacancy_mod:
        return 0.9
    
    return 0.5


def calculate_overall_match(desglose: MatchDesglose) -> float:
    """
    Calcular porcentaje total de matching
    
    Pesos configurables según importancia
    """
    weights = {
        "habilidades_tecnicas": 0.30,    # 30%
        "habilidades_blandas": 0.15,     # 15%
        "idiomas": 0.15,                 # 15%
        "experiencia": 0.15,             # 15%
        "carrera": 0.15,                 # 15%
        "semestre": 0.05,                # 5%
        "modalidad": 0.05                # 5%
    }
    
    total = 0.0
    for field, weight in weights.items():
        total += getattr(desglose, field) * weight
    
    return round(total * 100, 2)  # Convertir a porcentaje


async def perform_matching(vacancy_id: str, student_matricula: str) -> MatchDesglose:
    """
    Realizar matching entre vacante y estudiante
    
    Retorna desglose detallado
    """
    vacancies = await get_vacancies_collection()
    students = await get_students_collection()
    
    vacancy = await vacancies.find_one({"_id": ObjectId(vacancy_id)})
    student = await students.find_one({"matricula": student_matricula})
    
    if not vacancy or not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy or student not found"
        )
    
    # Calcular cada componente
    habilidades_tecnicas = calculate_skills_match(
        student.get("habilidades_tecnicas", []),
        vacancy.get("habilidades_tecnicas_requeridas", [])
    )
    
    habilidades_blandas = calculate_skills_match(
        student.get("habilidades_blandas", []),
        vacancy.get("habilidades_blandas_requeridas", [])
    )
    
    idiomas = calculate_language_match(
        student.get("idiomas", []),
        vacancy.get("idiomas_requeridos", [])
    )
    
    experiencia = calculate_experience_match(
        student.get("experiencia_laboral", []),
        vacancy.get("experiencia_minima", "Sin experiencia")
    )
    
    carrera = calculate_career_match(
        student.get("carrera", ""),
        vacancy.get("carrera_requerida", [])
    )
    
    semestre = calculate_semester_match(
        student.get("semestre", 0),
        vacancy.get("semestre_minimo", 0)
    )
    
    modalidad = calculate_modality_match(
        student.get("modalidad_preferida", ""),
        vacancy.get("modalidad", "")
    )
    
    return MatchDesglose(
        habilidades_tecnicas=habilidades_tecnicas,
        habilidades_blandas=habilidades_blandas,
        idiomas=idiomas,
        experiencia=experiencia,
        carrera=carrera,
        semestre=semestre,
        modalidad=modalidad
    )


# ============= ENDPOINTS =============

@router.post("/student/calculate", response_model=dict)
async def calculate_student_matching(
    request: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Calcular matching para un estudiante específico"""
    vacancy_id = request.get("vacancy_id")
    student_matricula = request.get("student_matricula")
    
    # Calcular matching
    desglose = await perform_matching(vacancy_id, student_matricula)
    porcentaje = calculate_overall_match(desglose)
    
    # Crear radar data
    radar_data = {
        "Habilidades Técnicas": round(desglose.habilidades_tecnicas * 100, 1),
        "Habilidades Blandas": round(desglose.habilidades_blandas * 100, 1),
        "Idiomas": round(desglose.idiomas * 100, 1),
        "Experiencia": round(desglose.experiencia * 100, 1),
        "Carrera": round(desglose.carrera * 100, 1),
        "Semestre": round(desglose.semestre * 100, 1),
        "Modalidad": round(desglose.modalidad * 100, 1)
    }
    
    return {
        "porcentaje_match": porcentaje,
        "desglose": desglose.dict(),
        "radar_chart_data": radar_data
    }

@router.post("/vacancy/{vacancy_id}/run", response_model=dict)
async def run_matching_for_vacancy(
    vacancy_id: str,
    min_match_percentage: float = Query(80.0, ge=0, le=100),
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Ejecutar matching para una vacante específica
    
    Encuentra todos los estudiantes que cumplan con el porcentaje mínimo
    """
    vacancies = await get_vacancies_collection()
    students = await get_students_collection()
    matches = await get_matches_collection()
    
    # Verificar que la vacante existe y pertenece a la empresa
    if not ObjectId.is_valid(vacancy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID"
        )
    
    vacancy = await vacancies.find_one({"_id": ObjectId(vacancy_id)})
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if str(vacancy["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only run matching on your own vacancies"
        )
    
    # Obtener todos los estudiantes visibles con perfil completo
    student_list = await students.find({
        "visible_empresas": True,
        "perfil_completo": True
    }).to_list(length=1000)
    
    if not student_list:
        return {
            "message": "No students found",
            "total_students_evaluated": 0,
            "matches_found": 0
        }
    
    # Realizar matching para cada estudiante
    matches_found = 0
    matches_created = 0
    
    for student in student_list:
        matricula = student.get("matricula")
        
        # Verificar si ya existe un match
        existing_match = await matches.find_one({
            "vacancy_id": ObjectId(vacancy_id),
            "student_matricula": matricula
        })
        
        if existing_match:
            continue  # Ya existe, saltar
        
        # Calcular matching
        desglose = await perform_matching(vacancy_id, matricula)
        porcentaje = calculate_overall_match(desglose)
        
        # Si cumple con el mínimo, crear match
        if porcentaje >= min_match_percentage:
            matches_found += 1
            
            # Crear radar chart data
            radar_data = {
                "Habilidades Técnicas": round(desglose.habilidades_tecnicas * 100, 1),
                "Habilidades Blandas": round(desglose.habilidades_blandas * 100, 1),
                "Idiomas": round(desglose.idiomas * 100, 1),
                "Experiencia": round(desglose.experiencia * 100, 1),
                "Carrera": round(desglose.carrera * 100, 1),
                "Semestre": round(desglose.semestre * 100, 1),
                "Modalidad": round(desglose.modalidad * 100, 1)
            }
            
            match_doc = {
                "vacancy_id": ObjectId(vacancy_id),
                "student_matricula": matricula,
                "porcentaje_match": porcentaje,
                "desglose": desglose.dict(),
                "radar_chart_data": radar_data,
                "fecha_match": datetime.utcnow(),
                "visto_por_empresa": False,
                "embedding_similarity": None  # Se puede agregar después con IA
            }
            
            await matches.insert_one(match_doc)
            matches_created += 1
    
    # Actualizar contador en la vacante
    await vacancies.update_one(
        {"_id": ObjectId(vacancy_id)},
        {"$set": {
            "num_candidatos_matched": matches_created,
            "fecha_actualizacion": datetime.utcnow()
        }}
    )
    
    return {
        "message": "Matching completed successfully",
        "total_students_evaluated": len(student_list),
        "matches_found": matches_found,
        "matches_created": matches_created,
        "min_match_percentage": min_match_percentage
    }


@router.get("/vacancy/{vacancy_id}/matches", response_model=MatchListResponse)
async def get_matches_for_vacancy(
    vacancy_id: str,
    skip: int = 0,
    limit: int = 50,
    min_percentage: float = Query(0, ge=0, le=100),
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Obtener matches de una vacante
    
    Lista de estudiantes compatibles (solo matrículas)
    """
    vacancies = await get_vacancies_collection()
    matches_coll = await get_matches_collection()
    students = await get_students_collection()
    
    # Verificar vacante
    if not ObjectId.is_valid(vacancy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID"
        )
    
    vacancy = await vacancies.find_one({"_id": ObjectId(vacancy_id)})
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if str(vacancy["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view matches for your own vacancies"
        )
    
    # Obtener matches
    filters = {
        "vacancy_id": ObjectId(vacancy_id),
        "porcentaje_match": {"$gte": min_percentage}
    }
    
    match_list = await matches_coll.find(filters).sort("porcentaje_match", -1).skip(skip).limit(limit).to_list(length=limit)
    
    # Construir respuesta con datos anónimos
    matches_response = []
    for match in match_list:
        # Marcar como visto
        if not match.get("visto_por_empresa", False):
            await matches_coll.update_one(
                {"_id": match["_id"]},
                {"$set": {
                    "visto_por_empresa": True,
                    "fecha_visto": datetime.utcnow()
                }}
            )
        
        # Obtener datos anónimos del estudiante
        student = await students.find_one({"matricula": match["student_matricula"]})
        
        if student:
            matches_response.append(MatchResponse(
                _id=str(match["_id"]),
                student_matricula=match["student_matricula"],
                porcentaje_match=match["porcentaje_match"],
                desglose=MatchDesglose(**match["desglose"]),
                fecha_match=match["fecha_match"],
                carrera=student.get("carrera", ""),
                semestre=student.get("semestre", 0),
                habilidades_tecnicas=student.get("habilidades_tecnicas", []),
                habilidades_blandas=student.get("habilidades_blandas", []),
                idiomas=student.get("idiomas", []),
                tiene_experiencia=len(student.get("experiencia_laboral", [])) > 0,
                modalidad_preferida=student.get("modalidad_preferida", ""),
                radar_chart_data=match.get("radar_chart_data", {})
            ))
    
    total_matches = await matches_coll.count_documents(filters)
    
    return MatchListResponse(
        vacancy_id=vacancy_id,
        vacancy_titulo=vacancy.get("titulo", ""),
        total_matches=total_matches,
        matches=matches_response
    )


@router.get("/vacancy/{vacancy_id}/match/{match_id}/radar", response_model=RadarChartData)
async def get_radar_chart_data(
    vacancy_id: str,
    match_id: str,
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Obtener datos para gráfica de araña de un match específico
    """
    matches_coll = await get_matches_collection()
    vacancies = await get_vacancies_collection()
    
    # Verificar IDs
    if not ObjectId.is_valid(match_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid match ID"
        )
    
    # Obtener match
    match = await matches_coll.find_one({"_id": ObjectId(match_id)})
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Verificar que la vacante pertenece a la empresa
    vacancy = await vacancies.find_one({"_id": match["vacancy_id"]})
    if str(vacancy["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Preparar datos para gráfica
    desglose = match["desglose"]
    
    categories = [
        "Habilidades Técnicas",
        "Habilidades Blandas",
        "Idiomas",
        "Experiencia",
        "Carrera",
        "Semestre",
        "Modalidad"
    ]
    
    valores_requeridos = [100, 100, 100, 100, 100, 100, 100]  # Lo que pide la vacante
    valores_candidato = [
        round(desglose["habilidades_tecnicas"] * 100, 1),
        round(desglose["habilidades_blandas"] * 100, 1),
        round(desglose["idiomas"] * 100, 1),
        round(desglose["experiencia"] * 100, 1),
        round(desglose["carrera"] * 100, 1),
        round(desglose["semestre"] * 100, 1),
        round(desglose["modalidad"] * 100, 1)
    ]
    
    return RadarChartData(
        categories=categories,
        valores_requeridos=valores_requeridos,
        valores_candidato=valores_candidato
    )


@router.delete("/vacancy/{vacancy_id}/matches", response_model=dict)
async def delete_all_matches_for_vacancy(
    vacancy_id: str,
    current_company: CompanyInDB = Depends(get_current_company)
):
    """
    Eliminar todos los matches de una vacante
    
    Útil para volver a ejecutar el matching con nuevos parámetros
    """
    vacancies = await get_vacancies_collection()
    matches_coll = await get_matches_collection()
    
    # Verificar vacante
    if not ObjectId.is_valid(vacancy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID"
        )
    
    vacancy = await vacancies.find_one({"_id": ObjectId(vacancy_id)})
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if str(vacancy["company_id"]) != str(current_company.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Eliminar matches
    result = await matches_coll.delete_many({"vacancy_id": ObjectId(vacancy_id)})
    
    # Actualizar contador
    await vacancies.update_one(
        {"_id": ObjectId(vacancy_id)},
        {"$set": {"num_candidatos_matched": 0}}
    )
    
    return {
        "message": "All matches deleted successfully",
        "matches_deleted": result.deleted_count
    }


# ============= ENDPOINTS ADMIN =============

@router.get("/admin/stats", response_model=dict)
async def get_matching_stats(current_user: UserInDB = Depends(get_current_user)):
    """
    Estadísticas del sistema de matching (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    matches_coll = await get_matches_collection()
    
    total_matches = await matches_coll.count_documents({})
    
    # Porcentaje promedio de matching
    pipeline_avg = [
        {"$group": {
            "_id": None,
            "avg_match": {"$avg": "$porcentaje_match"},
            "max_match": {"$max": "$porcentaje_match"},
            "min_match": {"$min": "$porcentaje_match"}
        }}
    ]
    
    avg_stats = await matches_coll.aggregate(pipeline_avg).to_list(length=1)
    stats = avg_stats[0] if avg_stats else {"avg_match": 0, "max_match": 0, "min_match": 0}
    
    # Distribución de matches por rango de porcentaje
    ranges = [
        (80, 100, "Excelente"),
        (70, 79, "Muy bueno"),
        (60, 69, "Bueno"),
        (0, 59, "Regular")
    ]
    
    distribution = {}
    for min_p, max_p, label in ranges:
        count = await matches_coll.count_documents({
            "porcentaje_match": {"$gte": min_p, "$lte": max_p}
        })
        distribution[label] = count
    
    return {
        "total_matches": total_matches,
        "porcentaje_promedio": round(stats.get("avg_match", 0), 2),
        "porcentaje_maximo": round(stats.get("max_match", 0), 2),
        "porcentaje_minimo": round(stats.get("min_match", 0), 2),
        "distribucion": distribution
    }
