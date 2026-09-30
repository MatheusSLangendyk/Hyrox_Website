# Imports Hyrox results from www.hyresult.com into data/RawData.
#

#
# How it works:
#   1. Count the event folders that already exist in RawData.
#   2. If that is fewer than NUMBER_OF_EVENTS, walk through the event
#      calendar from the newest month backwards and import every
#      IMPORT_EVERY_NTH_EVENT-th finished event until NUMBER_OF_EVENTS
#      folders exist.
#   3. Per event: download the ranking of every wanted division, take every
#      IMPORT_EVERY_NTH_ATHLETE-th finisher and download their split times.
#
# Run it from the project folder with:  python data/import_raw_data.py

import functools
import logging
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
import country_converter
import pandas as pd
from tqdm import tqdm

import hyresult_client

# Make backend/ importable so we can re-use the shared time helper.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from utils.time_conversion import convert_seconds_to_minutes  # noqa: E402


NUMBER_OF_EVENTS = 63  # total number of event folders wanted in RawData

IMPORT_EVERY_NTH_EVENT = 10  # newest, 11th newest, 21st newest, ... -> events spread over time

IMPORT_EVERY_NTH_ATHLETE = 10  # rank 1, 11, 21, ... -> athletes of every level

# Divisions whose name contains one of these words are not imported.
IGNORED_DIVISION_KEYWORDS = ["relay","adaptive"]

# Stop searching the calendar here (the first Hyrox race was in 2017).
OLDEST_YEAR_TO_SEARCH = 2017

RAW_DATA_FOLDER = Path(__file__).resolve().parent / "RawData"

# CSV column -> key of that split on hyresult.com (see hyresult_client.get_result_splits).
STATION_COLUMNS = {
    "Run_One": "t_r1",
    "Ski_Erg": "t_w1",
    "Run_Two": "t_r2",
    "Sled_Push": "t_w2",
    "Run_Three": "t_r3",
    "Sled_Pull": "t_w3",
    "Run_Four": "t_r4",
    "BBJ": "t_w4",
    "Run_Five": "t_r5",
    "Row_Erg": "t_w5",
    "Run_Six": "t_r6",
    "Farmers_Carry": "t_w6",
    "Run_Seven": "t_r7",
    "Lunges": "t_w7",
    "Run_Eight": "t_r8",
    "Wall_Balls": "t_w8",
    "Rox_zone": "t_rx",
}

CSV_COLUMNS = ["Name", "Class", "Age_Group", "Nationality", "Event", "Year"] + list(STATION_COLUMNS)

# The existing folders use "ue" instead of "ü" etc. (e.g. Muenchen, Nuernberg).
GERMAN_UMLAUTS = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}

# country_converter prints a warning for every unknown code; we handle those ourselves.
logging.getLogger("country_converter").setLevel(logging.ERROR)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def count_imported_events() -> int:
    """Return how many event folders already exist in RawData."""
    return len([folder for folder in RAW_DATA_FOLDER.iterdir() if folder.is_dir()])


def to_ascii(text: str) -> str:
    """Replace special characters, e.g. "München" -> "Muenchen", "Málaga" -> "Malaga"."""
    for umlaut, replacement in GERMAN_UMLAUTS.items():
        text = text.replace(umlaut, replacement)
    # Split letters like "á" into "a" + accent, then drop the accent.
    decomposed = unicodedata.normalize("NFKD", text)
    return decomposed.encode("ascii", "ignore").decode("ascii")


def make_folder_name(city: str, year: str) -> str:
    """Return the folder name of an event, e.g. ("Salt Lake City", "2026") -> "Salt-Lake-City_2026"."""
    return f"{to_ascii(city).replace(' ', '-')}_{year}"


@functools.cache  # remember answers: the same few codes are asked thousands of times
def convert_nation_code(code: str | None) -> str:
    """Turn an IOC country code into a name, e.g. "GER" -> "Germany".

    Doubles teams have no single nation, so they get an empty string (as in
    the existing files). Unknown codes are kept as they are.
    """
    if not code:
        return ""
    return country_converter.convert(code, src="IOC", to="name_short", not_found=code)


def get_class_name(event_slug: str, division_slug: str) -> str:
    """Return the class as written in the CSV files.

    e.g. ("s9-2026-rome", "s9-2026-rome-hyrox-pro-doubles-men") -> "HYROX PRO DOUBLES MEN"
    """
    division_part = division_slug.removeprefix(event_slug + "-")
    return division_part.replace("-", " ").upper()


def is_division_wanted(division_slug: str) -> bool:
    return not any(keyword in division_slug for keyword in IGNORED_DIVISION_KEYWORDS)


def is_event_finished(event: dict) -> bool:
    end_date = datetime.fromisoformat(event["end_date"])
    return end_date < datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Building the CSV rows
# ---------------------------------------------------------------------------

def build_athlete_row(athlete: dict, splits: dict, class_name: str, city: str, year: str) -> dict | None:
    """Combine ranking info and split times into one CSV row.

    Returns None if a split is missing (e.g. an athlete skipped a station),
    because such a result can not be compared with the others.
    """
    if not all(split_key in splits for split_key in STATION_COLUMNS.values()):
        return None

    row = {
        # For doubles the existing files use the first partner's name.
        "Name": athlete["team"][0]["slug"],
        "Class": class_name,
        "Age_Group": athlete["agegroup"],
        "Nationality": convert_nation_code(athlete["nation"]),
        "Event": city,
        "Year": year,
    }
    for column, split_key in STATION_COLUMNS.items():
        row[column] = convert_seconds_to_minutes(splits[split_key])
    return row


def import_division(event: dict, division_slug: str, city: str, year: str, progress_bar: tqdm) -> pd.DataFrame:
    """Download every n-th finisher of one division and return them as a table."""
    class_name = get_class_name(event["slug"], division_slug)
    # Show where we are next to the bar, e.g. "Perth 2026 - HYROX MEN"
    progress_bar.set_description(f"{city} {year} - {class_name}")

    finishers = hyresult_client.get_all_finishers(division_slug)
    # [::n] takes element 0, n, 2n, ... -> rank 1, 11, 21, ...
    selected_athletes = finishers[::IMPORT_EVERY_NTH_ATHLETE]

    rows = []
    for athlete_number, athlete in enumerate(selected_athletes, start=1):
        # Text after the bar, so you can see it is still working within an event.
        progress_bar.set_postfix_str(f"athlete {athlete_number}/{len(selected_athletes)}")
        splits = hyresult_client.get_result_splits(athlete["idp"])
        row = build_athlete_row(athlete, splits, class_name, city, year)
        if row is not None:
            rows.append(row)

    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def import_event(event: dict, event_folder: Path, progress_bar: tqdm) -> bool:
    """Import all wanted divisions of one event into its own folder.

    Returns True if the event was saved, False if it had no results.

    All divisions are downloaded first and only written at the very end, so an
    interrupted run never leaves a half-filled folder behind (which would
    otherwise be counted as "already imported" next time).
    """
    city = to_ascii(event["city"])
    year = event["start_date"][:4]  # "2026-09-22 ..." -> "2026"

    tables = {}
    for division_slug in event["division_slugs"]:
        if not is_division_wanted(division_slug):
            continue
        table = import_division(event, division_slug, city, year, progress_bar)
        if not table.empty:
            file_name = get_class_name(event["slug"], division_slug).replace(" ", "_") + ".csv"
            tables[file_name] = table

    # progress_bar.write() prints a line above the bar without breaking it.
    if not tables:
        progress_bar.write(f"{event['name']}: no results found, event skipped.")
        return False

    event_folder.mkdir()
    for file_name, table in tables.items():
        table.to_csv(event_folder / file_name, index=False)
    progress_bar.write(f"{event['name']}: saved {len(tables)} divisions to {event_folder.name}")
    return True


# ---------------------------------------------------------------------------
# Finding the events
# ---------------------------------------------------------------------------

def find_events_newest_first():
    """Yield finished events, newest first, by walking the calendar backwards.

    This is a generator ("yield"): it only downloads the next month when the
    caller asks for more events, so we never load the whole calendar.
    """
    today = datetime.now(timezone.utc)
    year, month = today.year, today.month

    while year >= OLDEST_YEAR_TO_SEARCH:
        events = [hyresult_client.get_event_details(slug)
                  for slug in hyresult_client.get_event_slugs_of_month(year, month)]
        finished_events = [event for event in events if is_event_finished(event)]
        finished_events.sort(key=lambda event: event["end_date"], reverse=True)
        yield from finished_events

        # Go one month back: January 2026 -> December 2025.
        month -= 1
        if month == 0:
            year, month = year - 1, 12


def main() -> None:
    events_to_import = NUMBER_OF_EVENTS - count_imported_events()
    print(f"{count_imported_events()} events in RawData, {NUMBER_OF_EVENTS} wanted.")

    if events_to_import <= 0:
        print("Nothing to import.")
        return

    # One progress bar over the events: it moves one step per saved event
   
    with tqdm(total=events_to_import, unit="event") as progress_bar:
        imported = 0
        # enumerate() numbers the events 0, 1, 2, ... in calendar order. We count
        # every finished event (also existing ones), so each run picks the same events.
        for event_number, event in enumerate(find_events_newest_first()):
            if event_number % IMPORT_EVERY_NTH_EVENT != 0:
                continue  # only event 0, 10, 20, ... is imported

            event_folder = RAW_DATA_FOLDER / make_folder_name(event["city"], event["start_date"][:4])
            if event_folder.exists():
                progress_bar.write(f"{event['name']}: folder {event_folder.name} exists already, skipped.")
                continue

            if import_event(event, event_folder, progress_bar):
                imported += 1
                progress_bar.update(1)  # one more event done -> move the bar one step

            if imported == events_to_import:
                break

    print(f"Done: {imported} new events imported.")


if __name__ == "__main__":
    main()
