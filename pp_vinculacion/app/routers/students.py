"""
Router de Estudiantes
Endpoints para gestión de perfiles de estudiantes
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import os

from app.models.student import (
    StudentProfile,
    StudentInDB,
    StudentUpdate,
    StudentPublicProfile,
    Idioma,
    Experiencia,
    Proyecto,
    Certificacion
)
from app.models.user import UserInDB
from app.database import get_students_collection, get_users_collection
from app.config import settings

# Importar cuando tengamos el módulo de auth completo
from app.routers.auth import get_current_user
from app.limiter import limiter

router = APIRouter()


# ============= FUNCIONES AUXILIARES =============

def student_helper(student) -> dict:
    """Convertir documento de MongoDB a dict"""
    return {
        "_id": str(student["_id"]),
        "user_id": str(student["user_id"]),
        **{k: v for k, v in student.items() if k not in ["_id", "user_id"]}
    }


async def get_current_student(current_user: UserInDB = Depends(get_current_user)) -> StudentInDB:
    """Obtener estudiante actual"""
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    students = await get_students_collection()
    student = await students.find_one({"user_id": current_user.id})
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    return StudentInDB(**student)


def check_profile_completeness(student: dict) -> bool:
    """Verificar si el perfil está completo"""
    required_fields = [
        "nombre_completo",
        "carrera",
        "semestre",
        "habilidades_tecnicas",
        "habilidades_blandas",
        "idiomas"
    ]
    
    for field in required_fields:
        if not student.get(field):
            return False
    
    # Al menos 3 habilidades técnicas
    if len(student.get("habilidades_tecnicas", [])) < 3:
        return False
    
    # Al menos 1 idioma
    if len(student.get("idiomas", [])) < 1:
        return False
    
    return True


# ============= ENDPOINTS =============

@router.post("/profile", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_student_profile(
    profile: StudentProfile,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Crear perfil de estudiante
    
    Solo usuarios con rol 'estudiante' pueden crear su perfil
    """
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create student profiles"
        )
    
    students = await get_students_collection()
    
    # Verificar si ya tiene perfil
    existing_profile = await students.find_one({"user_id": current_user.id})
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile already exists. Use PUT to update"
        )
    
    # Verificar que la matrícula no esté en uso
    matricula_exists = await students.find_one({"matricula": profile.matricula})
    if matricula_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Matricula already registered"
        )
    
    # Crear perfil
    student_dict = profile.dict()
    student_dict["user_id"] = current_user.id
    student_dict["created_at"] = datetime.utcnow()
    student_dict["updated_at"] = datetime.utcnow()
    student_dict["perfil_completo"] = check_profile_completeness(student_dict)
    student_dict["visible_empresas"] = True
    
    result = await students.insert_one(student_dict)
    student_dict["_id"] = str(result.inserted_id)
    
    return {
        "message": "Student profile created successfully",
        "profile_id": str(result.inserted_id),
        "perfil_completo": student_dict["perfil_completo"]
    }


@router.get("/profile", response_model=dict)
async def get_my_profile(current_user: UserInDB = Depends(get_current_user)):
    """
    Obtener mi perfil de estudiante
    
    Si no existe, devuelve estructura vacía indicando que debe crearse
    """
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    students = await get_students_collection()
    student = await students.find_one({"user_id": current_user.id})
    
    # Si no existe perfil, devolver indicador
    if not student:
        return {
            "exists": False,
            "message": "Profile not created yet. Use POST /api/students/profile to create",
            "user_id": str(current_user.id)
        }
    
    return {
        "exists": True,
        **student_helper(student)
    }


@router.put("/profile", response_model=dict)
async def update_my_profile(
    profile_update: StudentUpdate,
    current_student: StudentInDB = Depends(get_current_student)
):
    """
    Actualizar mi perfil de estudiante
    
    Solo se actualizan los campos proporcionados
    """
    students = await get_students_collection()
    
    # Obtener solo los campos que no son None
    update_data = {k: v for k, v in profile_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Agregar fecha de actualización
    update_data["updated_at"] = datetime.utcnow()
    
    # Actualizar perfil
    await students.update_one(
        {"_id": current_student.id},
        {"$set": update_data}
    )
    
    # Verificar si el perfil está completo
    updated_student = await students.find_one({"_id": current_student.id})
    perfil_completo = check_profile_completeness(updated_student)
    
    await students.update_one(
        {"_id": current_student.id},
        {"$set": {"perfil_completo": perfil_completo}}
    )
    
    return {
        "message": "Profile updated successfully",
        "perfil_completo": perfil_completo,
        "updated_fields": list(update_data.keys())
    }


@router.post("/profile/cv", response_model=dict)
@limiter.limit(lambda: settings.upload_limit)
async def upload_cv(
    request: Request,
    cv: UploadFile = File(...),
    current_student: StudentInDB = Depends(get_current_student)
):
    """
    Subir CV (PDF o DOCX)
    
    Tamaño máximo: configurado en settings.max_file_size_mb
    """
    # Validar extensión
    allowed_extensions = [".pdf", ".docx", ".doc"]
    file_ext = os.path.splitext(cv.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validar tamaño
    cv_content = await cv.read()
    file_size_mb = len(cv_content) / (1024 * 1024)
    
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Crear directorio si no existe
    cv_dir = os.path.join(settings.upload_dir, "cvs")
    os.makedirs(cv_dir, exist_ok=True)
    
    # Guardar archivo con nombre único
    filename = f"{current_student.matricula}_{datetime.utcnow().timestamp()}{file_ext}"
    file_path = os.path.join(cv_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(cv_content)
    
    # Actualizar perfil con info del CV
    students = await get_students_collection()
    await students.update_one(
        {"_id": current_student.id},
        {"$set": {
            "cv_filename": filename,
            "cv_upload_date": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "message": "CV uploaded successfully",
        "filename": filename,
        "size_mb": round(file_size_mb, 2)
    }


@router.delete("/profile/cv", response_model=dict)
async def delete_cv(current_student: StudentInDB = Depends(get_current_student)):
    """
    Eliminar CV actual
    """
    if not current_student.cv_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CV found"
        )
    
    # Eliminar archivo físico
    cv_path = os.path.join(settings.upload_dir, "cvs", current_student.cv_filename)
    if os.path.exists(cv_path):
        os.remove(cv_path)
    
    # Actualizar base de datos
    students = await get_students_collection()
    await students.update_one(
        {"_id": current_student.id},
        {"$set": {
            "cv_filename": None,
            "cv_upload_date": None,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "CV deleted successfully"}


@router.post("/profile/experiencia", response_model=dict)
async def add_experiencia(
    experiencia: Experiencia,
    current_student: StudentInDB = Depends(get_current_student)
):
    """
    Agregar experiencia laboral
    """
    students = await get_students_collection()
    
    await students.update_one(
        {"_id": current_student.id},
        {
            "$push": {"experiencia_laboral": experiencia.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Work experience added successfully"}


@router.post("/profile/proyecto", response_model=dict)
async def add_proyecto(
    proyecto: Proyecto,
    current_student: StudentInDB = Depends(get_current_student)
):
    """
    Agregar proyecto
    """
    students = await get_students_collection()
    
    await students.update_one(
        {"_id": current_student.id},
        {
            "$push": {"proyectos": proyecto.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Project added successfully"}


@router.post("/profile/certificacion", response_model=dict)
async def add_certificacion(
    certificacion: Certificacion,
    current_student: StudentInDB = Depends(get_current_student)
):
    """
    Agregar certificación
    """
    students = await get_students_collection()
    
    await students.update_one(
        {"_id": current_student.id},
        {
            "$push": {"certificaciones": certificacion.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Certification added successfully"}


@router.get("/profile/public/{matricula}", response_model=StudentPublicProfile)
async def get_student_public_profile(
    matricula: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtener perfil público de un estudiante (solo matrícula visible)
    
    Solo empresas y admins pueden ver esto
    """
    if current_user.role not in ["empresa", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies and admins can view student profiles"
        )
    
    students = await get_students_collection()
    student = await students.find_one({"matricula": matricula})
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    if not student.get("visible_empresas", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student profile is not visible"
        )
    
    # Retornar perfil público (sin datos personales)
    return StudentPublicProfile(
        matricula=student["matricula"],
        carrera=student.get("carrera", ""),
        semestre=student.get("semestre", 0),
        habilidades_tecnicas=student.get("habilidades_tecnicas", []),
        habilidades_blandas=student.get("habilidades_blandas", []),
        idiomas=student.get("idiomas", []),
        areas_interes=student.get("areas_interes", []),
        modalidad_preferida=student.get("modalidad_preferida", ""),
        descripcion_breve=student.get("descripcion_breve"),
        tiene_experiencia=len(student.get("experiencia_laboral", [])) > 0,
        num_proyectos=len(student.get("proyectos", [])),
        num_certificaciones=len(student.get("certificaciones", []))
    )


@router.patch("/profile/visibility", response_model=dict)
async def toggle_visibility(
    visible: bool,
    current_student: StudentInDB = Depends(get_current_student)
):
    """
    Cambiar visibilidad del perfil para empresas
    """
    students = await get_students_collection()
    
    await students.update_one(
        {"_id": current_student.id},
        {"$set": {
            "visible_empresas": visible,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "message": f"Profile {'visible' if visible else 'hidden'} to companies",
        "visible_empresas": visible
    }


@router.delete("/profile", response_model=dict)
async def delete_my_profile(
    password: str,
    current_user: UserInDB = Depends(get_current_user),
    current_student: StudentInDB = Depends(get_current_student)
):
    """
    Eliminar mi perfil de estudiante (requiere contraseña)
    
    ADVERTENCIA: Esta acción es irreversible
    """
    from app.routers.auth import verify_password
    
    # Verificar contraseña
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    students = await get_students_collection()
    
    # Eliminar CV si existe
    if current_student.cv_filename:
        cv_path = os.path.join(settings.upload_dir, "cvs", current_student.cv_filename)
        if os.path.exists(cv_path):
            os.remove(cv_path)
    
    # Eliminar perfil
    await students.delete_one({"_id": current_student.id})
    
    return {"message": "Student profile deleted successfully"}


# ============= ENDPOINTS ADMIN =============

@router.get("/admin/all", response_model=List[dict])
async def get_all_students(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtener todos los estudiantes (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    students = await get_students_collection()
    student_list = await students.find().skip(skip).limit(limit).to_list(length=limit)
    
    return [student_helper(student) for student in student_list]


@router.get("/admin/stats", response_model=dict)
async def get_student_stats(current_user: UserInDB = Depends(get_current_user)):
    """
    Estadísticas de estudiantes (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    students = await get_students_collection()
    
    total = await students.count_documents({})
    con_perfil_completo = await students.count_documents({"perfil_completo": True})
    con_cv = await students.count_documents({"cv_filename": {"$ne": None}})
    visibles = await students.count_documents({"visible_empresas": True})
    
    # Carreras más comunes
    pipeline = [
        {"$group": {"_id": "$carrera", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    carreras = await students.aggregate(pipeline).to_list(length=10)
    
    # Habilidades más comunes
    pipeline_skills = [
        {"$unwind": "$habilidades_tecnicas"},
        {"$group": {"_id": "$habilidades_tecnicas", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    habilidades = await students.aggregate(pipeline_skills).to_list(length=10)
    
    return {
        "total_estudiantes": total,
        "con_perfil_completo": con_perfil_completo,
        "con_cv": con_cv,
        "visibles_empresas": visibles,
        "porcentaje_completos": round((con_perfil_completo / total * 100) if total > 0 else 0, 2),
        "carreras_mas_comunes": [{"carrera": c["_id"], "count": c["count"]} for c in carreras],
        "habilidades_mas_demandadas": [{"habilidad": h["_id"], "count": h["count"]} for h in habilidades]
    }