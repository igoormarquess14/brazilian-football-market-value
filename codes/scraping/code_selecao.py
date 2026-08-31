#realiza o scraping da tabela com atletas convocados em 08/2025 para as seleções nacionais
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
    r = sess.get(url, timeout=15)
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

def scrape_national_players(url: str) -> pd.DataFrame:
    # tenta requests primeiro
    try:
        soup = _soup_via_requests(url)
    except Exception:
        soup = None

    table = soup.select_one("table.items") if soup else None
    if not table:
        # fallback Selenium
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

    # mapeia índices prováveis (PT/EN)
    idx_pos   = _find_idx(headers, "pos.", "posição", "position")
    idx_nat   = _find_idx(headers, "nacionalidade", "nation", "citizenship", "nac.", "nat.", "nat")
    idx_nt    = _find_idx(headers, "seleção", "national team", "selecao")
    # jogos/gols podem vir juntos ou separados
    idx_caps  = _find_idx(headers, "jogos", "partidas", "apps", "caps", "aparições", "appearances")
    idx_goals = _find_idx(headers, "gols", "goals")
    idx_cg    = _find_idx(headers, "jogos/gols", "apps/goals", "partidas/gols")

    data = []
    for tr in table.select("tbody > tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 2:
            continue

        # jogador (segue padrão Transfermarkt)
        a_player = tr.select_one("table.inline-table td.hauptlink a")
        if not a_player:
            # fallback: primeiro link 'de jogador'
            a_player = tr.select_one("td.hauptlink a")
        if not a_player:
            continue

        player = a_player.get_text(strip=True)
        player_url = a_player.get("href", "")

        # posição (segunda linha na mini-tabela)
        pos_el = tr.select_one("table.inline-table tr:nth-child(2) td")
        position = pos_el.get_text(strip=True) if pos_el else (tds[idx_pos].get_text(strip=True) if idx_pos is not None and idx_pos < len(tds) else None)

        # nacionalidade do jogador
        player_nat = None
        if idx_nat is not None and idx_nat < len(tds):
            td_nat = tds[idx_nat]
            flags = [img.get("title") for img in td_nat.select("img[title]")]
            txt = ", ".join([f for f in flags if f]) or td_nat.get_text(" ", strip=True)
            player_nat = txt if txt and txt != "-" else None
        if not player_nat:
            flags = [img.get("title") for img in tr.select("img.flaggenrahmen[title]")]
            player_nat = ", ".join([f for f in flags if f]) or None

        # seleção (time nacional) — pegue pelo link para /nationalmannschaft/
        nt_name = None
        nt_url  = None
        if idx_nt is not None and idx_nt < len(tds):
            td_nt = tds[idx_nt]
            a_nt = td_nt.select_one('a[href*="/nationalmannschaft/"], a[href*="/kader/verband/"]')
            if a_nt:
                nt_name = a_nt.get("title") or a_nt.get_text(strip=True)
                nt_url = a_nt.get("href")

        if not nt_name:
            a_nt = tr.select_one('a[href*="/nationalmannschaft/"], a[href*="/kader/verband/"]')
            if a_nt:
                nt_name = a_nt.get("title") or a_nt.get_text(strip=True)
                nt_url = a_nt.get("href")

        # jogos/gols
        caps = goals = None
        if idx_cg is not None and idx_cg < len(tds):
            txt = tds[idx_cg].get_text(strip=True)
            if "/" in txt:
                left, right = [x.strip() for x in txt.split("/", 1)]
                caps  = left if left and left != "-" else None
                goals = right if right and right != "-" else None
        else:
            if idx_caps is not None and idx_caps < len(tds):
                c = tds[idx_caps].get_text(strip=True)
                caps = c if c and c != "-" else None
            if idx_goals is not None and idx_goals < len(tds):
                g = tds[idx_goals].get_text(strip=True)
                goals = g if g and g != "-" else None

        data.append({
            "Player": player,
            "Position": position,
            "Player Nation": player_nat,
            "National Team": nt_name,
            "Caps": caps,
            "Goals": goals,
        })

    df = pd.DataFrame(data)
    # ordem de colunas mais “limpa”
    cols = ["Player","Position","Player Nation","National Team","Caps","Goals","Player URL","NT URL"]
    df = df[[c for c in cols if c in df.columns]]
    return df

def run(url: str, outfile: str | None = None):
    # nome de arquivo padrão: <slug>_<id>_national_players.csv
    if outfile is None:
        m = re.search(r"https?://[^/]+/([^/]+)/nationalspieler/verein/(\d+)", url)
        if m:
            slug, vid = m.group(1), m.group(2)
            outfile = f"{slug}_{vid}_national_players.csv"
        else:
            outfile = "national_players.csv"

    df = scrape_national_players(url)
    print(df.head(10))
    df.to_csv(outfile, index=False, encoding="utf-8-sig")
    print(f"CSV salvo em: {os.path.abspath(outfile)}")

if __name__ == "__main__":
    # colocar o link do transfermarkt das convocações do clube
    run("https://www.transfermarkt.com.br/vasco-da-gama-rio-de-janeiro/nationalspieler/verein/978")
