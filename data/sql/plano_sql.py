CRIAR_TABELA_PLANO = """
CREATE TABLE IF NOT EXISTS plano (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL
);
"""

INSERIR_PLANO = """
INSERT INTO plano (nome, preco)
VALUES (?, ?)
"""

ALTERAR_PLANO = """
UPDATE plano
SET nome=?, preco=?
WHERE id=?
"""

EXCLUIR_PLANO = """
DELETE FROM plano
WHERE id=?
"""

OBTER_POR_ID_PLANO = """
SELECT id, nome, preco
FROM plano
WHERE id=?
"""

OBTER_TODOS_PLANO = """
SELECT id, nome, preco
FROM plano
ORDER BY nome
"""
