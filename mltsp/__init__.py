"""Machine Learning Time-Series Platform (MLTSP)

See http://mltsp.io for more information.
"""

from .version import version as __version__


def install():
    """Install MLTSP config file in ~/.config/mltsp/mltsp.yaml.

    """
    import os
    import shutil
    from distutils.dir_util import copy_tree

    data_src = os.path.join(os.path.dirname(__file__), "data")
    data_dst = os.path.expanduser('~/.local/mltsp/')
    copy_tree(data_src, data_dst, update=1)
    print("Created data directory at {} and copied sample data.".format(
        os.path.expanduser('~/.local/mltsp/')))

    cfg = os.path.expanduser('~/.config/mltsp/mltsp.yaml')
    cfg_dir = os.path.dirname(cfg)

    if os.path.exists(cfg):
        print('Existing configuration at {} -- not overwriting.'.format(cfg))
        return

    if not os.path.exists(cfg_dir):
        os.makedirs(cfg_dir)

    shutil.copyfile(os.path.join(os.path.dirname(__file__),
                                 'mltsp.yaml.example'),
                    cfg)

    print('Installed {}'.format(cfg))
    print('Please customize this file with authentication tokens, etc.')
