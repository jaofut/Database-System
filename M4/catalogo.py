
import struct

TAMANHO_PAGINA = 4096
TAMANHO_CABECALHO = 16
CABECALHO = struct.Struct("<HHII")
ASSINATURA = b"MINIDB01"
PAGINA_ASSINATURA = 0
PAGINA_CATALOGO = 1          

class ErroSemantico(Exception):
    """Exceção lançada quando o comando é válido na sintaxe mas não bate com o banco"""


class Esquema:
    

    def __init__(self, colunas):
        self.colunas = [tuple(c) for c in colunas]
        self.tamanho = sum(t for _, _, t in self.colunas)

    def nomes(self):
        return [nome for nome, _, _ in self.colunas]

    def posicao(self, nome):
        for i, (n, _, _) in enumerate(self.colunas):
            if n == nome:
                return i
        raise ErroSemantico(f"coluna {nome} não existe")

    def serializa(self, valores):
        partes = []
        for (nome, tipo, tam), v in zip(self.colunas, valores):
            if tipo == "INT":
                partes.append(struct.pack("<i", v))
            else:
                partes.append(v.encode("utf-8").ljust(tam, b"\x00"))
        return b"".join(partes)

    def desserializa(self, dados):
        valores, p = [], 0
        for _, tipo, tam in self.colunas:
            pedaco = dados[p:p + tam]
            p += tam
            if tipo == "INT":
                valores.append(struct.unpack("<i", pedaco)[0])
            else:
                valores.append(pedaco.rstrip(b"\x00").decode("utf-8"))
        return tuple(valores)


ESQUEMA_CATALOGO = Esquema([("nome", "CHAR", 32), ("primeira", "INT", 4),
                            ("colunas", "CHAR", 200)])


def descreve_colunas(colunas):
   
    return ",".join(f"{n}:{t}:{tam}" for n, t, tam in colunas)


def analisa_colunas(texto):
    
    colunas = []
    for parte in texto.split(","):
        nome, tipo, tam = parte.split(":")
        colunas.append((nome, tipo, int(tam)))
    return colunas




def capacidade(tamanho_registro):
    return (TAMANHO_PAGINA - TAMANHO_CABECALHO) // tamanho_registro


def pagina_nova(numero, tamanho_registro):
    pagina = bytearray(TAMANHO_PAGINA)
    CABECALHO.pack_into(pagina, 0, 0, tamanho_registro, numero, 0)
    return pagina


def total_paginas(pager):
    pager.arquivo.seek(0, 2)
    return pager.arquivo.tell() // TAMANHO_PAGINA


def aloca_pagina(pager, tamanho_registro):
    
    numero = total_paginas(pager)
    pager.aloca(numero)
    pager.escreve(numero, pagina_nova(numero, tamanho_registro))
    return numero


def le_registros(cache, primeira, esquema):
    
    n = primeira
    while n:
        frame = cache.fixa(n)
        try:
            ocupados, tam, _, proxima = CABECALHO.unpack_from(frame, 0)
            linhas = [esquema.desserializa(frame[TAMANHO_CABECALHO + s * tam:
                                                  TAMANHO_CABECALHO + (s + 1) * tam])
                      for s in range(ocupados)]
        finally:
            cache.solta(n)          
        yield from linhas
        n = proxima


def grava_registro(cache, pager, primeira, esquema, valores):
    
    registro = esquema.serializa(valores)
    n = primeira
    while True:                                   
        frame = cache.fixa(n)
        ocupados, tam, _, proxima = CABECALHO.unpack_from(frame, 0)
        if proxima == 0:
            break
        cache.solta(n)
        n = proxima

    if ocupados < capacidade(tam):
        novo = bytearray(frame)
        inicio = TAMANHO_CABECALHO + ocupados * tam
        novo[inicio:inicio + tam] = registro
        struct.pack_into("<H", novo, 0, ocupados + 1)
        cache.frames[n] = bytes(novo)
        cache.solta(n, sujou=True)
        return n, ocupados

    
    nova = aloca_pagina(pager, tam)
    novo = bytearray(frame)
    struct.pack_into("<I", novo, 8, nova)
    cache.frames[n] = bytes(novo)
    cache.solta(n, sujou=True)
    return grava_registro(cache, pager, nova, esquema, valores)




class Catalogo:
    def __init__(self, cache):                     
        self.cache = cache
        self.tabelas = {}
        for nome, primeira, colunas in le_registros(cache, PAGINA_CATALOGO, ESQUEMA_CATALOGO):
            self.tabelas[nome] = (primeira, Esquema(analisa_colunas(colunas)))

    def busca(self, nome):
        if nome not in self.tabelas:
            raise ErroSemantico(f"tabela {nome} não existe")
        return self.tabelas[nome]

    def registra(self, nome, primeira, colunas):
        
        grava_registro(self.cache, self.cache.pager, PAGINA_CATALOGO, ESQUEMA_CATALOGO,
                       (nome, primeira, descreve_colunas(colunas)))
        self.tabelas[nome] = (primeira, Esquema(colunas))
