"""Machine Learning Time-Series Platform (cesium)

See http://cesium.mlfor more information.
"""

from .version import version as __version__


def install():
    """Install cesium config file and create data folders.

    Copies cesium.yaml.example to ~/.config/cesium/cesium.yaml and creates data
    directories as described in `cesium.config.cfg['paths']`
    """
    import os
    import shutil
    from distutils.dir_util import copy_tree

    data_src = os.path.join(os.path.dirname(__file__), "data")
    data_dst = os.path.expanduser('~/.local/cesium/')
    copy_tree(data_src, data_dst, update=1)
    print("Created data directory at {} and copied sample data.".format(
        os.path.expanduser('~/.local/cesium/')))

    cfg = os.path.expanduser('~/.config/cesium/cesium.yaml')
    cfg_dir = os.path.dirname(cfg)

    if os.path.exists(cfg):
        print('Existing configuration at {} -- not overwriting.'.format(cfg))
        return

    if not os.path.exists(cfg_dir):
        os.makedirs(cfg_dir)

    shutil.copyfile(os.path.join(os.path.dirname(__file__),
                                 'cesium.yaml.example'),
                    cfg)

    print('Installed {}'.format(cfg))
    print('Please customize this file with authentication tokens, etc.')
