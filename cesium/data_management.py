import os
import warnings
import numpy as np
import pandas as pd
from . import util
from . import time_series
from .time_series import TimeSeries


__all__ = ["parse_ts_data", "parse_headerfile", "parse_and_store_ts_data"]


# TODO more robust error handling
def parse_ts_data(filepath, sep=","):
    """Parses raw time series data file and returns an (n, 3) array of values.

    Data is expected as text in tabular format with separator `sep`. The output
    will always have three columns (time, measurement, error), even if the data
    file contains two or fewer:

    - For data containing three columns (time, measurement, error), all
      three are returned.
    - For data containing two columns, a dummy error column is added with
      value `time_series.DEFAULT_ERROR_VALUE`.
    - For data containing one column, a time column is also added with
      values evenly spaced from 0 to `time_series.DEFAULT_MAX_TIME`.

    Parameters
    ----------
    filename : str
        Path to raw time series data to be parsed.
    sep : str, optional
        Separator of columns in data file; defaults to ','.

    Returns
    -------
    np.ndarray
        3-column array of (time, measurement, error) values.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*input contained no data")
        ts_data = np.loadtxt(filepath, delimiter=sep, ndmin=2)
    ts_data = ts_data[:, :3]  # Only using T, M, E
    if ts_data.shape[0] == 0 or ts_data.shape[1] == 0:
        raise ValueError(
            "Incomplete or improperly formatted time series data file provided."
        )
    elif ts_data.shape[1] == 1:
        ts_data = np.c_[
            np.linspace(0, time_series.DEFAULT_MAX_TIME, len(ts_data)),
            ts_data,
            np.repeat(time_series.DEFAULT_ERROR_VALUE, len(ts_data)),
        ]
    elif ts_data.shape[1] == 2:
        ts_data = np.c_[
            ts_data, np.repeat(time_series.DEFAULT_ERROR_VALUE, len(ts_data))
        ]
    return ts_data.T


def parse_headerfile(headerfile_path, files_to_include=None):
    """Parse header file containing classes/targets and meta-feature
    information.

    Parameters
    ----------
    headerfile_path : str
        Path to header file.

    files_to_include : list, optional
        If provided, only return the subset of rows from the header
        corresponding to the given filenames.

    Returns
    -------
    pandas.Series
        Class labels/targets from header file (if missing, all values are None)

    pandas.DataFrame
        Feature data from other columns besides filename, label (can be empty)
    """
    try:
        header = pd.read_csv(headerfile_path, comment="#")
    except:  # noqa
        raise ValueError("Improperly formatted header file.")
    if "filename" in header:
        header.index = [util.shorten_fname(str(f)) for f in header["filename"]]
        header.drop("filename", axis=1, inplace=True)
    if files_to_include:
        short_fnames_to_include = [util.shorten_fname(str(f)) for f in files_to_include]
        try:
            header = header.loc[short_fnames_to_include]
        except:  # noqa
            raise ValueError(
                "Incomplete header file: make sure your "
                "header contains an entry for each time "
                "series file in the uploaded archive, and "
                "that the file names match the first column "
                "of the header."
            )
    header.rename(
        columns={c: "label" for c in ["label", "target", "class", "class_label"]},
        inplace=True,
    )
    labels = (
        header.label
        if "label" in header
        else pd.Series([None] * len(header.index), index=header.index)
    )
    feature_data = header.drop(["label", "class"], axis=1, errors="ignore")
    return labels, feature_data


def parse_and_store_ts_data(
    data_path,
    output_dir,
    header_path=None,
    cleanup_archive=True,
    cleanup_header=True,
    sep=",",
):
    """Parses raw time series data from a single file or archive and loads
    metadata from header file (if applicable). Data is stored as files within
    `output_dir`, and the list of these paths is returned.

    Parameters
    ----------
    data_path : str
        Path to an individual time series file or tarball of multiple time
        series files to be used for feature generation.
    output_dir : str
        Directory in which time series files will be saved.
    header_path : str, optional
        Path to header file containing file names, labels/targets, and
        meta_features.
    cleanup_archive : bool, optional
        Boolean specifying whether to delete the uploaded data file/archive
        (defaults to True).
    cleanup_header : bool, optional
        Boolean specifying whether to delete the uploaded header file (defaults
        to True).
    sep : str, optional
        Separator of columns in data file; defaults to ','.

    Returns
    -------
    List of paths to time series files
    """
    with util.extract_time_series(
        data_path, cleanup_archive=cleanup_archive, cleanup_files=True
    ) as ts_paths:
        short_fnames = [util.shorten_fname(f) for f in ts_paths]
        if header_path:
            labels, meta_features = parse_headerfile(header_path, ts_paths)
        else:
            labels = pd.Series([None] * len(short_fnames), index=short_fnames)
            meta_features = pd.DataFrame(index=short_fnames)

        all_time_series = []
        for ts_path in ts_paths:
            fname = util.shorten_fname(ts_path)
            t, m, e = parse_ts_data(ts_path, sep)
            ts_label = labels.loc[fname]
            ts_meta_features = meta_features.loc[fname]
            ts_path = f"{fname}.npz"
            ts_path = os.path.join(output_dir, ts_path)
            ts = TimeSeries(t, m, e, ts_label, ts_meta_features, fname, ts_path)
            ts.save(ts_path)
            all_time_series.append(ts_path)

    if header_path and cleanup_header:
        util.remove_files([header_path])

    return all_time_series
