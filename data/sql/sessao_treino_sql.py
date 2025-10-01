CRIAR_TABELA_SESSAO_TREINO = """
CREATE TABLE IF NOT EXISTS sessao_treino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    treino_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    ordem INTEGER NOT NULL,
    dia_semana TEXT,
    descricao TEXT,
    tempo_estimado INTEGER,
    status TEXT DEFAULT 'ativo',
    FOREIGN KEY (treino_id) REFERENCES treino_personalizado(id) ON DELETE CASCADE
);
"""

INSERIR_SESSAO_TREINO = """
INSERT INTO sessao_treino (
    treino_id, nome, ordem, dia_semana, 
    descricao, tempo_estimado, status
)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_SESSAO_TREINO = """
UPDATE sessao_treino
SET treino_id=?, nome=?, ordem=?, dia_semana=?,
    descricao=?, tempo_estimado=?, status=?
WHERE id=?
"""

EXCLUIR_SESSAO_TREINO = """
DELETE FROM sessao_treino WHERE id=?
"""

OBTER_POR_ID_SESSAO_TREINO = """
SELECT * FROM sessao_treino WHERE id=?
"""

OBTER_TODOS_SESSAO_TREINO = """
SELECT * FROM sessao_treino ORDER BY ordem
"""

OBTER_POR_TREINO = """
SELECT * FROM sessao_treino 
WHERE treino_id=? AND status='ativo'
ORDER BY ordem
"""
