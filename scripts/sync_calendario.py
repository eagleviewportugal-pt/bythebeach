"""Atualiza disponibilidade.json com as datas ocupadas.

Fontes (todas opcionais, usa as que estiverem configuradas):
  1. Portal de proprietários da Feels Like Home  -> segredos FLH_USER e FLH_PASS
  2. Links iCal (Airbnb, Booking...)             -> segredo ICAL_URLS (um por linha)
  3. Datas marcadas à mão no próprio ficheiro    -> "origem": "manual" (nunca são apagadas)

Do portal só se guardam datas de entrada e saída. Nomes de hóspedes, valores
e plataformas não vão para o site.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime
from html.parser import HTMLParser

FICHEIRO = "disponibilidade.json"

FLH_BASE = "https://feelslikehome.platerit.pt"
FLH_ALOJAMENTO = "1940"
FLH_MODULE_ID = "459"
FLH_TAB_ID = "68"


# ---------------------------------------------------------------- Feels Like Home
class _Campos(HTMLParser):
    """Recolhe os campos <input> da página de login (ASP.NET / DNN)."""

    def __init__(self):
        super().__init__()
        self.campos = {}

    def handle_starttag(self, tag, attrs):
        if tag != "input":
            return
        a = dict(attrs)
        if a.get("name") and a.get("type", "text") in ("hidden", "text", "password"):
            self.campos[a["name"]] = a.get("value", "")


def ler_flh(utilizador, password):
    import requests  # instalado no workflow

    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (bythebeach-calendar-sync)"

    # 1. página de login: campos escondidos e cookies
    r = s.get(f"{FLH_BASE}/owners/login", timeout=30)
    r.raise_for_status()
    p = _Campos()
    p.feed(r.text)
    campos = p.campos
    nome_user = next(k for k in campos if k.endswith("txtUsername"))
    nome_pass = next(k for k in campos if k.endswith("txtPassword"))
    botao = nome_user.replace("txtUsername", "cmdLogin")
    campos.update({
        "__EVENTTARGET": botao,
        "__EVENTARGUMENT": "",
        nome_user: utilizador,
        nome_pass: password,
    })
    campos = {k: v for k, v in campos.items() if "dnnSearch" not in k}

    # 2. login
    r = s.post(f"{FLH_BASE}/owners/login", data=campos, timeout=30)
    r.raise_for_status()

    # 3. página do alojamento: token de segurança para a API
    r = s.get(f"{FLH_BASE}/owners/accommodation/{FLH_ALOJAMENTO}", timeout=30)
    m = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', r.text)
    if "/login" in r.url.lower() or not m:
        raise RuntimeError("login no portal falhou (confirma FLH_USER e FLH_PASS)")

    # 4. reservas do alojamento
    r = s.get(
        f"{FLH_BASE}/owners/DeskTopModules/AlgoritmiaAngular/API/Query/List",
        params={
            "connection": "FLH_BE",
            "filters": f"ClientIdSystem:(eq)'{FLH_ALOJAMENTO}'",
            "groupby": "", "orderby": "-StartDate", "page": "1", "pagesize": "999",
            "select": "", "table": "vw_Owner_Apartments_Events",
        },
        headers={
            "ModuleId": FLH_MODULE_ID,
            "TabId": FLH_TAB_ID,
            "RequestVerificationToken": m.group(1),
            "Accept": "application/json",
        },
        timeout=30,
    )
    r.raise_for_status()
    itens = r.json().get("Items", [])

    reservas = []
    for ev in itens:
        if ev.get("EvType") != "Res":
            continue
        de = (ev.get("StartDate") or "")[:10]
        ate = (ev.get("EndDate") or "")[:10]
        if de and ate and ate > de:
            reservas.append({"de": de, "ate": ate, "origem": "flh"})
    return reservas


# ---------------------------------------------------------------- iCal
def ler_ical(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "bythebeach-calendar-sync"})
    with urllib.request.urlopen(pedido, timeout=30) as r:
        texto = r.read().decode("utf-8", "replace")
    texto = re.sub(r"\r?\n[ \t]", "", texto)  # linhas dobradas do formato iCal
    reservas = []
    for bloco in texto.split("BEGIN:VEVENT")[1:]:
        ini = re.search(r"DTSTART[^:]*:(\d{8})", bloco)
        fim = re.search(r"DTEND[^:]*:(\d{8})", bloco)
        if ini and fim:
            de = datetime.strptime(ini.group(1), "%Y%m%d").date()
            ate = datetime.strptime(fim.group(1), "%Y%m%d").date()
            if ate > de:
                reservas.append({"de": de.isoformat(), "ate": ate.isoformat(), "origem": "ical"})
    return reservas


# ---------------------------------------------------------------- principal
def main():
    try:
        with open(FICHEIRO, encoding="utf-8") as f:
            dados = json.load(f)
    except FileNotFoundError:
        dados = {"ocupado": []}

    manuais = [r for r in dados.get("ocupado", []) if r.get("origem", "manual") == "manual"]
    importadas = []
    falhou = False

    user, pw = os.environ.get("FLH_USER"), os.environ.get("FLH_PASS")
    if user and pw:
        try:
            flh = ler_flh(user, pw)
            importadas += flh
            print(f"Portal FLH: {len(flh)} reservas lidas.")
        except Exception as erro:
            falhou = True
            print(f"Aviso: portal FLH não respondeu como esperado ({erro})")

    for url in os.environ.get("ICAL_URLS", "").split():
        try:
            importadas += ler_ical(url)
        except Exception as erro:
            print(f"Aviso: não foi possível ler um calendário iCal ({erro})")

    if falhou and not importadas:
        # não apaga as reservas anteriores só porque o portal falhou
        anteriores = [r for r in dados.get("ocupado", []) if r.get("origem") in ("flh", "ical")]
        importadas = anteriores

    hoje = date.today().isoformat()
    vistos, todas = set(), []
    for r in sorted(manuais + importadas, key=lambda r: (r["de"], r["ate"])):
        chave = (r["de"], r["ate"])
        if r["ate"] >= hoje and chave not in vistos:
            vistos.add(chave)
            todas.append(r)

    dados["ocupado"] = todas
    dados["atualizado"] = hoje
    with open(FICHEIRO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(todas)} períodos ocupados gravados.")
    if falhou:
        sys.exit(1)  # o GitHub envia-te um e-mail a avisar


if __name__ == "__main__":
    main()
