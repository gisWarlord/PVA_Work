'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    UpdatePersonalPropertyPoints.py
'   Purpose:    Runs the scripts that update/package the Personal
'               Property Points for updating the AGOL data.
'
'---------------------------------------------------------------------
'     Notes:    Messages created by this script are recorded in
'               X:\GIS_IT\GIS_DEPT\Tools\Scripts\Update_Layers\AGOL\
'               UpdatePPP_log_<day of the week>
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  02/2019
'---------------------------------------------------------------------
'''
# Import modules
import sys, string, os, time, os.path

# Import the script utilities
sys.path.append(r"X:\GIS_IT\GIS_DEPT\Tools\Scripts")
import ScriptUtils_pva as ScriptUtils

try:
    step = "startup"
    dirScripts = r"X:\GIS_IT\GIS_DEPT\Tools\Scripts\UpdateLayers\AGOL"
    pyExe = "\"" + os.path.join(r"C:\Python27\ArcGIS10.3", "python.exe") + "\" "
    
    dow = time.strftime("%a")
    updateLog = "UpdatePPP_log_{0}.txt".format(dow)
    txtResults = os.path.join(dirScripts, updateLog)
    results = open(txtResults,'w+')
    results.write("Begin " + time.asctime() + "\r\n")
    
    step = "Run CreatePersonalPropPnts.py"
    runScript = os.path.join(dirScripts, "CreatePersonalPropPnts.py")
    cmdString = pyExe + runScript
    results.write(cmdString + "\r\n")
    os.system(cmdString)
    
    step = "Run PersonalPropPnts2Shp.py"
    runScript = os.path.join(dirScripts, "PersonalPropPnts2Shp.py {0}".format(dirScripts))
    cmdString = pyExe + runScript
    results.write(cmdString + "\r\n")
    os.system(cmdString)
except:
    results.write("Failed at " + step + "\r\n")
    print("Failed at " + step)
    # send email
    FROM = "pvagis@jeffersonpva.ky.gov"
    TO = ["gis@jeffersonpva.ky.gov"]
    SUBJECT = "UpdatePersonalPropertyPoints.py Error"
    TEXT = """
    The overnight script UpdatePersonalPropertyPoints.py failed. Read the following file for more
    details, X:\GIS_IT\GIS_DEPT\Tools\Scripts\Update_Layers\AGOL\UpdatePPP_log_<day of the week>

    """
    ScriptUtils.AddMsgAndPrint(TEXT, 2)
    ScriptUtils.SendEmail(FROM, TO, SUBJECT, TEXT)
finally:
    results.write("Done  " + time.asctime() + "\r\n")
    results.close()


