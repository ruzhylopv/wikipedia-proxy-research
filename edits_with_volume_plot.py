import pandas as pd
import matplotlib.pyplot as plt

def prepare_wiki_df(df: pd.DataFrame, drop_no_text = False):


    if drop_no_text:
        df = df[df.intro_text.isna().astype(int) == 0]
    df['is_revert'] = (df['sha1'] == df['sha1'].shift(2)).astype(int)
    
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["timestamp"] = df["timestamp"].dt.tz_convert("America/New_York")
    df["trading_day"] = (df["timestamp"] - pd.Timedelta(hours=16)).dt.date


    return df

def get_aggregated_wiki_stats(df: pd.DataFrame, sample="W"):

    before = df[~df['after_close']].resample(sample).agg({
        'is_revert': 'sum',
        'user': 'nunique',
        'sha1': 'count'
    }).rename(columns={
        'is_revert': 'reverts_before',
        'user': 'unique_editors_before',
        'sha1': 'total_edits_before'
    })
    # AFTER close
    after = df[df['after_close']].resample(sample).agg({
        'is_revert': 'sum',
        'user': 'nunique',
        'sha1': 'count'
    }).rename(columns={
        'is_revert': 'reverts_after',
        'user': 'unique_editors_after',
        'sha1': 'total_edits_after'
    })
    result = before.join(after, how='outer').fillna(0)
    return result


def prepare_stock_df(df: pd.DataFrame):
    df["Date"] = pd.to_datetime(df["Date"], utc=True)
    df.index = df["Date"]
    return df

def display_plot(master_df: pd.DataFrame, name: str):
    fig, ax1 = plt.subplots(figsize=(14, 7))


    color_edits = 'tab:blue'
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Monthly Major Edits', color=color_edits, fontsize=12)
    ax1.plot(master_df.index, master_df["n_edits"], 
            color=color_edits, alpha=0.6, label="Edit Intensity")
    ax1.tick_params(axis='y', labelcolor=color_edits)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx() # This creates the second Y-axis
    color_stock = 'tab:green'
    ax2.set_ylabel(f'{name} Stock Price (Volume)', color=color_stock, fontsize=12)
    ax2.plot(master_df.index, master_df.Volume, 
            color=color_stock, linewidth=2, label="Tesla Stock Price", alpha=0.3)
    ax2.tick_params(axis='y', labelcolor=color_stock)

    plt.title(f'{name} Wikipedia Editing Intensity vs. Stock market volume', fontsize=14)
    fig.tight_layout()


def plot_edits_with_volume(wiki_dir, stock_dir):

    name = wiki_dir.split("_")[-1].rstrip(".csv").capitalize()
    wiki = pd.read_csv(wiki_dir)
    stock = pd.read_csv(stock_dir)


    wiki = prepare_wiki_df(wiki)
    stock = prepare_stock_df(stock)

    monthly_snapshots_wiki = wiki.resample("MS").ffill()
    monthly_intensity = wiki.resample('MS').size()
    monthly_snapshots_wiki["n_edits"] = monthly_intensity.fillna(0)


    stock_monthly = stock.resample('MS').agg({
    'Close': 'mean', 
    'Volume': 'sum'
    })

    monthly_snapshots_wiki.index = monthly_snapshots_wiki.index.tz_localize(None)
    stock_monthly.index = stock_monthly.index.tz_localize(None)



    master_df = monthly_snapshots_wiki.join(stock_monthly, how='inner')


    display_plot(master_df, name)





