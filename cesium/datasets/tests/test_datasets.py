import os
import tarfile
from zipfile import ZipFile

import numpy as np
import numpy.testing as npt
import pandas as pd

from cesium.datasets import andrzejak
from cesium.datasets import asas_training

from io import BytesIO as StringIO

try:
    from unittest import mock
except ImportError:
    import unittest.mock as mock


def urlpatch(*args):
    import urllib.request  # noqa: F401

    return mock.patch("urllib.request.urlopen", side_effect=args[0])


class MockZipUrl:
    def __init__(self, url, num_columns=1):
        self.url = url
        self.num_columns = num_columns

    def read(self):
        out_buffer = StringIO()
        fname = os.path.basename(self.url)
        prefix = fname[0]
        if fname.endswith(".dat"):
            header = f"filename,class,meta1\n{prefix}001,{prefix},1.0\n"
            out_buffer.write(header.encode("utf-8"))
        else:
            X = np.random.random((10, self.num_columns))
            text = "\n".join(",".join(row) for row in X.astype("str"))
            if fname.endswith(".zip"):
                with ZipFile(out_buffer, "w") as z:
                    z.writestr(f"{prefix}001.txt", text)
            elif fname.endswith(".tar.gz"):
                with tarfile.open(fileobj=out_buffer, mode="w:gz") as t:
                    tarinfo = tarfile.TarInfo(f"{prefix}001.txt")
                    tarinfo.size = len(text)
                    t.addfile(tarinfo, StringIO(text.encode("utf-8")))
        return out_buffer.getvalue()


def _mock_andrzejak_url(*args):
    return MockZipUrl(url=args[0], num_columns=1)


@urlpatch(_mock_andrzejak_url)
def test_fetch_andrzejak(self, tmpdir):
    """Test EEG data download."""
    num_files = len(andrzejak.ZIP_FILES)
    andrzejak.MD5SUMS = None
    data = andrzejak.fetch_andrzejak(str(tmpdir))
    assert data["archive"].endswith("andrzejak.tar.gz") and os.path.exists(
        data["archive"]
    )
    header = pd.read_csv(data["header"])
    npt.assert_array_equal(header["class"], data["classes"])
    assert all(len(t) == len(m) for t, m in zip(data["times"], data["measurements"]))
    assert len(data["times"]) == num_files
    assert len(data["classes"]) == num_files
    assert all(c in ["Z", "N", "O", "S", "F"] for c in data["classes"])


def _mock_asas_training_url(*args):
    return MockZipUrl(url=args[0], num_columns=3)


@urlpatch(_mock_asas_training_url)
def test_fetch_asas_training(self, tmpdir):
    """Test ASAS training data download."""
    num_files = 1
    asas_training.MD5SUMS = None
    data = asas_training.fetch_asas_training(str(tmpdir))
    assert data["archive"].endswith("asas_training_set.tar.gz") and os.path.exists(
        data["archive"]
    )
    header = pd.read_csv(data["header"])
    npt.assert_array_equal(header["class"], data["classes"])
    assert all(
        len(t) == len(m) and len(m) == len(e)
        for t, m, e in zip(data["times"], data["measurements"], data["errors"])
    )
    assert len(data["times"]) == num_files
    assert len(data["classes"]) == num_files
    assert len(data["metadata"]) == num_files
    assert all(c in ["a"] for c in data["classes"])
