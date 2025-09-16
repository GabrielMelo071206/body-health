CRIAR_TABELA_ASSINATURA = """
CREATE TABLE IF NOT EXISTS assinatura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    plano_id INTEGER NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT,
    status TEXT DEFAULT 'ativo',
    FOREIGN KEY (cliente_id) REFERENCES cliente(id),
    FOREIGN KEY (plano_id) REFERENCES plano(id)
);
"""

INSERIR_ASSINATURA = """
INSERT INTO assinatura (cliente_id, plano_id, data_inicio, data_fim, status)
VALUES (?, ?, ?, ?, ?)
"""

ALTERAR_ASSINATURA = """
UPDATE assinatura
SET plano_id=?, data_inicio=?, data_fim=?, status=?
WHERE id=?
"""

EXCLUIR_ASSINATURA = """
DELETE FROM assinatura
WHERE id=?
"""

OBTER_POR_ID_ASSINATURA = """
SELECT a.id, a.cliente_id, a.plano_id, a.data_inicio, a.data_fim, a.status,
       u.nome, u.email, p.nome AS plano_nome
FROM assinatura a
INNER JOIN cliente c ON a.cliente_id = c.id
INNER JOIN usuario u ON c.id = u.id
INNER JOIN plano p ON a.plano_id = p.id
WHERE a.id=?
"""

OBTER_TODOS_ASSINATURA = """
SELECT a.id, a.cliente_id, a.plano_id, a.data_inicio, a.data_fim, a.status,
       u.nome, u.email, p.nome AS plano_nome
FROM assinatura a
INNER JOIN cliente c ON a.cliente_id = c.id
INNER JOIN usuario u ON c.id = u.id
INNER JOIN plano p ON a.plano_id = p.id
ORDER BY u.nome
"""
