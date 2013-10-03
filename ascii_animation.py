'''
Takes an xml file
'''
import moving_ascii
import time
import os

ims= dict()
with open("moving_ascii.xml") as f:
        xml_file = f.read()
success, g_map  = moving_ascii.obj_wrapper(xml_file)
if not success:
    print "NO SUCCESS!"
    exit()





if