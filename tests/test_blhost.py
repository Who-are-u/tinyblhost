# -*- encoding: utf-8 -*-
#@File    :   unittest.py
#@Time    :   2025/01/08 11:27:38
#@Author  :   Jianping Zhang 
#@Version :   1.0
#@Contact :   Jianping.zhang_2@nxp.com
#@Brief   :   

from tinyblhost import blhost as blhost


bl = blhost.Blhost()
status, responses = bl.get_property(1)
print(status)
print(responses)

status, responses = bl.get_property(2)
print(status)
print(responses)

status, responses = bl.get_property(3)
print(status)
print(responses)

status, responses = bl.get_property(7)
print(status)
print(responses)

