'''__________________________________________________________________
'
' Louisville/Jefferson County Information Consortium (LOJIC)
'____________________________________________________________________
'
'   Program:    ScriptUtils_pva.py
'   Purpose:    Script that contains re-useable modules
'____________________________________________________________________
'
' Arguments:    AddMsgAndPrint(msg, severity = 0)
'               CreateConnectionFile(username, password,
'                   version = "SDE.DEFAULT")
'               QueryRegistryKey(subKeyName, keyValue)
'               ReturnUserAndMachineNames()
'               ScriptPaths(scriptMode = 0)
'               SendEmail(From, Sendto, Subject, msg)
'               SetScriptMode(machine)
'____________________________________________________________________
'
'   History:    Stan Shelton - 08/2013
'               Stan Shelton - 11/2013
'                   - Changed the script name from sendEmail and added
'                     AddMsgAndPrint and CreateConnectionFile
'               Stan Shelton - 02/2014
'                   - Removed the extra print statement from 
'                     AddMsgAndPrint
'               Stan Shelton - 09/2015
'                   - Added QueryRegistryKey
'               Stan Shelton - 08/2016
'                   - Added ReturnUserAndMachineNames and changed 
'                     SendEmail to only work if ran from a
'                     production server
'               Stan Shelton - 12/2016
'                   - Added ScriptPaths and changed SendEmail to 
'                     also work on the Task servers
'               Stan Shelton - 02/2017
'                   - Added SetScriptMode
'               Stan Shelton - 06/2018
'                   - Changed SendEmail to utilize PVA's email system
'                     and changed the script name to ScriptUtils_pva.py
'               Stan Shelton - 02/2019
'                   - Changed the password used to send emails
'____________________________________________________________________
'''
import arcpy, sys, os, tempfile, os.path, traceback, string, smtplib, time, _winreg, getpass

def AddMsgAndPrint(msg, severity = 0):
    '''Adds a Message (in case this is run as a tool) and also prints the message to the screen (standard output)
    '''
    # Split the message on \n first, so that if it's multiple lines, 
    #  a GPMessage will be added for each line
    try:
        for string in msg.split('\n'):
            # Add appropriate geoprocessing message 
            #
            if severity == 0:
                arcpy.AddMessage(string)
            elif severity == 1:
                arcpy.AddWarning(string)
            elif severity == 2:
                arcpy.AddError(string)
    except:
        pass

def CreateConnectionFile(username, password, version = "SDE.DEFAULT"):
    '''Create an SDE connection in memory'''
    startTime = time.time()
    msgTxt = ""
    try:
        tempFolder = tempfile.gettempdir()
        fileName = "tempConnection.sde"
        connectionFile = os.path.join(tempFolder, fileName)
        serverName = "loicora1"
        serviceName = "sde:oracle11g:{0}".format(serverName)
        databaseName = ""
        authType = "DATABASE_AUTH"
        saveUserInfo = "SAVE_USERNAME"
        saveVersionInfo = "SAVE_VERSION"

        # Remove temporary connection file if it already exists
        if os.path.isfile(connectionFile):
            os.remove(connectionFile)

        # Create temporary connection file in memory
        if not os.path.isfile(connectionFile):
            arcpy.CreateArcSDEConnectionFile_management(tempFolder, fileName, serverName, serviceName, databaseName, authType, username, password, saveUserInfo, version, saveVersionInfo)     
        return connectionFile
    except:
        # Return any Python specific errors
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n    {1}: {2}\n".format(tbinfo, str(sys.exc_type), str(sys.exc_value))
        tmRun = time.strftime("%X", time.localtime())
        endTime = time.time()
        prodInfo = "\tScript errored after running for {0} seconds.".format(str(round((endTime - startTime))))
        msgTxt += "\n\n\tScript error at: {0}\n{1}\n\n{2}".format(tmRun, prodInfo, pymsg)
        AddMsgAndPrint(msgTxt, 2)

def QueryRegistryKey(subKeyName, keyValue):
    '''Returns the value from subKeyName/keyValue from HKEY_LOCAL_MACHINE
    '''
    regPath = r"SOFTWARE\Wow6432Node\LOJICReg"
    try:
        regConn = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
        registry_key = _winreg.OpenKey(regConn, regPath)
        asubkey = _winreg.OpenKey(registry_key, subKeyName)
        value, regtype = _winreg.QueryValueEx(asubkey, keyValue)
        _winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        AddMsgAndPrint("Unable to Connect to the Window Registry and read keys", 2)
        return None

def ReturnUserAndMachineNames():
    '''Returns the User Name (UserName) and Computer Name (Machine) of the current user.
    
    Return - dictionary["UserName", "Machine"]
    '''
    userName = getpass.getuser()
    hostName = os.environ['COMPUTERNAME']
    returnInfo = {}
    returnInfo["UserName"] = userName
    returnInfo["Machine"] = hostName
    return returnInfo

def ScriptPaths(scriptMode = 0):
    '''Sets the paths needed to for the different script levels (Production = 0, Test =  1, Development = 2).
    
    Return - dictionary["SupportPath", "DatabaseName", "Workspace"]
    '''
    path = r"\\pc.lojic.local\arcgisdesktop\10.2.1"
    ws = r"\\pc.lojic.local\home\libadm\SDEconnections"
    supportPath = ""
    dbName = "lojic"
    devDb = "dev"
    tstDb = "tst"
    prdDb = "ora1"
    supportPath = os.path.join(path, r"Production")
    workSpace = os.path.join(ws, "pl_")
    if scriptMode == 1:
        supportPath = os.path.join(path, r"Test")
        dbName += tstDb
        workSpace = os.path.join(ws, "t_")
    elif scriptMode == 2:
        supportPath = os.path.join(path, r"Development")
        dbName += devDb
        workSpace = os.path.join(ws, "d_")
    elif scriptMode == 3:
        dbName += prdDb
        workSpace = os.path.join(ws, "prodmnt_")
    else:
        dbName += prdDb

    returnInfo = {}
    returnInfo["SupportPath"] = supportPath
    returnInfo["DatabaseName"] = dbName
    returnInfo["Workspace"] = workSpace
    return returnInfo

def SetScriptMode(machine):
    '''Reads the machine that is passed in and adjust the script's mode accordingly
    '''
    mode = 0
    if machine.startswith("LCTX") and not machine.endswith("D") and not machine.endswith("T") or machine.find("TASK") != -1:
        mode = 0
    elif machine.startswith("LCTX") and machine.endswith("T"):
        mode = 1
    else:
        mode = 2
    return mode

def SendEmail(From, Sendto, Subject, msg):
    '''Uses smtplib.SMTP to send an email'''
    startTime = time.time()
    msgTxt = ""
    try:
        username = 'pvagis@jeffersonpva.ky.gov'
        password = 'St@rt!23'
        sender = From 
        headers = "From: {0}\r\nTo: {1}\r\nSubject: {2}\r\n\r\n".format(sender, Sendto, Subject)
        msg2 = headers + msg + "\n"
        # mserver = smtplib.SMTP('mailrelay')
        mserver = smtplib.SMTP('smtp.gmail.com:587')
        mserver.starttls()
        mserver.login(username,password)
        mserver.sendmail(sender, Sendto, msg2)
        mserver.quit()    
    except:
        # Return any Python specific errors
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\n  Traceback Info:\n{0}\n  Error Info:\n    {1}: {2}\n".format(tbinfo, str(sys.exc_type), str(sys.exc_value))
        tmRun = time.strftime("%X", time.localtime())
        endTime = time.time()
        prodInfo = "\tScript errored after running for {0} seconds.".format(str(round((endTime - startTime))))
        msgTxt += "\n\n\tScript error at: {0}\n{1}\n\n{2}".format(tmRun, prodInfo, pymsg)
        AddMsgAndPrint(msgTxt, 2)
