from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Artigo:
    id: int
    profissional_id: int       # referência ao Profissional
    titulo: str
    conteudo: str
    gratuito: bool = True
    data_publicacao: datetime = datetime.now()