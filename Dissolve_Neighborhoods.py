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
    
    # Process: Make Feature Layer of the Old Parcels
    ScriptUtils.AddMsgAndPrint("\tProcessing the Old Parcels...", 0)
    whereClause = "\"PVA_NEIGHB\" >= 100000"    
    # Create a fieldinfo object
    arcpy.MakeFeatureLayer_management(OLD_Parcels,  "tmpOldParcels")
    fields = arcpy.ListFields("tmpOldParcels")
    fieldInfo = arcpy.FieldInfo()
    # Iterate through the fields and set them to fieldinfo
    for field in fields:
        name = field.name
        if name == "PVA_NEIGHB":
            fieldInfo.addField(name, "Neighborhoods", "VISIBLE", "")
        else:
            fieldInfo.addField(name, name, "VISIBLE", "")
    arcpy.MakeFeatureLayer_management(OLD_Parcels, OldParcels_Layer, whereClause, "", fieldInfo)

    # Process: 1st Dissolve
    arcpy.Dissolve_management(OldParcels_Layer, OldParcel_Neighborhoods_shp, "Neighborhoods", "LRSN COUNT", "MULTI_PART", "DISSOLVE_LINES")
    ScriptUtils.AddMsgAndPrint("\tCreated {0}...".format(OldParcel_Neighborhoods_shp), 0)

    ScriptUtils.AddMsgAndPrint("\tCompiling new Parcel data...", 0)
    
    # Process: Make Table View of pva.remf_master
    where = "PVA_NEIGHBOR >= 100000"    
    # Create a fieldinfo object
    arcpy.MakeTableView_management(pva_remf_master,  "tmpremf_master")
    fields = arcpy.ListFields("tmpremf_master")
    fldInfo = arcpy.FieldInfo()
    lstFields = ["PVA_NEIGHBOR", "PARCELID", "LRSN"]
    # Iterate through the fields and set them to fieldinfo
    for field in fields:
        name = field.name
        if name in lstFields:
            if name == "PVA_NEIGHBOR":
                fldInfo.addField(name, "Neighborhoods", "VISIBLE", "")
            else:
                fldInfo.addField(name, name, "VISIBLE", "")
        else:
            fldInfo.addField(name, name, "HIDDEN", "")
    arcpy.MakeTableView_management(pva_remf_master, remf_View, where, "", fldInfo)

    # Process: Table to Table
    arcpy.TableToTable_conversion(remf_View, PVA_Data_gdb, "remf_master")

    # Process: Make Feature Layer of PVA.Parcel
    # Create a fieldinfo object
    arcpy.MakeFeatureLayer_management(PVA_Parcel,  "tmpParcels")
    fields = arcpy.ListFields("tmpParcels")
    fInfo = arcpy.FieldInfo()
    lstFields = ["PARCELID", "LRSN"]
    # Iterate through the fields and set them to fieldinfo
    for field in fields:
        name = field.name
        if name in lstFields:
            fInfo.addField(name, name, "VISIBLE", "")
        else:
            fInfo.addField(name, name, "HIDDEN", "")
    arcpy.MakeFeatureLayer_management(PVA_Parcel, Parcel_Layer, "", "", fInfo)

    # Process: Feature Class to Feature Class
    arcpy.FeatureClassToFeatureClass_conversion(Parcel_Layer, PVA_Data_gdb, "Parcels")

    # Process: Make Feature Layer of the Parcels that we just copied above
    arcpy.MakeFeatureLayer_management(Parcels, Parcels_Layer, "", "", "OBJECTID OBJECTID {0};'' '' {0};PARCELID PARCELID {0};LRSN LRSN {0}".format("VISIBLE NONE"))

    # Process: Add Join
    arcpy.AddJoin_management(Parcels_Layer, "LRSN", remf_master, "LRSN", "KEEP_COMMON")

    # Process: 2nd Dissolve
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
