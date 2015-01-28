""" read files into numpy arrays """
from __future__ import print_function

import numpy
class vizier_importer(object):
	def open_file(self):
		filepath = 'table.dat'
		data = open(filepath, mode='r')
		for line in data:
			jd = line[10:21] #julian date, specified from http://vizier.u-strasbg.fr/viz-bin/Cat?II/217
			mag = line[23:28] #[-0.93/16.0]? V (Johnson) magnitude
			if mag != '     ':
				print(jd, mag)
		return None
if __name__ == '__main__':
	importer = vizier_importer()
	importer.open_file()