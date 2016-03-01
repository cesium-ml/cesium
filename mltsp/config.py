# config.py
#
# Config file for MLTSP app.
#
from __future__ import print_function
import os, sys
import multiprocessing
import yaml
from . import util
import glob

# Load configuration
config_files = [
    os.path.expanduser('~/.config/mltsp/mltsp.yaml'),
    ]

config_files.extend(glob.glob(
    os.path.join(os.path.dirname(__file__), '../mltsp-*.yaml')))

config_files = [os.path.abspath(cf) for cf in config_files]

# Load example config file as default template
cfg = util.warn_defaultdict()
cfg.update(yaml.load(open(os.path.join(os.path.dirname(__file__),
                             "mltsp.yaml.example"))))

for cf in config_files:
    try:
        more_cfg = yaml.load(open(cf))
        print('[MLTSP] Loaded {}'.format(cf))
        cfg.update(more_cfg)
    except IOError:
        pass

# Expand home variable;
cfg['paths'] = {key: os.path.expanduser(value)
                   for (key, value) in cfg['paths'].items()}
cfg['paths'] = {key: value.format(**cfg['paths'])
                   for (key, value) in cfg['paths'].items()}


# Specify default features to plot in browser:
features_to_plot = [
    "freq1_freq",
    "freq1_amplitude1",
    "median",
    "fold2P_slope_90percentile",
    "maximum",
    "minimum",
    "percent_difference_flux_percentile",
    "freq1_rel_phase2"]


# Specify number of time series to featurize as part of a "test run"
TEST_N = 5


for path_name, path in cfg['paths'].items():
    if path_name == 'err_log_path':
        path = os.path.dirname(path)

    if not os.path.exists(path):
        print("Creating %s" % path)
        try:
            os.makedirs(path)
        except Exception as e:
            print(e)

del yaml, os, sys, print_function, config_files, multiprocessing

cfg['mltsp'] = locals()


def show_config():
    print()
    print("=" * 78)
    print("MLTSP configuration")

    for key in ('paths', 'database', 'testing'):
        if key in cfg:
            print("-" * 78)
            print(key)
            print("-" * 78)

            for key, val in cfg[key].items():
                print(key.ljust(30), val)

    print("=" * 78)

show_config()
