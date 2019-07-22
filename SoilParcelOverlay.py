# -*- coding: utf-8 -*-
'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    SoilParcelOverlay.py
'   Purpose:    Uses the input Parcel Id to create a soil overlay map
'               and report for farm assessments.
'
'---------------------------------------------------------------------
'     Usage:    SoilParcelOverlay <Block> <Lot> <Sublot> <Output 
'                                 Directory>
'---------------------------------------------------------------------
'   Returns:    PDFs of the soil map and report in the output directory
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  07/2019
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path

# Import the script utilities
sPath = r"J:\pva\Toolboxes"
sys.path.append(sPath)
import ScriptUtils_pva as ScriptUtils

# Script arguments
block = arcpy.GetParameterAsText(0)
if block == '#' or not block or len(block) > 4:
    ScriptUtils.AddMsgAndPrint("\t--\tPlease enter a valid Block\t--", 0)
    sys.exit(0)                                      # value needed

lot = arcpy.GetParameterAsText(1)
if lot == '#' or not lot or len(lot) > 4:
    ScriptUtils.AddMsgAndPrint("\t--\tPlease enter a valid Lot\t--", 0)
    sys.exit(0)                                      # value needed

sublot = arcpy.GetParameterAsText(2)
if sublot == '#' or not sublot or len(sublot) > 4:
    ScriptUtils.AddMsgAndPrint("\t--\tPlease enter a valid Sublot\t--", 0)
    sys.exit(0)                                      # value needed

outDir = arcpy.GetParameterAsText(3)
if outDir == "#" or not outDir:
    ScriptUtils.AddMsgAndPrint("\t--\tPlease select an output directory\t--", 0)
    sys.exit(0)                                      # value needed

# Local variables
msgTxt = ""
startTime = time.time()

def cleanup():
    '''
    Removes the temp files created by this proccess
    '''
    try:
        if arcpy.Exists(parcelSoil_Intersect):
            arcpy.Delete_management(parcelSoil_Intersect, "")
        if arcpy.Exists(parcelSoil_Dissolve):
            arcpy.Delete_management(parcelSoil_Dissolve, "")
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

def format_string(str):
    while len(str) < 4:
        str = "0" + str
    return str.upper()

try:
    block = format_string(block)
    lot = format_string(lot)
    sublot = format_string(sublot)
    outTmpName = "{0}-{1}-{2}".format(block, lot, sublot)
    outMapName =  os.path.join(outDir, outTmpName + "_Map")
    outRptName =  os.path.join(outDir, outTmpName + "_Report")

    parcelId = "{0}{1}{2}".format(block, lot, sublot)
    Expression = "PARCELID = '{0}'".format(parcelId)
    wkDir = r"J:\pva\Stan"
    dbConnection = os.path.join(wkDir, "pvastaff_connection.sde")
    jeflib_soils = os.path.join(dbConnection, "jeflib.soils")
    pva_parcel = os.path.join(dbConnection, "PVA.Land", "PVA.Parcel")
    Site_Addresses = os.path.join(dbConnection, "address.address", "ADDRESS.addresssite")
    lyrParcel = "parcel_Layer"
    lyrParcelSelected = "Parcel_Selected"
    lyrSoils = "lyrSoils"
    lyrAddresses = "siteAddesses"

    mxdPath = os.path.join(wkDir, "FarmTemplate.mxd")
    mxdPathRpt = os.path.join(wkDir, "FarmReportTemplate.mxd")
    parcelSoil_Intersect =  os.path.join(wkDir, "PVA_Tst.gdb", "tmp_Intersect")
    parcelSoil_Dissolve = os.path.join(wkDir, "PVA_Tst.gdb", "tmp_Dissolve")

    cleanup()

    # Get the fields from the input Address Points
    arcpy.MakeFeatureLayer_management(pva_parcel,  lyrParcel)
    fields= arcpy.ListFields(lyrParcel)

    # Create a fieldinfo object
    fieldInfo = arcpy.FieldInfo()
    lstFields = ["PARCELID", "BLOCK", "LOT", "SUBLOT"]
    # Iterate through the fields and set them to fieldinfo
    for field in fields:
        name = field.name
        if name in lstFields:
            fieldInfo.addField(name, name, "VISIBLE", "")
        else:
            fieldInfo.addField(name, name, "HIDDEN", "")

    # Process: Make Feature Layer of Parcel REMF Master
    ScriptUtils.AddMsgAndPrint("\tSelecting the parcel...", 0)
    arcpy.MakeFeatureLayer_management(lyrParcel, lyrParcelSelected, Expression, "", fieldInfo)
    count = int(arcpy.GetCount_management(lyrParcelSelected)[0])
    # ---------------------- only process the request if a parcel was found ----------------------
    if count > 0:
        # Process: Make Feature Layer of jeflib.soils
        arcpy.MakeFeatureLayer_management(jeflib_soils, lyrSoils)

        # Process: Make Feature Layer of Site Addresses
        arcpy.MakeFeatureLayer_management(Site_Addresses, lyrAddresses)

        # Process: Select Site Addresses By Location
        arcpy.SelectLayerByLocation_management(lyrAddresses, "INTERSECT", lyrParcelSelected, "", "NEW_SELECTION")

        # Get the address of the selected parcel
        matchcount = int(arcpy.GetCount_management(lyrAddresses)[0]) 
        address = ""
        if matchcount == 1:
            fields = ["HOUSENO", "DIR", "STRNAME", "TYPE"]
            with arcpy.da.SearchCursor(lyrAddresses, fields) as cursor:
                for row in cursor:
                    address += str(row[0]) + " " + "{0} {1} {2}".format(row[1], row[2], row[3]).strip()
        elif matchcount > 1:
            address += "Multiple Addresses"
        else:
            address += "None"

        # Process: Intersect
        ScriptUtils.AddMsgAndPrint("\tIntersecting with soils...", 0)
        inFeatures = [lyrParcelSelected, lyrSoils]
        arcpy.Intersect_analysis(inFeatures, parcelSoil_Intersect, "ALL")

        # Process: Dissolve 
        ScriptUtils.AddMsgAndPrint("\tDissolving data...", 0)
        dissolveFields = ["SOIL_CLASS", "SOIL_CAP"]
        arcpy.Dissolve_management(parcelSoil_Intersect, parcelSoil_Dissolve, dissolveFields, "SHAPE_Area SUM", "MULTI_PART", "DISSOLVE_LINES")

        # Process: Calculate Field
        ScriptUtils.AddMsgAndPrint("\tCalculating the acres...", 0)
        arcpy.CalculateField_management(parcelSoil_Dissolve, "SUM_SHAPE_Area", "round(!SHAPE_Area! / 43560, 2)", "PYTHON", "")

        # Get the total area in acres
        fldValue = 0
        fields = ['SUM_SHAPE_Area']
        with arcpy.da.SearchCursor(parcelSoil_Dissolve, fields) as cur:
            for row in cur:
                fldValue += row[0]

        # --------------------------- Create the report ---------------------------
        ScriptUtils.AddMsgAndPrint("\tCreating the report...", 0)
        rptClass = ""
        rptCap = ""
        rptArea = ""
        rptPercent = ""
        fields = ['SOIL_CLASS', 'SOIL_CAP', 'SUM_SHAPE_Area']
        with arcpy.da.SearchCursor(parcelSoil_Dissolve, fields) as cursor:
            for row in cursor:
                tmpValue = round((row[2] / fldValue) * 100, 2)
                rptClass += "{0}\n".format(row[0])
                rptCap += "{0}\n".format(row[1])
                rptArea += "{0}\n".format(row[2])
                rptPercent += "{0}\n".format(tmpValue)
                
        underscore = "______"
        rptArea += "\n{0}\n{1}\n".format(underscore, fldValue)
        rptPercent += "\n{0}\n{1}\n".format(underscore, "100")
        mxdReport = arcpy.mapping.MapDocument(mxdPathRpt)
    
        # Update the text elements (Address, Block Lot, Sublot)    
        for elm in arcpy.mapping.ListLayoutElements(mxdReport, "TEXT_ELEMENT"):
            if elm.name == "parcelID":
                elm.text = parcelId
            if elm.name == "reportClass":
                elm.text = rptClass
            if elm.name == "reportCap":
                elm.text = rptCap 
            if elm.name == "reportArea":
                elm.text = rptArea
            if elm.name == "reportPercent":
                elm.text = rptPercent

        # Export the Report layout to a PDF
        outReport = "{0}.pdf".format(outRptName)
        if os.path.exists(outReport):
            os.remove(outReport)
        arcpy.mapping.ExportToPDF(mxdReport, outRptName)
        
        # --------------------------- Create the map ---------------------------
        # Open the MXD and set the map extent
        ScriptUtils.AddMsgAndPrint("\tCreating the map...", 0)
        mxd = arcpy.mapping.MapDocument(mxdPath)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        desc = arcpy.Describe(parcelSoil_Dissolve)
        extent = desc.Extent
        df.extent = extent
        df.scale = df.scale * 1.1                  # zoom out by 10%
        
        # Set the definition query for the layer "Parcel Soil" to the data expression above
        lyr = arcpy.mapping.ListLayers(mxd, "Parcel Soil", df)[0]
        if lyr.supports("DEFINITIONQUERY"):
            lyr.definitionQuery = Expression
        
        # Update the text elements (Address, Block Lot, Sublot)    
        for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
            if elm.name == "propAddress":
                elm.text = address.title()        # Change text to title case
            if elm.name == "propBlock":
                elm.text = block 
            if elm.name == "propLot":
                elm.text = lot
            if elm.name == "propSublot":
                elm.text = sublot

        # Export the layout to a PDF
        outFileName = "{0}.pdf".format(outMapName)
        if os.path.exists(outFileName):
            os.remove(outFileName)
        arcpy.mapping.ExportToPDF(mxd, outMapName)
    else:   # --------------------- inform the user that no parcel was found ---------------------
        msgTxt += "\t--\tNo Parcel found with the ID of '{0}'\t--".format(parcelId)
        ScriptUtils.AddMsgAndPrint(msgTxt, 2)
    cleanup()
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
