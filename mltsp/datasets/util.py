import hashlib
import os
import tarfile

import pandas as pd

from .. import util

try:
    import urllib.request as request
except:
    import urllib2 as request


DATA_PATH = os.path.expanduser('~/.local/')


def _md5sum_file(path):
    """Calculate the MD5 sum of a file."""
    with open(path, 'rb') as f:
        m = hashlib.md5()
        while True:
            data = f.read(8192)
            if not data:
                break
            m.update(data)
    return m.hexdigest()


def download_file(data_dir, base_url, filename):
    """Download a single file into the given directory."""
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    file_path = os.path.join(data_dir, filename)
    opener = request.urlopen(base_url + filename)
    with open(file_path, 'wb') as f:
        f.write(opener.read())
    return file_path


def download_and_extract_archives(data_dir, base_url, filenames, md5sums=None,
                                 remove_archive=True):
    """Download list of data archives, verify md5 checksums (if applicable),
    and extract into the given directory.
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    all_file_paths = []
    for fname in filenames:
        archive_path = os.path.join(data_dir, fname)
        opener = request.urlopen(base_url + fname)
        with open(archive_path, 'wb') as f:
            f.write(opener.read())
        if md5sums:
            if _md5sum_file(archive_path) != md5sums[fname]:
                raise ValueError("File {} checksum verification has failed."
                                 " Dataset fetching aborted.".format(fname))
        with util.extract_time_series(archive_path,
                                      cleanup_archive=remove_archive,
                                      extract_dir=data_dir) as file_paths:
            all_file_paths.extend(file_paths)
    return all_file_paths


def build_time_series_archive(archive_path, ts_paths):
    """Write a .tar.gz archive containing the given time series files, as
    required for data uploaded via the front end.
    """
    with tarfile.TarFile(archive_path, 'w') as t:
        for fname in ts_paths:
            t.add(fname, arcname=os.path.basename(fname))


def write_header(header_path, filenames, classes, metadata={}):
    """Write a header file for the given time series files, as required for
    data uploaded via the front end.
    """
    data_dict = {'filename': [util.shorten_fname(f) for f in filenames],
                 'class': classes}
    data_dict.update(metadata)
    df = pd.DataFrame(data_dict)
    df.to_csv(header_path, index=False)
