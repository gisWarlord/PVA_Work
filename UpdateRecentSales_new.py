'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    UpdateRecentSales_new.py
'   Purpose:    Updates recent sales files for the subscription maps
'
'---------------------------------------------------------------------
'   Returns:    J:\common\PVA_SALES.gdb
'                       RECENT_CONDO_SALES - New
'                       RECENT_SALES
'                       RECENT_SALES_POINTS
'---------------------------------------------------------------------
'     Notes:    This is a modified version of the script created by
'               Trey Nunn. It was changed to be run from ArcCatalog or
'               ArcMap and only need the Sales table as an input. The 
'               sales table can be ether a dBase table or CSV file. 
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

# parameters
VSalesDBF = arcpy.GetParameterAsText(0)
msgTxt = ""
startTime = time.time()

connection = r"J:\pva\LOJIC_Sales_Data\LojicRecentSales_Script\pvastaff_connection.sde"
Parcel_Poly = os.path.join(connection, "PVA.Land", "PVA.Parcel")
Parcels = "Parcel_Layer"
Parcel_Point = os.path.join(connection, "PVA.Land", "PVA.Parcel_Point")
ParcelPnts = "Parcel_Pnts"
outGDB = r"J:\common\PVA_SALES.gdb"
workspace = r"J:\pva\LOJIC_Sales_Data\LojicRecentSales_Script\Intermediate.gdb"
# outGDB = r"H:\pvawork\PVA_SALES.gdb"
# workspace = r"H:\pvawork\Intermediate.gdb"

try:
    if not arcpy.Exists(workspace):
        arcpy.CreateFileGDB_management(os.path.dirname(workspace), "Intermediate")

    arcpy.env.workspace = workspace
    arcpy.env.overwriteOutput = True
    
    ScriptUtils.AddMsgAndPrint("\tJoining Parcel points to the sales table...")
    
    arcpy.MakeFeatureLayer_management(Parcel_Point, ParcelPnts)
    arcpy.CopyFeatures_management(ParcelPnts, "ParcelCopy")
    arcpy.MakeFeatureLayer_management("ParcelCopy", "ParcelCopy_Layer")
    arcpy.CopyRows_management(VSalesDBF, "VSALES")
    arcpy.AddJoin_management("ParcelCopy_Layer", "LRSN", "VSALES", "LRSN", "KEEP_COMMON")
    arcpy.CopyFeatures_management("ParcelCopy_Layer", "ParcelDBF_Join")
    
    ScriptUtils.AddMsgAndPrint("\tAdding and calculating new fields...")
    
    arcpy.AddField_management("ParcelDBF_Join", "PARCELID", "TEXT", "", "", 12)
    arcpy.AddField_management("ParcelDBF_Join", "LRSN", "DOUBLE", 10)
    arcpy.AddField_management("ParcelDBF_Join", "CONSIDERATION", "DOUBLE", 10)                            
    arcpy.AddField_management("ParcelDBF_Join", "PVA_NEIGHBOR", "LONG", 6)
    arcpy.AddField_management("ParcelDBF_Join", "PROP_CLASS", "SHORT", 3)
    arcpy.AddField_management("ParcelDBF_Join", "TRANSFER_DATE", "DATE")

    arcpy.CalculateField_management("ParcelDBF_Join", "PARCELID", "[ParcelCopy_PARCELID]")
    arcpy.CalculateField_management("ParcelDBF_Join", "LRSN", "[ParcelCopy_LRSN]")
    
    fields = arcpy.ListFields("ParcelDBF_Join")
    for f in fields:
        if "VSALES_Considerat" in f.name:
            arcpy.CalculateField_management("ParcelDBF_Join", "CONSIDERATION", "[{0}]".format(f.name))
        if "VSALES_Neighborho" in f.name:
            arcpy.CalculateField_management("ParcelDBF_Join", "PVA_NEIGHBOR", "[{0}]".format(f.name))
        if f.name == "VSALES_PC":
            arcpy.CalculateField_management("ParcelDBF_Join", "PROP_CLASS", "[{0}]".format(f.name))
        if "VSALES_Transfer_D" in f.name:
            arcpy.CalculateField_management("ParcelDBF_Join", "TRANSFER_DATE", "[{0}]".format(f.name))                                

    if not arcpy.Exists(outGDB):
        ScriptUtils.AddMsgAndPrint("\tCreating {0}...".format(outGDB))
        arcpy.CreateFileGDB_management(os.path.dirname(outGDB), 'PVA_SALES')
        
    ScriptUtils.AddMsgAndPrint("\tCreating point features...")
    
    # Use ListFields to get a list of field objects
    fieldObjList = arcpy.ListFields("ParcelDBF_Join")
 
    # Create an empty list that will be populated with field names        
    fieldNameList = []
    
    # For each field in the object list, add the field name to the name
    # list. If the field is required, exclude it, to prevent errors.
    for field in fieldObjList:
        if not field.required and field.name not in {"OBJECTID","PARCELID","LRSN","CONSIDERATION","PROP_CLASS","TRANSFER_DATE","PVA_NEIGHBOR","ParcelCopy_POINTTYPE"}:
            fieldNameList.append(field.name)
    
    arcpy.DeleteField_management("ParcelDBF_Join", fieldNameList)
    
    ScriptUtils.AddMsgAndPrint("\tSelecting Condo Sales...")
    arcpy.MakeFeatureLayer_management("ParcelDBF_Join", "Parcel_Point_NonCentroid", "ParcelCopy_POINTTYPE = 0")
    arcpy.FeatureClassToFeatureClass_conversion("Parcel_Point_NonCentroid", outGDB, "RECENT_CONDO_SALES")
    ScriptUtils.AddMsgAndPrint("\tSelecting Recent Sales...")
    arcpy.MakeFeatureLayer_management("ParcelDBF_Join", "Parcel_Point_Centroid", "ParcelCopy_POINTTYPE = 1")    
    arcpy.FeatureClassToFeatureClass_conversion("Parcel_Point_Centroid", outGDB, "RECENT_SALES_POINTS")
    
    arcpy.DeleteField_management(outGDB +"\\RECENT_CONDO_SALES", "ParcelCopy_POINTTYPE")
    arcpy.DeleteField_management(outGDB +"\\RECENT_SALES_POINTS", "ParcelCopy_POINTTYPE")
    
    ScriptUtils.AddMsgAndPrint("\tCreating recent sales polygon features...")
    
    arcpy.MakeFeatureLayer_management(Parcel_Poly, Parcels)
    arcpy.SpatialJoin_analysis(Parcels, outGDB +"\\RECENT_SALES_POINTS", "ParcelDBF_Poly", "JOIN_ONE_TO_MANY", "KEEP_COMMON", "#", "INTERSECT", "#", "#")
    
    # Use ListFields to get a list of field objects
    fldObjList = arcpy.ListFields("ParcelDBF_Poly")
    
    # Create an empty list that will be populated with field names        
    fldNameList = []
    
    # For each field in the object list, add the field name to the name
    # list. If the field is required, exclude it, to prevent errors.
    for fld in fldObjList:
        if not fld.required and fld.name not in {"OBJECTID","PARCELID","LRSN","CONSIDERATION","PROP_CLASS","TRANSFER_DATE","PVA_NEIGHBOR","PARCEL_TYPE"}:
            fldNameList.append(fld.name)
    
    arcpy.DeleteField_management("ParcelDBF_Poly", fldNameList)
    arcpy.FeatureClassToFeatureClass_conversion("ParcelDBF_Poly", outGDB, "RECENT_SALES")
    
    ScriptUtils.AddMsgAndPrint("\tCleaning up...")    
    if arcpy.Exists("ParcelDBF_Poly"):
        arcpy.Delete_management("ParcelDBF_Poly", "")
    if arcpy.Exists("ParcelDBF_Join"):
        arcpy.Delete_management("ParcelDBF_Join", "")
    if arcpy.Exists("ParcelCopy"):
        arcpy.Delete_management("ParcelCopy", "")
    if arcpy.Exists("VSALES"):
        arcpy.Delete_management("VSALES", "")
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
    ScriptUtils.AddMsgAndPrint("\tProcess completed")
