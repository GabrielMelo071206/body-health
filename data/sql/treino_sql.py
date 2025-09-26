@dataclass
class Treino:
    id: int
    id_cliente: int
    id_profissional: int
    capa: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    duracao: Optional[int] = None
    nivel_dificuldade: Optional[str] = None
    objetivo: Optional[str] = None
    status: str = 'ativo'
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
    criado_por: Optional[int] = None  
    atualizado_por: Optional[int] = None 




CRIAR_TABELA_TREINO = """
CREATE TABLE IF NOT EXISTS treino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL,
    id_profissional INTEGER NOT NULL,
    capa TEXT,
    nome TEXT NOT NULL,
    descricao TEXT,
    duracao INTEGER,
    nivel_dificuldade TEXT,
    objetivo TEXT,
    status TEXT DEFAULT 'ativo',
    criado_em DATETIME,
    atualizado_em DATETIME,
    criado_por INTEGER,
    atualizado_por INTEGER
);
"""

INSERIR_TREINO = """
INSERT INTO treino (nome, descricao, duracao, nivel_dificuldade, objetivo, status, criado_em, atualizado_em, criado_por, atualizado_por)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_TREINO = """
UPDATE treino
SET nome=?, descricao=?, duracao=?, nivel_dificuldade=?, objetivo=?, status=?, criado_em=?, atualizado_em=?, criado_por=?, atualizado_por=?
WHERE id=(?, ?)
"""

EXCLUIR_TREINO = """
DELETE FROM treino
WHERE id=?
"""

OBTER_POR_ID_TREINO = """
SELECT id, nome, descricao, gratuito
FROM treino
WHERE id=?
"""

OBTER_TODOS_TREINO = """
SELECT id, nome, descricao, gratuito
FROM treino
ORDER BY nome
"""
