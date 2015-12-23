import mock
import os
import shutil
import tempfile
from zipfile import ZipFile

import numpy as np
import numpy.testing as npt
import pandas as pd
from sklearn.datasets.base import Bunch

import mltsp.datasets.andrzejak as andrzejak
import mltsp.datasets.util as dsutil

try:
    from io import BytesIO as StringLike
except:
    import StringIO as StringLike

 
def urlpatch(*args):
    try:
        import urllib.request
        return mock.patch('urllib.request.urlopen', side_effect=args[0])
    except:
        import urllib2
        return mock.patch('urllib2.urlopen', side_effect=args[0])


class MockZipUrl(object):
    def __init__(self, url, num_columns=1):
        self.url = url
        self.num_columns = num_columns

    def read(self):
        string_like = StringLike()
        X = np.random.random((10, self.num_columns))
        text = '\n'.join(','.join(row) for row in X.astype('str'))
        fname = os.path.basename(self.url)
        prefix = fname[0]
        if fname.endswith('.zip'):
            with ZipFile(string_like, 'w') as z:
                z.writestr('{}001.txt'.format(prefix), text)
        else:
            pass #  TODO tarfiles
        return string_like.getvalue()


def _mock_andrzejak_url(*args):
    return MockZipUrl(url=args[0], num_columns=1)


@urlpatch(_mock_andrzejak_url)
def test_fetch_andrzejak(self):
    """Test EEG data download."""
    num_files = len(andrzejak.ZIP_FILES)
    data_dir = tempfile.mkdtemp()
    andrzejak.MD5SUMS = None
    data = andrzejak.fetch_andrzejak(data_dir)
    assert(data.archive.endswith('andrzejak.tar.gz') 
           and os.path.exists(data.archive))
    header = pd.read_csv(data.header)
    npt.assert_array_equal(header['class'], data.target)
    assert(all(len(t) == len(m)
               for t, m in zip(data.times, data.measurements)))
    assert(len(data.times) == num_files)
    assert(len(data.target) == num_files)
    assert(all(c in ['Z', 'N', 'O', 'S', 'F'] for c in data.target))
    shutil.rmtree(data_dir)
