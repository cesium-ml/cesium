"""
noisifier_pilot.py

Pulls the string to noisify signal data.

NOTE:
 - Requires system environment variable: TCP_DIR
     - This is the full path of the top directory of TCP project
     - In other words, the TCP directory which was svn checked-out
     - e.g. .bashrc/execute for bash:
                export TCP_DIR=/home/pteluser/src/TCP/
"""
from __future__ import print_function
from __future__ import absolute_import

import os, sys

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code'))

from .Code import generators_importers, feature_interfaces

signals_list = []

gen = generators_importers.from_xml(signals_list)
gen.generate(xml_handle="../../Data/source_5.xml",register=False)
gen.sig.add_features_to_xml_string(gen.signals_list)

interface = feature_interfaces.feature_interface
noisify_extr = interface.request_extractor('noisify') # grab the noisifying extractor from the interface

for i in range(len(signals_list)):
	signal = signals_list[i]
	signal.register_signal(initialize=False)
	
interface.notify(noisify_extr)

def fetch_noisified(signal, band):
	noisified = signal.properties['data'][band]['inter']['noisify'].result
	return noisified

feature_added_VOSource_XML_fpath = '/tmp/test_feature_algorithms.VOSource.xml'
gen.sig.write_xml(out_xml_fpath=feature_added_VOSource_XML_fpath)
print("Wrote VOSource XML (with features) to:", feature_added_VOSource_XML_fpath)


def main():
	pass


if __name__ == '__main__':
	main()

