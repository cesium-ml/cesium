import collections
import contextlib
import errno
import os
import tarfile
import tempfile
import zipfile

from .custom_exceptions import DataFormatError


__all__ = ['shorten_fname', 'remove_files', 'extract_time_series']


def shorten_fname(file_path):
    """Extract the name of a file (omitting directory names and extensions).

    Parameters
    ----------
    file_path : str
        Absolute or relative path to a file.

    Returns
    -------
    str
       The name of the file with directory names and extensions removed.

    """
    return os.path.splitext(os.path.basename(file_path))[0]


def make_list(x):
    """Wrap `x` in a list if it isn't already a list or tuple.

    Parameters
    ----------
    x : any valid object
        The parameter to be wrapped in a list.

    Returns
    -------
    list or tuple
        Returns `[x]` if `x` is not already a list or tuple, otherwise
        returns `x`.

    """
    if isinstance(x, collections.Iterable) and not isinstance(x, (str, dict)):
        return x
    else:
        return [x]


def remove_files(paths):
    """Remove specified file(s) from disk.

    Parameters
    ----------
    paths : str or list of str
        Path(s) to file(s) to be removed from disk.

    """
    paths = make_list(paths)
    for path in paths:
        try:
            os.remove(path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            else:
                pass


@contextlib.contextmanager
def extract_time_series(data_path, cleanup_archive=True, cleanup_files=False,
                        extract_dir=None):
    """Extract zip- or tarfile of time series file and return file paths.

    If the given file is not a tar- or zipfile then it is treated as a single
    time series filepath.

    Parameters
    ----------
    data_path : str
        Path to data archive or single data file.

    cleanup_archive : bool, optional
        Boolean specifying whether to delete the original archive (if
        applicable). Defaults to True.

    cleanup_files : bool, optional
        Boolean specifying whether to delete the extracted files when exiting
        the given context. Defaults to False.

    extract_dir : str, optional
        Directory into which files are to be extracted (if applicable). If
        None, a temporary directory is created.

    Yields
    ------
    list of str
        List of full paths to time series files.
    """
    if extract_dir is None:
        extract_dir = tempfile.mkdtemp()

    if tarfile.is_tarfile(data_path):
        archive = tarfile.open(data_path)
        archive.extractall(path=extract_dir)
        all_paths = [os.path.join(extract_dir, f) for f in archive.getnames()]
    elif zipfile.is_zipfile(data_path):
        archive = zipfile.ZipFile(data_path)
        archive.extractall(path=extract_dir)
        all_paths = [os.path.join(extract_dir, f) for f in archive.namelist()]
    else:
        archive = None
        all_paths = [data_path]

    if archive:
        archive.close()
        if cleanup_archive:
            remove_files(data_path)

    file_paths = [f for f in all_paths if not os.path.isdir(f)]
    try:
        yield file_paths
    finally:
        if cleanup_files:
            remove_files(file_paths)
