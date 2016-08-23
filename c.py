import fileinput
import time
from timeout import timeout



time.sleep(5)
@timeout(4)


with open('WCNSS_qcom_cfg.ini', 'r') as file:
    # read a list of lines into data
    data = file.readlines()

dataout = [None] * len(data)
i = 0;
for line in data:
	if 'gEnableImps=' in line:
		line = 'gEnableImps=0'
	if 'gEnableBmps=' in line:
		line = 'gEnableBmps=0'
	if 'gDot11Mode=' in line:
		line = 'gDot11Mode=3'
#	if  line == '\n':
#		continue
	dataout[i] = line
	i = i + 1
print data
print dataout

with open('WCNSS_qcom_cfg.ini', "w") as f:
	f.write('\n'.join(dataout))
