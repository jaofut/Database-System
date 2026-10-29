from cache import Cache
from pager_indice import PagerIndice
from parser import analisa
from catalogo import (Catalogo, ASSINATURA, PAGINA_ASSINATURA, PAGINA_CATALOGO,
                      ESQUEMA_CATALOGO, aloca_pagina, total_paginas, le_registros,
                      grava_registro)
import semantica

class Resultado:

    def __init__(self, mensagem=None, colunas=None, linhas=None):
        self.mensagem = mensagem
        self.colunas = colunas
        self.linhas = linhas

    def __str__(self):
        if self.colunas is None:
            return self.mensagem
        tabela = [self.colunas] + [[str(v) for v in linha] for linha in self.linhas]
        larguras = [max(len(l[i]) for l in tabela) for i in range(len(self.colunas))]
        fmt = lambda l: " | ".join(c.ljust(w) for c, w in zip(l, larguras)).rstrip()
        saida = [fmt(tabela[0]), "-+-".join("-" * w for w in larguras)]
        saida += [fmt(l) for l in tabela[1:]]
        saida.append(f"({len(self.linhas)} linha{'' if len(self.linhas) == 1 else 's'})")
        return "\n".join(saida)


class MiniDB:
    def __init__(self, caminho, capacidade=16):
        self.pager = PagerIndice(caminho)
        self.cache = Cache(self.pager, capacidade)
        if total_paginas(self.pager) == 0:
            self._cria_arquivo()
        elif self.cache_le_assinatura() != ASSINATURA:
            self.pager.fecha()
            raise ValueError(f"{caminho} não é um arquivo do MiniDB")
        self.catalogo = Catalogo(self.cache)

    def _cria_arquivo(self):
        self.pager.aloca(PAGINA_ASSINATURA)
        self.pager.escreve(PAGINA_ASSINATURA, ASSINATURA)
        pagina = aloca_pagina(self.pager, ESQUEMA_CATALOGO.tamanho)
        assert pagina == PAGINA_CATALOGO
        self.pager.sync()

    def cache_le_assinatura(self):
        frame = self.cache.fixa(PAGINA_ASSINATURA)
        self.cache.solta(PAGINA_ASSINATURA)
        return frame[:len(ASSINATURA)]


    def executa(self, sql):
        arvore = analisa(sql)                                 
        if arvore["op"] == "CREATE":
            semantica.confere_create(self.catalogo, arvore)    
            primeira = aloca_pagina(self.pager, sum(t for _, _, t in arvore["colunas"]))  
            self.catalogo.registra(arvore["tabela"], primeira, arvore["colunas"])
            return Resultado("OK")
        if arvore["op"] == "INSERT":
            primeira, esquema = semantica.confere_insert(self.catalogo, arvore)  
            grava_registro(self.cache, self.pager, primeira, esquema, arvore["valores"])  
            return Resultado("OK 1")
        if arvore["op"] == "SELECT":
            primeira, esquema, projecao, filtro = semantica.confere_select(self.catalogo, arvore)
            linhas = []
            for linha in le_registros(self.cache, primeira, esquema):     
                if filtro is None or linha[filtro[0]] == filtro[1]:      
                    linhas.append(tuple(linha[i] for i in projecao))
            nomes = [esquema.colunas[i][0] for i in projecao]
            return Resultado(colunas=nomes, linhas=linhas)

    def descarrega(self):
        self.cache.descarrega()

    def fecha(self):
        self.descarrega()
        self.pager.fecha()
