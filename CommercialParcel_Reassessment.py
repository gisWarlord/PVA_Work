'''-------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    CommercialParcel_Reassessment.py
'   Purpose:    Intersecs the Zoning & FIRM data with the selected
'               commercial property areas for reassessments.
'
'---------------------------------------------------------------------
'   Returns:    H:\ConcatOutput_Zoning.dbf
'               H:\ConcatOutput_Flood.dbf
'---------------------------------------------------------------------
'     Notes:    The input query expression needs to be reset to the
'               needed areas
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  08/2018
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env

# Import the script that sends emails
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

# Script arguments
Expression = arcpy.GetParameterAsText(0)
if Expression == '#' or not Expression:
    Expression = "CN_NUM >= 10 AND CN_NUM <= 18" # provide a default value if unspecified

# Local variables:
msgTxt = ""
startTime = time.time()
Commercial_Neighborhoods = r"J:\pva\Commercial\Commercial Neighborhoods.gdb\Commercial_Neighborhoods\Commercial_Neighborhoods"
connection = r"J:\pva\Toolboxes\CommercialReassessment\pvastaff_connection.sde"
workspace = r"H:\PVA_Data.gdb"
PVA_Parcel = os.path.join(connection, "PVA.Land", "PVA.Parcel")
pva_remf_master = os.path.join(connection, "pva.remf_master")
JEFLIB_Zoning = os.path.join(connection, "JEFLIB.Planning", "JEFLIB.Zoning")
FEMA_Flood = os.path.join(connection, "DFIRM.X_S_FLD_HAZ_AR_BFE")
Commercial_Neighborhoods_Lay = Expression
Parcel_SpatialJoin = os.path.join(workspace, "Parcel_SpatialJoin")
Parcel_SpatialJoin_Intersect = Parcel_SpatialJoin + "Intersect"
Parcel_Flood_SpatialJoin_Intersect = Parcel_SpatialJoin + "FloodIntersect"
Parcel_Frequency = os.path.join(workspace, "Parcel_Frequency")
Parcel_Flood_Frequency = os.path.join(workspace, "Parcel_Flood_Frequency")
ConcatOutput_dbf = r"H:\ConcatOutput.dbf"
ConcatOutput_Zoning = r"H:\ConcatOutput_Zoning.dbf"
ConcatOutput_Flood = r"H:\ConcatOutput_Flood.dbf"
Parcel_Layer = "Parcel_Layer"
remf_master_View = "remf_master_View"
Zoning_Layer = "Zoning_Layer"
Flood_Layer = "Flood_Layer"

def cleanup():
    '''
    Removes the temp files created by this proccess
    '''
    try:
        if arcpy.Exists(ConcatOutput_dbf):
            arcpy.Delete_management(ConcatOutput_dbf, "")
        if arcpy.Exists(Parcel_Frequency):
            arcpy.Delete_management(Parcel_Frequency, "")
        if arcpy.Exists(Parcel_SpatialJoin):
            arcpy.Delete_management(Parcel_SpatialJoin, "")
        if arcpy.Exists(Parcel_SpatialJoin_Intersect):
            arcpy.Delete_management(Parcel_SpatialJoin_Intersect, "")
        if arcpy.Exists(Parcel_Flood_SpatialJoin_Intersect):
            arcpy.Delete_management(Parcel_Flood_SpatialJoin_Intersect, "")
        if arcpy.Exists(Parcel_Flood_Frequency):
            arcpy.Delete_management(Parcel_Flood_Frequency, "")
    except:
        # Return any Python specific errors
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n    {1}: {2}\n".format(tbinfo, str(sys.exc_type), str(sys.exc_value))
        tmRun = time.strftime("%X", time.localtime())
        endTime = time.time()
        prodInfo = "\tScript errored after running for {0} seconds.".format(str(round((endTime - startTime))))
        msg = "\n\n\tScript error at: {0}\n{1}\n\n{2}".format(tmRun, prodInfo, pymsg)
        ScriptUtils.AddMsgAndPrint(msg, 2)

def CalculateLastTwoFields(inTable, freqTable, newView, expression):
    '''
    Calculates the TTL_ZONING field. Then calls the script that concatenates the TTL_ZONING field based 
    on the PARCELID field. Calculates MULTZONE field based on the frequency of the PARCELID field.
    '''
    try:
        ScriptUtils.AddMsgAndPrint("\tProcessing the TTL_ZONING field...", 0)    
        # Process: Add TTL_ZONING Field
        arcpy.AddField_management(inTable, "TTL_ZONING", "TEXT", "", "", "100", "", "NULLABLE", "NON_REQUIRED", "")

        # Process: Calculate TTL_ZONING Field
        codeblk = "#"
        if inTable.find("Flood") != -1:
            codeblk = '''def GetFZone(plotcode):
            if (plotcode == 4):
                return "A"
            if (plotcode == 9):
                return "AE"
            if (plotcode == 23):
                return "AE"
            if (plotcode < 4):
                return "X"'''
        arcpy.CalculateField_management(inTable, "TTL_ZONING", expression, "PYTHON", codeblk)
        
        # Process: Run Concatenate
        ScriptUtils.AddMsgAndPrint("\tConcatenating data...", 0)    
        arcpy.AddToolbox(r"J:\pva\Toolboxes\Concatenate\Concatenate.tbx")
        arcpy.Concatenate_pvaConcatenate(inTable, "PVA_Parcel_PARCELID", "TTL_ZONING")
        
        # Process: Make Table View
        arcpy.MakeTableView_management(ConcatOutput_dbf, newView)

        # Process: Make Table View
        Frequency_View = "Frequency_" + newView
        arcpy.MakeTableView_management(freqTable, Frequency_View)

        # Process: Add Field
        ScriptUtils.AddMsgAndPrint("\tProcessing the MULTZONE field...", 0)    
        arcpy.AddField_management(newView, "MULTZONE", "TEXT", "", "", "5", "", "NULLABLE", "NON_REQUIRED", "")

        # Process: Add Join
        arcpy.AddJoin_management(newView, "UniqueID", Frequency_View, "PVA_Parcel_PARCELID", "KEEP_ALL")

        # Process: Calculate Field
        fieldName = ""
        fieldObjList = arcpy.ListFields(newView)
        for field in fieldObjList:
            if "MULTZONE" in field.name:
                fieldName = field.name
        calcExp = "SetMultiZone( !{0}.FREQUENCY! )".format(os.path.basename(freqTable))
        codeblk = '''def SetMultiZone(frequency):
            value = ""
            if frequency == 1:
                value = "NO"
            if frequency > 1:
                value = "YES"
            return value'''
        # ScriptUtils.AddMsgAndPrint("\t\t---fieldName: {0}\n\t\t---  calcExp: {1}".format(fieldName, calcExp), 0)
        arcpy.CalculateField_management(newView, fieldName, calcExp, "PYTHON", codeblk)
        
        del newView, Frequency_View
    except:
        # Return any Python specific errors
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n    {1}: {2}\n".format(tbinfo, str(sys.exc_type), str(sys.exc_value))
        tmRun = time.strftime("%X", time.localtime())
        endTime = time.time()
        prodInfo = "\tScript errored after running for {0} seconds.".format(str(round((endTime - startTime))))
        msg = "\n\n\tScript error at: {0}\n{1}\n\n{2}".format(tmRun, prodInfo, pymsg)
        ScriptUtils.AddMsgAndPrint(msg, 2)

try:
    ScriptUtils.AddMsgAndPrint("\tPreparing the workspace...", 0)
    if not arcpy.Exists(workspace):
        arcpy.CreateFileGDB_management(os.path.dirname(workspace), "PVA_Data")    
    if arcpy.Exists(ConcatOutput_Zoning):
        arcpy.Delete_management(ConcatOutput_Zoning, "")
    if arcpy.Exists(ConcatOutput_Flood):
        arcpy.Delete_management(ConcatOutput_Flood, "")
    cleanup()
    ScriptUtils.AddMsgAndPrint("\tConnecting to the data...", 0)
    # Process: Make Parcel Feature Layer
    fieldMapping = "OBJECTID OBJECTID {0};REV_DATE REV_DATE {0};PARCELID PARCELID {1};HISTORICPIN HISTORICPIN {0};PARCEL_TYPE PARCEL_TYPE {0};BLOCK BLOCK {0};LOT LOT {0};SUBLOT SUBLOT {0};BLOCKLOT BLOCKLOT {0};HBLOCKLOT HBLOCKLOT {0};HBLOCK HBLOCK {0};HLOT HLOT {0};HSUBLOT HSUBLOT {0};CAT CAT {0};CLASS CLASS {0};LRSN LRSN {1};UNIT_COUNT UNIT_COUNT {0};EFF_DATE EFF_DATE {0};SHAPE SHAPE {0};PBA_ID PBA_ID {0};SHAPE.AREA SHAPE.AREA {0};SHAPE.LEN SHAPE.LEN {0}".format("HIDDEN NONE", "VISIBLE NONE")
    arcpy.MakeFeatureLayer_management(PVA_Parcel, Parcel_Layer, "", "", fieldMapping)

    # Process: Make REMF Master Table View
    fieldMapping2 = "OBJECTID OBJECTID {0};PVA_DISTRICT PVA_DISTRICT {0};BLOCK BLOCK {0};LOT LOT {0};SUBLOT SUBLOT {0};SUBDIVISION SUBDIVISION {0};LAND_SIZE LAND_SIZE {0};FIRE_DISTRICT FIRE_DISTRICT {0};SATELLITE_CITY SATELLITE_CITY {0};PROP_ADDRESS PROP_ADDRESS {0};PROP_HOUSE PROP_HOUSE {0};PROP_DIR PROP_DIR {0};PROP_STREET PROP_STREET {0};PROP_STREETTYPE PROP_STREETTYPE {0};UNIT UNIT {0};REASSESS_REASON REASSESS_REASON {0};REASSESS_YEAR REASSESS_YEAR {0};ANCHORAGE_CODE ANCHORAGE_CODE {0};VIDEO_FRAME VIDEO_FRAME {0};VIDEO_CLUSTER VIDEO_CLUSTER {0};NOTICE_REASON NOTICE_REASON {0};NOTICE_YEAR NOTICE_YEAR {0};PRIOR_REASON PRIOR_REASON {0};PRIOR_YEAR PRIOR_YEAR {0};OLDEST_REASON OLDEST_REASON {0};OLDEST_YEAR OLDEST_YEAR {0};DEED_BOOK1 DEED_BOOK1 {0};DEED_PAGE1 DEED_PAGE1 {0};TRANSFER_DATE1 TRANSFER_DATE1 {0};CONSIDERATION1 CONSIDERATION1 {0};TRANSFER_TYPE1 TRANSFER_TYPE1 {0};STATE_VALID1 STATE_VALID1 {0};PVA_VALID1 PVA_VALID1 {0};DEED_BOOK2 DEED_BOOK2 {0};DEED_PAGE2 DEED_PAGE2 {0};TRANSFER_DATE2 TRANSFER_DATE2 {0};CONSIDERATION2 CONSIDERATION2 {0};TRANSFER_TYPE2 TRANSFER_TYPE2 {0};STATE_VALID2 STATE_VALID2 {0};PVA_VALID2 PVA_VALID2 {0};DEED_BOOK3 DEED_BOOK3 {0};DEED_PAGE3 DEED_PAGE3 {0};TRANSFER_DATE3 TRANSFER_DATE3 {0};CONSIDERATION3 CONSIDERATION3 {0};TRANSFER_TYPE3 TRANSFER_TYPE3 {0};STATE_VALID3 STATE_VALID3 {0};PVA_VALID3 PVA_VALID3 {0};PVA_NEIGHBOR PVA_NEIGHBOR {0};PARENT_PIN PARENT_PIN {0};MERGED_PIN MERGED_PIN {0};REM_DEEDBOOK REM_DEEDBOOK {0};REM_DEEDPAGE REM_DEEDPAGE {0};REM_DEEDDATE REM_DEEDDATE {0};CUR_LASTNAME CUR_LASTNAME {0};CUR_FIRSTNAME CUR_FIRSTNAME {0};CUR_NAME2 CUR_NAME2 {0};CUR_ADDRESS1 CUR_ADDRESS1 {0};CUR_ADDRESS2 CUR_ADDRESS2 {0};CUR_CITY CUR_CITY {0};CUR_STATE CUR_STATE {0};CUR_ZIP CUR_ZIP {0};CUR_PROP_CLASS CUR_PROP_CLASS {0};CUR_LAND CUR_LAND {0};CUR_IMPROVEMENT CUR_IMPROVEMENT {0};CUR_TOTAL CUR_TOTAL {0};CUR_AG_VALUE CUR_AG_VALUE {0};CUR_AG_LAND CUR_AG_LAND {0};CUR_HOMESTEAD CUR_HOMESTEAD {0};PROP_CLASS PROP_CLASS {1};LRSN LRSN {1};PARCELID PARCELID {1};BLOCKLOT BLOCKLOT {0};CUR_FULLNAME CUR_FULLNAME {0}".format("HIDDEN NONE", "VISIBLE NONE")
    arcpy.MakeTableView_management(pva_remf_master, remf_master_View, "\"PROP_CLASS\" >= 296 AND \"PROP_CLASS\" <= 499", "", fieldMapping2)

    # Process: Add Join
    ScriptUtils.AddMsgAndPrint("\tJoining {0} to {1}...".format(os.path.basename(PVA_Parcel), os.path.basename(pva_remf_master)), 0)
    arcpy.AddJoin_management(Parcel_Layer, "PARCELID", remf_master_View, "PARCELID", "KEEP_ALL")

    # Process: Make Commercial Neighborhoods Feature Layer
    fieldMapping3 = "OBJECTID OBJECTID {0};Shape Shape {0};CN_NUM CN_NUM {0};CN_NAME CN_NAME {0};Shape_Length Shape_Length {0};Shape_Area Shape_Area {0}".format("VISIBLE NONE")
    arcpy.MakeFeatureLayer_management(Commercial_Neighborhoods, Commercial_Neighborhoods_Lay, Expression, "", fieldMapping3)

    # Process: Spatial Join
    ScriptUtils.AddMsgAndPrint("\tProcessing the Spatial Join...", 0)    
    spatialFieldMapping = "PVA_Parcel_PARCELID \"PARCELID\" true true false 12 Text 0 0 ,First,#,Parcel_Layer,PVA.Parcel.PARCELID,-1,-1;PVA_Parcel_LRSN \"LRSN\" true true false 4 Long 0 10 ,First,#,Parcel_Layer,PVA.Parcel.LRSN,-1,-1;pva_remf_master_PROP_CLASS \"PROP_CLASS\" true true false 2 Short 0 3 ,First,#,Parcel_Layer,pva.remf_master.PROP_CLASS,-1,-1;pva_remf_master_LRSN \"LRSN\" true true false 8 Double 0 10 ,First,#,Parcel_Layer,pva.remf_master.LRSN,-1,-1;pva_remf_master_PARCELID \"PARCELID\" true true false 12 Text 0 0 ,First,#,Parcel_Layer,pva.remf_master.PARCELID,-1,-1;CN_NUM \"CN_NUM\" true true false 2 Short 0 0 ,First,#,Commercial_Neighborhoods_Lay,CN_NUM,-1,-1;CN_NAME \"CN_NAME\" true true false 50 Text 0 0 ,First,#,Commercial_Neighborhoods_Lay,CN_NAME,-1,-1;Shape_Length \"Shape_Length\" false true true 8 Double 0 0 ,First,#,Commercial_Neighborhoods_Lay,Shape_Length,-1,-1;Shape_Area \"Shape_Area\" false true true 8 Double 0 0 ,First,#,Commercial_Neighborhoods_Lay,Shape_Area,-1,-1"
    arcpy.SpatialJoin_analysis(Parcel_Layer, Commercial_Neighborhoods_Lay, Parcel_SpatialJoin, "JOIN_ONE_TO_ONE", "KEEP_COMMON", spatialFieldMapping, "WITHIN", "", "")

    # Process: Add LAND_SIZE Field
    ScriptUtils.AddMsgAndPrint("\tProcessing the LAND_SIZE field...", 0)    
    arcpy.AddField_management(Parcel_SpatialJoin, "LAND_SIZE", "DOUBLE", "10", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Calculate LAND_SIZE Field
    calcExpression = "[SHAPE_Area] / 43560"
    arcpy.CalculateField_management(Parcel_SpatialJoin, "LAND_SIZE", calcExpression, "VB", "")
    
    #
    # -----------------------Calculate Zoning for the selected Parcels-----------------------
    #
    # Process: Make Zoning Feature Layer
    fieldMapping4 = "OBJECTID OBJECTID {0};ZONING_CODE ZONING_CODE {1};ZONING_NAME ZONING_NAME {1};ZONING_TYPE ZONING_TYPE {1};SHAPE SHAPE {0};SHAPE.AREA SHAPE.AREA {0};SHAPE.LEN SHAPE.LEN {0}".format("HIDDEN NONE", "VISIBLE NONE")
    arcpy.MakeFeatureLayer_management(JEFLIB_Zoning, Zoning_Layer, "", "", fieldMapping4)

    # Process: Intersect Zoning layer with the selected parcels
    ScriptUtils.AddMsgAndPrint("\tIntersecting the Zoning data...", 0)    
    inFeatures = "{0}\\Parcel_SpatialJoin #;Zoning_Layer #".format(workspace)
    arcpy.Intersect_analysis(inFeatures, Parcel_SpatialJoin_Intersect, "ALL", "", "INPUT")

    # Process: Frequency
    arcpy.Frequency_analysis(Parcel_SpatialJoin_Intersect, Parcel_Frequency, "PVA_Parcel_PARCELID", "")

    # Process: Add ZONE_AREA Field
    ScriptUtils.AddMsgAndPrint("\tProcessing the ZONE_AREA field...", 0)    
    arcpy.AddField_management(Parcel_SpatialJoin_Intersect, "ZONE_AREA", "DOUBLE", "10", "4", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Calculate ZONE_AREA Field
    arcpy.CalculateField_management(Parcel_SpatialJoin_Intersect, "ZONE_AREA", calcExpression, "VB", "")

    # Process: Add ZONE_PCT Field
    arcpy.AddField_management(Parcel_SpatialJoin_Intersect, "ZONE_PCT", "DOUBLE", "3", "0", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Calculate ZONE_PCT Field
    calcExpression2 = "GetPctArea( !ZONE_AREA!, !LAND_SIZE! )"
    codeblock = '''def GetPctArea(zoneArea, landSize):
        area = (zoneArea /  landSize) * 100
        return round(area, 1)'''
    arcpy.CalculateField_management(Parcel_SpatialJoin_Intersect, "ZONE_PCT", calcExpression2, "PYTHON", codeblock)
    
    calcExp1 = """\"(" +  !ZONING_CODE! + "    " + str(round(!ZONE_AREA!, 3)) + " AC    " + str(!ZONE_PCT!) + "% )\""""
    new_View = "ConcatOutput_View"  
    CalculateLastTwoFields(Parcel_SpatialJoin_Intersect, Parcel_Frequency, new_View, calcExp1)
    
    arcpy.Rename_management(ConcatOutput_dbf, ConcatOutput_Zoning)
    
    #
    # -----------------------Calculate FEMA Flood Zones for the selected Parcels-----------------------
    #
    # Process: Make FEMA Flood Feature Layer
    arcpy.MakeFeatureLayer_management(FEMA_Flood, Flood_Layer)
    
    # Process: Intersect flood zones with the selected parcels
    ScriptUtils.AddMsgAndPrint("\tIntersecting the Flood data...", 0)    
    inFeatures = "{0}\\Parcel_SpatialJoin #;Flood_Layer #".format(workspace)
    arcpy.Intersect_analysis(inFeatures, Parcel_Flood_SpatialJoin_Intersect, "ALL", "", "INPUT")

    # Process: Frequency
    arcpy.Frequency_analysis(Parcel_Flood_SpatialJoin_Intersect, Parcel_Flood_Frequency, "PVA_Parcel_PARCELID", "")

    # Process: Add ZONE_AREA Field
    ScriptUtils.AddMsgAndPrint("\tProcessing the ZONE_AREA field...", 0)    
    arcpy.AddField_management(Parcel_Flood_SpatialJoin_Intersect, "ZONE_AREA", "DOUBLE", "10", "4", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Calculate ZONE_AREA Field
    arcpy.CalculateField_management(Parcel_Flood_SpatialJoin_Intersect, "ZONE_AREA", calcExpression, "VB", "")

    # Process: Add ZONE_PCT Field
    ScriptUtils.AddMsgAndPrint("\tProcessing the ZONE_PCT field...", 0)    
    arcpy.AddField_management(Parcel_Flood_SpatialJoin_Intersect, "ZONE_PCT", "DOUBLE", "3", "0", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Calculate Field (3)
    arcpy.CalculateField_management(Parcel_Flood_SpatialJoin_Intersect, "ZONE_PCT", calcExpression2, "PYTHON", codeblock)

    calcExp1 = """\"(" +  GetFZone(!PLOTCODE!) + "    " + str(round(!ZONE_AREA!, 3)) + " AC    " + str(!ZONE_PCT!) + "% )\""""
    new_View = "Concat_View"  
    CalculateLastTwoFields(Parcel_Flood_SpatialJoin_Intersect, Parcel_Flood_Frequency, new_View, calcExp1)
    
    arcpy.Rename_management(ConcatOutput_dbf, ConcatOutput_Flood)
    
    cleanup()
except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n    {1}: {2}\n".format(tbinfo, str(sys.exc_type), str(sys.exc_value))
    gpmsg = "ARCPY ERRORS:\n{0}\n".format(arcpy.GetMessages(2))
    tmRun = time.strftime("%X", time.localtime())
    endTime = time.time()
    prodInfo = "\tScript errored after running for {0} seconds.".format(str(round((endTime - startTime))))
    msgTxt += "\n\n\tScript error at: {0}\n{1}\n\n{2}{3}".format(tmRun, prodInfo, gpmsg, pymsg)
    ScriptUtils.AddMsgAndPrint(msgTxt, 2)
    