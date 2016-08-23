import re

with open('WCNSS_qcom_cfg.ini', 'r') as fh:
  file_data = fh.read()

# Replace the target string
file_data = re.sub(
    pattern=r'gEnableImps=\d*',
    repl='gEnableImps=0',
    string=file_data)

# Write the file out again
with open('WCNSS_qcom_cfg.ini', 'w') as file:
  file.write(file_data)
print'WCNSS_qcom_cfg.ini modified: \ngEnableImps=0'
  
# Replace the target string
file_data = re.sub(
    pattern=r'gEnableBmps=\d*',
    repl='gEnableBmps=0',
    string=file_data)

# Write the file out again
with open('D:/Script/WCNSS_qcom_cfg', 'w') as file:
  file.write(file_data)
print'WCNSS_qcom_cfg modified: \ngEnableBmps=0'
  
# Replace the target string
file_data = re.sub(
    pattern=r'gDot11Mode=\d*',
    repl='gDot11Mode=3',
    string=file_data)

# Write the file out again
with open('D:/Script/WCNSS_qcom_cfg.ini', 'w') as file:
  file.write(file_data)
print'WCNSS_qcom_cfg modified: \ngDot11Mode=3'
