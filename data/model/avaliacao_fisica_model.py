from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class AvaliacaoFisica:
    """Avaliação física do aluno"""
    id: int
    personal_aluno_id: int  # referência ao relacionamento Personal-Aluno
    data_avaliacao: datetime
    peso: Optional[float] = None
    altura: Optional[float] = None
    imc: Optional[float] = None
    percentual_gordura: Optional[float] = None
    massa_magra: Optional[float] = None
    circunferencias: Optional[str] = None  # JSON com medidas (pescoço, braço, cintura, etc)
    observacoes: Optional[str] = None
    proxima_avaliacao: Optional[datetime] = None
