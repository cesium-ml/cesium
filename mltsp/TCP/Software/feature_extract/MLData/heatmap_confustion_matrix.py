#!/usr/bin/env python 
"""
   v0.1 Make an HTML heatmap table of a Weka classify confusion matrix.
"""
from __future__ import print_function
import sys, os

__old__input_table_str = """
   a   b   c   d   e   f   g   h   i   j   k   l   m   n   o   p   q   r   s   t   u   v   w   x   y   z  aa  ab  ac  ad   <-- classified as
 438  25  41   0   0   0   0   0   0   0   0   0   0   4   0   0   0   5   0   1   0   1   3   0   0   0   0   0   0   0 |   a = Algol (Beta Persei)
  83  84  68   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   1   0   0   0   1   0   0   0   2   0   0   1 |   b = Beta Lyrae
  21  26 930   3   0   0   1   0   0   1   0   0   0   6   0   5   2   1   0   1   0   0   2   0   0   0  10   1   0   1 |   c = W Ursae Majoris
   1   0   3  12   0   0   0   0   1   0   0   0   0  22   0   0   0   0   0   5   0   0   7   0   0   0   4   0   0   0 |   d = Binary
   1   0   0   0   1   0   0   0   0   0   0   0   0   6   0   0   0   0   0   1   0   0   3   0   1   0   0   0   0   2 |   e = T Tauri
   0   0   0   0   1  15   0   0   0   0   0   0   0   1   0   0   0   0   0   5   0   0  10   0   0   0   2   0   0   0 |   f = Wolf-Rayet
   0   0   0   0   0   0  45   0   1   0   0   0   0   3   0   0   0   1   0   2   0   0   0   0   0   0   0   0   0   0 |   g = Type Ia Supernovae
   0   1   0   1   0   1   0  12   1   0   0   0   0   9   0   0   0   2   0   1   0   0   0   0   0   0   0   0   0   0 |   h = BL Lac
   1   0   4   1   0   0   1   0 576   0   0   0   0   4   0   3   0   0   0   0   0   0   0   0   0   0   0   0   0   0 |   i = Microlensing Event
   0   0   0   0   0   0   0   0   0  11   0   0   0   0   0   0   0   0   0   0   0   0   1   0   0   0   0   0   0   2 |   j = Semiregular Pulsating Red Giants
   1   0   0   0   0   0   0   0   0   0  14   0   0  11   0   0   0   0   0   0   0   0   3   0   0   0   0   0   0   5 |   k = Semiregular Pulsating Variable
   0   0   2   0   0   0   0   0   0   0   0   0   0  11   1   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0 |   l = Short period (BL Herculis)
   0   0   0   0   0   0   0   0   0   0   0   0   0  12   0   0   0   0   0   4   0   0   0   0   0   0   0   0   0   1 |   m = Population II Cepheid
   2   3   8   2   1   1   1   0   2   0   4   0   0 864  11   1   0   4   0   8   1   0   4   0   0   0   0   0   2   2 |   n = Classical Cepheid
   0   0   0   1   0   0   0   0   2   0   1   0   0  18  20   2   0   0   0   1   0   0   3   0   0   0   0   0   0   0 |   o = Symmetrical
   0   0   2   0   0   0   0   0   0   0   0   0   0  11   0  92   0   0   0   1   0   0   0   0   0   0   1   0   0   0 |   p = Multiple Mode Cepheid
   0   0   6   0   0   0   0   0   0   0   0   0   0   1   0   3  20   0   0   0   1   0   0   0   0   0   0   0   0   0 |   q = RR Lyrae - Asymmetric
   0   0   0   0   0   0   0   0   0   0   0   0   0   2   0   0   0 105   0   3   0   1   0   0   0   0   0   0   0   0 |   r = RR Lyrae, Double Mode
   0   0   4   0   0   0   0   0   0   0   0   0   0   2   0   0   0   0   3   0   0   0   4   0   0   0   1   0   0   2 |   s = RR Lyrae
   4   0   0   0   0   0   0   0   0   0   0   0   0   8   1   3   0   1   1 268   0   1   1   0   0   0   3   0   0   0 |   t = RR Lyrae, Fundamental Mode
   0   0  11   0   0   0   0   0   0   0   0   0   0   0   0   0   1   0   0   0   3   0   0   0   0   0   0   0   0   0 |   u = RR Lyrae - Near Symmetric
   2   0   0   0   0   0   0   0   0   0   0   0   0   2   0   0   0   9   0   0   0   0   0   0   0   0   0   0   0   0 |   v = RR Lyrae, Closely Spaced Modes
   4   1   4   0   0  11   0   0   1   0   1   0   0   4   2   0   0   2   2   0   0   0  64   2   1   0  12   0   0   0 |   w = Pulsating Variable
   0   0   0   1   0   1   0   0   0   0   0   0   0   0   1   0   0   0   0   0   0   0   3   8   1   0  18   0   0   0 |   x = Beta Cephei
   6   1   0   0   0   1   0   0   0   1   0   0   0   0   0   0   0   0   0   4   0   0   6   0   6   2  14   0   0   0 |   y = Gamma Doradus
   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   1   2   2   0   8   0   0   0 |   z = Lambda Bootis Variable
   0   0  32   0   0   5   0   0   1   0   0   0   0   4   0   2   1   0   0   6   0   0  11   5   4   5  74   0   0   0 |  aa = Delta Scuti
   0   0   1   0   0   0   0   0   0   0   0   0   0   1   0   0   0   0   0   3   0   0   0   0   0   0   0   9   0   0 |  ab = SX Phoenicis
   0   0   1   0   0   0   1   1   0   0   0   0   0  28   0   0   0   0   0   0   0   0   0   0   0   0   0   0   2   1 |  ac = Long Period (W Virginis)
   0   0   3   0   0   0   0   0   0   0   1   0   0   4   0   0   2   0   0   0   0   0   0   0   0   0   0   0   0 103 |  ad = Mira
"""

input_table_str = """
    a    b    c    d    e    f    g    h    i    j    k    l    m    n    o    p    q    r   <-- classified as
   87    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0 |    a = RR Lyrae, Fundamental Mode
    0 1072    0    0    0    0    0    0    0    0    0    2    0    0    0    0    4    0 |    b = W Ursae Majoris
    0    0   10    0    0    0    0    0    1    0    0    0    0    0    0    0    0    0 |    c = Population II Cepheid
    0    0    0   59    0    0    0    0    0    0    0    0    0    0    0    0    0    0 |    d = Ellipsoidal
    0    0    0    0  204    0    0    0    0    0    0    1    0    0    1    0    1    0 |    e = Binary
    0    2    0    0    2  450    0    0    0    0    0    3    0    0    0    0    2    0 |    f = Algol (Beta Persei)
    0    0    0    0    0    0   33    0    0    1    0    0    0    0    0    0    0    0 |    g = Wolf-Rayet
    0    0    0    0    0    0    0  149    0    0    0    0    0    0    0    0    0    0 |    h = Beta Cephei
    0    0    2    0    0    0    0    0  110    0    0    0    0    0    0    0    0    0 |    i = Classical Cepheid
    0    0    0    0    0    0    6    3    0  290    0    0   12    1    0    1    0    0 |    j = Mira
    0    0    1    0    1    0    0    0    0    0  228    0    0    0    1    0    0    0 |    k = Multiple Mode Cepheid
    0    0    0    0    0    7    0    0    0    0    0  318    0    0    0    0    0    0 |    l = Beta Lyrae
    0    0    0    0    0    0    0    0    0    5    0    0   30    1    0    1    0    0 |    m = Semiregular Pulsating Variable
    0    0    0    1    0    0    0    0    0    0    0    0    0   71    0    0    0    1 |    n = Gamma Doradus
    0    0    0    0    0    0    0    0    8    0    2    0    0    0  565    0    0    0 |    o = Symmetrical
    0    0    0    0    0    0    1    0    0    0    0    0    0    0    0   16    0    0 |    p = Be Star
    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   18    0 |    q = Pulsating Variable
    0    1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0  215 |    r = Delta Scuti
"""


if __name__ == '__main__':

    input_table_name = "/tmp/a"
    output_costmatrix_fpath = "/home/pteluser/scratch/cost_matrix.cost"
    if len(sys.argv) >= 3:
        input_table_name = sys.argv[1]
        output_costmatrix_fpath = sys.argv[2]

    ###DISABLED### input_table_str = open(input_table_name).read()
    input_table_str = open(input_table_name).read()

    output_html_fpath = "/tmp/heatmap.html"

    input_line_list = input_table_str.split('\n')
    for i_header_row in range(len(input_line_list)):
        if "classified as" in input_line_list[i_header_row]:
            break # i_header_row is the correct value.

    val_listoflists = []
    total_per_class_list = []
    class_name_list = []

    line = input_line_list[i_header_row]
    short_line = line[:line.rfind('<')]
    col_name_list = short_line.split()

    for line in input_line_list[i_header_row +1:-1]:
        if len(line) < 4:
            continue # does not contain data
        short_line = line[:line.rfind('|')]
        #class_name = line[line.rfind('=')+2:]
        class_name = line[line.rfind('|')+3:]
        class_name_list.append(class_name)
        str_val_list = short_line.split()
        val_list = []
        for str_val in str_val_list:
            val_list.append(int(str_val))
        total_per_class_list.append(sum(val_list))
        val_listoflists.append(val_list)

    
    out_str = """
    <HTML><head></head>
    <body>
    <table style="color: white;" cellpadding="2">
    """
    #<table color="#%ffffff">

    out_str += "<tr>"            
    for col_name in col_name_list:
        out_str += '<td bgcolor="#2a2a2a">%s</td>' % (col_name)
    out_str += '</tr>\n'

    for i_class in range(len(val_listoflists)):
        val_list = val_listoflists[i_class]
        out_str += "<tr>"            
        for val in val_list:
            try:
                percent = val / float(total_per_class_list[i_class])
            except:
                percent = 0.0 # div by zero catch
            if percent < 0.0099999:
                percent_str = "&nbsp&nbsp&nbsp&nbsp&nbsp"
            else:
                percent_str_a = "%2.2f" % (percent)
                percent_str = percent_str_a[1:]
            if ((percent > 0.0099999) and (percent < 0.15)):
                percent = 0.15 # give small percents some minimum color
            full_hex_str = "%2.2x" % (int((percent * 255)))
            hex_str = full_hex_str[full_hex_str.rfind('x')+1:]
            out_str += '<td bgcolor="#%s0000">%s</td>' % (hex_str, percent_str)
        out_str += '<td bgcolor="#2a2a2a">%s</td></tr>\n' % (class_name_list[i_class])
    out_str += "</table></body></html>"

    os.system("rm " + output_html_fpath)
    fp = open(output_html_fpath, 'w')
    fp.write(out_str)
    fp.close()

    for i in range(len(total_per_class_list)):
        print(total_per_class_list[i], '\t', class_name_list[i])

    # TODO: make a cost matrix which is all normalized.
    n_avg = sum(total_per_class_list) / float(len(total_per_class_list))

    os.system("rm " + output_costmatrix_fpath)
    fp = open(output_costmatrix_fpath, 'w')

    #header_str = "\% Rows \tColumns\n%d \t%d\n\% Matrix elements\n" % (len(total_per_class_list), len(total_per_class_list))
    header_str = "%% Rows \tColumns\n%d \t%d\n%%Matrix elements\n" % (len(total_per_class_list), len(total_per_class_list))
    fp.write(header_str)
    for i in range(len(total_per_class_list)):
        percent = n_avg / total_per_class_list[i]
        line_str = ""
        for j in range(len(total_per_class_list)):
            if i == j:
                line_str += "0.0\t"
            else:
                line_str += "%0.3f\t" % (percent)
        fp.write(line_str + '\n')
    fp.close()
