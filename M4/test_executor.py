import os
import tempfile
import unittest

from executor import MiniDB
from catalogo import capacidade, PAGINA_CATALOGO, ESQUEMA_CATALOGO


class BaseBanco(unittest.TestCase):
    CAPACIDADE_CACHE = 16

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.caminho = os.path.join(self.dir.name, "t.db")
        self.db = MiniDB(self.caminho, self.CAPACIDADE_CACHE)

    def tearDown(self):
        try:
            self.db.fecha()
        except ValueError:         
            pass
        self.dir.cleanup()

    def reabre(self):
        self.db.fecha()
        self.db = MiniDB(self.caminho, self.CAPACIDADE_CACHE)

    def bytes_do_arquivo(self):
        self.db.descarrega()
        with open(self.caminho, "rb") as f:
            return f.read()


class TestCreateInsertSelect(BaseBanco):
    def setUp(self):
        super().setUp()
        self.db.executa("CREATE TABLE aluno (id INT, matricula INT, nome CHAR(20))")

    def test_mensagens(self):
        self.assertEqual(str(self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")), "OK 1")

    def test_select_todos(self):
        self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")
        self.db.executa("INSERT INTO aluno VALUES (2, 20260002, 'Bruno')")
        r = self.db.executa("SELECT * FROM aluno")
        self.assertEqual(r.colunas, ["id", "matricula", "nome"])
        self.assertEqual(r.linhas, [(1, 20260001, "Ana"), (2, 20260002, "Bruno")])

    def test_select_tabela_vazia(self):
        self.assertEqual(self.db.executa("SELECT * FROM aluno").linhas, [])

    def test_projecao_respeita_a_ordem_pedida(self):
        self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")
        r = self.db.executa("SELECT nome, id FROM aluno")
        self.assertEqual(r.colunas, ["nome", "id"])
        self.assertEqual(r.linhas, [("Ana", 1)])

    def test_where_em_int(self):
        for i, n in enumerate(["Ana", "Bruno", "Carla"], 1):
            self.db.executa(f"INSERT INTO aluno VALUES ({i}, {20260000 + i}, '{n}')")
        self.assertEqual(self.db.executa("SELECT nome FROM aluno WHERE id = 2").linhas, [("Bruno",)])

    def test_where_em_char(self):
        for i, n in enumerate(["Ana", "Bruno", "Carla"], 1):
            self.db.executa(f"INSERT INTO aluno VALUES ({i}, {20260000 + i}, '{n}')")
        self.assertEqual(self.db.executa("SELECT id FROM aluno WHERE nome = 'Carla'").linhas, [(3,)])

    def test_where_sem_resultado(self):
        self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")
        self.assertEqual(self.db.executa("SELECT * FROM aluno WHERE id = 99").linhas, [])

    def test_where_devolve_todas_as_linhas_iguais(self):
        for _ in range(3):
            self.db.executa("INSERT INTO aluno VALUES (7, 1, 'Ana')")
        self.assertEqual(len(self.db.executa("SELECT * FROM aluno WHERE id = 7").linhas), 3)

    def test_valores_extremos_e_texto_vazio_e_acentos(self):
        self.db.executa("INSERT INTO aluno VALUES (0, 2147483647, '')")
        self.db.executa("INSERT INTO aluno VALUES (5, 3, 'José Ângelo')")
        self.assertEqual(self.db.executa("SELECT * FROM aluno").linhas,
                         [(0, 2147483647, ""), (5, 3, "José Ângelo")])

    def test_tabelas_independentes(self):
        self.db.executa("CREATE TABLE curso (codigo INT, titulo CHAR(10))")
        self.db.executa("INSERT INTO aluno VALUES (1, 1, 'Ana')")
        self.db.executa("INSERT INTO curso VALUES (9, 'BD2')")
        self.assertEqual(self.db.executa("SELECT * FROM curso").linhas, [(9, "BD2")])
        self.assertEqual(self.db.executa("SELECT * FROM aluno").linhas, [(1, 1, "Ana")])

    def test_saida_formatada(self):
        self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")
        texto = str(self.db.executa("SELECT id, nome FROM aluno"))
        self.assertEqual(texto, "id | nome\n---+-----\n1  | Ana\n(1 linha)")


class TestPaginas(BaseBanco):
    def test_tabela_ocupa_varias_paginas(self):
        self.db.executa("CREATE TABLE t (id INT, nome CHAR(20))")      
        por_pagina = capacidade(24)
        total = por_pagina * 2 + 5
        for i in range(total):
            self.db.executa(f"INSERT INTO t VALUES ({i}, 'n{i}')")
        linhas = self.db.executa("SELECT * FROM t").linhas
        self.assertEqual(linhas, [(i, f"n{i}") for i in range(total)])
        self.assertEqual(len(self.bytes_do_arquivo()) // 4096, 2 + 3)    

    def test_registro_que_ocupa_a_pagina_inteira(self):
        self.db.executa("CREATE TABLE grande (x CHAR(4080))")
        self.db.executa("INSERT INTO grande VALUES ('a')")
        self.db.executa("INSERT INTO grande VALUES ('b')")
        self.assertEqual(self.db.executa("SELECT * FROM grande").linhas, [("a",), ("b",)])

    def test_where_atravessa_paginas(self):
        self.db.executa("CREATE TABLE t (id INT, nome CHAR(20))")
        total = capacidade(24) + 10
        for i in range(total):
            self.db.executa(f"INSERT INTO t VALUES ({i}, 'x')")
        self.assertEqual(self.db.executa(f"SELECT id FROM t WHERE id = {total - 1}").linhas, [(total - 1,)])

    def test_catalogo_com_mais_tabelas_do_que_cabem_em_uma_pagina(self):
        n = capacidade(ESQUEMA_CATALOGO.tamanho) + 3
        for i in range(n):
            self.db.executa(f"CREATE TABLE t{i} (a INT)")
            self.db.executa(f"INSERT INTO t{i} VALUES ({i})")
        self.reabre()
        self.assertEqual(len(self.db.catalogo.tabelas), n)
        self.assertEqual(self.db.executa(f"SELECT a FROM t{n - 1}").linhas, [(n - 1,)])


class TestCachePequeno(BaseBanco):
    CAPACIDADE_CACHE = 2         

    def test_funciona_com_cache_de_duas_paginas(self):
        self.db.executa("CREATE TABLE t (id INT, nome CHAR(20))")
        total = capacidade(24) * 3 + 1
        for i in range(total):
            self.db.executa(f"INSERT INTO t VALUES ({i}, 'x')")
        self.assertEqual(len(self.db.executa("SELECT * FROM t").linhas), total)
        self.assertGreater(self.db.cache.faltas, 0)
        self.assertTrue(all(v == 0 for v in self.db.cache.fixada.values()))   

    def test_nenhuma_pagina_fica_fixada_depois_de_erro(self):
        with self.assertRaises(Exception):
            self.db.executa("INSERT INTO nao_existe VALUES (1)")
        self.assertTrue(all(v == 0 for v in self.db.cache.fixada.values()))


class TestPersistencia(BaseBanco):
    def test_processo_novo_sabe_que_aluno_existe(self):
        self.db.executa("CREATE TABLE aluno (id INT, matricula INT, nome CHAR(20))")
        self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")
        self.reabre()
        self.assertIn("aluno", self.db.catalogo.tabelas)
        self.assertEqual(self.db.executa("SELECT * FROM aluno").linhas, [(1, 20260001, "Ana")])

    def test_continua_inserindo_depois_de_reabrir(self):
        self.db.executa("CREATE TABLE t (id INT)")
        self.db.executa("INSERT INTO t VALUES (1)")
        self.reabre()
        self.db.executa("INSERT INTO t VALUES (2)")
        self.reabre()
        self.assertEqual(self.db.executa("SELECT * FROM t").linhas, [(1,), (2,)])

    def test_esquema_lido_do_disco_confere_tipos(self):
        self.db.executa("CREATE TABLE t (id INT, nome CHAR(3))")
        self.reabre()
        with self.assertRaises(Exception):
            self.db.executa("INSERT INTO t VALUES (1, 'abcd')")

    def test_sem_descarregar_o_disco_nao_tem_o_dado(self):
        
        self.db.executa("CREATE TABLE t (id INT)")
        self.db.descarrega()
        self.db.executa("INSERT INTO t VALUES (1)")
        with open(self.caminho, "rb") as f:
            self.assertNotIn(b"\x01\x00\x00\x00", f.read()[8192 + 16:8192 + 20])
        self.assertEqual(self.bytes_do_arquivo()[8192 + 16:8192 + 20], b"\x01\x00\x00\x00")

    def test_arquivo_que_nao_e_minidb_e_recusado(self):
        self.db.fecha()
        outro = os.path.join(self.dir.name, "lixo.db")
        with open(outro, "wb") as f:
            f.write(b"X" * 4096)
        with self.assertRaises(ValueError):
            MiniDB(outro)
        self.db = MiniDB(self.caminho)


class TestGabaritoHexdump(BaseBanco):
    

    def test_bytes_da_pagina_2(self):
        self.db.executa("CREATE TABLE aluno (id INT, matricula INT, nome CHAR(20))")
        self.assertEqual(str(self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")), "OK 1")
        dados = self.bytes_do_arquivo()
        esperado = bytes.fromhex(
            "0100 1c00 02000000 00000000 00000000"     
            "01000000 a1243501 416e61 0000000000"     
            "000000000000000000000000 00000000")       
        self.assertEqual(len(esperado), 48)
        self.assertEqual(dados[8192:8192 + 48], esperado)
        self.assertEqual(0x013524a1, 20260001)

    def test_registro_termina_em_0000202b(self):
        self.db.executa("CREATE TABLE aluno (id INT, matricula INT, nome CHAR(20))")
        self.db.executa("INSERT INTO aluno VALUES (1, 20260001, 'Ana')")
        dados = self.bytes_do_arquivo()
        self.assertEqual(dados[0x2010 + 8 + 3: 0x202c], b"\x00" * 17)   
        self.assertEqual(dados[0x202c], 0)

    def test_catalogo_na_pagina_1_aponta_para_a_pagina_2(self):
        self.db.executa("CREATE TABLE aluno (id INT, matricula INT, nome CHAR(20))")
        self.assertEqual(self.db.catalogo.busca("aluno")[0], 2)        
        dados = self.bytes_do_arquivo()
        reg = dados[4096 + 16: 4096 + 16 + ESQUEMA_CATALOGO.tamanho]
        self.assertEqual(reg[:32].rstrip(b"\x00"), b"aluno")
        self.assertEqual(int.from_bytes(reg[32:36], "little"), 2)
        self.assertEqual(reg[36:].rstrip(b"\x00"), b"id:INT:4,matricula:INT:4,nome:CHAR:20")


if __name__ == "__main__":
    unittest.main(verbosity=2)
