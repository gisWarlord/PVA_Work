'''
'---------------------------------------------------------------------
'
' Jefferson County Property Valuation Administrator (PVA)
'---------------------------------------------------------------------
'
'   Program:    PersonalPropPntsUpload.py
'   Purpose:    Publishes shapefiles saved inside zip files to AGOL
'---------------------------------------------------------------------
'   History:    Stan Shelton - 01/17/2019
'---------------------------------------------------------------------
'''
import arcpy, sys, string, os, os.path, smtplib, traceback, time
from arcgis.gis import *
from fnmatch import filter

# Import the script utilities
sys.path.append(r"J:\pva\Toolboxes")
import ScriptUtils_pva as ScriptUtils

# Local variables
msgTxt = ""

try:
    startTime = time.strftime("%X", time.localtime())
    ScriptUtils.AddMsgAndPrint("---\tStarted at {0}\t---\n".format(startTime))
    
    # Local variables
    url = "https://lojic.maps.arcgis.com"
    username = "jeffersonpva"
    pass1 = "St@rt!23"

    gis = GIS(url, username, pass1)

    # Change the path to the zip files as needed
    zipDir = r"J:\pva\Toolboxes\PersonalProperty\zip"
    # zipDir = r"V:\Stan\Data\zip"
    msgTxt = ""
    count = 0
    xcount = 0
    for fldPath, fldName, files in os.walk(zipDir):
        validFlds = filter(files, "*.zip")
        msgTxt += "Total number of zip files found: {0}\n".format(str(len(validFlds)))

        for f in validFlds:
            fPath = os.path.join(fldPath, f)
            fName = f[:-4]
            # Split the zip file name based on capital letters and return a readable string
            query = "{0} AND owner: {1}".format(re.sub(r'([^A-Z])([A-Z])', r'\1 \2', fName), username)
            search_result = gis.content.search(query, "Shapefile")
            if len(search_result) == 1:
                item = search_result[0]
##                item.update(data=fPath)
                count += 1
            elif len(search_result) == 0:
                # if the search above didn't find anything re-query using the zip file's base name
                qry = "{0} AND owner: {1}".format(fName, username)
                result = gis.content.search(qry, "Shapefile")
                if len(result) == 1:
                    item = result[0]
##                    item.update(data=fPath)
                    count += 1
                else:
                    xcount += 1
                    msgTxt += "\t{0}\t- Query String: {1}\n".format(f, qry)
                    msgTxt += "\t    Number of records returned: {0}\n".format(str(len(result)))
                    for item in result:
                        msgTxt += "\t\t{0}\n".format(item.name)
            elif len(search_result) > 1:
                for item in search_result:
                    if item.name == f:
##                        item.update(data=fPath)
                        count += 1
                        break
            else:
                xcount += 1
                msgTxt += "\t{0}\t- Query String: {1}\n".format(f, query)
                msgTxt += "\t    Number of records returned: {0}\n".format(str(len(search_result)))
                for item in search_result:
                    msgTxt += "\t\t{0}\n".format(item.title)

    if xcount > 0:
        msgTxt += "    Updated {0} items\n\n    {1} items not updated:\n{2}".format(str(count), str(xcount), msgTxt)
    else:
        msgTxt += "    Updated {0} items".format(str(count))
    ScriptUtils.AddMsgAndPrint(msgTxt, 0)
except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n\t{1}: {2}\n".format(tbinfo, str(sys.exc_info()[0]), str(sys.exc_info()[2]))
    gpmsg = "ARCPY ERRORS:\n{0}\n".format(arcpy.GetMessages(2))
    tmRun = time.strftime("%X", time.localtime())
    msgTxt += "\n\tScript error at: {0}\n\n{1}{2}".format(tmRun, gpmsg, pymsg)
    ScriptUtils.AddMsgAndPrint(msgTxt, 2)
finally:
    endTime = time.strftime("%X", time.localtime())
    ScriptUtils.AddMsgAndPrint("\n---\tDone at {0}\t---".format(endTime))
