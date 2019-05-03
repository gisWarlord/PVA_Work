'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    SelectRoute.py
'   Purpose:    Sets the Query Definitions of the Orders & Routes
'               layers and zooms to the Route so the map(s) can be
'               exported.
'---------------------------------------------------------------------
'     Usage:    SelectRoute <Route Number>
'---------------------------------------------------------------------
'     Notes:    This script is designed save time when printing the
'               routes. Run this script from the Map document that
'               was used to create the routes.
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  04/2019
'               Stan Shelton  -  05/2019
'                   Changed the code that zooms to the selected route
'                   to zoom out by 2%.
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
routeValue = arcpy.GetParameterAsText(0)
if routeValue == "#" or not routeValue:
    ScriptUtils.AddMsgAndPrint("Please enter the route number", 0)
    sys.exit()                                      # value needed

msgTxt = ""
startTime = time.time()

try:
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd)[0]

    # Set the definition Queries of the Orders & Routes layers and zoom the the selected route
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.name == "Orders":
            lyr.definitionQuery = "\"RouteName\" = '{0}'".format(routeValue)
        elif lyr.name == "Routes":
            lyr.definitionQuery = "\"Name\" = '{0}'".format(routeValue)
            df.extent = lyr.getExtent()
            df.scale = df.scale * 1.02      # zoom out by 2%

    # Change the title of the layout to include the route number
    for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
        if elm.name == "pvaRouteTitle":
            txtTitle = elm.text
            lstTitle = txtTitle.split(" ")
            elm.text = txtTitle.replace(lstTitle[-1], routeValue)

    msg = "---\tThe Orders & Routes layer Query Definitions have been set to display \"Route {0}\"\t---".format(routeValue)
    ScriptUtils.AddMsgAndPrint(msg)
    arcpy.RefreshTOC()
    arcpy.RefreshActiveView()
    del mxd
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
