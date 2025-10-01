from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ProgressoAluno:
    """Registro de progresso do aluno"""
    id: int
    personal_aluno_id: int
    data_registro: datetime
    peso: Optional[float] = None
    medidas: Optional[str] = None  # JSON com medidas
    fotos: Optional[str] = None  # URLs das fotos de progresso
    observacoes: Optional[str] = None
    humor: Optional[str] = None  # Como o aluno está se sentindo
    energia: Optional[int] = None  # Nível de energia (1-10)

