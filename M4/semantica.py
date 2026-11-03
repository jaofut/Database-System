from catalogo import (ErroSemantico, ESQUEMA_CATALOGO, TAMANHO_PAGINA, TAMANHO_CABECALHO,
                      descreve_colunas)

INT_MIN, INT_MAX = -(1 << 31), (1 << 31) - 1

def confere_valor(coluna, valor):
    nome, tipo, tam = coluna
    if tipo == "INT":
        if type(valor) is not int or not INT_MIN <= valor <= INT_MAX:
            raise ErroSemantico(f"coluna {nome} é INT (inteiro de 32 bits)")
    else:
        if type(valor) is not str or "\x00" in valor or len(valor.encode("utf-8")) > tam:
            raise ErroSemantico(f"coluna {nome} é CHAR({tam})")


def confere_create(catalogo, arvore):
    tabela, colunas = arvore["tabela"], arvore["colunas"]
    if tabela in catalogo.tabelas:
        raise ErroSemantico(f"tabela {tabela} já existe")
    limites = dict((nome, tam) for nome, _, tam in ESQUEMA_CATALOGO.colunas)
    if len(tabela.encode("utf-8")) > limites["nome"]:
        raise ErroSemantico(f"nome de tabela maior que {limites['nome']} bytes")
    vistos = set()
    for nome, tipo, tam in colunas:
        if nome in vistos:
            raise ErroSemantico(f"coluna {nome} repetida")
        vistos.add(nome)
        if tipo == "CHAR" and tam < 1:
            raise ErroSemantico(f"coluna {nome}: CHAR precisa de tamanho maior que zero")
    if sum(tam for _, _, tam in colunas) > TAMANHO_PAGINA - TAMANHO_CABECALHO:
        raise ErroSemantico("registro não cabe em uma página")
    if len(descreve_colunas(colunas).encode("utf-8")) > limites["colunas"]:
        raise ErroSemantico(f"descrição das colunas maior que {limites['colunas']} bytes")


def confere_insert(catalogo, arvore):
  
    primeira, esquema = catalogo.busca(arvore["tabela"])         
    valores = arvore["valores"]
    if len(valores) != len(esquema.colunas):                     
        raise ErroSemantico(f"esperava {len(esquema.colunas)} valores, vieram {len(valores)}")
    for coluna, valor in zip(esquema.colunas, valores):           
        confere_valor(coluna, valor)
    return primeira, esquema


def confere_select(catalogo, arvore):
    primeira, esquema = catalogo.busca(arvore["tabela"])
    if arvore["colunas"] == ["*"]:
        projecao = list(range(len(esquema.colunas)))
    else:
        projecao = [esquema.posicao(nome) for nome in arvore["colunas"]]
    filtro = None
    if arvore["where"] is not None:
        nome, valor = arvore["where"]
        posicao = esquema.posicao(nome)
        confere_valor(esquema.colunas[posicao], valor)
        filtro = (posicao, valor)
    return primeira, esquema, projecao, filtro
