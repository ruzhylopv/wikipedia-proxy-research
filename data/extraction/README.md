
## Folder contents and purpose

### Contents:
- `utils.py` — helper functions for fetching Wikipedia revisions and extracting intro text
- `cleaning.py` — text cleaning utilities (`wikitext_to_clean_intro` and related functions)
- `main.ipynb` — main enviroment to work in and test methods

### Purpose:
It contains everything you need to load the revisions data from wikipedia. In particular, you will almost surely require only `get_revision_data(title: str)` method.
## Setup

Recommended: use a virtual environment.

```bash
pip install pandas mwparserfromhell requests ipython
```

## Load the data

### Option 1: use existing CSV
Contains revisions for "Tesla, Inc." article.
```python
import pandas as pd

data_path = 'revisions_with_text.csv'
df = pd.read_csv(data_path)
print(df.head())
```

### Option 2: fetch and build from Wikipedia

TODO: Test if it even works

**IMPORTANT**: main method is `get_revision_data(title: str)`. If i did everything right, no need to dive deeper.
```python
from utils import get_revisions_data

# Choose any Wikipedia page title; default is "Tesla, Inc."
page_title = 'Tesla, Inc.'
df = get_revisions_data(page_title)
print(df.head())
```

`get_revisions_data` does:
- `get_revisions_metadata(title)` calls Wikipedia API for metadata
- `get_dataframe_with_revisions(metadata)` converts metadata to DataFrame
- `get_intros(df)` downloads page revisions and extracts introductory text
- populates `intro_text` in DataFrame