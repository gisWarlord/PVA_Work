##################################################
##Updates recent sales files for subscription maps
##################################################

# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env

# Import the script that sends emails
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

arcpy.env.workspace = r'J:\pva\LOJIC_Sales_Data\LojicRecentSales_Script\Intermediate.gdb'
arcpy.env.overwriteOutput = True

#PARAMETERS#
msgTxt = ""
startTime = time.time()
VSalesDBF = arcpy.GetParameterAsText(0)
Parcels = arcpy.GetParameterAsText(1)
outGDB = r'J:\common\PVA_SALES.gdb'

ScriptUtils.AddMsgAndPrint("\tBeginning the Process...")

try:
    ScriptUtils.AddMsgAndPrint("\tJoining Parcels to DBF table...")
    
    arcpy.CopyFeatures_management(Parcels, "ParcelCopy")
    arcpy.MakeFeatureLayer_management("ParcelCopy", "ParcelCopy_Layer")
    arcpy.CopyRows_management(VSalesDBF, "VSALES")
    arcpy.AddJoin_management("ParcelCopy_Layer",'PVA_Parcel_LRSN',"VSALES",'LRSN', 'KEEP_COMMON')
    arcpy.CopyFeatures_management("ParcelCopy_Layer", "ParcelDBF_Join")

    ScriptUtils.AddMsgAndPrint("\tAdding and calculating new fields...")
    
    arcpy.AddField_management("ParcelDBF_Join", "PARCELID", "TEXT", "", "", 12)
    arcpy.AddField_management("ParcelDBF_Join", "LRSN", "DOUBLE", 10)
    arcpy.AddField_management("ParcelDBF_Join", "CONSIDERATION", "DOUBLE", 10)                            
    arcpy.AddField_management("ParcelDBF_Join", "PVA_NEIGHBOR", "LONG", 6)
    arcpy.AddField_management("ParcelDBF_Join", "PROP_CLASS", "SHORT", 3)
    arcpy.AddField_management("ParcelDBF_Join", "TRANSFER_DATE", "DATE")

    arcpy.CalculateField_management("ParcelDBF_Join", "PARCELID", "[ParcelCopy_PVA_Parcel_PARCELID]")
    arcpy.CalculateField_management("ParcelDBF_Join", "LRSN", "[ParcelCopy_PVA_Parcel_LRSN]")
    arcpy.CalculateField_management("ParcelDBF_Join", "CONSIDERATION", "[VSALES_CONSIDERAT]")
    arcpy.CalculateField_management("ParcelDBF_Join", "PVA_NEIGHBOR", "[VSALES_NEIGHBORHO]")
    arcpy.CalculateField_management("ParcelDBF_Join", "PROP_CLASS", "[VSALES_PC]")
    arcpy.CalculateField_management("ParcelDBF_Join", "TRANSFER_DATE", "[VSALES_TRANSFER_D]")                                

    ScriptUtils.AddMsgAndPrint("\tCreating final results in {0}".format(outGDB))

    if not arcpy.Exists(outGDB):
        arcpy.CreateFileGDB_management(r'J:\common', 'PVA_SALES')
    
    # Use ListFields to get a list of field objects
    fieldObjList = arcpy.ListFields("ParcelDBF_Join")
 
    # Create an empty list that will be populated with field names        
    fieldNameList = []
 
    # For each field in the object list, add the field name to the name
    # list. If the field is required, exclude it, to prevent errors.
    for field in fieldObjList:
        if not field.required and field.name not in {"OBJECTID","PARCELID","LRSN","CONSIDERATION","PROP_CLASS","TRANSFER_DATE","PVA_NEIGHBOR"}:
            fieldNameList.append(field.name)

    arcpy.DeleteField_management("ParcelDBF_Join", fieldNameList)

    arcpy.FeatureClassToFeatureClass_conversion("ParcelDBF_Join", r'J:\common\PVA_SALES.gdb', 'RECENT_SALES')
    arcpy.DeleteField_management(r'J:\common\PVA_SALES.gdb\RECENT_SALES', ["Parcel_SHAPE_Length", "Parcel_SHAPE_Area"])
    arcpy.FeatureToPoint_management(r'J:\common\PVA_SALES.gdb\RECENT_SALES', r'J:\common\PVA_SALES.gdb\RECENT_SALES_POINTS')
    arcpy.DeleteField_management(r'J:\common\PVA_SALES.gdb\RECENT_SALES_POINTS', ["ORIG_FID"])

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
    print "Process completed"
    ScriptUtils.AddMsgAndPrint("\tProcess completed")

                                 


    

