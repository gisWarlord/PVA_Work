# -*- coding: utf-8 -*-
'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    Dissolve_Neighborhoods.py
'   Purpose:    Dissolves old and current Residential Neighborhoods
'
'---------------------------------------------------------------------
'   Returns:    J:\pva\Residential\Neighborhoods\OldParcel_Neighborhoods.shp
'               J:\pva\Residential\Neighborhoods\Parcel_Neighborhoods.shp
'---------------------------------------------------------------------
'     Notes:    
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  09/2018
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env

# Import the script utilities
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

OLD_Parcels = arcpy.GetParameterAsText(0)
if OLD_Parcels == "#" or not OLD_Parcels:
    OLD_Parcels = "J:\\pva\\Residential\\OLD Parcel File 02162011.shp"

# Email notifications
msgTxt = ""
startTime = time.time()

# Local variables
workspace = r"J:\pva\Residential\Neighborhoods"
PVA_Parcel = os.path.join(workspace, "pvastaff_connection.sde", "PVA.Land", "PVA.Parcel")
pva_remf_master = os.path.join(workspace, "pvastaff_connection.sde", "pva.remf_master")
PVA_Data_gdb = os.path.join(workspace, "PVA_Data.gdb")
OldParcel_Neighborhoods_shp = os.path.join(workspace, "OldParcel_Neighborhoods.shp")
remf_master = os.path.join(PVA_Data_gdb, "remf_master")
Parcel_Neighborhoods_shp = os.path.join(workspace, "Parcel_Neighborhoods.shp")
Parcels = os.path.join(PVA_Data_gdb, "Parcels")
OldParcels_Layer = "OLDParcelFile02162011_Layer"
Parcels_Layer = "Parcels_Layer"
Parcel_Layer = "Parcel_Layer"
remf_View = "remf_master_View"

def cleanup():
    '''
    Removes the temp files created by this proccess
    '''
    try:
        if arcpy.Exists(remf_master):
            arcpy.Delete_management(remf_master, "")
        if arcpy.Exists(Parcels):
            arcpy.Delete_management(Parcels, "")
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
    cleanup()
    
    if arcpy.Exists(OldParcel_Neighborhoods_shp):
        arcpy.Delete_management(OldParcel_Neighborhoods_shp, "")
    if arcpy.Exists(Parcel_Neighborhoods_shp):
        arcpy.Delete_management(Parcel_Neighborhoods_shp, "")
    # Process: Make Feature Layer
    whereClause = "\"PVA_NEIGHB\" >= 100000"
    fieldInfo = "FID FID {0};Shape Shape {0};OBJECTID OBJECTID {0};REV_DATE REV_DATE {0};PARCELID PARCELID {0};HISTORICPI HISTORICPI {0};PARCEL_TYP PARCEL_TYP {0};BLOCK BLOCK {0};LOT LOT {0};SUBLOT SUBLOT {0};BLOCKLOT BLOCKLOT {0};HBLOCKLOT HBLOCKLOT {0};HBLOCK HBLOCK {0};HLOT HLOT {0};HSUBLOT HSUBLOT {0};CAT CAT {0};CLASS CLASS {0};LRSN LRSN {0};UNIT_COUNT UNIT_COUNT {0};EFF_DATE EFF_DATE {0};OBJECTID_1 OBJECTID_1 {0};PVA_DISTRI PVA_DISTRI {0};BLOCK_1 BLOCK_1 {0};LOT_1 LOT_1 {0};SUBLOT_1 SUBLOT_1 {0};SUBDIVISIO SUBDIVISIO {0};LAND_SIZE LAND_SIZE {0};FIRE_DISTR FIRE_DISTR {0};SATELLITE_ SATELLITE_ {0};PROP_ADDRE PROP_ADDRE {0};PROP_HOUSE PROP_HOUSE {0};PROP_DIR PROP_DIR {0};PROP_STREE PROP_STREE {0};PROP_STR_1 PROP_STR_1 {0};UNIT UNIT {0};REASSESS_R REASSESS_R {0};REASSESS_Y REASSESS_Y {0};ANCHORAGE_ ANCHORAGE_ {0};VIDEO_FRAM VIDEO_FRAM {0};VIDEO_CLUS VIDEO_CLUS {0};NOTICE_REA NOTICE_REA {0};NOTICE_YEA NOTICE_YEA {0};PRIOR_REAS PRIOR_REAS {0};PRIOR_YEAR PRIOR_YEAR {0};OLDEST_REA OLDEST_REA {0};OLDEST_YEA OLDEST_YEA {0};DEED_BOOK1 DEED_BOOK1 {0};DEED_PAGE1 DEED_PAGE1 {0};TRANSFER_D TRANSFER_D {0};CONSIDERAT CONSIDERAT {0};TRANSFER_T TRANSFER_T {0};STATE_VALI STATE_VALI {0};PVA_VALID1 PVA_VALID1 {0};DEED_BOOK2 DEED_BOOK2 {0};DEED_PAGE2 DEED_PAGE2 {0};TRANSFER_1 TRANSFER_1 {0};CONSIDER_1 CONSIDER_1 {0};TRANSFER_2 TRANSFER_2 {0};STATE_VA_1 STATE_VA_1 {0};PVA_VALID2 PVA_VALID2 {0};DEED_BOOK3 DEED_BOOK3 {0};DEED_PAGE3 DEED_PAGE3 {0};TRANSFER_3 TRANSFER_3 {0};CONSIDER_2 CONSIDER_2 {0};TRANSFER_4 TRANSFER_4 {0};STATE_VA_2 STATE_VA_2 {0};PVA_VALID3 PVA_VALID3 {0};PVA_NEIGHB Neighborhoods {0};PARENT_PIN PARENT_PIN {0};MERGED_PIN MERGED_PIN {0};REM_DEEDBO REM_DEEDBO {0};REM_DEEDPA REM_DEEDPA {0};REM_DEEDDA REM_DEEDDA {0};CUR_LASTNA CUR_LASTNA {0};CUR_FIRSTN CUR_FIRSTN {0};CUR_NAME2 CUR_NAME2 {0};CUR_ADDRES CUR_ADDRES {0};CUR_ADDR_1 CUR_ADDR_1 {0};CUR_CITY CUR_CITY {0};CUR_STATE CUR_STATE {0};CUR_ZIP CUR_ZIP {0};CUR_PROP_C CUR_PROP_C {0};CUR_LAND CUR_LAND {0};CUR_IMPROV CUR_IMPROV {0};CUR_TOTAL CUR_TOTAL {0};CUR_AG_VAL CUR_AG_VAL {0};CUR_AG_LAN CUR_AG_LAN {0};CUR_HOMEST CUR_HOMEST {0};PROP_CLASS PROP_CLASS {0};LRSN_1 LRSN_1 {0};PARCELID_1 PARCELID_1 {0};BLOCKLOT_1 BLOCKLOT_1 {0}".format("VISIBLE NONE")
    arcpy.MakeFeatureLayer_management(OLD_Parcels, OldParcels_Layer, whereClause, "", fieldInfo)

    # Process: Dissolve
    ScriptUtils.AddMsgAndPrint("\tProcessing the Old Parcels...", 0)
    arcpy.Dissolve_management(OldParcels_Layer, OldParcel_Neighborhoods_shp, "Neighborhoods", "LRSN COUNT", "MULTI_PART", "DISSOLVE_LINES")
    ScriptUtils.AddMsgAndPrint("\tCreated {0}...".format(OldParcel_Neighborhoods_shp), 0)

    # Process: Make Table View
    where = "PVA_NEIGHBOR >= 100000"
    fldInfo = "OBJECTID OBJECTID {0};PVA_DISTRICT PVA_DISTRICT {0};BLOCK BLOCK {0};LOT LOT {0};SUBLOT SUBLOT {0};SUBDIVISION SUBDIVISION {0};LAND_SIZE LAND_SIZE {0};FIRE_DISTRICT FIRE_DISTRICT {0};SATELLITE_CITY SATELLITE_CITY {0};PROP_ADDRESS PROP_ADDRESS {0};PROP_HOUSE PROP_HOUSE {0};PROP_DIR PROP_DIR {0};PROP_STREET PROP_STREET {0};PROP_STREETTYPE PROP_STREETTYPE {0};UNIT UNIT {0};REASSESS_REASON REASSESS_REASON {0};REASSESS_YEAR REASSESS_YEAR {0};ANCHORAGE_CODE ANCHORAGE_CODE {0};VIDEO_FRAME VIDEO_FRAME {0};VIDEO_CLUSTER VIDEO_CLUSTER {0};NOTICE_REASON NOTICE_REASON {0};NOTICE_YEAR NOTICE_YEAR {0};PRIOR_REASON PRIOR_REASON {0};PRIOR_YEAR PRIOR_YEAR {0};OLDEST_REASON OLDEST_REASON {0};OLDEST_YEAR OLDEST_YEAR {0};DEED_BOOK1 DEED_BOOK1 {0};DEED_PAGE1 DEED_PAGE1 {0};TRANSFER_DATE1 TRANSFER_DATE1 {0};CONSIDERATION1 CONSIDERATION1 {0};TRANSFER_TYPE1 TRANSFER_TYPE1 {0};STATE_VALID1 STATE_VALID1 {0};PVA_VALID1 PVA_VALID1 {0};DEED_BOOK2 DEED_BOOK2 {0};DEED_PAGE2 DEED_PAGE2 {0};TRANSFER_DATE2 TRANSFER_DATE2 {0};CONSIDERATION2 CONSIDERATION2 {0};TRANSFER_TYPE2 TRANSFER_TYPE2 {0};STATE_VALID2 STATE_VALID2 {0};PVA_VALID2 PVA_VALID2 {0};DEED_BOOK3 DEED_BOOK3 {0};DEED_PAGE3 DEED_PAGE3 {0};TRANSFER_DATE3 TRANSFER_DATE3 {0};CONSIDERATION3 CONSIDERATION3 {0};TRANSFER_TYPE3 TRANSFER_TYPE3 {0};STATE_VALID3 STATE_VALID3 {0};PVA_VALID3 PVA_VALID3 {0};PVA_NEIGHBOR Neighborhoods {1};PARENT_PIN PARENT_PIN {0};MERGED_PIN MERGED_PIN {0};REM_DEEDBOOK REM_DEEDBOOK {0};REM_DEEDPAGE REM_DEEDPAGE {0};REM_DEEDDATE REM_DEEDDATE {0};CUR_LASTNAME CUR_LASTNAME {0};CUR_FIRSTNAME CUR_FIRSTNAME {0};CUR_NAME2 CUR_NAME2 {0};CUR_ADDRESS1 CUR_ADDRESS1 {0};CUR_ADDRESS2 CUR_ADDRESS2 {0};CUR_CITY CUR_CITY {0};CUR_STATE CUR_STATE {0};CUR_ZIP CUR_ZIP {0};CUR_PROP_CLASS CUR_PROP_CLASS {0};CUR_LAND CUR_LAND {0};CUR_IMPROVEMENT CUR_IMPROVEMENT {0};CUR_TOTAL CUR_TOTAL {0};CUR_AG_VALUE CUR_AG_VALUE {0};CUR_AG_LAND CUR_AG_LAND {0};CUR_HOMESTEAD CUR_HOMESTEAD {0};PROP_CLASS PROP_CLASS {0};LRSN LRSN {1};PARCELID PARCELID {1};BLOCKLOT BLOCKLOT {0};CUR_FULLNAME CUR_FULLNAME {0}".format("HIDDEN NONE", "VISIBLE NONE")
    arcpy.MakeTableView_management(pva_remf_master, remf_View, where, "", fldInfo)

    # Process: Table to Table
    ScriptUtils.AddMsgAndPrint("\tCompiling new Parcel data...", 0)
    arcpy.TableToTable_conversion(remf_View, PVA_Data_gdb, "remf_master")

    # Process: Make Feature Layer (2)
    fInfo = "OBJECTID OBJECTID {0};REV_DATE REV_DATE {0};PARCELID PARCELID {1};HISTORICPIN HISTORICPIN {0};PARCEL_TYPE PARCEL_TYPE {0};BLOCK BLOCK {0};LOT LOT {0};SUBLOT SUBLOT {0};BLOCKLOT BLOCKLOT {0};HBLOCKLOT HBLOCKLOT {0};HBLOCK HBLOCK {0};HLOT HLOT {0};HSUBLOT HSUBLOT {0};CAT CAT {0};CLASS CLASS {0};LRSN LRSN {1};UNIT_COUNT UNIT_COUNT {0};EFF_DATE EFF_DATE {0};SHAPE SHAPE {0};PBA_ID PBA_ID {0};SHAPE.AREA SHAPE.AREA {0};SHAPE.LEN SHAPE.LEN {0}".format("HIDDEN NONE", "VISIBLE NONE")
    arcpy.MakeFeatureLayer_management(PVA_Parcel, Parcel_Layer, "", "", fInfo)

    # Process: Feature Class to Feature Class
    arcpy.FeatureClassToFeatureClass_conversion(Parcel_Layer, PVA_Data_gdb, "Parcels")

    # Process: Make Feature Layer (3)
    arcpy.MakeFeatureLayer_management(Parcels, Parcels_Layer, "", "", "OBJECTID OBJECTID {0};'' '' {0};PARCELID PARCELID {0};LRSN LRSN {0}".format("VISIBLE NONE"))

    # Process: Add Join
    arcpy.AddJoin_management(Parcels_Layer, "LRSN", remf_master, "LRSN", "KEEP_COMMON")

    # Process: Dissolve (2)
    ScriptUtils.AddMsgAndPrint("\tProcessing the New Parcels", 0)
    arcpy.Dissolve_management(Parcels_Layer, Parcel_Neighborhoods_shp, "remf_master.Neighborhoods", "Parcels.LRSN COUNT", "MULTI_PART", "DISSOLVE_LINES")
    ScriptUtils.AddMsgAndPrint("\tCreated {0}...".format(Parcel_Neighborhoods_shp), 0)
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
finally:
    ScriptUtils.AddMsgAndPrint("\tRemoving temporary files...", 0)
    cleanup()
