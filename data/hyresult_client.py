
#


import json
import math
import re
import time

import requests

BASE_URL = "https://www.hyresult.com"

# Wait between two requests so we do not overload the website.
DELAY_BETWEEN_REQUESTS_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30
ATHLETES_PER_RANKING_PAGE = 100

# One shared session re-uses the connection for all requests (faster and
# friendlier for the server than opening a new connection every time).
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (private Hyrox data hobby project)"


def fetch_html(path: str) -> str:
    """Download one page of hyresult.com, e.g. fetch_html("/event/s9-2026-rome")."""
    time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)
    response = session.get(BASE_URL + path, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()  # stop with an error for e.g. 404 or 500
    return response.text


def extract_page_data(html: str) -> str:
    """Return the data Next.js hides in the page as one big text.

    The page contains many pieces like  self.__next_f.push([1,"<text>"]).
    Each <text> is a JSON string, so json.loads() turns escapes like \\" back
    into normal characters. Glued together they form the page data.
    """
    pieces = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, flags=re.DOTALL)
    return "".join(json.loads('"' + piece + '"') for piece in pieces)


def get_event_slugs_of_month(year: int, month: int) -> list[str]:
    """Return the slugs of all events in one month, e.g. ["s9-2026-rome", ...]."""
    html = fetch_html(f"/events/{year}/{month:02d}")
    slugs = re.findall(r'href="/event/([^"]+)"', html)
    return sorted(set(slugs))  # set() removes links that appear twice


def get_event_details(event_slug: str) -> dict:
    """Return name, city, dates and division slugs of one event.

    The name and dates come from the page's "structured data" block
    (<script type="application/ld+json">) which search engines read.
    """
    html = fetch_html(f"/event/{event_slug}")

    sports_event = None
    for block in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, flags=re.DOTALL):
        data = json.loads(block)
        if data.get("@type") == "SportsEvent":
            sports_event = data

    if sports_event is None:
        raise ValueError(f"No event information found on page of '{event_slug}'")

    division_slugs = sorted(set(re.findall(r'href="/ranking/([^"]+)"', html)))

    return {
        "slug": event_slug,
        "name": sports_event["name"],  # e.g. "HYROX Rome 2026"
        "city": sports_event["location"]["address"]["addressLocality"],  # e.g. "Rome"
        "start_date": sports_event["startDate"],  # e.g. "2026-09-22 22:00:00+00"
        "end_date": sports_event["endDate"],
        "division_slugs": division_slugs,  # e.g. ["s9-2026-rome-hyrox-men", ...]
    }


def read_ranking_lists(page_data: str) -> list[dict]:
    """Return the athletes of every "ranking":[...] list found in the page data.

    raw_decode() reads exactly one JSON value (here: the list) starting at
    the given position and ignores whatever text follows it.
    """
    athletes = []
    for match in re.finditer(r'"ranking":\[', page_data):
        list_start = match.end() - 1  # position of the "["
        entries, _ = json.JSONDecoder().raw_decode(page_data, list_start)
        # Other page parts also use the word "ranking"; keep only real athletes.
        athletes.extend(entry for entry in entries if isinstance(entry, dict) and "rank" in entry)
    return athletes


def get_ranking_page(division_slug: str, page_number: int, max_attempts: int = 3) -> tuple[list[dict], int]:
    """Return (athletes on this page, total number of finishers in the division).

    Each athlete is a dict like:
        {"idp": "LR3MS4JI588D8D", "rank": 53, "agegroup": "25-29",
         "nation": "FRA", "t_total": 3785,
         "team": [{"name": "Dylan Arcidiacono", "slug": "dylan-arcidiacono", ...}]}
    For doubles, "team" holds both partners.

    Pitfall: the page also contains a "loading placeholder" list that always
    shows page 1, and sometimes the real list arrives empty. That is why we
    keep only the ranks that belong to the requested page and try again if
    athletes are missing.
    """
    first_rank = (page_number - 1) * ATHLETES_PER_RANKING_PAGE + 1
    last_rank = page_number * ATHLETES_PER_RANKING_PAGE

    for _ in range(max_attempts):
        page_data = extract_page_data(fetch_html(f"/ranking/{division_slug}?p={page_number}"))

        total_match = re.search(r'"numRows":(\d+)', page_data)
        if total_match is None:
            return [], 0  # no results (yet) for this division
        total_finishers = int(total_match.group(1))

        athletes_by_rank = {}
        for athlete in read_ranking_lists(page_data):
            if first_rank <= athlete["rank"] <= last_rank:
                athletes_by_rank[athlete["rank"]] = athlete
        athletes = [athletes_by_rank[rank] for rank in sorted(athletes_by_rank)]

        expected_count = min(last_rank, total_finishers) - first_rank + 1
        if len(athletes) >= expected_count:
            return athletes, total_finishers

    print(f"    Warning: page {page_number} of {division_slug} is incomplete "
          f"({len(athletes)} of {expected_count} athletes)")
    return athletes, total_finishers


def get_all_finishers(division_slug: str) -> list[dict]:
    """Return every finisher of a division by walking through all ranking pages."""
    athletes, total_finishers = get_ranking_page(division_slug, page_number=1)
    number_of_pages = math.ceil(total_finishers / ATHLETES_PER_RANKING_PAGE)

    for page_number in range(2, number_of_pages + 1):
        more_athletes, _ = get_ranking_page(division_slug, page_number)
        athletes.extend(more_athletes)

    return athletes


def get_result_splits(result_id: str) -> dict[str, int]:
    """Return the split times (in seconds) of one result.

    The result page shows one card per split, stored like
        {"name":"SkiErg","time":259, ... ,"station":"t_w1"}
    The keys mean:
        t_r1 .. t_r8  -> Run 1 .. Run 8
        t_w1 .. t_w8  -> the 8 stations (SkiErg .. Wall Balls)
        t_rx          -> Roxzone
    Splits that are missing (e.g. a skipped station) are simply not in the dict.
    """
    page_data = extract_page_data(fetch_html(f"/result/{result_id}"))

    splits = {}
    for match in re.finditer(r'\{"name":"[^"]*","time":(\d+)[^{}]*?"station":"(t_\w+)"', page_data):
        seconds, split_key = int(match.group(1)), match.group(2)
        # The same card can appear twice on the page; keep the first one.
        splits.setdefault(split_key, seconds)
    return splits
