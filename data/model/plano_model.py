from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Plano:
    id: int
    nome: str
    descricao: str
    preco: float           # 0.0 se gratuito
    duracao_dias: int      # duração do plano em dias
    ativo: bool = True     # NOVO CAMPO
    data_criacao: datetime = None