import os
import tempfile
import unittest

from executor import MiniDB
from catalogo import ErroSemantico


class BaseBanco(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = MiniDB(os.path.join(self.dir.name, "t.db"))
        self.db.executa("CREATE TABLE aluno (id INT, matricula INT, nome CHAR(20))")

    def tearDown(self):
        self.db.fecha()
        self.dir.cleanup()

    def erro(self, sql, trecho):
        with self.assertRaises(ErroSemantico) as c:
            self.db.executa(sql)
        self.assertIn(trecho, str(c.exception))


class TestSemanticaInsert(BaseBanco):
    def test_insert_valido_passa(self):
        self.assertEqual(str(self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")), "OK 1")

    def test_tabela_inexistente(self):
        self.erro("INSERT INTO professor VALUES (1)", "tabela professor não existe")

    def test_valores_a_menos(self):
        self.erro("INSERT INTO aluno VALUES (1, 2)", "esperava 3 valores, vieram 2")

    def test_valores_a_mais(self):
        self.erro("INSERT INTO aluno VALUES (1, 2, 'Ana', 4)", "esperava 3 valores, vieram 4")

    def test_texto_em_coluna_int(self):
        self.erro("INSERT INTO aluno VALUES ('um', 2, 'Ana')", "coluna id é INT")

    def test_numero_entre_aspas_nao_e_int(self):
        self.erro("INSERT INTO aluno VALUES ('1', 2, 'Ana')", "coluna id é INT")

    def test_numero_em_coluna_char(self):
        self.erro("INSERT INTO aluno VALUES (1, 2, 3)", "coluna nome é CHAR(20)")

    def test_int_fora_de_32_bits(self):
        self.erro("INSERT INTO aluno VALUES (2147483648, 2, 'Ana')", "coluna id é INT")

    def test_int_maximo_de_32_bits_passa(self):
        self.db.executa("INSERT INTO aluno VALUES (2147483647, 0, 'Ana')")

    def test_texto_maior_que_char(self):
        self.erro("INSERT INTO aluno VALUES (1, 2, '%s')" % ("a" * 21), "coluna nome é CHAR(20)")

    def test_texto_exatamente_do_tamanho_passa(self):
        self.db.executa("INSERT INTO aluno VALUES (1, 2, '%s')" % ("a" * 20))

    def test_char_conta_bytes_e_nao_letras(self):
       
        self.erro("INSERT INTO aluno VALUES (1, 2, '%s')" % ("ã" * 11), "coluna nome é CHAR(20)")

    def test_insert_invalido_nao_grava_nada(self):
        self.erro("INSERT INTO aluno VALUES (1, 2, 3)", "CHAR")
        self.assertEqual(self.db.executa("SELECT * FROM aluno").linhas, [])


class TestSemanticaCreate(BaseBanco):
    def test_tabela_repetida(self):
        self.erro("CREATE TABLE aluno (x INT)", "tabela aluno já existe")

    def test_coluna_repetida(self):
        self.erro("CREATE TABLE t (a INT, a CHAR(5))", "coluna a repetida")

    def test_char_zero(self):
        self.erro("CREATE TABLE t (a CHAR(0))", "maior que zero")

    def test_registro_maior_que_pagina(self):
        self.erro("CREATE TABLE t (a CHAR(5000))", "não cabe em uma página")

    def test_nome_de_tabela_muito_longo(self):
        self.erro("CREATE TABLE %s (a INT)" % ("t" * 33), "nome de tabela")

    def test_colunas_demais_para_o_catalogo(self):
        colunas = ", ".join(f"coluna_numero_{i} INT" for i in range(20))
        self.erro(f"CREATE TABLE t ({colunas})", "descrição das colunas")

    def test_create_invalido_nao_registra_tabela(self):
        self.erro("CREATE TABLE t (a INT, a INT)", "repetida")
        self.erro("SELECT * FROM t", "tabela t não existe")


class TestSemanticaSelect(BaseBanco):
    def test_tabela_inexistente(self):
        self.erro("SELECT * FROM professor", "tabela professor não existe")

    def test_coluna_inexistente_na_projecao(self):
        self.erro("SELECT idade FROM aluno", "coluna idade não existe")

    def test_coluna_inexistente_no_where(self):
        self.erro("SELECT * FROM aluno WHERE idade = 1", "coluna idade não existe")

    def test_where_com_tipo_errado(self):
        self.erro("SELECT * FROM aluno WHERE id = 'um'", "coluna id é INT")
        self.erro("SELECT * FROM aluno WHERE nome = 1", "coluna nome é CHAR(20)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
