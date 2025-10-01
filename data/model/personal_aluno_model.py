from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class PersonalAluno:
    """Relacionamento entre Personal e Aluno"""
    id: int
    personal_id: int
    aluno_id: int  # referência ao Cliente
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    status: str = 'ativo'  # ativo, inativo, cancelado
    objetivo: Optional[str] = None  # Ex: "Perda de peso", "Ganho de massa"
    observacoes: Optional[str] = None
