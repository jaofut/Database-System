import os
import struct

class Pager:
    def __init__(self, local_arquivo):
        self.local_arquivo = local_arquivo
        self.tamanho_pag = 4096
        self.tamanho_cabecalho = 16
        self.tamanho_registro = 8
        self.arquivo = None

        if not os.path.exists(self.local_arquivo):
            self.arquivo = open(self.local_arquivo, "w+b")
        else:
            self.arquivo = open(self.local_arquivo, "r+b")

    def aloca(self, page_id):
        inicio_gravacao = self.tamanho_pag * page_id
        self.arquivo.seek(inicio_gravacao)
        self.arquivo.write(bytearray(self.tamanho_pag))
        #self.sync() #precisa forçar a escrita no hd dessa função que aloca uma página?

    def escreve(self,page_id,dados):
        if type(dados) != str:
            dados = str(dados)
        dados_em_binario = dados.encode("utf-8")
        inicio_gravacao = self.tamanho_pag * page_id
        self.arquivo.seek(inicio_gravacao)
        self.arquivo.write(dados_em_binario)
        self.sync()

    def escreve_registro_unico(self, page_id, slot_id, dados):
        if type(dados) != str:
            dados = str(dados)
        dados_em_binario = dados.encode("utf-8")
        if len(dados_em_binario) > self.tamanho_registro:
            print("Tamanho dos dados excede o tamanho máximo de um registro")
            return 
        inicio_gravacao = self.deslocamento(page_id, slot_id)
        self.arquivo.seek(inicio_gravacao)
        self.arquivo.write(dados_em_binario)
        self.sync()
        
    def le(self, page_id):
        self.arquivo = open(self.local_arquivo, "r+b")
        inicio_leitura = self.tamanho_pag * page_id
        self.arquivo.seek(inicio_leitura)
        return self.arquivo.read(self.tamanho_pag)

    def sync(self):
        if self.arquivo:
            self.arquivo.flush()
            os.fsync(self.arquivo.fileno())

    def fecha(self):
            self.arquivo.close()
   
            
    
    def deslocamento(self, page_id, slot_id):
        return (self.tamanho_pag * page_id) + self.tamanho_cabecalho + (self.tamanho_registro * slot_id)
        
    def serializador(self, dados1):
        return struct.pack("<I", dados1)

