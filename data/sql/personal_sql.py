CRIAR_TABELA_PERSONAL = """
CREATE TABLE IF NOT EXISTS personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER NOT NULL,
    cref TEXT,
    especialidades TEXT,
    biografia TEXT,
    anos_experiencia INTEGER,
    valor_mensalidade REAL,
    status TEXT DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    foto_perfil TEXT,
    avaliacoes_media REAL,
    total_alunos INTEGER DEFAULT 0,
    FOREIGN KEY (profissional_id) REFERENCES profissional(id) ON DELETE CASCADE
);
"""

INSERIR_PERSONAL = """
INSERT INTO personal (
    profissional_id, cref, especialidades, biografia, 
    anos_experiencia, valor_mensalidade, status, data_cadastro,
    foto_perfil, avaliacoes_media, total_alunos
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_PERSONAL = """
UPDATE personal
SET profissional_id=?, cref=?, especialidades=?, biografia=?,
    anos_experiencia=?, valor_mensalidade=?, status=?, 
    foto_perfil=?, avaliacoes_media=?, total_alunos=?
WHERE id=?
"""

EXCLUIR_PERSONAL = """
DELETE FROM personal WHERE id=?
"""

OBTER_POR_ID_PERSONAL = """
SELECT p.*, u.nome, u.email, prof.especialidade
FROM personal p
INNER JOIN profissional prof ON p.profissional_id = prof.id
INNER JOIN usuario u ON prof.id = u.id
WHERE p.id=?
"""

OBTER_TODOS_PERSONAL = """
SELECT p.*, u.nome, u.email, prof.especialidade
FROM personal p
INNER JOIN profissional prof ON p.profissional_id = prof.id
INNER JOIN usuario u ON prof.id = u.id
WHERE p.status = 'ativo'
ORDER BY u.nome
"""

OBTER_POR_PROFISSIONAL = """
SELECT * FROM personal WHERE profissional_id=?
"""
