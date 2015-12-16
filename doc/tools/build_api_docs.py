#!/usr/bin/env python
"""Script to auto-generate our API docs.
"""
# stdlib imports
import os, sys

# local imports
from apigen import ApiDocWriter

#*****************************************************************************

if __name__ == '__main__':
    package = 'mltsp'
    import mltsp
    module = sys.modules[package]

    outdir = 'api'
    # Unlike skimage, for now we just manually specify which files to inspect
    modules = ['mltsp', 'mltsp.featurize', #mltsp.custom_feature_tools',
               'mltsp.obs_feature_tools', 'mltsp.science_feature_tools',
               'mltsp.science_features', 'mltsp.build_model', 'mltsp.predict',
               'mltsp.util']

    try:
        from unittest.mock import MagicMock
    except:
        from mock import MagicMock
    sys.modules['mltsp.science_features._lomb_scargle'] = MagicMock()

    docwriter = ApiDocWriter(package, modules)
#    docwriter.package_skip_patterns += [r'filter$']
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'api', relative_to='api')
    print('%d files written' % len(docwriter.written_modules))
