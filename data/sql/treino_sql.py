CRIAR_TABELA_TREINO = """
CREATE TABLE IF NOT EXISTS treino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    gratuito INTEGER DEFAULT 1  -- 1=gratuito, 0=apenas plano
);
"""

INSERIR_TREINO = """
INSERT INTO treino (nome, descricao, gratuito)
VALUES (?, ?, ?)
"""

ALTERAR_TREINO = """
UPDATE treino
SET nome=?, descricao=?, gratuito=?
WHERE id=?
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
