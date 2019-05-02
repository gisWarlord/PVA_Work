'''
'---------------------------------------------------------------------
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    MakeVehicleRoutingProblemLayer_Workflow.py
'   Purpose:    Creates a Vehicle Routing Problem (VRP) layer, adds
'               the orders, depots and routes. Then it will solve the
'               VRP and save the resulting routes as a layer file.
'
'---------------------------------------------------------------------
'     Usage:    MakeVehicleRoutingProblemLayer_Workflow
'               <Order Points Shapefile> <Depot Points> <Routes>
'---------------------------------------------------------------------
'   Returns:    <Order Points Shapefile>_Routes.lyr
'---------------------------------------------------------------------
'   History:    Stan Shelton  -  03/2019
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, smtplib, time, traceback, os.path, datetime
from arcpy import env

# Import the script utilities
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

def main(inOrders, inDepots, inRoutes):
    # Local variables
    msgTxt = ""
    startTime = time.time()
    workingDir = os.path.dirname(inOrders)

    try:
        # Check out the Network Analyst extension license
        arcpy.CheckOutExtension("Network")

        #Set environment settings
        env.workspace = workingDir
        env.overwriteOutput = True

        # Set script variables
        networkGDB = r"J:\pva\PVA_Routing\Routing Geodatabase.gdb"
        inNetworkDataset = os.path.join(networkGDB, "Network_Dataset", "Network_Dataset_ND")
        fileName, fileExt = os.path.splitext(os.path.basename(inOrders))
        outNALayerName = "{0}_Routes".format(fileName)
        impedanceAttribute = "DriveTime"
        distanceAttribute = "Miles"
        timeUntis = "Minutes"
        distanceUntis = "Miles"
        outLayerFile = os.path.join(workingDir, "{0}.lyr".format(outNALayerName))
        d = datetime.datetime.today()
        today = d.strftime('%m/%d/%Y')

        ScriptUtils.AddMsgAndPrint("\tCreating a new Vehicle Routing Problem...", 0)

        # Create the VRP layer
        outNALayer = arcpy.na.MakeVehicleRoutingProblemLayer(inNetworkDataset,
                                                                outNALayerName,
                                                                impedanceAttribute,
                                                                "Distance",
                                                                timeUntis,
                                                                distanceUntis,
                                                                "#", "#",
                                                                "Medium", "Medium",
                                                                "ALLOW_UTURNS",
                                                                "Oneway;RestrictedTurns",
                                                                "NO_HIERARCHY", "#",
                                                                "TRUE_LINES_WITH_MEASURES")

        ScriptUtils.AddMsgAndPrint("\tAdding Locations...", 0)

        # Get the layer object from the result object. The VRP layer can now be
        # referenced using the layer object.
        outNALayer = outNALayer.getOutput(0)

        #Get the names of all the sublayers within the VRP layer.
        subLayerNames = arcpy.na.GetNAClassNames(outNALayer)
        #Stores the layer names that we will use later
        ordersLayerName = subLayerNames["Orders"]
        depotsLayerName = subLayerNames["Depots"]
        routesLayerName = subLayerNames["Routes"]


        # Add Depots to the VRP
        arcpy.na.AddLocations(outNALayer, depotsLayerName, inDepots,
                              "Name Name #;Description Description #;TimeWindowStart1 TimeWindowStart1 #;TimeWindowEnd1 TimeWindowEnd1 #;TimeWindowStart2 TimeWindowStart2 #;TimeWindowEnd2 TimeWindowEnd2 #;CurbApproach CurbApproach 0",
                              "5000 Meters",
                              "Name",
                              "StreetCenterlines SHAPE;Network_Dataset_ND_Junctions NONE",
                              "MATCH_TO_CLOSEST",
                              "APPEND",
                              "NO_SNAP",
                              "5 Meters",
                              "INCLUDE",
                              "StreetCenterlines #;Network_Dataset_ND_Junctions #")

        # Add Orders to the VRP
        arcpy.na.AddLocations(outNALayer, ordersLayerName, inOrders,
                              "ServiceTime TIME #;Name FULL_ADD #",
                              "5000 Meters","PARCELID",
                              "StreetCenterlines SHAPE;Network_Dataset_ND_Junctions NONE",
                              "MATCH_TO_CLOSEST",
                              "APPEND",
                              "NO_SNAP",
                              "5 Meters",
                              "INCLUDE",
                              "StreetCenterlines #;Network_Dataset_ND_Junctions #")

        # Add Routes to the VRP
        arcpy.na.AddLocations(outNALayer, routesLayerName, inRoutes,
                              "Name Name #;Description Description #;StartDepotName StartDepotName #;EndDepotName EndDepotName #;StartDepotServiceTime StartDepotServiceTime #;EndDepotServiceTime EndDepotServiceTime #;EarliestStartTime EarliestStartTime '7:30:00 AM';LatestStartTime LatestStartTime '7:30:00 AM';ArriveDepartDelay ArriveDepartDelay #;Capacities Capacities #;FixedCost FixedCost #;CostPerUnitTime CostPerUnitTime 1;CostPerUnitDistance CostPerUnitDistance #;OvertimeStartTime OvertimeStartTime #;CostPerUnitOvertime CostPerUnitOvertime #;MaxOrderCount MaxOrderCount 25;MaxTotalTime MaxTotalTime 480;MaxTotalTravelTime MaxTotalTravelTime #;MaxTotalDistance MaxTotalDistance #;SpecialtyNames SpecialtyNames #;AssignmentRule AssignmentRule 1",
                              "5000 Meters",
                              "Name",
                              "StreetCenterlines SHAPE;Network_Dataset_ND_Junctions NONE",
                              "MATCH_TO_CLOSEST",
                              "APPEND",
                              "NO_SNAP",
                              "5 Meters",
                              "INCLUDE",
                              "StreetCenterlines #;Network_Dataset_ND_Junctions #")

        ScriptUtils.AddMsgAndPrint("\tSolving...", 0)

        # Solve the VRP layer
        arcpy.na.Solve(outNALayer)

        ScriptUtils.AddMsgAndPrint("\tSaving the routes as {0}...".format(outLayerFile), 0)

        #Save the solved VRP layer as a layer file on disk with relative paths
        arcpy.management.SaveToLayerFile(outNALayer, outLayerFile, "RELATIVE")

        # ScriptUtils.AddMsgAndPrint("\t--\tScript completed successfully\t--", 0)
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

if __name__ == "__main__":
    orders = sys.argv[1]
    if orders == "#" or not orders:
        ScriptUtils.AddMsgAndPrint("Please enter the Orders shapefile", 0)
        sys.exit()                                      # value needed

    depots = sys.argv[2]
    if depots == "#" or not depots:
        ScriptUtils.AddMsgAndPrint("Please enter the Depots to be used", 0)
        sys.exit()                                      # value needed

    routes = sys.argv[3]
    if routes == '#' or not routes:
        ScriptUtils.AddMsgAndPrint("Please enter the default Routes", 0)
        sys.exit()                                      # value needed

    main(orders, depots, routes)
