#retira os dados de todas transferências envolvendo clubes da Brasileirão Série A 2025, atleta por atleta
from bs4 import BeautifulSoup
import pandas as pd
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os

BASE = "https://www.transfermarkt.com.br"

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

def _abs_url(href: str | None) -> str | None:
    if not href:
        return None
    return href if href.startswith("http") else (BASE + href)

def _soup_via_requests(url: str):
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    r = sess.get(url, timeout=25)
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
    WebDriverWait(d, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
    )
    soup = BeautifulSoup(d.page_source, "html.parser")
    d.quit()
    return soup

def _club_id_from_href(href: str | None):
    if not href:
        return None
    m = re.search(r"/verein/(\d+)", href)
    return m.group(1) if m else None

_MONEY_RE = re.compile(
    r"(€\s?[\d\.,]+(?:\s?(?:mi\.|mio\.?|mil|m|k|bn))?)",
    flags=re.I
)

def _find_money_fragments(text: str) -> list[str]:
    return [m.group(1) for m in _MONEY_RE.finditer(text or "")]

def _detect_transfer_details(fee_text: str | None, tr_text: str | None):
    """
    Retorna dict com:
      - Transfer Type
      - Is Loan (bool)
      - Loan With Option (bool)
      - Loan With Obligation (bool)
      - Clause Fee (€) (se detectada no texto; ex.: opção/obrigação)
      - Type Notes (frase/keyword que motivou a classificação)
    """
    s = _norm((fee_text or "") + " " + (tr_text or ""))
    notes = []

    # sinais
    loan_kw = ["empréstimo", "emprestimo", "loan", "leihe", "por emprestimo", "por empréstimo"]
    endloan_kw = ["fim do empréstimo", "retorno de empréstimo", "retorno do empréstimo",
                  "end of loan", "ende leihvertrag", "loan ended", "return from loan"]
    option_kw = ["opção de compra", "opcao de compra", "option to buy", "kaufoption"]
    obligation_kw = ["obrigação de compra", "obrigacao de compra", "obligation to buy", "kaufpflicht"]
    free_kw = ["sem custo", "custo zero", "free", "ablösefrei", "ablöse frei", "livre", "sem taxa"]
    term_kw = ["fim de contrato", "end of contract", "contract terminated", "rescis", "rescindido", "rescindida"]
    swap_kw = ["troca", "swap", "tauschgeschäft", "tausch"]
    permanent_hint_kw = ["ablöse", "transfer fee", "taxa de transferência"]

    is_loan = any(k in s for k in loan_kw)
    is_endloan = any(k in s for k in endloan_kw)
    has_option = any(k in s for k in option_kw)
    has_obligation = any(k in s for k in obligation_kw)
    is_free = any(k in s for k in free_kw)
    is_termination = any(k in s for k in term_kw)
    is_swap = any(k in s for k in swap_kw)
    has_money_symbol = ("€" in s) or any(k in s for k in permanent_hint_kw)

    clause_fee = None
    if has_option or has_obligation:
        monies = _find_money_fragments(s)
        if monies:
            clause_fee = monies[0]

    # define tipo
    if is_endloan:
        ttype = "End of loan / Return"; notes.append("end of loan")
    elif is_loan and has_obligation:
        ttype = "Loan with obligation"; notes.append("loan + obligation")
    elif is_loan and has_option:
        ttype = "Loan with option"; notes.append("loan + option")
    elif is_loan:
        ttype = "Loan"; notes.append("loan")
    elif is_termination:
        ttype = "Contract termination"; notes.append("termination")
    elif is_free:
        ttype = "Free"; notes.append("free")
    elif is_swap:
        ttype = "Swap"; notes.append("swap")
    elif has_money_symbol:
        ttype = "Permanent"; notes.append("fee present / permanent")
    else:
        ttype = None

    return {
        "Transfer Type": ttype,
        "Is Loan": bool(is_loan),
        "Loan With Option": bool(has_option and is_loan and not is_endloan),
        "Loan With Obligation": bool(has_obligation and is_loan and not is_endloan),
        "Clause Fee (€)": clause_fee,
        "Type Notes": "; ".join(notes) or None
    }

def _parse_transfers_table(tbl, direction: str, club_name: str, club_id: str):
    rows = []

    thead = tbl.select_one("thead")
    header_cells = thead.select("th") if thead else []
    headers = [_norm(th.get_text(" ", strip=True)) for th in header_cells]

    def idx_of(*cands):
        for i, h in enumerate(headers):
            for c in cands:
                if h == c or h.startswith(c) or (" " + c + " ") in (" " + h + " "):
                    return i
        return None

    idx_date = idx_of("data", "datum", "date")
    idx_age  = idx_of("idade", "age", "alter")
    idx_pos  = idx_of("posição", "pos.", "posicao", "position", "pos")
    idx_fee  = idx_of("valor", "ablöse", "fee", "taxa", "valor de transferência", "transfer fee")

    for tr in tbl.select("tbody tr"):
        # ignora linhas de total/agrupadoras
        if 'bg_blau' in tr.get("class", []) or tr.find("strong"):
            continue

        tds = tr.find_all("td", recursive=False)
        if len(tds) < 2:
            continue

        # Jogador
        a_player = tr.select_one('td a.spielprofil_tooltip, td a[href*="/spieler/"], td a[href*="/profil/"]')
        if not a_player:
            continue
        player = a_player.get("title") or a_player.get_text(strip=True)
        player_url = _abs_url(a_player.get("href"))

        # Clube contraparte
        a_counter = tr.select_one('td a[href*="/verein/"]')
        counter_name = (a_counter.get("title") if a_counter else None) or (a_counter.get_text(strip=True) if a_counter else None)
        counter_id = _club_id_from_href(a_counter.get("href", "")) if a_counter else None

        # campos por índice
        def _txt(idx):
            if idx is not None and idx < len(tds):
                t = tds[idx].get_text(" ", strip=True)
                return t if t and t != "-" else None
            return None

        date  = _txt(idx_date)
        age   = _txt(idx_age)
        pos   = _txt(idx_pos)
        fee   = _txt(idx_fee)

        # Nation via ícones
        nat_td = None
        for td in tds:
            if td.select_one("img.flaggenrahmen"):
                nat_td = td
                break
        if nat_td:
            nations = [img.get("title") for img in nat_td.select("img.flaggenrahmen[title]")]
            nation = ", ".join([n for n in nations if n]) or None
        else:
            nation = None

        # tipo de transferência (heurística com texto da linha inteira)
        tr_text = tr.get_text(" ", strip=True)
        type_info = _detect_transfer_details(fee, tr_text)

        # From/To + IDs
        if direction == "In":
            from_club, from_id = counter_name, counter_id
            to_club,   to_id   = club_name,  club_id
        else:  # Out
            from_club, from_id = club_name,  club_id
            to_club,   to_id   = counter_name, counter_id

        row = {
            "Club": club_name,
            "Club ID": club_id,
            "Direction": direction,          # In / Out
            "Date": date,
            "Player": player,
            "Player URL": player_url,
            "Age": age,
            "Nation": nation,
            "Position": pos,
            "From Club": from_club,
            "From Club ID": from_id,
            "To Club": to_club,
            "To Club ID": to_id,
            "Fee (€)": fee,
        }
        row.update(type_info)
        rows.append(row)

    return rows

def scrape_competition_transfers(url: str) -> pd.DataFrame:
    # tenta requests; fallback Selenium se necessário
    soup = None
    try:
        soup = _soup_via_requests(url)
    except Exception:
        pass
    if not soup or not soup.select("div.box, table"):
        soup = _soup_via_selenium(url)

    rows = []

    # cada clube vem num "box" com título e 2 tabelas (Entradas/Saídas)
    for box in soup.select("div.box"):
        header = box.select_one("h2, div.table-header, div.content-box-headline")
        if not header:
            continue
        a_club = header.select_one('a[href*="/verein/"]')
        if not a_club:
            continue

        club_name = a_club.get("title") or a_club.get_text(strip=True)
        club_id = _club_id_from_href(a_club.get("href", ""))

        # normalmente duas tabelas: primeira Entradas, segunda Saídas
        tables = box.select("table.items")
        if not tables:
            tables = box.select("table")
        if not tables:
            continue

        # tenta rótulos explícitos
        labels = []
        for sub in box.select("h2, h3, h4, div.table-header"):
            t = _norm(sub.get_text(" ", strip=True))
            if any(k in t for k in ("entradas", "zugänge", "arrivals", "ins", "chegadas")):
                labels.append("In")
            elif any(k in t for k in ("saídas", "abgänge", "departures", "outs", "saidas")):
                labels.append("Out")

        for i, tbl in enumerate(tables[:2]):  # geralmente 2
            direction = labels[i] if i < len(labels) else ("In" if i == 0 else "Out")
            rows.extend(_parse_transfers_table(tbl, direction, club_name, club_id))

    df = pd.DataFrame(rows).drop_duplicates()

    # ordenação amigável
    cols = [
        "Club","Club ID","Direction","Date","Player","Player URL","Age","Nation","Position",
        "From Club","From Club ID","To Club","To Club ID","Fee (€)",
        "Transfer Type","Is Loan","Loan With Option","Loan With Obligation",
        "Clause Fee (€)","Type Notes"
    ]
    df = df[[c for c in cols if c in df.columns]]
    return df

def run(url: str, outfile: str | None = None):
    if outfile is None:
        comp = re.search(r"/wettbewerb/([^/]+)", url)
        saison = re.search(r"/saison_id/(\d+)", url)
        comp_part = comp.group(1) if comp else "comp"
        saison_part = saison.group(1) if saison else "current"
        outfile = f"transfers_{comp_part}_{saison_part}.csv"

    df = scrape_competition_transfers(url)
    print(df.head(20))
    df.to_csv(outfile, index=False, encoding="utf-8-sig")
    print(f"CSV salvo em: {os.path.abspath(outfile)}")

if __name__ == "__main__":
    run("https://www.transfermarkt.com.br/campeonato-brasileiro-serie-a/transfers/wettbewerb/BRA1")
