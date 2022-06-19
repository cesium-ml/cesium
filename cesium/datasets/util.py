import hashlib
import os
import tarfile

import pandas as pd

from .. import util

import urllib.request as request


DATA_PATH = os.path.expanduser("~/.local/")


def _md5sum_file(path):
    """Calculate the MD5 sum of a file."""
    with open(path, "rb") as f:
        m = hashlib.md5()
        while True:
            data = f.read(8192)
            if not data:
                break
            m.update(data)
    return m.hexdigest()


def download_file(data_dir, base_url, filename):
    """Download a single file into the given directory.

    Parameters
    ----------
    data_dir : str
        Path to directory in which to save file.
    base_url : str
        URL of file to download, minus the file name.
    filename : str
        Name of file to be downloaded.

    Returns
    -------
    str
        The path to the newly downloaded file.
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    file_path = os.path.join(data_dir, filename)
    opener = request.urlopen(base_url + filename)
    with open(file_path, "wb") as f:
        f.write(opener.read())
    return file_path


def download_and_extract_archives(
    data_dir, base_url, filenames, md5sums=None, remove_archive=True
):
    """Download list of data archives, verify md5 checksums (if applicable),
    and extract into the given directory.

    Parameters
    ----------
    data_dir : str
        Path to directory in which to download and extract archives.
    base_url : str
        URL of files to download, minus the file names.
    filenames : list or tuple of str
        Name of file to be downloaded.
    md5sums : dict, optional
        Dictionary whose keys are file names and values are
        corresponding hexadecimal md5 checksums to be checked against.
    remove_archive : bool, optional
        Boolean indicating whether to delete the archive(s) from disk
        after the contents have been extracted. Defaults to True.

    Returns
    -------
    list of str
        The paths to the newly downloaded and unzipped files.
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    all_file_paths = []
    for fname in filenames:
        archive_path = os.path.join(data_dir, fname)
        opener = request.urlopen(base_url + fname)
        with open(archive_path, "wb") as f:
            f.write(opener.read())
        if md5sums:
            if _md5sum_file(archive_path) != md5sums[fname]:
                raise ValueError(
                    "File {} checksum verification has failed."
                    " Dataset fetching aborted.".format(fname)
                )
        with util.extract_time_series(
            archive_path, cleanup_archive=remove_archive, extract_dir=data_dir
        ) as file_paths:
            all_file_paths.extend(file_paths)
    return all_file_paths


def build_time_series_archive(archive_path, ts_paths):
    """Write a .tar.gz archive containing the given time series files, as
    required for data uploaded via the front end.

    Parameters
    ----------
    archive_path : str
        Path at which to create the tarfile.
    ts_paths : list of str
        Paths to time-series file to be included in tarfile.
    """
    with tarfile.TarFile(archive_path, "w") as t:
        for fname in ts_paths:
            t.add(fname, arcname=os.path.basename(fname))


def write_header(header_path, filenames, classes, metadata={}):
    """Write a header file for the given time series files, as required for
    data uploaded via the front end.

    Parameters
    ----------
    header_path : str
        Path at which header file will be created.
    filenames : list of str
        List of time-series file names associated with header file.
    classes : list of str
        List of class names associated with each time-series file.
    metadata : dict, optional
        Dictionary describing meta features associated with each time-series.
        Keys are time-series file names.
    """
    data_dict = {
        "filename": [util.shorten_fname(f) for f in filenames],
        "class": classes,
    }
    data_dict.update(metadata)
    df = pd.DataFrame(data_dict)
    df.to_csv(header_path, index=False)
