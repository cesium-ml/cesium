"""Machine Learning Time-Series Platform (MLTSP)

See http://mltsp.io for more information.
"""

__version__ = '0.3dev'


def install():
    """Install MLTSP config file in ~/.config/mltsp/mltsp.yaml.

    """
    import os
    import shutil

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
