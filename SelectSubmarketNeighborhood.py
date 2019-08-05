# -*- coding: utf-8 -*-
'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    SelectSubmarketNeighborhood.py
'   Purpose:    Selects the Submarket then zooms to the area and
'               creates a map of the Neighborhoods.
'
'---------------------------------------------------------------------
'     Usage:    SelectSubmarketNeighborhood <Submarket> 
'                                           <Output Directory>
'---------------------------------------------------------------------
'   Returns:    PDF of the Submarket Neighborhoods map in the output
'               directory
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  07/2019
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env

# Import the script utilities
sPath = r"J:\pva\Toolboxes"
if not os.path.isdir(sPath):
    sPath = r"X:\GIS_IT\GIS_DEPT\Tools\Scripts"
sys.path.append(sPath)
import ScriptUtils_pva as ScriptUtils

# Script arguments
Submarket = arcpy.GetParameterAsText(0)
if Submarket == '#' or not Submarket:
    ScriptUtils.AddMsgAndPrint("Please enter a valid Submarket", 0)
    sys.exit(0)                                      # value needed

outDir = arcpy.GetParameterAsText(1)
if outDir == "#" or not outDir:
    ScriptUtils.AddMsgAndPrint("Please enter the output directory", 0)
    sys.exit(0)                                      # value needed

# Local variables
msgTxt = ""
startTime = time.time()

Submarket = Submarket.upper()
Expression = "SUBMARKET_NUMBER = '{0}'".format(Submarket)
Output_Map = "Submarket_{0}".format(Submarket)

# outDir = r"J:\pva\Stan"
Res_Neigh = r"J:\pva\PVA Library\PVA_Data.gdb\Residential\Residential_Neighborhoods"
Res_Neigh_Layer = "Res_Neigh_Layer"

try:
    # Process: Make Residential Neighborhoods Feature Layer
    ScriptUtils.AddMsgAndPrint("\tSelecting Residential Neighborhoods...", 0)
    arcpy.MakeFeatureLayer_management(Res_Neigh, Res_Neigh_Layer, Expression)

    result = arcpy.GetCount_management(Res_Neigh_Layer)
    if result.getOutput(0) == "0":
        ScriptUtils.AddMsgAndPrint("---\tNo Residential Neighborhoods Selected\t---", 0)
    else:
        # Update the MXD and export it to a PDF 
        mapOutput = os.path.join(outDir, Output_Map)
        ScriptUtils.AddMsgAndPrint("\tCreating {0}.pdf...".format(mapOutput), 0)
        if os.path.exists(mapOutput + ".pdf"):
            os.remove(mapOutput + ".pdf")
        # Get the MXD
        mxdPath = r"J:\pva\Stan\Neighborhood_Submarkets.mxd"
        mxd = arcpy.mapping.MapDocument(mxdPath)
        df = arcpy.mapping.ListDataFrames(mxd)[0]

        # Set the definition query of the "Residential_Neighborhoods" layer
        lyrRes_Neigh = arcpy.mapping.ListLayers(mxd, "Residential_Neighborhoods", df)[0]
        if lyrRes_Neigh.supports("DEFINITIONQUERY"):
            lyrRes_Neigh.definitionQuery = Expression

        # Set the map extent
        arcpy.SelectLayerByAttribute_management(lyrRes_Neigh, "NEW_SELECTION", Expression)
        df.extent = lyrRes_Neigh.getSelectedExtent()
        arcpy.SelectLayerByAttribute_management(lyrRes_Neigh, "CLEAR_SELECTION")
        df.scale = df.scale * 1.05                  # zoom out by 5%
   
        # Reset the symbology of the "Residential_Neighborhoods" layer
        if lyrRes_Neigh.symbologyType == "UNIQUE_VALUES":
            lyrRes_Neigh.symbology.valueField = "NEIGHBORHOOD_NAME"
            lyrRes_Neigh.symbology.addAllValues()

        # Turn on all of the layers in the MXD
        for lyr in arcpy.mapping.ListLayers(mxd, "*", df):
            lyr.visible = True
        arcpy.RefreshActiveView()
        # arcpy.RefreshTOC()

        # Change the layout title 
        for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
            if elm.name == "MapTitle":
                elm.text = "Submarket: {0}".format(Submarket)
        # Export the layout to a PDF
        arcpy.mapping.ExportToPDF(mxd, mapOutput)
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
