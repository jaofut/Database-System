import sys
import os
import struct
tamanho_pag = 4096
def gravador(local_arquivo, page_id,slot_id, dados:str):
    tamanho_pag = 4096
    tamanho_cabecalho = 16
    tamanho_registro = 8
    dados_em_bytes = dados.encode("utf-8")
    if not os.path.exists(local_arquivo):
        with open(local_arquivo , "wb") as arquivo:
            inicio_gravacao =tamanho_pag * page_id
            arquivo.seek(inicio_gravacao)
            arquivo.write(bytearray(tamanho_pag)) #preenchendo a página de bytes de valores nulo
    if len(dados_em_bytes) <= tamanho_registro:
        with open(local_arquivo, "r+b") as arquivo: #gravando os dados
            inicio_gravacao = (tamanho_pag *page_id) +tamanho_cabecalho + (tamanho_registro*slot_id)
            arquivo.seek(inicio_gravacao)
            arquivo.write(dados_em_bytes)
    else: 
        print("Tamanho dos dados excede o tamanho máximo de um registro")


                   
def leitor(local_arquivo , page_id):
    tamanho_pag = 4096
    with open(local_arquivo , "rb") as arquivo:
        inicio_leitura = tamanho_pag * page_id
        arquivo.seek(inicio_leitura) #seek serve para indicar onde será o inicio da leitura
        dados_pagina= arquivo.read(tamanho_pag)

        return dados_pagina

def deslocamento(page_id,slot_id):

    return (tamanho_pag *page_id) +tamanho_cabecalho + (tamanho_registro*slot_id)
        
def serializador(dados1, dados2):
    dados_serializados = struct.pack("<II",dados1,dados2)
    return dados_serializados




