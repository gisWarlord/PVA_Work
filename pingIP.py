'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    pingIP.py
'   Purpose:    Python script to ping IP address on the network
'
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  02/2019
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
    with open(os.devnull, "wb") as limbo:
        ip = "10.200.203.155"
        sTime = time.strftime("%X", time.localtime())
        result = subprocess.Popen(["ping", "-n", "1", "-w", "200", ip], stdout = limbo, stderr=limbo).wait()
        msgTxt += "\n\tTime: {0}\tIP: {1} --> ".format(sTime, ip)
        if result:
            msgTxt += "inactive\n"
        else:
            msgTxt += "active\n"
    print("---\tPrint Command\t---" + msgTxt)
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
