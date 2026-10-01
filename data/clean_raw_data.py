# Cleans the imported Hyrox results in data/RawData and writes them to data/CleanedData.
#
# Run it from the project folder with:  .venv\Scripts\python.exe data/clean_raw_data.py

from pathlib import Path
import pandas as pd

RAW_DATA_FOLDER = Path(__file__).parent / "RawData"
CLEANED_DATA_FOLDER = Path(__file__).parent / "CleanedData"

# All times are decimal minutes.
RUN_COLUMNS = ["Run_One", "Run_Two", "Run_Three", "Run_Four",
               "Run_Five", "Run_Six", "Run_Seven", "Run_Eight"]
WORKOUT_COLUMNS = ["Ski_Erg", "Sled_Push", "Sled_Pull", "BBJ",
                   "Row_Erg", "Farmers_Carry", "Lunges", "Wall_Balls"]
ALL_TIME_COLUMNS = RUN_COLUMNS + WORKOUT_COLUMNS + ["Rox_zone"]


def main():
    # Step 1: read all CSV files of all events into one big table.
    tables = []
    for csv_file in RAW_DATA_FOLDER.glob("*/*.csv"):  # e.g. RawData/Oslo_2026/HYROX_MEN.csv
        tables.append(pd.read_csv(csv_file))
    data = pd.concat(tables)

    # Step 2: remove athletes with at least one missing time.
    data = data.dropna(subset=ALL_TIME_COLUMNS)

    # Step 3: add new columns. sum(axis=1) adds up the columns of each row (= each athlete).
    data["Total_Running_Time"] = data[RUN_COLUMNS].sum(axis=1)
    data["Total_Workout_Time"] = data[WORKOUT_COLUMNS].sum(axis=1)
    data["Total_Race_Time"] = data[ALL_TIME_COLUMNS].sum(axis=1)

    slowest_run = data[RUN_COLUMNS].max(axis=1)
    fastest_run = data[RUN_COLUMNS].min(axis=1)
    data["Running_Spread"] = (slowest_run - fastest_run) / slowest_run

    data["Sled_Push_Pull_Ratio"] = data["Sled_Push"] / data["Sled_Pull"]

    # Step 4: write one file per class, e.g. "HYROX MEN" -> CleanedData/HYROX_MEN.csv
    CLEANED_DATA_FOLDER.mkdir(exist_ok=True)
    for class_name in data["Class"].unique():
        class_data = data[data["Class"] == class_name]
        file_name = class_name.replace(" ", "_") + ".csv"
        class_data.to_csv(CLEANED_DATA_FOLDER / file_name, index=False)
        print(f"{file_name}: {len(class_data)} athletes")


if __name__ == "__main__":
    main()
