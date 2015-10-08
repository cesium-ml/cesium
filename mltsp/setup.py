def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration('mltsp', parent_package, top_path)
    config.add_subpackage('science_features')
    config.add_data_files('mltsp.yaml.example')
    return config


if __name__ == "__main__":
    from numpy.distutils.core import setup

    config = configuration(top_path='').todict()
    setup(**config)
