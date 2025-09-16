CRIAR_TABELA_DIETA = """
CREATE TABLE IF NOT EXISTS dieta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    gratuito INTEGER DEFAULT 1  -- 1=gratuito, 0=apenas plano
);
"""

INSERIR_DIETA = """
INSERT INTO dieta (nome, descricao, gratuito)
VALUES (?, ?, ?)
"""

ALTERAR_DIETA = """
UPDATE dieta
SET nome=?, descricao=?, gratuito=?
WHERE id=?
"""

EXCLUIR_DIETA = """
DELETE FROM dieta
WHERE id=?
"""

OBTER_POR_ID_DIETA = """
SELECT id, nome, descricao, gratuito
FROM dieta
WHERE id=?
"""

OBTER_TODOS_DIETA = """
SELECT id, nome, descricao, gratuito
FROM dieta
ORDER BY nome
"""
