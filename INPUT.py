import fileinput
import sys

#from_base = "gEnableImps ="
#to_base = "gEnableImps = 0"
#files = sys.argv['D:/Script/WCNSS_qcom_cfg.ini']
files = 'D:/Script/WCNSS_qcom_cfg.ini'
#for line in fileinput.input(files, inplace=True):
#    line = line.replace(from_base, to_base)
#    print line
line = open(files)
if line.startswith(files,"gEnableImps ="):
    print "gEnableImps = 0"
else:
    print line
