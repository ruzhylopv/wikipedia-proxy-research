import pandas as pd
import requests
import time
from IPython.display import clear_output
from data.extraction.cleaning import wikitext_to_clean_intro

URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "RevisionText/1.0 (contact@example.com)"}
COLUMNS_LIST = ["revid", "parentid", "timestamp", "user", "temp", "comment", "size", "sha1", "flags", "intro_text", "minor"]

def progressbar_notebook(clean_intros_len, time_start, current, whole):
    """Display a notebook-style progress bar for intro extraction.

    Args:
        clean_intros_len (int): number of cleaned introductions already collected.
        time_start (float): timestamp when the current batch started.
        current (int): number of revisions processed so far.
        whole (int): total number of revisions to process.
    """
    clear_output(wait=True)
    frac = current / whole
    print("="*100)
    print("Loaded revisions: ", current, " | Total revisions: ", whole)
    print("Length of clean_intros: ", clean_intros_len)
    print(f"Current progress: {100*frac}%")
    print("Time since last batch: ", round(time.time() - time_start, 3), "s", sep="")
    print("="*100)

    print("▮" * int(frac * 100) + "▯" * int((1 - frac) * 100))

def progressbar(func):
    """Decorator to wrap the get_intros function and provide progress updates.

    Wraps the target function so that a progress callback is injected with total
    and per-batch timing info.
    """
    def wrapper(*args, **kwargs):

        state = {
            "start_time": None,
            "last_exec_time": None
        }

        def update(clean_intros_len, current, whole):
            if state["start_time"] is None:
                state["start_time"] = time.time()
                state["last_exec_time"] = time.time()

            clear_output(wait=True)

            frac = current / whole
            elapsed = (now := time.time()) - state["start_time"]
            time_from_last = now - state["last_exec_time"]
            state["last_exec_time"] = now

            print("STEP 2: EXTRACTING INTRO TEXT")
            print("=" * 100)
            print("Loaded revisions:", current, "| Total revisions:", whole)
            print("Length of clean_intros:", clean_intros_len)
            print(f"Current progress: {100 * frac:.2f}%")
            print("Time elapsed (total):", round(elapsed, 3), "s")
            print("Time elapsed (from last batch):", round(time_from_last, 3), "s")

            print("=" * 100)

            print("▮" * int(frac * 100) + "▯" * int((1 - frac) * 100))

        return func(*args, progress_callback=update, **kwargs)

    return wrapper

def get_revisions_metadata(title: str) -> list[object]:
    """Fetch revision metadata for a Wikipedia page title.

    Queries the Wikipedia API for revision IDs and metadata like timestamp,
    user, size, and sha1, with support for continuation paging.

    Args:
        title (str): Wikipedia article title.

    Returns:
        list[object]: List of revision metadata dictionaries.
    """
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "format": "json",
        "rvlimit": "max",
        "rvprop": "ids|timestamp|user|size|sha1|flags",
        "rvslots": "main",
        "formatversion": "2"
    }

    revisions_no_content = []
    while True:
        data = requests.get(URL, params=params, headers=HEADERS)
        if data.status_code != 200:
            print(f"Error fetching revisions: {data.status_code}")
            break
        data = data.json()

        page = data["query"]["pages"][0]
        batch = page.get("revisions", [])
        revisions_no_content.extend(batch)
        clear_output(wait=True)
        print("="*100)
        print("STEP 1: INITIAL EXTRACTION. EXTRACTING REVISIONS METADATA WITH NO CONTENT (update check)")
        print(f"Current batch size: {len(batch)}")
        print(f"Fetched {len(revisions_no_content)} revisions (no content) so far...")
        if "continue" in data:
            params.update(data["continue"])
        else:
            break

    return revisions_no_content


def get_dataframe_with_revisions(metadata: list[dict]):
    """Convert revision metadata list into a pandas DataFrame.

    Args:
        metadata (list[dict]): List of revisions from get_revisions_metadata.

    Returns:
        pd.DataFrame: A dataframe with standard columns defined in COLUMNS_LIST.
    """
    rows = []

    for rev in metadata:
        rows.append({
            "revid": rev.get("revid"),
            "parentid": rev.get("parentid"),
            "timestamp": rev.get("timestamp"),
            "user": rev.get("user"),
            "temp": rev.get("temp", False),
            "comment": rev.get("comment"),
            "size": rev.get("size"),
            "sha1": rev.get("sha1"),
            "flags": rev.get("flags"),
            "minor": rev.get("minor"),
        })

    return pd.DataFrame(rows, columns=COLUMNS_LIST)


@progressbar
def get_intros(df: pd.DataFrame, progress_callback = None) -> list:
    """Download raw revision page text and extract cleaned intro sentences.

    Splits the DataFrame into chunks, fetches content for each revision id, uses
    wikitext_to_clean_intro to parse the intro, and keeps ordering consistent.

    Args:
        df (pd.DataFrame): DataFrame containing revision metadata with revid column.
        progress_callback (callable, optional): Optional callback for progress updates.

    Returns:
        list: Cleaned intro texts for each revision in the same order as df.
    """
    n = df.shape[0]
    all_clean_intros = []

    for i in range(0, n, 50):
        time_start = time.time()
        chunk = df.iloc[i:i+50]
        ids = chunk["revid"]

        ids_string = "|".join(map(str, ids))

        params_content = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "revids": ids_string,
            "rvprop": "ids|content",
            "rvslots": "main",
            "formatversion": "2"
        }
        
        response = requests.get(URL, params=params_content, headers=HEADERS).json()
        found_revisions = {}
        pages = response["query"].get("pages", [])

        #Initial pull for chunk
        for p in pages:
            for rev in p.get("revisions", []):
                try:
                    wikitext_content = rev.get("slots", {}).get("main", {}).get("content")
                    intro = wikitext_to_clean_intro(wikitext_content)
                    found_revisions[rev["revid"]] = intro
                except Exception:
                    found_revisions[rev["revid"]] = ""

        #Validating + matching 1 to 1 relationship
        for original_id in chunk["revid"]:
            if original_id in found_revisions:
                all_clean_intros.append(found_revisions[original_id])
            else:
                all_clean_intros.append("")

        if progress_callback:
            progress_callback(len(all_clean_intros), i + len(chunk), n)

        # progressbar_notebook(len(all_clean_intros), time_start, i + len(chunk), n)

    return all_clean_intros

def populate_df_with_intros(df, intros):
    """Insert intro text list into dataframe and keep structure stable.

    Args:
        df (pd.DataFrame): Revisions dataframe prepared by get_dataframe_with_revisions.
        intros (list): List of intro_text values corresponding to df rows.

    Returns:
        bool: True on success, False on failure with printed traceback.
    """
    try:
        df["intro_text"] = intros
        return True
    except Exception as e:
        print(f"Cannot populate dataframe. {type(e).__name__} occurred.")
        import traceback
        traceback.print_exc()
        return False

def get_revisions_data(title = "Tesla, Inc."):
    """Full workflow helper: fetch revisions, parse intros, and return dataframe.

    Args:
        title (str): Wikipedia article title. Defaults to "Tesla, Inc.".

    Returns:
        pd.DataFrame | list: DataFrame with intro_text on success, or intros list on failure.
    """
    metadata = get_revisions_metadata(title)
    df = get_dataframe_with_revisions(metadata)
    intros = get_intros(df)

    success = populate_df_with_intros(df, intros)
    if not success:
        return intros
    return df




