CRIAR_TABELA_CLIENTE = """
CREATE TABLE IF NOT EXISTS cliente (
    id INTEGER PRIMARY KEY,
    plano_id INTEGER,
    FOREIGN KEY (id) REFERENCES usuario(id),
    FOREIGN KEY (plano_id) REFERENCES plano(id)
);
"""

INSERIR_CLIENTE = """
INSERT INTO cliente (id, plano_id)
VALUES (?, ?)
"""

ALTERAR_CLIENTE = """
UPDATE cliente
SET plano_id=?
WHERE id=?
"""

EXCLUIR_CLIENTE = """
DELETE FROM cliente
WHERE id=?
"""

OBTER_POR_ID_CLIENTE = """
SELECT c.id, c.plano_id, u.nome, u.email, u.senha
FROM cliente c
INNER JOIN usuario u ON c.id = u.id
WHERE c.id=?
"""

OBTER_TODOS_CLIENTE = """
SELECT c.id, c.plano_id, u.nome, u.email, u.senha
FROM cliente c
INNER JOIN usuario u ON c.id = u.id
ORDER BY u.nome
"""
