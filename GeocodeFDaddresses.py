'''-------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    GeocodeFDaddresses.py
'   Purpose:    Uses a Composite locator to geocode addresses that are
'               in the input table.
'
'---------------------------------------------------------------------
'   Returns:    H:\MotaxAddresses.dbf
'---------------------------------------------------------------------
'     Notes:    
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  06/2018
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path, datetime, glob
from arcpy import env

# Import the script that sends emails
# sys.path.append(r"X:\GIS_IT\GIS_DEPT\Tools\Scripts")
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

tblAddress = arcpy.GetParameterAsText(0)

# Local variables:
msgTxt = ""
startTime = time.time()
# workspace = r"H:\pvawork"
workspace = "H:\\"
outFDB = os.path.join(workspace, "PVA_Data.gdb")
tmpMotaxSub = os.path.join(outFDB, "tmpMotaxSub")
tmpMotaxGeocoded = os.path.join(outFDB, "tmpMotaxGeocoded")
tmpMotaxJoin1 = os.path.join(outFDB, "tmpMotaxJoin1")
tmpMotaxJoin2 = os.path.join(outFDB, "tmpMotaxJoin2")
output_MotaxAdds = os.path.join(workspace, "MotaxAddresses.dbf")
outAddressTable = os.path.join(outFDB, "Motax_Address")
outSample = os.path.join(outFDB, "FD_Addresses_Sample")
# locators = ["JeffAdds.loc", "JeffStreets.loc", "JeffNames.loc", "Jeff_Composite.loc"]
locators = ["JeffAdds.*", "JeffStreets.*", "JeffNames.*", "Jeff_Composite.*"]
inAddressTable = os.path.join(workspace, "moAddresses.xlsx")
if tblAddress != "":
    inAddressTable = tblAddress
tmpMotaxTab = inAddressTable
tmpMotaxView = "tmpMotaxView"
tmpMotaxView2 = "tmpMotaxView2"
Personal_Property_Taxing_Districts = r"J:\pva\PVA Library\PVA_Data.gdb\Personal_Property_Taxing_Districts"
PVA_Parcel = r"J:\pva\Toolboxes\MotaxData\pvastaff_connection.sde\PVA.Land\PVA.Parcel"
parcels = os.path.join(outFDB, "Parcels") 

dbfName = os.path.join(os.path.dirname(tmpMotaxTab), os.path.splitext(os.path.basename(tmpMotaxTab))[0] +  ".dbf")

def cleanup():
    '''
    Removes the temp files created by this proccess
    '''
    try:
        if arcpy.Exists(tmpMotaxSub):
            arcpy.Delete_management(tmpMotaxSub, "")
        if arcpy.Exists(tmpMotaxGeocoded):
            arcpy.Delete_management(tmpMotaxGeocoded, "")
        if arcpy.Exists(tmpMotaxJoin1):
            arcpy.Delete_management(tmpMotaxJoin1, "")
        if arcpy.Exists(tmpMotaxJoin2):
            arcpy.Delete_management(tmpMotaxJoin2, "")
        if arcpy.Exists(outAddressTable):
            arcpy.Delete_management(outAddressTable, "")
        if arcpy.Exists(outSample):
            arcpy.Delete_management(outSample, "")
        if arcpy.Exists(dbfName):
            arcpy.Delete_management(dbfName, "")
        if arcpy.Exists(parcels):
            arcpy.Delete_management(parcels, "")
        for loc in locators:
            locator = os.path.join(workspace, loc)
            for fname in glob.glob(locator):
                if os.path.exists(fname):
                    os.remove(fname)
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

def createLocator():
    '''
    Copies locators from \\lojic-files.msd.louky.local\Data\Locators that are needed to create a composite locator for Jefferson 
    County addresses. The locators needed to create the composite locator have to be accessible to this script.
    '''
    try:
        locPath = r"\\lojic-files.msd.louky.local\Data\Locators"
        JeffAdds = os.path.join(locPath, "JeffAdds")
        JeffStreets = os.path.join(locPath, "JeffStreets")
        JeffNames = os.path.join(locPath, "JeffNames")
        Jeff_Composite = os.path.join(workspace, "Jeff_Composite")
        JeffAdds_copy = os.path.join(workspace, "JeffAdds")
        JeffStreets_copy = os.path.join(workspace, "JeffStreets")
        JeffNames_copy = os.path.join(workspace, "JeffNames")
        inLocators = "{0} JeffAdds;{1} JeffStreets;{2} JeffNames".format(JeffAdds_copy, JeffStreets_copy, JeffNames_copy)
        inFieldMap = "Street \"Street or Intersection\" true true true 100 Text 0 0 ,First,#,{0},Street,0,0,{1},Street,0,0,{2},Street,0,0".format(JeffAdds_copy, JeffStreets_copy, JeffNames_copy)
        
        # Process: Copy JeffAdds
        ScriptUtils.AddMsgAndPrint("\tCopying address locators...", 0)
        arcpy.Copy_management(JeffAdds, JeffAdds_copy, "AddressLocator")

        # Process: Copy JeffStreets
        arcpy.Copy_management(JeffStreets, JeffStreets_copy, "AddressLocator")

        # Process: Copy JeffNames
        arcpy.Copy_management(JeffNames, JeffNames_copy, "AddressLocator")

        # Process: Create Composite Address Locator
        ScriptUtils.AddMsgAndPrint("\tCreating the composite address locator...", 0)
        arcpy.CreateCompositeAddressLocator_geocoding(inLocators, inFieldMap, "JeffAdds #;JeffStreets #;JeffNames #", Jeff_Composite)
        return Jeff_Composite
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
        return ""


try:
    # Make sure the output database exists before doing anything
    if not arcpy.Exists(outFDB):
        ScriptUtils.AddMsgAndPrint("\tCreating {0}...".format(outFDB), 0)
        # Execute CreateFileGDB
        out_name = os.path.basename(outFDB)
        arcpy.CreateFileGDB_management(workspace, out_name)

    # Perform some cleanup first
    ScriptUtils.AddMsgAndPrint("\tPreparing the workspace...", 0)
    if arcpy.Exists(output_MotaxAdds):
        arcpy.Delete_management(output_MotaxAdds, "")
    
    cleanup()
    
    locComposite = createLocator()
    
    # Process: Excel To Table
    ScriptUtils.AddMsgAndPrint("\tCreating a connection to {0}...".format(tblAddress), 0)
    arcpy.ExcelToTable_conversion(tblAddress, dbfName)
    
    # Process: Make Table View (2)
    expression = "\"State\" = 'KY'"
    arcpy.MakeTableView_management(dbfName, tmpMotaxView, expression)

    # Process: Copy Rows
    arcpy.CopyRows_management(tmpMotaxView, tmpMotaxSub, "")

    # Process: Geocode Addresses
    ScriptUtils.AddMsgAndPrint("\tGeocoding addresses...", 0)
    arcpy.GeocodeAddresses_geocoding(tmpMotaxSub, locComposite, "Street Address VISIBLE NONE", tmpMotaxGeocoded, "STATIC")
    
    # Process: Spatial Join
    ScriptUtils.AddMsgAndPrint("\tProcessing the first spatial join...", 0)
    arcpy.SpatialJoin_analysis(tmpMotaxGeocoded, Personal_Property_Taxing_Districts, tmpMotaxJoin1, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT", "", "")

    # Process: Copy (4)
    arcpy.Copy_management(PVA_Parcel, parcels, "FeatureClass")

    # Process: Spatial Join (2)
    ScriptUtils.AddMsgAndPrint("\tProcessing the second spatial join...", 0)
    arcpy.SpatialJoin_analysis(tmpMotaxJoin1, parcels, tmpMotaxJoin2, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT", "", "")
    
    # Process: Make Table View
    arcpy.MakeTableView_management(tmpMotaxJoin2, tmpMotaxView2)
    
    # Process: Create Table
    template = r"J:\pva\Toolboxes\MotaxData\Date.gdb\FD_Addresses"
    ScriptUtils.AddMsgAndPrint("\tCreating the output table {0}...".format(outAddressTable), 0)
    arcpy.CreateTable_management(outFDB, os.path.basename(outAddressTable), template)

    # Process: Add Field
    arcpy.AddField_management(outAddressTable, "VIN_Num", "TEXT", "", "", "", "VIN", "NULLABLE", "NON_REQUIRED", "")
    
    # Process: Delete Field
    arcpy.DeleteField_management(outAddressTable, "HOUSENO;HAFHOUSE;APT;DIR;STRNAME;TYPE_")

    # Process: Append
    ScriptUtils.AddMsgAndPrint("\tAppending data...", 0)
    fieldMapping = "FULL_ADDRE \"FULL_ADDRE\" true true false 255 Text 0 0 ,First,#,tmpMotaxJoin2_View,Address,-1,-1;PARCELID \"PARCELID\" true true false 255 Text 0 0 ,First,#,tmpMotaxJoin2_View,PARCELID,-1,-1;LRSN \"LRSN\" true true false 8 Double 0 0 ,First,#,tmpMotaxJoin2_View,LRSN,-1,-1;ZIPCODE \"ZIPCODE\" true true false 255 Text 0 0 ,First,#,tmpMotaxJoin2_View,ZIP,-1,-1;MUNI_NAME \"MUNI_NAME\" true true false 255 Text 0 0 ,First,#,tmpMotaxJoin2_View,MUNI_NAME,-1,-1;STATE \"STATE\" true true false 255 Text 0 0 ,First,#,tmpMotaxJoin2_View,State,-1,-1;JCFD_DIST \"JCFD_DIST\" true true false 255 Text 0 0 ,First,#,tmpMotaxJoin2_View,JCFD_DIST,-1,-1;JCFDTAXNUM \"JCFDTAXNUM\" true true false 255 Text 0 0 ,First,#,tmpMotaxJoin2_View,JCFDTAXNUM,-1,-1;VIN_Num \"VIN\" true true false 255 Text 0 0 ,First,#,tmpMotaxJoin2_View,VIN_Num,-1,-1"
    arcpy.Append_management(tmpMotaxView2, outAddressTable, "NO_TEST", fieldMapping, "")

    # Process: Table to Table
    arcpy.TableToTable_conversion(outAddressTable, workspace, os.path.basename(output_MotaxAdds), "LRSN IS NOT NULL")           
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
