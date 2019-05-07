'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    RoutingTableExport.py
'   Purpose:    Joins the input Routing table to the "Orders" from
'               the Vehicle Routing Problem and calculates the Order__
'               field. Then the table is exported to an Excel table.
'
'---------------------------------------------------------------------
'     Usage:    RoutingTableExport <Route Table> <Output Directory>
'---------------------------------------------------------------------
'     Notes:    Run this script from the Map document that was used
'               to create the routes.
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  01/2019
'               Stan Shelton  -  04/2019
'                   Changed the messages returned if the needed
'                   variables are not entered.
'               Stan Shelton  -  05/2019
'                   Added code to clear the definition Queries of
'                   the Orders & Routes layers.
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path
from arcpy import env

# Import the script utilities
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

# Local variables
msgTxt = ""
startTime = time.time()

Routing_Input_Table = arcpy.GetParameterAsText(0)
if Routing_Input_Table == "#" or not Routing_Input_Table:
    ScriptUtils.AddMsgAndPrint("Please select the Routing Table", 0)
    sys.exit()                                      # value needed

outDir = arcpy.GetParameterAsText(1)
if outDir == "#" or not outDir:
    ScriptUtils.AddMsgAndPrint("Please select the output directory", 0)
    sys.exit()                                      # value needed

Orders = arcpy.GetParameterAsText(2)
if Orders == "#" or not Orders:
    ScriptUtils.AddMsgAndPrint("Please select the Orders from the Vehicle Routing Problem layer", 0)
    sys.exit()                                      # value needed

Routing_Input_Table_View = "Routing_Input_Table_View"

try:
    mxd = arcpy.mapping.MapDocument("CURRENT")

    # Clear the definition Queries of the Orders & Routes layers
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.name == "Orders":
            lyr.definitionQuery = ""
        elif lyr.name == "Routes":
            lyr.definitionQuery = ""

    ScriptUtils.AddMsgAndPrint("\tJoining {0} to {1}...".format(Routing_Input_Table, Orders), 0)
    # Process: Make Table View
    arcpy.MakeTableView_management(Routing_Input_Table, Routing_Input_Table_View)

    # Process: Add Join
    arcpy.AddJoin_management(Routing_Input_Table_View, "FULL_ADD", Orders, "Name", "KEEP_ALL")

    # Process: Calculate Field
    ScriptUtils.AddMsgAndPrint("\tCalculating the \"Order__\" field...", 0)
    fldName = "{0}.Order__".format(os.path.basename(Routing_Input_Table))
    arcpy.CalculateField_management(Routing_Input_Table_View, fldName, "[Orders.RouteName] + [Orders.Sequence]", "VB", "")

    # Process: Remove Join
    arcpy.RemoveJoin_management(Routing_Input_Table_View, "")

    # Process: Table To Excel
    Routing_Output_Table = os.path.join(outDir, "{0}_Output.xls".format(os.path.basename(Routing_Input_Table)))
    ScriptUtils.AddMsgAndPrint("\tCreating the output table {0}...".format(Routing_Output_Table), 0)
    arcpy.TableToExcel_conversion(Routing_Input_Table_View, Routing_Output_Table)
    # arcpy.TableToTable_conversion()
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
