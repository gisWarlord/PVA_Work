'''
'---------------------------------------------------------------------
'
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    PersonalPropPnts2Shp.py
'   Purpose:    Converts data in PersonalPropertyPoints.mxd to
'               individual shapefiles-->zip files for AGOL
'---------------------------------------------------------------------
'     Notes:    This script runs for 5 minutes.
'---------------------------------------------------------------------
'   History:    Stan Shelton - 01/2019
'               Stan Shelton - 02/2019
'                   Changed the data paths used to run from the
'                   overnight PC.
'---------------------------------------------------------------------
'''
# Import modules
import arcpy, sys, string, os, os.path, smtplib, traceback, time, glob
##from fnmatch import filter
from zipfile import *

# Import the script utilities
sys.path.append(r"X:\GIS_IT\GIS_DEPT\Tools\Scripts")
import ScriptUtils_pva as ScriptUtils

outputFolder = arcpy.GetParameterAsText(0)
if outputFolder == "#" or not outputFolder:
    outputFolder = r"X:\GIS_IT\GIS_DEPT\Tools\Scripts\UpdateLayers\AGOL"

# Local variables
msgTxt = ""
email1 = "pvagis@jeffersonpva.ky.gov"
toErrlst = ["gis@jeffersonpva.ky.gov"]
subjectFail = "PersonalPropPnts2Shp.py Error"

def zipDirectory(source, destination):
    '''Zip all shapefiles in the "source" directory individually'''
    try:
        #change the current directory
        os.chdir(source)
         
        #test current directory
        retval = os.getcwd()
         
        #list all files with extension .shp
        shps = glob.glob(source+"/*.shp")
         
        # create empty list for zipfile names
        ziplist = []
         
        # create destination directory if it does not exist
        if not os.path.exists(destination):
            os.makedirs(destination)
         
        #populate ziplist list of unique shapefile root names by finding all files with .shp extension and removing extension
        for name in shps:
            #retrieves just the files name for each name in shps
            file = os.path.basename(name)
            #removes .shp extension
            names = file[:-4]
            #adds each shapefile name to ziplist list
            ziplist.append(names)

        #creates zipefiles in destination folder with basenames
        for f in ziplist:
            #creates the name for each zipefile based on shapefile root names
            file_name = os.path.join(destination, f+".zip")
            #created the zipfiles with names defined above
            zips = ZipFile(file_name, "w")
            #files lists all files with the current basename (f) from ziplist
            files = glob.glob(str(f)+".*")
            # iterate through each basename and add all shapefile components to the zipefile
            for s in files:
                zips.write(s)
            zips.close()

            # now remove the shapefiles
            for d in files:
                os.remove(d)
        return None
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n\t{1}: {2}\n".format(tbinfo, str(sys.exc_info()[0]), str(sys.exc_info()[2]))
        gpmsg = "ARCPY ERRORS:\n{0}\n".format(arcpy.GetMessages(2))
        tmRun = time.strftime("%X", time.localtime())
        msgTxt += "\n\tScript error in zipDirectory at: {0}\n\n{1}{2}".format(tmRun, gpmsg, pymsg)
        ScriptUtils.AddMsgAndPrint(msgTxt, 2)

try:
    startTime = time.strftime("%X", time.localtime())
    ScriptUtils.AddMsgAndPrint("\n---\tStarting PersonalPropPnts2Shp.py at {0}\t---\n".format(startTime))
    
    # Local variables:
    folder = outputFolder
    mapDoc =   r"X:\GIS_IT\GIS_DEPT\Tools\Scripts\UpdateLayers\AGOL\PersonalPropertyPoints.mxd"
    shpFolder = outputFolder
    tmpFGDB = os.path.join(folder, "pppData.gdb")
    mxd = arcpy.mapping.MapDocument(mapDoc)
    deleteFGDB = False

    #  ************* Convert the layers in the MXD to shapefiles *************
    if not arcpy.Exists(tmpFGDB):
        arcpy.CreateFileGDB_management(shpFolder, "pppData.gdb", "CURRENT")
        deleteFGDB = True

    ScriptUtils.AddMsgAndPrint("\tExporting layers in {0} to {1}...".format(os.path.basename(mapDoc), tmpFGDB))
    for df in arcpy.mapping.ListDataFrames(mxd):
        for lyr in arcpy.mapping.ListLayers(mxd, "*", df):
            name = lyr.name
            # ScriptUtils.AddMsgAndPrint("\t\tExporting {0}...".format(name))
            tmpFC = os.path.join(tmpFGDB, name)
            if arcpy.Exists(tmpFC):
                arcpy.Delete_management(tmpFC)
            if lyr.isFeatureLayer:
                arcpy.FeatureClassToFeatureClass_conversion(lyr, tmpFGDB, name)

    # Create the output Shapefile
    ScriptUtils.AddMsgAndPrint("\tConverting data in {0} to shapefiles...".format(tmpFGDB))
    for dirpath, dirnames, filenames in arcpy.da.Walk(tmpFGDB, datatype="FeatureClass"):
        for filename in filenames:
            inFC = os.path.join(dirpath, filename)
            # ScriptUtils.AddMsgAndPrint("\t\tConverting {0} to shapefile...".format(inFC))
            outShp = os.path.join(shpFolder, "{0}.shp".format(filename))
            if arcpy.Exists(outShp):
                arcpy.Delete_management(outShp)
            arcpy.conversion.FeatureClassToShapefile(inFC, shpFolder)
    
    # Clean up the unneeded featureclasses
    for dirpath, dirnames, filenames in arcpy.da.Walk(tmpFGDB, datatype="FeatureClass"):
        for filename in filenames:
            inFC = os.path.join(dirpath, filename)
            arcpy.Delete_management(inFC)
    
    # ************* Start zipping the shapefiles *************
    zipD = os.path.join(folder, "zip")
    ScriptUtils.AddMsgAndPrint("\tCreating zip files in {0}...".format(zipD))
    zipDirectory(shpFolder, zipD)
    
    if deleteFGDB:
        arcpy.Delete_management(tmpFGDB)

    del mxd, tmpFGDB, shpFolder
except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n\t{1}: {2}\n".format(tbinfo, str(sys.exc_info()[0]), str(sys.exc_info()[2]))
    gpmsg = "ARCPY ERRORS:\n{0}\n".format(arcpy.GetMessages(2))
    tmRun = time.strftime("%X", time.localtime())
    msgTxt += "\n\tScript error at: {0}\n\n{1}{2}".format(tmRun, gpmsg, pymsg)
    ScriptUtils.SendEmail(email1, toErrlst, subjectFail, msgTxt)
    ScriptUtils.AddMsgAndPrint(msgTxt)
finally:
    endTime = time.strftime("%X", time.localtime())
    ScriptUtils.AddMsgAndPrint("\n---\tDone at {0}\t---".format(endTime))
