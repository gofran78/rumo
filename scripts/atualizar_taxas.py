"""Atualiza as taxas do Banco Central dentro do index.html do Trilha.

Busca no SGS (Sistema Gerenciador de Séries Temporais do Banco Central):
  12  - CDI diário (% ao dia)
  11  - Selic diária (% ao dia)
  433 - IPCA mensal (%)
  195 - Poupança: rentabilidade de cada data de aniversário (%)
  432 - Selic meta (% ao ano)

e troca só a linha `const BCB = {...};` do arquivo, no mesmo formato compacto que a página lê.
Usa só a biblioteca padrão do Python. Se alguma série falhar, não mexe no arquivo.

Uso: python scripts/atualizar_taxas.py index.html
"""
import datetime as dt
import json
import re
import sys
import time
import urllib.request

API = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.{s}/dados?formato=json&dataInicial={a}&dataFinal={b}'


def baixar(serie, inicio, fim):
    """Baixa uma série em janelas de até 10 anos (limite da API para séries diárias)."""
    linhas, a = [], inicio
    while a <= fim:
        b = min(fim, dt.date(a.year + 9, 12, 31))
        url = API.format(s=serie, a=a.strftime('%d/%m/%Y'), b=b.strftime('%d/%m/%Y'))
        for tentativa in range(4):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    linhas += json.load(r)
                break
            except Exception as e:  # rede instável ou 5xx: tenta de novo
                if tentativa == 3:
                    raise RuntimeError(f'série {serie} ({a} a {b}): {e}')
                time.sleep(5 * (tentativa + 1))
        a = dt.date(b.year + 1, 1, 1)
    vistos, saida = set(), []
    for r in linhas:
        if r['data'] not in vistos:
            vistos.add(r['data'])
            saida.append(r)
    saida.sort(key=lambda r: data(r['data']))
    return saida


def data(s):
    return dt.datetime.strptime(s, '%d/%m/%Y').date()


def b36(n):
    s, neg, n = '', n < 0, abs(n)
    while True:
        n, r = divmod(n, 36)
        s = '0123456789abcdefghijklmnopqrstuvwxyz'[r] + s
        if not n:
            break
    return ('-' if neg else '') + s


def rle(vals):
    """Repetições seguidas viram valor*quantidade, em base 36."""
    out, i = [], 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        n = j - i + 1
        v = '' if vals[i] is None else b36(vals[i])
        out.append(v + ('*' + b36(n) if n > 1 else ''))
        i = j + 1
    return ','.join(out)


def diaria(serie, hoje):
    rows = baixar(serie, dt.date(2000, 1, 1), hoje)
    ds = [data(r['data']) for r in rows]
    gaps = ''.join(str((ds[k] - ds[k - 1]).days) for k in range(1, len(ds)))
    if not all(c in '123456789' for c in gaps):
        raise RuntimeError(f'série {serie}: intervalo inesperado entre dias úteis')
    vals = [round(float(r['valor']) * 1e6) for r in rows]
    return {'d0': ds[0].isoformat(), 'g': gaps, 'v': rle(vals), 'n': len(ds), 'last': ds[-1].isoformat()}


def main(caminho):
    hoje = dt.date.today()
    cdi, selic = diaria('12', hoje), diaria('11', hoje)
    ip = baixar('433', dt.date(1995, 1, 1), hoje)
    ipca = {'m0': data(ip[0]['data']).strftime('%Y-%m'), 'v': rle([round(float(r['valor']) * 100) for r in ip]),
            'n': len(ip), 'last': data(ip[-1]['data']).strftime('%Y-%m')}
    pr = baixar('195', dt.date(2012, 5, 4), hoje)
    pd = {data(r['data']): round(float(r['valor']) * 1e4) for r in pr}
    p0, p1 = min(pd), max(pd)
    pv, x = [], p0
    while x <= p1:
        pv.append(pd.get(x))
        x += dt.timedelta(days=1)
    poup = {'d0': p0.isoformat(), 'v': rle(pv), 'n': len(pv), 'last': p1.isoformat()}
    meta = [r for r in baixar('432', dt.date(hoje.year - 1, 1, 1), hoje) if data(r['data']) <= hoje]
    dados = {'asOf': hoje.isoformat(), 'cdi': cdi, 'selic': selic, 'ipca': ipca, 'poup': poup,
             'selicMeta': float(meta[-1]['valor'])}

    html = open(caminho, encoding='utf-8').read()
    linha = 'const BCB = ' + json.dumps(dados, separators=(',', ':')) + ';'
    novo, n = re.subn(r'^const BCB = \{.*\};$', lambda m: linha, html, count=1, flags=re.M)
    if n != 1:
        raise RuntimeError('não achei a linha "const BCB = {...};" no arquivo')
    # proteção: nunca trocar por menos dados do que já havia
    antigo = json.loads(re.search(r'^const BCB = (\{.*\});$', html, flags=re.M).group(1))
    for k in ('cdi', 'selic', 'ipca', 'poup'):
        if dados[k]['n'] < antigo[k]['n']:
            raise RuntimeError(f'{k}: veio com menos dados ({dados[k]["n"]}) do que o arquivo tinha ({antigo[k]["n"]})')
    open(caminho, 'w', encoding='utf-8').write(novo)
    print(f"CDI até {cdi['last']}, Selic até {selic['last']}, IPCA até {ipca['last']}, poupança até {poup['last']}, Selic meta {dados['selicMeta']}%")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'index.html')
