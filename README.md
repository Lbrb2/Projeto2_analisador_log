# Projeto 2 — Analisador de Log de Servidor HTTP

BD015 - Algoritmo e Estrutura de Dados | Aula 7 (Persistência de Dados em Arquivos)

**Aluno:** Lucas Barreto Rodrigues de Barros

## Objetivo

Sistema de auditoria e monitoramento de servidores: lê o arquivo de tráfego
`acesso.log` e contabiliza quantas requisições retornaram o código **HTTP 200**
(Sucesso) e quantas retornaram **404** (Não Encontrado).

## Arquivos

| Arquivo | Descrição |
|---|---|
| `analisador_log.py` | Script principal |
| `acesso.log` | Arquivo de tráfego analisado |
| `relatorio.txt` | Relatório gerado pelo script |

## Como executar

Com os arquivos na mesma pasta:

```
python analisador_log.py
```

Para analisar um log com outro nome, basta informá-lo na execução:

```
python analisador_log.py servidor_producao.log
```

O relatório é exibido na tela e gravado em `relatorio.txt`.

### Codificação do arquivo

O script tenta ler o log em UTF-8 e, se encontrar bytes fora desse padrão,
relê automaticamente em Latin-1, avisando na tela. Isso evita que um log
gerado por um servidor antigo derrube o programa com `UnicodeDecodeError`.

## Formato de cada linha do log

O log segue o *Common Log Format*, usado pelos servidores Apache e Nginx:

```
189.45.112.6 - - [08/Oct/2026:08:05:06 -0300] "GET /produtos HTTP/1.1" 200 3258
└──────────────────┬─────────────────────────┘ └──────────┬──────────┘ └┬┘
          antes das aspas: IP e data               entre aspas:      depois:
                                                método e página      código
```

A requisição sempre aparece entre aspas duplas, então o script usa as aspas
como ponto de referência: divide a linha com `split('"')` e pega o código no
primeiro campo depois delas.

### Por que não contar posições fixas

A primeira versão pegava o código pela posição 8 de `split()`. Funciona no
formato acima, mas quebra silenciosamente em logs sem o fuso horário na data:

```
10.0.0.1 - - [08/Oct/2026:10:00:00] "GET /a HTTP/1.1" 200 100
```

Aqui há um campo a menos, tudo desloca uma posição, e a posição 8 passa a
conter `100` — o tamanho da resposta — em vez de `200`. O programa não
acusaria erro: contaria `100` como se fosse um código HTTP. Usar as aspas
como referência elimina esse risco, porque não importa quantos campos existem
antes delas.

### Formatos aceitos

| Variação | Aceita |
|---|---|
| Common Log Format | sim |
| Combined (com *referer* e *user-agent*) | sim |
| Sem fuso horário na data | sim |
| Com usuário autenticado no lugar dos hífens | sim |
| CSV, JSON ou outro formato sem aspas | não — as linhas são ignoradas e contabilizadas |

## Conceitos da Aula 7 aplicados

| Conceito | Onde aparece |
|---|---|
| `with open(...)` | Abertura do log e do relatório, com fechamento automático |
| Modo `'r'` | Leitura do `acesso.log` |
| Modo `'w'` | Gravação do `relatorio.txt` |
| `encoding='utf-8'` | Nas duas aberturas, com Latin-1 como alternativa na leitura |
| `for linha in arquivo` | Leitura sob demanda, uma linha por vez |
| `.strip()` | Remove o `\n` e espaços invisíveis de cada linha |
| `.split()` | Separa a linha em campos, usando as aspas como referência |
| `try/except` | Trata `FileNotFoundError` e `UnicodeDecodeError` na leitura |

## Decisões de implementação

**Leitura linha a linha.** O script usa `for linha in arquivo` em vez de
`read()` ou `readlines()`. Logs de servidor chegam facilmente a gigabytes, e os
dois últimos carregariam o arquivo inteiro na memória RAM de uma só vez.

**Linhas fora do formato não interrompem a análise.** Linhas em branco ou
corrompidas são contadas à parte e ignoradas, em vez de quebrar o programa.
O relatório informa quantas foram descartadas.

**Dicionário acumulador.** As contagens usam
`contagem[chave] = contagem.get(chave, 0) + 1`, o mesmo padrão de um `GROUP BY`:
o `.get()` devolve zero na primeira ocorrência da chave, permitindo criar e
somar na mesma linha.

**Conferência no relatório.** A última seção mostra linhas lidas, válidas,
ignoradas e a soma das contagens por código. Válidas e soma devem sempre
coincidir — é a verificação de que nenhuma requisição foi perdida ou contada
duas vezes.
