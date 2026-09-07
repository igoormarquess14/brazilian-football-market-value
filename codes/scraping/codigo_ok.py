#realiza o scraping dos dados da tabela completa do elenco de cada clube envolvido no Brasileirão Série A 2025
from bs4 import BeautifulSoup
import pandas as pd
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

def scrape_squad_table(club_url: str) -> pd.DataFrame:
    # extrai o ID do clube do próprio URL (para diferenciar do ex-clube)
    m = re.search(r"/verein/(\d+)", club_url)
    club_id = m.group(1) if m else None

    driver = make_driver()
    driver.get(club_url)

    # aceitar cookies se aparecer
    try:
        WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except:
        pass

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.items"))
    )
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    table = soup.select_one("table.items")
    if not table:
        return pd.DataFrame()

    # cabeçalhos (última linha do thead)
    thead_rows = table.select("thead tr")
    header_cells = thead_rows[-1].select("th") if thead_rows else []
    headers = [_norm(th.get_text(" ", strip=True)) for th in header_cells]

    def find_idx(*cands):
        # evita falsos positivos (ex.: "de" em "data de nascimento")
        for i, h in enumerate(headers):
            for c in cands:
                if h == c or h.startswith(c) or (" " + c + " ") in (" " + h + " "):
                    return i
        return None

    idx_age    = find_idx("idade", "data de nasc", "nasc", "date of birth", "born", "age")
    idx_height = find_idx("altura", "height")
    idx_value  = find_idx("valor de mercado", "valor", "market value")
    idx_nation = find_idx("nacionalidade", "nac.", "nac", "nat.", "nat", "nation", "citizenship")
    # nomes comuns para ex-clube (não usar "de" genérico)
    idx_from   = find_idx("contratado de", "clube anterior", "ex-clube",
                          "proveniente", "clube de origem", "origem",
                          "joined from", "from", "former club")

    data = []
    for tr in table.select("tbody > tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 3:
            continue

        # Nome
        a_player = tr.select_one("table.inline-table td.hauptlink a")
        if not a_player:
            continue
        player = a_player.get_text(strip=True)

        # Posição
        pos_el  = tr.select_one("table.inline-table tr:nth-child(2) td")
        position = pos_el.get_text(strip=True) if pos_el else None

        # Idade
        age = None
        if idx_age is not None and idx_age < len(tds):
            txt = tds[idx_age].get_text(" ", strip=True)
            age = txt if txt and txt != "-" else None

        # Altura
        height = None
        if idx_height is not None and idx_height < len(tds):
            txt = tds[idx_height].get_text(strip=True)
            height = txt if txt and txt != "-" else None

        # Nation (por coluna; fallback por ícones no TR)
        nation = None
        if idx_nation is not None and idx_nation < len(tds):
            td_nat = tds[idx_nation]
            flags = [img.get("title") for img in td_nat.select("img[title]")]
            txt = ", ".join([f for f in flags if f]) or td_nat.get_text(" ", strip=True)
            nation = txt if txt and txt != "-" else None
        if not nation:
            flags = [img.get("title") for img in tr.select("img.flaggenrahmen[title]")]
            nation = ", ".join([f for f in flags if f]) or None

        # Ex Club: tenta pela coluna; se não houver, pega o primeiro link de clube != club_id
        ex_club = None
        if idx_from is not None and idx_from < len(tds):
            td_from = tds[idx_from]
            names = [img.get("title") for img in td_from.select("img[title]")]
            names = [n for n in names if n]
            if names:
                ex_club = ", ".join(names)
            else:
                alist = [a.get("title") or a.get_text(strip=True) for a in td_from.find_all("a")]
                alist = [a for a in alist if a and a != "-"]
                if alist:
                    ex_club = alist[0]

        if not ex_club:
            # fallback robusto varrendo a linha toda
            for a in tr.select('a[href*="/verein/"]'):
                href = a.get("href", "")
                m2 = re.search(r"/verein/(\d+)", href)
                if m2:
                    vid = m2.group(1)
                    if club_id and vid == club_id:
                        continue  # ignora o clube atual
                    name = a.get("title") or a.get_text(strip=True)
                    if name and name != "-":
                        ex_club = name
                        break

        # Valor de mercado
        market_val = None
        if idx_value is not None and idx_value < len(tds):
            txt = tds[idx_value].get_text(strip=True)
            market_val = txt if txt and txt != "-" else None

        data.append({
            "Player": player,
            "Age": age,
            "Position": position,
            "Height": height,
            "Nation": nation,
            "Ex Club": ex_club,
            "Value (€)": market_val
        })

    return pd.DataFrame(data)

if __name__ == "__main__":
    url = "https://www.transfermarkt.com.br/cr-flamengo/kader/verein/614/saison_id/2025/plus/1"
    df = scrape_squad_table(url)
    print(df.head(10))
    out = "flamengo_2025_table_only.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"CSV salvo em: {os.path.abspath(out)}")
