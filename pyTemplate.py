# -*- coding: utf-8 -*-
'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    
'   Purpose:    
'
'---------------------------------------------------------------------
'     Usage:    
'---------------------------------------------------------------------
'   Returns:    
'---------------------------------------------------------------------
'     Notes:    
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  mm/yyyy
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env

# Import the script utilities
sPath = r"J:\pva\Toolboxes"
if not os.path.isdir(sPath):
    sPath = r"X:\GIS_IT\GIS_DEPT\Tools\Scripts"
sys.path.append(sPath)
import ScriptUtils_pva as ScriptUtils

# Local variables
msgTxt = ""
startTime = time.time()

try:
    # Add main code 

except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n\t{1}: {2}\n".format(tbinfo, str(sys.exc_type), str(sys.exc_value))
    gpmsg = "ARCPY ERRORS:\n{0}\n".format(arcpy.GetMessages(2))
    tmRun = time.strftime("%X", time.localtime())
    endTime = time.time()
    prodInfo = "\tScript errored after running for {0} seconds.".format(str(round((endTime - startTime))))
    msgTxt += "\n\n\tScript error at: {0}\n{1}\n\n{2}{3}".format(tmRun, prodInfo, gpmsg, pymsg)
    ScriptUtils.AddMsgAndPrint(msgTxt, 2)
# finally:
    # endTime = time.time()
    # ScriptUtils.AddMsgAndPrint("\tScript completed (Run time: {0} minutes)".format(str(round((endTime - startTime) / 60))))
