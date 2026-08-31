#retira os dados dos montantes das transferências envolvendo clubes do Brasileirão Série A 2025
from bs4 import BeautifulSoup
import pandas as pd
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os

# silencia o __del__ barulhento do undetected_chromedriver no Windows
try:
    uc.Chrome.__del__ = lambda self: None
except:
    pass

def make_driver():
    opts = uc.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.page_load_strategy = "eager"
    d = uc.Chrome(options=opts)
    d.implicitly_wait(5)
    return d

def _norm(s: str) -> str:
    return " ".join((s or "").split()).strip().lower()

def _find_idx(headers, *cands):
    for i, h in enumerate(headers):
        for c in cands:
            if h == c or h.startswith(c) or (" " + c + " ") in (" " + h + " "):
                return i
    return None

def _soup_via_requests(url: str):
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    r = sess.get(url, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def _soup_via_selenium(url: str):
    d = make_driver()
    d.get(url)
    try:
        WebDriverWait(d, 6).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except:
        pass
    WebDriverWait(d, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.items"))
    )
    soup = BeautifulSoup(d.page_source, "html.parser")
    d.quit()
    return soup

def scrape_transfer_income_expense(url: str) -> pd.DataFrame:
    # tenta via requests primeiro
    try:
        soup = _soup_via_requests(url)
    except Exception:
        soup = None

    table = soup.select_one("table.items") if soup else None
    if not table:
        # fallback Selenium (cookies/JS)
        try:
            soup = _soup_via_selenium(url)
            table = soup.select_one("table.items")
        except Exception:
            table = None

    if not table:
        return pd.DataFrame()

    # cabeçalhos
    thead_rows = table.select("thead tr")
    header_cells = thead_rows[-1].select("th") if thead_rows else []
    headers = [_norm(th.get_text(" ", strip=True)) for th in header_cells]

    # mapeia possíveis nomes (PT/EN/DE)
    idx_club   = _find_idx(headers, "clube", "club", "verein", "times", "team")
    idx_league = _find_idx(headers, "liga", "league", "wettbewerb", "competição", "competition")
    idx_in_n   = _find_idx(headers, "chegadas", "entradas", "zugänge", "arrivals", "ins")
    idx_out_n  = _find_idx(headers, "saídas", "abgänge", "departures", "outs")
    idx_income = _find_idx(headers, "receitas", "einnahmen", "income")
    idx_exp    = _find_idx(headers, "despesas", "ausgaben", "expenditure", "expenses", "gastos")
    idx_bal    = _find_idx(headers, "saldo", "balance", "bilanz")

    data = []
    for tr in table.select("tbody > tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 3:
            continue

        # Club (preferir link que aponta para /verein/)
        club = None
        club_url = None
        td_club = tds[idx_club] if (idx_club is not None and idx_club < len(tds)) else None
        if td_club:
            a = td_club.select_one('a[href*="/verein/"]')
            if a:
                club = a.get("title") or a.get_text(strip=True)
                club_url = a.get("href")
            else:
                # fallback texto
                txt = td_club.get_text(" ", strip=True)
                club = txt if txt and txt != "-" else None
        if not club:
            a = tr.select_one('a[href*="/verein/"]')
            if a:
                club = a.get("title") or a.get_text(strip=True)
                club_url = a.get("href")

        # League (link para /wettbewerb/)
        league = None
        league_url = None
        if idx_league is not None and idx_league < len(tds):
            td_lg = tds[idx_league]
            a = td_lg.select_one('a[href*="/wettbewerb/"]')
            if a:
                league = a.get("title") or a.get_text(strip=True)
                league_url = a.get("href")
            else:
                txt = td_lg.get_text(" ", strip=True)
                league = txt if txt and txt != "-" else None

        # números e valores
        def _txt(idx):
            if idx is not None and idx < len(tds):
                t = tds[idx].get_text(" ", strip=True)
                return t if t and t != "-" else None
            return None

        arrivals   = _txt(idx_in_n)
        departures = _txt(idx_out_n)
        income     = _txt(idx_income)
        expense    = _txt(idx_exp)
        balance    = _txt(idx_bal)

        data.append({
            "Club": club,
            "League": league,
            "Arrivals (N)": arrivals,
            "Departures (N)": departures,
            "Income (€)": income,
            "Expenditure (€)": expense,
            "Balance (€)": balance,
            "Club URL": club_url,
            "League URL": league_url
        })

    df = pd.DataFrame(data)
    # ordena colunas de forma limpa
    cols = ["Club","League","Arrivals (N)","Departures (N)","Income (€)","Expenditure (€)","Balance (€)","Club URL","League URL"]
    df = df[[c for c in cols if c in df.columns]]
    return df

def run(url: str, outfile: str | None = None):
    # cria um nome de arquivo padrão amigável
    if outfile is None:
        season = re.search(r"/saison_id/(\d+)", url)
        country = re.search(r"/land_id/(\d+)", url)
        s_part = f"s{season.group(1)}" if season else "s"
        c_part = f"land{country.group(1)}" if country else "land"
        outfile = f"transfer_income_expense_{s_part}_{c_part}.csv"

    df = scrape_transfer_income_expense(url)
    print(df.head(10))
    df.to_csv(outfile, index=False, encoding="utf-8-sig")
    print(f"CSV salvo em: {os.path.abspath(outfile)}")

if __name__ == "__main__":
    # Exemplo: Brasil, temporada 2025
    run("https://www.transfermarkt.com.br/transfers/einnahmenausgaben/statistik/a/ids/a/sa//saison_id/2025/saison_id_bis/2025/land_id/26/nat/0/kontinent_id/0/pos//w_s//intern/0")
