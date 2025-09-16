CRIAR_TABELA_ARTIGO = """
CREATE TABLE IF NOT EXISTS artigo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    gratuito INTEGER DEFAULT 1,   -- 1=visível para todos, 0=só para plano
    data_publicacao TEXT NOT NULL,
    FOREIGN KEY (profissional_id) REFERENCES profissional(id)
);
"""

INSERIR_ARTIGO = """
INSERT INTO artigo (profissional_id, titulo, conteudo, gratuito, data_publicacao)
VALUES (?, ?, ?, ?, ?)
"""

ALTERAR_ARTIGO = """
UPDATE artigo
SET titulo=?, conteudo=?, gratuito=?, data_publicacao=?
WHERE id=?
"""

EXCLUIR_ARTIGO = """
DELETE FROM artigo
WHERE id=?
"""

OBTER_POR_ID_ARTIGO = """
SELECT a.id, a.profissional_id, a.titulo, a.conteudo, a.gratuito, a.data_publicacao,
       u.nome, u.email
FROM artigo a
INNER JOIN profissional p ON a.profissional_id = p.id
INNER JOIN usuario u ON p.id = u.id
WHERE a.id=?
"""

OBTER_TODOS_ARTIGO = """
SELECT a.id, a.profissional_id, a.titulo, a.conteudo, a.gratuito, a.data_publicacao,
       u.nome, u.email
FROM artigo a
INNER JOIN profissional p ON a.profissional_id = p.id
INNER JOIN usuario u ON p.id = u.id
ORDER BY a.data_publicacao DESC
"""
