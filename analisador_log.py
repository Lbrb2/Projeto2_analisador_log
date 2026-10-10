"""
Projeto 2 - Analisador de Log de Servidor HTTP
BD015 - Algoritmo e Estrutura de Dados | Aula 7 (Persistência em Arquivos)

Lê o arquivo de tráfego 'acesso.log' e contabiliza quantas requisições
retornaram o código 200 (Sucesso) e quantas retornaram 404 (Não Encontrado).

Formato esperado de cada linha (Common Log Format):

    IP - - [data] "METODO /pagina HTTP/1.1" CODIGO TAMANHO
    └──────┬─────┘ └─────────┬───────────┘  └──┬─┘
      antes das          entre aspas        depois das
        aspas                                 aspas
"""

import sys

ARQUIVO_LOG_PADRAO = "acesso.log"
ARQUIVO_RELATORIO = "relatorio.txt"

# Tentadas nesta ordem. Latin-1 aceita qualquer byte, então serve de
# último recurso para logs antigos que não estão em UTF-8.
CODIFICACOES = ("utf-8", "latin-1")

ASPAS = '"'
TAMANHO_DO_CODIGO_HTTP = 3


def extrair_dados(linha):
    """Separa uma linha do log em (ip, pagina, codigo).

    A requisição sempre aparece entre aspas duplas, então as aspas são
    usadas como ponto de referência para localizar os campos. Contar
    posições a partir do início seria frágil: logs sem o fuso horário na
    data, por exemplo, têm um campo a menos e deslocariam tudo, fazendo o
    programa ler o tamanho da resposta achando que é o código HTTP.

    Devolve None quando a linha está vazia ou fora do formato esperado,
    para que o programa simplesmente a ignore em vez de quebrar.
    """
    linha_limpa = linha.strip()
    if not linha_limpa:
        return None

    pedacos = linha_limpa.split(ASPAS)
    if len(pedacos) < 3:
        return None

    antes_das_aspas = pedacos[0].split()    # IP, identidade, usuário, data
    requisicao = pedacos[1].split()         # MÉTODO, página, versão HTTP
    depois_das_aspas = pedacos[2].split()   # código, tamanho

    if not antes_das_aspas or len(requisicao) < 2 or not depois_das_aspas:
        return None

    codigo = depois_das_aspas[0]
    # Códigos HTTP têm sempre três dígitos (200, 404, 500...)
    if not codigo.isdigit() or len(codigo) != TAMANHO_DO_CODIGO_HTTP:
        return None

    ip = antes_das_aspas[0]
    pagina = requisicao[1]

    return ip, pagina, codigo


def analisar_log(caminho, codificacao):
    """Percorre o arquivo linha por linha e acumula as estatísticas.

    A leitura usa 'for linha in arquivo', que carrega uma linha de cada vez
    em vez do arquivo inteiro — importante porque logs reais são enormes.
    """
    contagem_codigos = {}
    contagem_paginas = {}
    contagem_ips = {}
    total_de_linhas = 0
    linhas_validas = 0
    linhas_ignoradas = 0

    with open(caminho, "r", encoding=codificacao) as arquivo:
        for linha in arquivo:
            total_de_linhas += 1

            dados = extrair_dados(linha)
            if dados is None:
                linhas_ignoradas += 1
                continue

            ip, pagina, codigo = dados
            linhas_validas += 1

            # Dicionário acumulador: cria a chave na primeira ocorrência
            # e soma nas seguintes (mesma lógica de um GROUP BY).
            contagem_codigos[codigo] = contagem_codigos.get(codigo, 0) + 1
            contagem_paginas[pagina] = contagem_paginas.get(pagina, 0) + 1
            contagem_ips[ip] = contagem_ips.get(ip, 0) + 1

    return {
        "codigos": contagem_codigos,
        "paginas": contagem_paginas,
        "ips": contagem_ips,
        "total_de_linhas": total_de_linhas,
        "linhas_validas": linhas_validas,
        "linhas_ignoradas": linhas_ignoradas,
    }


def calcular_percentual(parte, total):
    if total == 0:
        return 0.0
    return (parte / total) * 100


def montar_relatorio(estatisticas):
    """Monta o texto do relatório e devolve como uma única string."""
    codigos = estatisticas["codigos"]
    validas = estatisticas["linhas_validas"]

    sucessos = codigos.get("200", 0)
    nao_encontrados = codigos.get("404", 0)

    linhas = []
    linhas.append("=" * 52)
    linhas.append("RELATORIO DE AUDITORIA - SERVIDOR HTTP")
    linhas.append("=" * 52)
    linhas.append("")

    linhas.append("RESULTADO PRINCIPAL")
    linhas.append(f"  Requisicoes 200 (Sucesso).........: {sucessos}")
    linhas.append(f"  Requisicoes 404 (Nao Encontrado)..: {nao_encontrados}")

    if nao_encontrados > 0:
        proporcao = sucessos / nao_encontrados
        linhas.append(f"  Proporcao 200 para 404............: {proporcao:.2f} para 1")
    else:
        linhas.append("  Proporcao 200 para 404............: nenhum 404 registrado")

    linhas.append("")
    linhas.append("TODOS OS CODIGOS ENCONTRADOS")
    for codigo in sorted(codigos):
        quantidade = codigos[codigo]
        percentual = calcular_percentual(quantidade, validas)
        barra = "#" * int(percentual / 4)
        linhas.append(f"  {codigo}: {quantidade:>3} requisicao(oes)  "
                      f"{percentual:5.1f}%  {barra}")

    linhas.append("")
    linhas.append("PAGINAS MAIS ACESSADAS")
    for pagina, quantidade in ordenar_por_quantidade(estatisticas["paginas"])[:5]:
        linhas.append(f"  {quantidade:>3}x  {pagina}")

    linhas.append("")
    linhas.append("IPS MAIS ATIVOS")
    for ip, quantidade in ordenar_por_quantidade(estatisticas["ips"])[:5]:
        linhas.append(f"  {quantidade:>3}x  {ip}")

    linhas.append("")
    linhas.append("CONFERENCIA DA LEITURA")
    linhas.append(f"  Linhas lidas do arquivo...........: {estatisticas['total_de_linhas']}")
    linhas.append(f"  Linhas validas processadas........: {validas}")
    linhas.append(f"  Linhas ignoradas (fora do formato): {estatisticas['linhas_ignoradas']}")
    linhas.append(f"  Soma das contagens por codigo.....: {sum(codigos.values())}")
    linhas.append("=" * 52)

    return "\n".join(linhas)


def ordenar_por_quantidade(contagem):
    """Ordena o dicionário da maior para a menor quantidade."""
    return sorted(contagem.items(), key=lambda item: item[1], reverse=True)


def salvar_relatorio(texto, caminho):
    """Grava o relatório em disco no modo 'w' (cria ou sobrescreve)."""
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto + "\n")


def obter_caminho_do_log():
    """Usa o nome passado na linha de comando ou, na falta dele, o padrão."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return ARQUIVO_LOG_PADRAO


def analisar_com_codificacao_tolerante(caminho):
    """Analisa o log tentando cada codificação até uma funcionar.

    Logs gerados por servidores antigos nem sempre estão em UTF-8. Sem este
    tratamento, um único byte fora do padrão derrubaria o programa inteiro
    com UnicodeDecodeError.
    """
    for codificacao in CODIFICACOES:
        try:
            return analisar_log(caminho, codificacao), codificacao
        except UnicodeDecodeError:
            continue  # tenta a próxima da lista
    return None, None


def main():
    caminho = obter_caminho_do_log()

    try:
        estatisticas, codificacao = analisar_com_codificacao_tolerante(caminho)
    except FileNotFoundError:
        # O modo 'r' falha quando o arquivo não existe
        print(f"[ERRO] O arquivo '{caminho}' nao foi encontrado.")
        print(f"Coloque o log na mesma pasta deste script com o nome "
              f"'{ARQUIVO_LOG_PADRAO}',")
        print("ou informe outro nome ao executar:")
        print("    python analisador_log.py meu_arquivo.log")
        return

    if estatisticas is None:
        print(f"[ERRO] Nao foi possivel ler '{caminho}' com as codificacoes "
              f"testadas: {', '.join(CODIFICACOES)}.")
        return

    if codificacao != CODIFICACOES[0]:
        print(f"[AVISO] O arquivo nao esta em {CODIFICACOES[0]}. "
              f"Lido como {codificacao}.\n")

    relatorio = montar_relatorio(estatisticas)
    print(relatorio)

    salvar_relatorio(relatorio, ARQUIVO_RELATORIO)
    print(f"\nRelatorio gravado em '{ARQUIVO_RELATORIO}'.")


if __name__ == "__main__":
    main()
