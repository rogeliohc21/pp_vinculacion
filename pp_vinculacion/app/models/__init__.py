"""
Modelos de datos de la aplicación
"""
from app.models.base import PyObjectId

from app.models.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserInDB,
    UserResponse,
    Token,
    TokenData
)

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

from app.models.company import (
    CompanyProfile,
    CompanyInDB,
    CompanyUpdate,
    CompanyPublicProfile
)

from app.models.vacancy import (
    VacancyCreate,
    VacancyInDB,
    VacancyUpdate,
    VacancyPublic,
    IdiomaRequerido,
    Requisito
)

from app.models.match import (
    MatchCreate,
    MatchInDB,
    MatchResponse,
    MatchListResponse,
    MatchDesglose,
    RadarChartData
)

from app.models.contact_request import (
    ContactRequestCreate,
    ContactRequestInDB,
    ContactRequestUpdate,
    ContactRequestResponse,
    StudentContactInfo,
    ContactRequestList
)

from app.models.message import (
    MessageCreate,
    MessageInDB,
    MessageResponse,
    MessageAdminResponse,
    MessageUpdate,
    MessageList,
    MessageStats
)

__all__ = [
    # Bsase
    "PyObjectId",
    # User
    "UserBase", "UserCreate", "UserLogin", "UserInDB", "UserResponse", "Token", "TokenData",
    # Student
    "StudentProfile", "StudentInDB", "StudentUpdate", "StudentPublicProfile",
    "Idioma", "Experiencia", "Proyecto", "Certificacion",
    # Company
    "CompanyProfile", "CompanyInDB", "CompanyUpdate", "CompanyPublicProfile",
    # Vacancy
    "VacancyCreate", "VacancyInDB", "VacancyUpdate", "VacancyPublic",
    "IdiomaRequerido", "Requisito",
    # Match
    "MatchCreate", "MatchInDB", "MatchResponse", "MatchListResponse",
    "MatchDesglose", "RadarChartData",
    # Contact Request
    "ContactRequestCreate", "ContactRequestInDB", "ContactRequestUpdate",
    "ContactRequestResponse", "StudentContactInfo", "ContactRequestList",
    # Message
    "MessageCreate", "MessageInDB", "MessageResponse", "MessageAdminResponse",
    "MessageUpdate", "MessageList", "MessageStats"
]
