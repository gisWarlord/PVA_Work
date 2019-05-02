'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    RoutingTable2PointsAddTime.py
'   Purpose:    Runs RoutingTable2Points.py then calculates the extra
'               time from the Extra Time Table.
'
'---------------------------------------------------------------------
'     Usage:    RoutingTable2PointsAddTime <Route Table>
'                  <Output Directory> <Extra Time Table>
'                  <ParcelId from Extra Time Table>
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  03/2019
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env

# Import the script utilities
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

def ExtraTimeCodeBlock():
    '''
    Return the code block used to add extra time
    '''
    codeBlock = '''
def ExtraTime(time):
    if time > 100:
        return time + 60
    else:
        return time + 30
'''
    return codeBlock

def main(RouteTable, outDir, extraTable, extraParcelId):
    # Local variables
    msgTxt = ""
    startTime = time.time()
    connection = r"J:\pva\PVA_Routing\pvastaff_connection.sde"
    Parcel_Point = os.path.join(connection, "PVA.Land", "PVA.Parcel_Point")
    ParcelPnts = "Parcel_Pnts"

    try:
        # sys.path.append(r"J:\pva\PVA_Routing")
        sys.path.append(r"V:\Stan")
        import RoutingTable2Points
        RoutingTable2Points.main(RouteTable, outDir)

        # Convert the new feature class to a shapefile
        outShp = os.path.join(outDir, os.path.basename(RouteTable)) + ".shp"
        if arcpy.Exists(outShp):
            ScriptUtils.AddMsgAndPrint("\tAdding extra time...")

            # Connect to the new route points
            routingPointsLayer = "RouteShpOutput"
            # Process: Make Feature Layer from the new route points
            arcpy.MakeFeatureLayer_management(outShp, routingPointsLayer)

            # Connect to the extra time table
            extraTimeView = "ExtraTimeTable"
            # Process: Make Table View from the extra time table
            arcpy.MakeTableView_management(extraTable, extraTimeView)

            # Process: Add Join
            arcpy.AddJoin_management(routingPointsLayer, "PARCELID", extraTimeView, extraParcelId, "KEEP_COMMON")

            # Process: Calculate Field
            calcField = "{0}.TIME".format(os.path.basename(RouteTable))
            expression = "ExtraTime(!{0}!)".format(calcField)
            codeBlk = ExtraTimeCodeBlock()
            # ScriptUtils.AddMsgAndPrint("\t\t     calcField: {0}\n\t\tcalcExpression: {1}\n{2}...".format(calcField, expression, codeBlk))
            arcpy.CalculateField_management(routingPointsLayer, calcField, expression, "PYTHON_9.3", codeBlk)

            # Process: Remove Join
            arcpy.RemoveJoin_management(routingPointsLayer, "")
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        gpmsg = "ARCPY ERRORS:\n{0}\n".format(arcpy.GetMessages(2))
        pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n\t{1}: {2}\n".format(tbinfo, str(sys.exc_type), str(sys.exc_value))
        tmRun = time.strftime("%X", time.localtime())
        endTime = time.time()
        prodInfo = "\tScript errored after running for {0} seconds.".format(str(round((endTime - startTime))))
        msgTxt += "\n\n\tScript error at: {0}\n{1}\n\n{2}{3}".format(tmRun, prodInfo, gpmsg, pymsg)
        ScriptUtils.AddMsgAndPrint(msgTxt, 2)

if __name__ == "__main__":
    RouteTable = sys.argv[1]
    if RouteTable == "#" or not RouteTable:
        ScriptUtils.AddMsgAndPrint("Please enter the route table", 0)
        sys.exit()                                      # value needed


    outDir = sys.argv[2]
    if outDir == "#" or not outDir:
        ScriptUtils.AddMsgAndPrint("Please enter the output directory", 0)
        sys.exit()                                      # value needed

    extraTable = sys.argv[3]
    if extraTable == '#' or not extraTable:
        ScriptUtils.AddMsgAndPrint("Please enter the Extra Time Table", 0)
        sys.exit()                                      # value needed

    extraParcelId = sys.argv[4]
    if extraParcelId == '#' or not extraParcelId:
        ScriptUtils.AddMsgAndPrint("Please select the parcel ID from the Extra Time Table", 0)
        sys.exit()                                      # value needed

    main(RouteTable, outDir, extraTable, extraParcelId)
