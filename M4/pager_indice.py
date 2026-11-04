from service_pager import Pager


class PagerIndice(Pager):
    def _validar_id(self, page_id):
        if type(page_id) is not int or page_id < 0:
            raise ValueError("ID de página deve ser um inteiro não negativo")

    def _abrir(self):
        if self.arquivo is None or self.arquivo.closed:
            self.arquivo = open(self.local_arquivo, "r+b")

    def le(self, page_id):
        self._validar_id(page_id)
        self._abrir()
        self.arquivo.seek(page_id * self.tamanho_pag)
        return self.arquivo.read(self.tamanho_pag)

    def escreve(self, page_id, dados):
        self._validar_id(page_id)
        if not isinstance(dados, (bytes, bytearray)):
            raise TypeError("O pager do índice recebe bytes ou bytearray")
        if len(dados) > self.tamanho_pag:
            raise ValueError("Conteúdo maior que uma página")
        self._abrir()
        self.arquivo.seek(page_id * self.tamanho_pag)
        self.arquivo.write(bytes(dados).ljust(self.tamanho_pag, b"\x00"))
