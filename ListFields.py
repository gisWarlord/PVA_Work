'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    ListFields.py
'   Purpose:    This is a helper script that lists the field 
'               properties of the table in the variable dataPath
'
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  06/2019
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, time, traceback, subprocess

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
    # For each field in the feature class, print
    #  the field name, type, and length.
    # dataPath = r"C:\Stan\Data\Routing Geodatabase.gdb\Example_RouteTable"
    dataPath = r"C:\Stan\Data\PVA_Data.gdb\Chris_06012019"

    if arcpy.Exists(dataPath):
        msgTxt += "\n\t-- Reporting Field Info for \"{0}\" --\n".format(dataPath)
        fields = arcpy.ListFields(dataPath)
        for field in fields:
            msgTxt += "\tField: {0}\t\t\tType: {1}\t\tLength: {2}\n".format(field.name, field.type, field.length)
    else:
        msgTxt += "\n-- Could not find \"{0}\" --\n".format(dataPath)

    ScriptUtils.AddMsgAndPrint(msgTxt, 0)
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
