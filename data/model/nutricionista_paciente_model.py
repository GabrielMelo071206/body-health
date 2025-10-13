from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class NutricionistaPaciente:
    """Relacionamento entre Nutricionista e Paciente"""
    id: int
    nutricionista_id: int
    paciente_id: int  # referência ao Cliente
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    status: str = 'ativo'  # ativo, inativo, cancelado
    objetivo: Optional[str] = None  # Ex: "Emagrecimento", "Ganho de massa"
    observacoes: Optional[str] = None  # Alergias, restrições alimentares, medicamentos