from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Exercicio:
    id: int
    nome: str
    descricao: Optional[str] = None
    grupo_muscular: Optional[str] = None  # Ex: Peito, Costas, Pernas
    imagem: Optional[str] = None  # URL ou caminho para imagem do exercício
    id_profissional: Optional[int] = None  # ID do profissional que criou o exercício
    series: int