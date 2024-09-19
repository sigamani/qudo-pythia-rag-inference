import re
import pandas as pd


def strip_html(x) -> str:
    """
    This function is aimed to remove all HTML tags from a provided input string.

    Parameters
    ----------
    x : Any type (integer, float, string, etc.,).
         It gets converted to string in the function for processing. This is the text from which HTML tags needs to be removed.
    Returns
    -------
    str
        The string with all HTML tags removed.
    Raises
    ------
    ValueError
         Raises ValueError when there is any error in the regular expression used to identify the html tags from input string.
    Example
    -------
    strip_html('<html><body><h1>my first heading</h1><p>my first paragraph</p></body></html>')
    'my first heading my first paragraph'
    """
    x = str(x)
    try:
        return re.sub("<[^<]+?>", "", x)
    except:
        raise ValueError(f"Inspect regex for {x}")


def convert_to_shortname(full_name: str) -> str:
    """
    Converts an underscore delimited string to a shorter version by stripping off the last part.
    If the last part is 'ord' or 'iso', the input string will be returned as it is.

    Parameters:
    full_name (str): The full name as an underscore delimited string.
    Returns:
    str: The shorter name as an underscore delimited string, or the original name if the last part is 'ord' or 'iso'.
    Raises:
    TypeError: If the input is not a string.
    ValueError: If the input string does not contain an underscore.
    """
    # Validation and error handling
    if not isinstance(full_name, str):
        raise TypeError("Input should be a string")
    if "_" not in full_name:
        raise ValueError("Input string should be underscore delimited")
    try:

        # Split the string on underscore
        name_parts = full_name.split("_")
        # Return as is if last part isn't to be stripped
        if name_parts[-1] in ["ord", "iso"]:
            return full_name
        # Strip off the last part
        name_parts.pop()
        return "_".join(name_parts)
    except Exception as e:
        return str(e)


def prep_data(self, data, qtype, q_code, title) -> pd.DataFrame:
    data_grouped = data.groupby([self.Q_CODE, self.TITLE])[self.category_percentages_col].apply(list).reset_index()
    data_grouped[self.category_percentages_col] = data_grouped[self.category_percentages_col].apply(
        lambda x: [item for sublist in x for item in sublist]
    )
    seg_modes_chi_squared = self.seg_modes_data[self.seg_modes_data["qtype"] == qtype][
        [self.Q_CODE, self.TITLE, self.MODE]
    ].merge(data_grouped[[self.Q_CODE, self.category_percentages_col, self.TITLE]], how="outer", on=[q_code, title])
    return seg_modes_chi_squared


def load_parquet(file_path):
    """
    Load a Parquet file into a DataFrame.
    Args:
        file_path (str): The file path of the Parquet file to load.
    Returns:
        pd.DataFrame: The loaded DataFrame.
    """
    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        print(f"Error loading Parquet file: {e}")
        return None


def save_parquet(df, file_path):
    """
    Save a DataFrame to a Parquet file.
    Args:
        df (pd.DataFrame): The DataFrame to save.
        file_path (str): The file path to save the DataFrame to.
    """
    try:
        df.to_parquet(file_path, index=False)
    except Exception as e:
        print(f"Error saving DataFrame to Parquet: {e}")
