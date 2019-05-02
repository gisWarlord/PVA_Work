'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    RoutingTable2Points.py
'   Purpose:    Add/calculate the TIME & FULL_ADD fields to the address
'               routing table and returns a point shapefile.
'
'---------------------------------------------------------------------
'     Usage:    RoutingTable2Points <Route Table> <Output Directory>
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  09/2018
'               Stan Shelton  -  10/2018
'                 Added a new calculation to the TIME field code block:
'                 (Permit_Type == "NEW CONSTRUCTION" and
'                  Flag_Type <> "0")
'               Stan Shelton  -  11/2018
'                 Added code to set the default TIME to 30. Also,
'                 calculating the Order__ field if it has 0's.
'               Stan Shelton  -  12/2018
'                 Added code to join the routing table to
'                 PVA.Parcel_Point to create a feature class with
'                 the needed data.
'               Stan Shelton  -  01/2019
'                 Rearranged the query in the TIME field code block to
'                 make sure Flag_Type == "PERMIT REVISIT" is set first.
'               Stan Shelton  -  03/2019
'                 Rearranged the code by placing the bulk of the
'                 processing in "main" def so this script could be
'                 called from RoutingTable2PointsAddTime.py. Also,
'                 added "ONE YEAR ONLY - FV NEEDED" to the TIME the
'                 code block.
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env

# Import the script utilities
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils


def TimeCodeBlock():
    '''
    Return the code block used to calculate the TIME field
    '''
    codeBlock = '''
def ConstVisit(newConst, fldVisit, flagType, permitType):
    if flagType in ["PERMIT REVISIT", "GENERAL MAINTENANCE", "GENERAL MAINTENANCE REVISIT"]:
        return 30
    elif newConst == "YES" and fldVisit == "0":
        return 60
    elif permitType in ["B-FOUNDATION ONLY", "FOUNDATION ONLY"]:
        return 60
    elif newConst == "YES" and fldVisit <> "0":
        return 30
    elif permitType in ["ADDITION", "B-ADDITION", "B-RENOVATION", "GARAGE/CARPORT"]:
        return 30
    elif permitType == "B-NEW CONSTRUCTION" and newConst == "NO":
        return 30
    elif permitType == "NEW CONSTRUCTION" and fldVisit <> "0":
        return 30
    elif flagType in ["MAINTENANCE FIELD VISIT", "ONE YEAR ONLY - FV NEEDED"]:
        return 15
    elif flagType == "MAINTENANCE PHOTO FIELD VISIT":
        return 10
    elif permitType in ["W-WRECK TYPE A", "W-WRECK TYPE B", "W-WRECK TYPE C"]:
        return 10
    else:
        return 30
'''
    return codeBlock

def OrderCodeBlock():
    '''
    Return the code block used to calculate the Order__ field
    '''
    codeBlock = '''
rec = 0
def autoIncrement():
    global rec
    pStart = 101
    pInterval = 1
    if (rec == 0):
        rec = pStart
    else:
        rec = rec + pInterval
    return str(rec)
'''
    return codeBlock

def main(RouteTable, outDir):
    # Local variables
    startTime = time.time()
    connection = r"J:\pva\PVA_Routing\pvastaff_connection.sde"
    Parcel_Point = os.path.join(connection, "PVA.Land", "PVA.Parcel_Point")
    ParcelPnts = "Parcel_Pnts"

    try:
        workspace = os.path.join(outDir, "Field_Visits.gdb")
        if not arcpy.Exists(workspace):
            ScriptUtils.AddMsgAndPrint("\tCreating {0}...".format(workspace), 0)
            arcpy.CreateFileGDB_management(outDir, "Field_Visits")

        arcpy.env.workspace = workspace
        arcpy.env.overwriteOutput = True

        fields = arcpy.ListFields(RouteTable)
        addTime = True
        addFAdd = True
        for fld in fields:
            if fld.name == "TIME":
                addTime = False
            if fld.name == "FULL_ADD":
                addFAdd = False

        # Process: Add TIME Field
        if addTime:
            ScriptUtils.AddMsgAndPrint("\tAdding TIME Field...", 0)
            arcpy.AddField_management(RouteTable, "TIME", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

        # Process: Add FULL_ADD Field
        if addFAdd:
            ScriptUtils.AddMsgAndPrint("\tAdding FULL_ADD Field...", 0)
            arcpy.AddField_management(RouteTable, "FULL_ADD", "TEXT", "", "", "50", "", "NULLABLE", "NON_REQUIRED", "")

        # Process: Calculate TIME Field
        ScriptUtils.AddMsgAndPrint("\tCalculating the TIME Field...", 0)
        expression = "ConstVisit( !New_Const!, !F__Field_Visits!, !Flag_Type!, !Permit_Type! )"
        codeBlk = TimeCodeBlock()

        # ScriptUtils.AddMsgAndPrint("\t\tExpression:\n{0}\n...\n\t\tCode Block:\n{1}\n...".format(expression, codeBlk), 0)
        arcpy.CalculateField_management(RouteTable, "TIME", expression, "PYTHON", codeBlk)

        # Process: Calculate FULL_ADD Field
        ScriptUtils.AddMsgAndPrint("\tCalculating the FULL_ADD Field...", 0)
        expression = "!Parcel_No! + \" / \" + !Prop_Addr!"
        arcpy.CalculateField_management(RouteTable, "FULL_ADD", expression, "PYTHON", "")

        # Process: Calculate Order Field
        cBlock = OrderCodeBlock()

        # ScriptUtils.AddMsgAndPrint("\t---\tCode Block:\n{0}\n...".format(cBlock), 0)
        whereClause = "Order__ = '0'"
        arcpy.MakeTableView_management(RouteTable, "RouteTbl", whereClause)
        result = arcpy.GetCount_management("RouteTbl")
        if result.getOutput(0) > "0":
            ScriptUtils.AddMsgAndPrint("\tCalculating the Order__ Field...", 0)
            calcExp = "autoIncrement()"
            arcpy.CalculateField_management(RouteTable, "Order__", calcExp, "PYTHON_9.3", cBlock)

        # Joining to Parcel points to create a featureclass
        ScriptUtils.AddMsgAndPrint("\tJoining {0} to Parcel points...".format(os.path.basename(RouteTable)))

        arcpy.MakeFeatureLayer_management(Parcel_Point, ParcelPnts, "", "", "OBJECTID OBJECTID HIDDEN NONE;PARCELID PARCELID VISIBLE NONE;LRSN LRSN VISIBLE NONE;BLOCK BLOCK HIDDEN NONE;LOT LOT HIDDEN NONE;SUBLOT SUBLOT HIDDEN NONE;BLOCKLOT BLOCKLOT HIDDEN NONE;PBA_ID PBA_ID HIDDEN NONE;POINTTYPE POINTTYPE HIDDEN NONE;POINTCLASS POINTCLASS HIDDEN NONE;SHAPE SHAPE VISIBLE NONE")
        arcpy.AddJoin_management(ParcelPnts, "PARCELID", RouteTable, "Parcel_No", "KEEP_COMMON")
        outName = os.path.join(workspace, os.path.basename(RouteTable))
        if arcpy.Exists(outName):
            arcpy.Delete_management(outName, "")
        ScriptUtils.AddMsgAndPrint("\tExporting the joined data...")
        arcpy.CopyFeatures_management(ParcelPnts, outName)

        # Remove the unneeded fields and change the name of the fields we need
        arcpy.DeleteField_management(outName,"PVA_Parcel_Point_BLOCK;PVA_Parcel_Point_LOT;PVA_Parcel_Point_SUBLOT;PVA_Parcel_Point_BLOCKLOT;PVA_Parcel_Point_PBA_ID;PVA_Parcel_Point_POINTTYPE;PVA_Parcel_Point_POINTCLASS;{0}_OBJECTID".format(os.path.basename(RouteTable)))
        arcpy.AlterField_management(outName,"PVA_Parcel_Point_PARCELID","PARCELID","#")
        arcpy.AlterField_management(outName,"PVA_Parcel_Point_LRSN","LRSN","#")
        fieldList = {"Parcel_No","Flag_Id","Order__","Nbh","Prop_Class","Prop_Addr","Flag_Type","Status","Assigned_to","Activation_Date","Year","Permit_Category","Permit_Type","New_Const","F__Field_Visits","F__Complete","TIME","FULL_ADD"}
        for field in fieldList:
            fName = "{0}_{1}".format(os.path.basename(RouteTable), field)
            arcpy.AlterField_management(outName, fName, field, "")

        # Convert the new feature class to a shapefile
        outShp = os.path.join(outDir, os.path.basename(RouteTable)) + ".shp"
        ScriptUtils.AddMsgAndPrint("\tCreating the shapefile {0}...".format(outShp))
        if arcpy.Exists(outShp):
            arcpy.Delete_management(outShp, "")
        arcpy.FeatureClassToShapefile_conversion(outName, outDir)
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n\t{1}: {2}\n".format(tbinfo, str(sys.exc_type), str(sys.exc_value))
        gpmsg = "ARCPY ERRORS:\n{0}\n".format(arcpy.GetMessages(2))
        tmRun = time.strftime("%X", time.localtime())
        endTime = time.time()
        prodInfo = "\tScript errored after running for {0} seconds.".format(str(round((endTime - startTime))))
        msgTxt = "\n\n\tScript error at: {0}\n{1}\n\n{2}{3}".format(tmRun, prodInfo, gpmsg, pymsg)
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

    main(RouteTable, outDir)
