'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    CreateRouteLayer.py
'   Purpose:    Runs the script needed to create the Order points with
'               or without the extra time. Then runs the script that
'               will create a Vehicle Routing Problem Layer. This layer
'               can then be added to an ArcMap document and used to
'               print the maps & directions.
'
'---------------------------------------------------------------------
'     Usage:    CreateRouteLayer <Route Table>
'                  <Output Directory> (Extra Time Table)
'                  (ParcelId from Extra Time Table)
'                  <Depot Points> <Routes>
'---------------------------------------------------------------------
'     Notes:    Run this script from an ArcMap document.
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  03/2019
'               Stan Shelton  -  04/2019
'                   This script now adds the new Routes to the current
'                   MXD and changes the title of the layout.
'               Stan Shelton  -  05/2019
'                   Added code to handle creating commercial points
'                   and adding them to the current MXD.
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env
from datetime import datetime

# Import the script utilities
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

RouteTable = arcpy.GetParameterAsText(0)
if RouteTable == "#" or not RouteTable:
    ScriptUtils.AddMsgAndPrint("Please enter the route table", 0)
    sys.exit()                                          # value needed

outDir = arcpy.GetParameterAsText(1)
if outDir == "#" or not outDir:
    ScriptUtils.AddMsgAndPrint("Please enter the output directory", 0)
    sys.exit()                                          # value needed

isCommercial = arcpy.GetParameterAsText(2)              # value needed
if str(isCommercial) == "false":
    extraTable = arcpy.GetParameterAsText(3)            # optional input

    extraParcelId = arcpy.GetParameterAsText(4)         # optional input

    depots = arcpy.GetParameterAsText(5)
    if depots == "#" or not depots:
        ScriptUtils.AddMsgAndPrint("Please enter the depots", 0)
        sys.exit()                                      # value needed

    routes = arcpy.GetParameterAsText(6)
    if routes == '#' or not routes:
        ScriptUtils.AddMsgAndPrint("Please enter the routes", 0)
        sys.exit()                                      # value needed

# Local variables
msgTxt = ""
startTime = time.time()
routeBaseName = os.path.basename(RouteTable)
outShp = os.path.join(outDir, routeBaseName) + ".shp"

try:
    env.overwriteOutput = True
    sys.path.append(r"J:\pva\PVA_Routing")
    # sys.path.append(r"V:\Stan")

    # Convert the new feature class to a shapefile
    if str(isCommercial) == "true":
        import RoutingTable2Points
        RoutingTable2Points.main(RouteTable, outDir)

        # Add the new points to the current MXD
        if arcpy.Exists(outShp):
            ScriptUtils.AddMsgAndPrint("\tAdding {0} to the current MXD...".format(outShp), 0)
            mxd = arcpy.mapping.MapDocument("CURRENT")
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            addLayer = arcpy.mapping.Layer(outShp)
            arcpy.mapping.AddLayer(df, addLayer, "TOP")

            # Change the layout's title
            lstRouteInput = routeBaseName.split("_")
            routeDate = datetime.strptime(lstRouteInput[1], '%m%d%Y')
            date_string = routeDate.strftime('%m/%d/%Y')
            for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
                if elm.name == "pvaRouteTitle":
                    elm.text = "{0} - Field Checks - {1}".format(lstRouteInput[0], date_string)
    else:
        if extraTable == '#' or not extraTable:
            import RoutingTable2Points
            RoutingTable2Points.main(RouteTable, outDir)
        else:
            if extraParcelId == '#' or not extraParcelId:
                sys.exit("Please select the 'Parcel ID Field' from the Extra Time Table")
            import RoutingTable2PointsAddTime
            RoutingTable2PointsAddTime.main(RouteTable, outDir, extraTable, extraParcelId)

        if arcpy.Exists(outShp):
            import MakeVehicleRoutingProblemLayer_Workflow
            MakeVehicleRoutingProblemLayer_Workflow.main(outShp, depots, routes)

            # Add the new Vehicle Routing Problem to the current MXD
            routesLayer = arcpy.mapping.Layer(os.path.join(outDir, routeBaseName) + "_Routes.lyr")
            mxd = arcpy.mapping.MapDocument("CURRENT")
            ScriptUtils.AddMsgAndPrint("\tAdding {0} to the current MXD...".format(routesLayer), 0)
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            arcpy.mapping.AddLayer(df, routesLayer, "TOP")

            # Change the layout's title
            lstRouteInput = routeBaseName.split("_")
            routeDate = datetime.strptime(lstRouteInput[1], '%m%d%Y')
            date_string = routeDate.strftime('%m/%d/%Y')
            for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
                if elm.name == "pvaRouteTitle":
                    elm.text = "{0} (through {1}): Route ???".format(lstRouteInput[0], date_string)
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
