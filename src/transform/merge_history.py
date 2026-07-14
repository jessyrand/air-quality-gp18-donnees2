import pandas as pd


def merge_history_dataframe(
    old_df: pd.DataFrame,
    new_df: pd.DataFrame,
) -> pd.DataFrame:

    old_df["date"] = pd.to_datetime(old_df["date"], utc=True)
    new_df["date"] = pd.to_datetime(new_df["date"], utc=True)

    merged_df = pd.concat([old_df, new_df],ignore_index=True,)
    merged_df = merged_df.drop_duplicates(subset=["date"],keep="last")
    merged_df = merged_df.sort_values("date")
    merged_df = merged_df.reset_index(drop=True)

    return merged_df