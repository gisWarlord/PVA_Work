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
'     Usage:    SoilParcelOverlay <Block> <Lot> <Sublot> 
'                                 <Output Directory>
'---------------------------------------------------------------------
'   Returns:    PDFs of the soil map and report in the output directory
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  07/2019
'               Stan Shelton  -  07/2019
'                 Changed the code to call SoilParcelOverlay_ParcelID.py
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, time, traceback

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

def format_string(str):
    while len(str) < 4:
        str = "0" + str
    return str.upper()

try:
    block = format_string(block)
    lot = format_string(lot)
    sublot = format_string(sublot)
    parcelId = "{0}{1}{2}".format(block, lot, sublot)

    sys.path.append(r"J:\pva\Stan")
    # sys.path.append(r"V:\Stan")
    import SoilParcelOverlay_ParcelID
    SoilParcelOverlay_ParcelID.main(parcelId, outDir)

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
