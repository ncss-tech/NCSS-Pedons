#-------------------------------------------------------------------------------
# Name:        NASISpedons_Extract_ALL_Pedons_from_NASIS.py
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Author: Jason.Nemecek
# e-mail: jason.nemecek@wi.usda.gov
# phone: 608.662.4422 ext. 190
#
# Created:     7/04/2016
# Last Modified: 5/18/2017

#-------------------------------------------------------------------------------

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print msg

        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError("\n" + msg)

    except:
        pass

## ===================================================================================
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

### ===================================================================================
def setScratchWorkspace():
    """ This function will set the scratchWorkspace for the interim of the execution
        of this tool.  The scratchWorkspace is used to set the scratchGDB which is
        where all of the temporary files will be written to.  The path of the user-defined
        scratchWorkspace will be compared to existing paths from the user's system
        variables.  If there is any overlap in directories the scratchWorkspace will
        be set to C:\TEMP, assuming C:\ is the system drive.  If all else fails then
        the packageWorkspace Environment will be set as the scratchWorkspace. This
        function returns the scratchGDB environment which is set upon setting the scratchWorkspace"""

    try:
        AddMsgAndPrint("\nSetting Scratch Workspace")
        scratchWK = arcpy.env.scratchWorkspace

        # -----------------------------------------------
        # Scratch Workspace is defined by user or default is set
        if scratchWK is not None:

            # dictionary of system environmental variables
            envVariables = os.environ

            # get the root system drive
            if envVariables.has_key('SYSTEMDRIVE'):
                sysDrive = envVariables['SYSTEMDRIVE']
            else:
                sysDrive = None

            varsToSearch = ['ESRI_OS_DATADIR_LOCAL_DONOTUSE','ESRI_OS_DIR_DONOTUSE','ESRI_OS_DATADIR_MYDOCUMENTS_DONOTUSE',
                            'ESRI_OS_DATADIR_ROAMING_DONOTUSE','TEMP','LOCALAPPDATA','PROGRAMW6432','COMMONPROGRAMFILES','APPDATA',
                            'USERPROFILE','PUBLIC','SYSTEMROOT','PROGRAMFILES','COMMONPROGRAMFILES(X86)','ALLUSERSPROFILE']

            """ This is a printout of my system environmmental variables - Windows 7
            -----------------------------------------------------------------------------------------
            ESRI_OS_DATADIR_LOCAL_DONOTUSE C:\Users\adolfo.diaz\AppData\Local\
            ESRI_OS_DIR_DONOTUSE C:\Users\ADOLFO~1.DIA\AppData\Local\Temp\6\arc3765\
            ESRI_OS_DATADIR_MYDOCUMENTS_DONOTUSE C:\Users\adolfo.diaz\Documents\
            ESRI_OS_DATADIR_COMMON_DONOTUSE C:\ProgramData\
            ESRI_OS_DATADIR_ROAMING_DONOTUSE C:\Users\adolfo.diaz\AppData\Roaming\
            TEMP C:\Users\ADOLFO~1.DIA\AppData\Local\Temp\6\arc3765\
            LOCALAPPDATA C:\Users\adolfo.diaz\AppData\Local
            PROGRAMW6432 C:\Program Files
            COMMONPROGRAMFILES :  C:\Program Files (x86)\Common Files
            APPDATA C:\Users\adolfo.diaz\AppData\Roaming
            USERPROFILE C:\Users\adolfo.diaz
            PUBLIC C:\Users\Public
            SYSTEMROOT :  C:\Windows
            PROGRAMFILES :  C:\Program Files (x86)
            COMMONPROGRAMFILES(X86) :  C:\Program Files (x86)\Common Files
            ALLUSERSPROFILE :  C:\ProgramData
            ------------------------------------------------------------------------------------------"""

            bSetTempWorkSpace = False

            """ Iterate through each Environmental variable; If the variable is within the 'varsToSearch' list
                list above then check their value against the user-set scratch workspace.  If they have anything
                in common then switch the workspace to something local  """
            for var in envVariables:

                if not var in varsToSearch:
                    continue

                # make a list from the scratch and environmental paths
                varValueList = (envVariables[var].lower()).split(os.sep)          # ['C:', 'Users', 'adolfo.diaz', 'AppData', 'Local']
                scratchWSList = (scratchWK.lower()).split(os.sep)                 # [u'C:', u'Users', u'adolfo.diaz', u'Documents', u'ArcGIS', u'Default.gdb', u'']

                # remove any blanks items from lists
                if '' in varValueList: varValueList.remove('')
                if '' in scratchWSList: scratchWSList.remove('')

                # First element is the drive letter; remove it if they are
                # the same otherwise review the next variable.
                if varValueList[0] == scratchWSList[0]:
                    scratchWSList.remove(scratchWSList[0])
                    varValueList.remove(varValueList[0])

                # obtain a similarity ratio between the 2 lists above
                #sM = SequenceMatcher(None,varValueList,scratchWSList)

                # Compare the values of 2 lists; order is significant
                common = [i for i, j in zip(varValueList, scratchWSList) if i == j]

                if len(common) > 0:
                    bSetTempWorkSpace = True
                    break

            # The current scratch workspace shares 1 or more directory paths with the
            # system env variables.  Create a temp folder at root
            if bSetTempWorkSpace:
                AddMsgAndPrint("\tCurrent Workspace: " + scratchWK,0)

                if sysDrive:
                    tempFolder = sysDrive + os.sep + "TEMP"

                    if not os.path.exists(tempFolder):
                        os.makedirs(tempFolder,mode=777)

                    arcpy.env.scratchWorkspace = tempFolder
                    AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                else:
                    packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                    if arcpy.env[packageWS[0]]:
                        arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                        AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)
                    else:
                        AddMsgAndPrint("\tCould not set any scratch workspace",2)
                        return False

            # user-set workspace does not violate system paths; Check for read/write
            # permissions; if write permissions are denied then set workspace to TEMP folder
            else:
                arcpy.env.scratchWorkspace = scratchWK

                if arcpy.env.scratchGDB == None:
                    AddMsgAndPrint("\tCurrent scratch workspace: " + scratchWK + " is READ only!",0)

                    if sysDrive:
                        tempFolder = sysDrive + os.sep + "TEMP"

                        if not os.path.exists(tempFolder):
                            os.makedirs(tempFolder,mode=777)

                        arcpy.env.scratchWorkspace = tempFolder
                        AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                    else:
                        packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                        if arcpy.env[packageWS[0]]:
                            arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                            AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                        else:
                            AddMsgAndPrint("\tCould not set any scratch workspace",2)
                            return False

                else:
                    AddMsgAndPrint("\tUser-defined scratch workspace is set to: "  + arcpy.env.scratchGDB,0)

        # No workspace set (Very odd that it would go in here unless running directly from python)
        else:
            AddMsgAndPrint("\tNo user-defined scratch workspace ",0)
            sysDrive = os.environ['SYSTEMDRIVE']

            if sysDrive:
                tempFolder = sysDrive + os.sep + "TEMP"

                if not os.path.exists(tempFolder):
                    os.makedirs(tempFolder,mode=777)

                arcpy.env.scratchWorkspace = tempFolder
                AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

            else:
                packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                if arcpy.env[packageWS[0]]:
                    arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                    AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                else:
                    return False

        arcpy.Compact_management(arcpy.env.scratchGDB)
        return arcpy.env.scratchGDB

    except:

        # All Failed; set workspace to packageWorkspace environment
        try:
            packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
            if arcpy.env[packageWS[0]]:
                arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                arcpy.Compact_management(arcpy.env.scratchGDB)
                return arcpy.env.scratchGDB
            else:
                AddMsgAndPrint("\tCould not set scratchWorkspace. Not even to default!",2)
                return False
        except:
            errorMsg()
            return False

## ================================================================================================================
def tic():
    """ Returns the current time """

    return time.time()

## ================================================================================================================
def toc(_start_time):
    """ Returns the total time by subtracting the start time - finish time"""

    try:

        t_sec = round(time.time() - _start_time)
        (t_min, t_sec) = divmod(t_sec,60)
        (t_hour,t_min) = divmod(t_min,60)

        if t_hour:
            return ('{} hour(s): {} minute(s): {} second(s)'.format(int(t_hour),int(t_min),int(t_sec)))
        elif t_min:
            return ('{} minute(s): {} second(s)'.format(int(t_min),int(t_sec)))
        else:
            return ('{} second(s)'.format(int(t_sec)))

    except:
        errorMsg()

## ================================================================================================================
def splitThousands(someNumber):
    """ will determine where to put a thousands seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ================================================================================================================
def getListOfAllPedonIDs():
    """ This function will send a request using the 'Web Pedon PEIID List All of NASIS' NASIS
        report and return a list of ALL pedons in NASIS.  Pedons include regular
        NASIS pedons and LAB pedons.  Each record in the report will contain the following values:

        START 1204126, 1204127, 1204128 STOP"""

    try:
        AddMsgAndPrint("\nRequesting a list of ALL pedonIDs from NASIS")
        arcpy.SetProgressorLabel("Requesting a list of ALL pedonIDs from NASIS")

        #URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT' + coordinates
        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_PEDON_PEIID_LIST_ALL_OF_NASIS'

        # Open a network object using the URL with the search string already concatenated
        startTime = tic()
        #AddMsgAndPrint("\tNetwork Request Time: " + toc(startTime))

        """ --------------------------------------  Try connecting to NASIS to read the report ------------------------"""
        try:
            theReport = urlopen(URL).readlines()
        except:
            try:
                AddMsgAndPrint("\t2nd attempt at requesting data")
                theReport = urlopen(URL).readlines()

            except:
                try:
                    AddMsgAndPrint("\t3rd attempt at requesting data")
                    theReport = urlopen(URL).readlines()

                except URLError, e:
                    if hasattr(e, 'reason'):
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\tURL Error: " + str(e.reason), 2)

                    elif hasattr(e, 'code'):
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\t" + e.msg + " (errorcode " + str(e.code) + ")", 2)

                    return False

                except socket.timeout, e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tServer Timeout Error", 2)
                    return False

                except socket.error, e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                    return False

                except httplib.BadStatusLine:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                    return False

        """ --------------------------------------  Read the NASIS report ------------------------------------"""
        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

        arcpy.SetProgressor("step", "Reading NASIS Report: 'WEB_PEDON_PEIID_LIST_ALL_OF_NASIS'", 0, len(theReport), 1)

        # iterate through the report until a valid record is found
        for theValue in theReport:
            theValue = theValue.strip() # removes whitespace characters

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue == "STOP":  # written as part of the report; end of lines
                    break

                # Found a valid record
                if not theValue == None:

                    # All of the peodonIDs will be contained in 1 line
                    pedonDict = {val.strip():None for val in theValue.split(",")}

                else:
                    continue

            else:
                if theValue.startswith('<div id="ReportData">START'):
                    bValidRecord = True

            arcpy.SetProgressorPosition()

        #Resets the progressor back to its initial state
        arcpy.ResetProgressor()

        if len(pedonDict) == 0:
            AddMsgAndPrint("\tThere were no pedons returned from this report",2)
            return False

        else:
            return pedonDict

    except:
        errorMsg()
        return False

## ================================================================================================================
def createPedonFGDB():
    """This Function will create a new File Geodatabase using a pre-established XML workspace
       schema.  All Tables will be empty and should correspond to that of the access database.
       Relationships will also be pre-established.
       Return false if XML workspace document is missing OR an existing FGDB with the user-defined
       name already exists and cannot be deleted OR an unhandled error is encountered.
       Return the path to the new Pedon File Geodatabase if everything executes correctly."""

    try:
        AddMsgAndPrint("\nCreating New Pedon File Geodatabase",0)
        arcpy.SetProgressorLabel("Creating New Pedon File Geodatabase")

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "Extract_Pedons_from_NASIS_XMLWorkspace.xml"
        localPedonGDB = os.path.dirname(sys.argv[0]) + os.sep + "NasisPedonsTemplate.gdb"

        # Return false if pedon fGDB template is not found
        if not arcpy.Exists(localPedonGDB):
            AddMsgAndPrint("\t" + os.path.basename(localPedonGDB) + " FGDB template was not found!",2)
            return False

        newPedonFGDB = os.path.join(outputFolder,GDBname + ".gdb")

        if arcpy.Exists(newPedonFGDB):
            try:
                arcpy.Delete_management(newPedonFGDB)
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Deleting and re-creating FGDB\n",1)
            except:
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Failed to delete\n",2)
                return False

        # copy template over to new location
        AddMsgAndPrint("\tCreating " + GDBname + ".gdb with NCSS Pedon Schema 7.3")
        arcpy.Copy_management(localPedonGDB,newPedonFGDB)

        """ ------------------------------ Code to use XML Workspace -------------------------------------------"""
##        # Return false if xml file is not found
##        if not arcpy.Exists(pedonXML):
##            AddMsgAndPrint("\t" + os.path.basename(pedonXML) + " Workspace document was not found!",2)
##            return False
##
##        # Create empty temp File Geodatabae
##        arcpy.CreateFileGDB_management(outputFolder,os.path.splitext(os.path.basename(newPedonFGDB))[0])
##
##        # set the pedon schema on the newly created temp Pedon FGDB
##        AddMsgAndPrint("\tImporting NCSS Pedon Schema 7.3 into " + GDBname + ".gdb")
##        arcpy.ImportXMLWorkspaceDocument_management(newPedonFGDB, pedonXML, "DATA", "DEFAULTS")

        arcpy.UncompressFileGeodatabaseData_management(newPedonFGDB)
        arcpy.RefreshCatalog(outputFolder)
        AddMsgAndPrint("\tSuccessfully created: " + GDBname + ".gdb")

        return newPedonFGDB

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        return False

## ===============================================================================================================
def getTableAliases(pedonFGDBloc):
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores physical names (key) and aliases (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}
    # Fieldnames are Physical Name = AliasName,IEfilename

    try:

        arcpy.SetProgressorLabel("Gathering Table and Field aliases")

        # Open Metadata table containing information for other pedon tables
        theMDTable = pedonFGDBloc + os.sep + "MetadataTable"
        arcpy.env.workspace = pedonFGDBloc

        # Establishes a cursor for searching through field rows. A search cursor can be used to retrieve rows.
        # This method will return an enumeration object that will, in turn, hand out row objects
        if not arcpy.Exists(theMDTable):
            return False

        tableList = arcpy.ListTables("*")
        tableList.append("pedon")

        nameOfFields = ["TablePhysicalName","TableLabel"]

        for table in tableList:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            expression = arcpy.AddFieldDelimiters(theMDTable,"TablePhysicalName") + " = '" + table + "'"
            with arcpy.da.SearchCursor(theMDTable,nameOfFields, where_clause = expression) as cursor:

                for row in cursor:
                    # read each table record and assign 'TablePhysicalName' and 'TableLabel' to 2 variables
                    physicalName = row[0]
                    aliasName = row[1]

                    # i.e. {phtexture:'Pedon Horizon Texture',phtexture}; will create a one-to-many dictionary
                    # As long as the physical name doesn't exist in dict() add physical name
                    # as Key and alias as Value.
                    if not tblAliases.has_key(physicalName):
                        tblAliases[physicalName] = aliasName

                    del physicalName,aliasName

        del theMDTable,tableList,nameOfFields

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (GetTableAliases)", 2)
        errorMsg()
        return False

## ===============================================================================================================
def createEmptyDictOfTables():
    # Create a new dictionary called pedonGDBtables that will contain every table in the newly created
    # pedonFGDB above as a key.  Individual records of tables will be added as values to the table keys.
    # These values will be in the form of lists.  This dictionary will be populated using the results of
    # the WEB_AnalysisPC_MAIN_URL_EXPORT NASIS report.  Much faster than opening and closing cursors.

    try:

        arcpy.env.workspace = pedonFGDB
        tables = arcpy.ListTables()
        tables.append(arcpy.ListFeatureClasses('pedon','Point')[0])  ## pedon is a feature class and gets excluded by the ListTables function

        # Create dictionary where keys will be tables and values will be later populated
        # {'area': [],'areatype': [],'basalareatreescounted': [],'beltdata': [],'belttransectsummary': []........}
        pedonGDBtablesDict = dict()

        for table in tables:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue
            pedonGDBtablesDict[str(table)] = []

        del tables
        return pedonGDBtablesDict

    except:
        AddMsgAndPrint("\nUnhandled exception (GetTableAliases)\n", 2)
        errorMsg()
        exit()

## ===============================================================================================================
def createTableFieldLookuup():
    # This function will create a dictionary that will contain table:number of fields in order
    # to double check that the values from the web report are correct. This was added b/c there
    # were text fields that were getting disconnected in the report and being read as 2 lines
    # and Jason couldn't address this issue in NASIS.  This also serves as a QC against values
    # have an incorrect number of values relative to the available fields.  This has been a problem
    # with values having a pipe (|) which causes a problem with splitting values.

    try:

        arcpy.env.workspace = pedonFGDB

        tableInfoDict = dict()    # contains all valid tables and the number of fields that it contains i.e. petext:11
        validTables = arcpy.ListTables("*")
        validTables.append('pedon')

        for table in validTables:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            uniqueFields = arcpy.Describe(os.path.join(pedonFGDB,table)).fields
            numOfValidFlds = 0

            for field in uniqueFields:
                if not field.type.lower() in ("oid","geometry","FID"):
                    numOfValidFlds +=1

            # Add 2 more fields to the pedon table for X,Y
            if table == 'pedon':
                numOfValidFlds += 2

            tableInfoDict[table] = numOfValidFlds
            del uniqueFields;numOfValidFlds

        return tableInfoDict

    except:
        AddMsgAndPrint("\nUnhandled exception (createTableFieldLookup)\n", 2)
        errorMsg()
        exit()

## ===============================================================================================================
def parsePedonsIntoLists():
    """ This function will parse pedons into manageable chunks that will be sent to the 2nd URL report.
        There is an inherent URL character limit of 2,083.  The report URL is 123 characters long which leaves 1,960 characters
        available. I arbitrarily chose to have a max URL of 1,860 characters long to avoid problems.  Most pedonIDs are about
        6 characters.  This would mean an average max request of 265 pedons at a time.

        This function returns a list of pedon lists"""
        #1860 = 265

    try:
        arcpy.SetProgressorLabel("Determining the number of requests to send the server")

        # Total Count
        i = 1
        listOfPedonStrings = list()  # List containing pedonIDstring lists; individual lists are comprised of about 265 pedons
        pedonIDstr = ""

        for pedonID in pedonidList:
            pedonID = pedonID.strip()

            # End of pedon list has been reached
            if i == len(pedonidList):
                pedonIDstr = pedonIDstr + str(pedonID)
                listOfPedonStrings.append(pedonIDstr)

            # End of pedon list NOT reached
            else:
                # Max URL length reached - retrieve pedon data and start over
                if len(pedonIDstr) > 1860:
                    pedonIDstr = pedonIDstr + str(pedonID)
                    listOfPedonStrings.append(pedonIDstr)

                    ## reset the pedon ID string to empty
                    pedonIDstr = ""
                    i+=1

                # concatenate pedonID to string and continue
                else:
                    pedonIDstr = pedonIDstr + str(pedonID) + ",";i+=1

        numOfPedonStrings = len(listOfPedonStrings)  # Number of unique requests that will be sent

        if not numOfPedonStrings:
            AddMsgAndPrint("\n\t Something Happened here.....WTF!",2)
            exit()

        else:
            return listOfPedonStrings,numOfPedonStrings

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        exit()

## ================================================================================================================
def getPedonHorizon(pedonList):

    # Here is an example of the output report

    """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head><title>

    </title><link href="basepage.css" rel="stylesheet" type="text/css" />
    	<title></title>
    </head>
    <body>
    	<form name="aspnetForm" method="post" action="./limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&amp;pedonid_list=36186" id="aspnetForm">
    <div>
    <input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="/wEPDwUKLTM2NDk4NDg3MA9kFgJmD2QWAgIDD2QWAgIBD2QWAgIDDw8WAh4HVmlzaWJsZWdkZGTGpOLNcjJy57o09/vgOTuu/3Y32k0Fja4e1d5/Fegb1w==" />
    </div>

    <div>

    	<input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="DCF944DC" />
    </div>
    	<div>

    	<div id="ctl00_ContentPlaceHolder1_pnlReportOutput">

    	<div id="ReportData">@begin ncsspedonlabdata
    pedlabsampnum|peiidref|psctopdepth|psctopdepth_s|pscbotdepth|pscbotdepth_s|noncarbclaywtavg|claytotwtavg|le0to100|wf0175wtavgpsc|volfractgt2wtavg|cec7clayratiowtavg|labdatasheeturl|ncsspedbiidref|grpiidref|objwlupdated|objuseriidref|recwlupdated|recuseriidref|ncsspedonlabdataiid
    @end
    @begin ncsslayerlabdata
    ncsspedonlabdataiidref|layerseqnum|labsampnum|hzdept|hzdepb|layertype|hzname|hznameoriginal|stratextsflag|moistprepstate|texcl|sandvcmeasured|sandcomeasured|sandmedmeasured|sandfinemeasured|sandvfmeasured|sandtotmeasured|siltcomeasured|siltfinemeasured|silttotmeasured|claycarbmeasured|clayfinemeasured|claytotmeasured|carbonorganicpctmeasured|carbontotalpctmeasured|ompctest|fiberrubbedpct|fiberunrubbedpct|fragwt25|fragwt520|fragwt2075|fragwt275|wtpct0175|wtpctgt2ws|ph1to1h2o|ph01mcacl2|phnaf|phoxidized|resistivity|ecmeasured|esp|sar|cecsumcations|cec7|ecec|sumbases|basesatsumcations|basesatnh4oac|caco3equivmeasured|caco3lt20measured|gypsumequivlt2measured|gypsumequivmeasured|feoxalatemeasured|feextractable|fetotal|sioxalatemeasured|extracid|extral|aloxalatemeasured|altotal|pmehlich3|ph2osolublemeasured|poxalatemeasured|polsenmeasured|ptotalmeasured|nzpretention|dbthirdbar|dbovendry|aggstabpct|wtenthbarclod|wtenthbarsieve|wthirdbarclod|wthirdbarsieve|wfifteenbarmeasured|wretentiondiffws|wfifteenbartoclay|adod|lep|cole|liquidlimitmeasured|pi|recwlupdated|recuseriidref|ncsslayerlabdataiid
    @end
    @begin site
    usiteid|latdegrees|latminutes|latseconds|latdir|longdegrees|longminutes|longseconds|longdir|horizdatnm|locdesc|plsssdetails|plsssection|plsstownship|plssrange|plssmeridian|utmzone|utmnorthing|utmeasting|geocoordsource|elev|geomposhill|geomposmntn|geompostrce|geomposflats|hillslopeprof|geomslopeseg|slope|aspect|slopelenusle|slopelenuptro|shapeacross|shapedown|slopecomplex|locphysnm|siteksatclassupper|siteksatclasslower|drainagecl|runoff|drainagepattern|pmgroupname|pmgroupname_s|climstaid|climstanm|climstatype|ffd|map|reannualprecip|airtempa|soiltempa|airtemps|soiltemps|airtempw|soiltempw|benchmarksoilflag|flodfreqcl|floddurcl|flodmonthbeg|pondfreqcl|ponddurcl|pondmonthbeg|wtabledur|latstddecimaldegrees|longstddecimaldegrees|gpspositionalerror|gpspdop|elevcorrected|sdbiidref|siteiid
    94IL111028|42|18|45.00|North|88|13|43.00|West|North American Datum of 1927|500 feet south and 2,600 feet east of the northwest corner of sec. 7, T. 44 N., R. 9 E.||||||||||229.0|Side Slope||||Backslope||27.0|270|||Linear|Linear|||||Excessively drained|Very high||||||||||||||||0||||||||42.3125106|-88.2286481||||139|36242
    @end
    @begin siteobs
    seqnum|obsdate|obsdatekind|datacollector|photoid|swaterkind|swaterdepth|hydrologystatus|geomicrorelief|geommicelev|geommicpat|ecostateid|ecostatename|commphaseid|commphasename|plantassocnm|earthcovkind1|earthcovkind2|resourceretentionclass|bareareamaxwidth|pedodermclass|pedodermcovind|biolcrusttypedom|biolcrusttypesecond|physcrustsubtype|crustdevcl|soilredistributionclass|exposedsoilpct|localdisturbancedistance|localdisturbancedescription|drainedflag|beddingflag|plantationflag|forestrotationstage|yldstudyid|currweathcond|currairtemp|tidalperiod|bottomtype|saswatertempupper|saswatertemplower|saswaterphupper|saswaterphlower|phdetermeth|sasdissolvedoxyupper|sasdissolvedoxylower|saswatersalinityupper|saswatersalinitylower|siteiidref|siteobsiid
    |10/14/1994 12:00:00 AM|Actual Site Observation Date||BXA-2-41|||||||||||||||||0|||||||||0|0|0||||||||||||||||36242|36165
    @end
    @begin siteerosionacc
    seqnum|erokind|siteobsiidref|siteeroacciid
    |Water erosion|36165|4703
    @end
    @begin sitegeomordesc
    seqnum|geomfiidref|geomfmod|geomfeatid|existsonfeat|siteiidref|sitegeomdiid
    |70||||36242|52245
    @end
    @begin siteobstext
    seqnum|recdate|recauthor|siteobstextkind|textcat|textsubcat|textentry|siteobsiidref|siteobstextiid
    @end
    @begin siteaoverlap
    seqnum|areaiidref|siteiidref|sareaoviid|areaname|areasymbol|areatypename
    |643|36242|1050900|La Salle County, Illinois|IL099|Non-MLRA Soil Survey Area
    |649|36242|1050901|McHenry County, Illinois|IL111|Non-MLRA Soil Survey Area
    |68910|36242|1050899|United States|US|Country
    @end
    @begin sitemuoverlap
    siteiidref|seqnum|lmapunitiidref|recwlupdated|recuseriidref|smuoviid
    36242||2108706|9/22/2011 12:54:23 PM|1099|124012
    @end
    @begin sitepm
    seqnum|pmorder|pmdept|pmdepb|pmmodifier|pmgenmod|pmkind|pmorigin|pmweathering|siteiidref|sitepmiid
    @end
    @begin sitesoilmoist
    seqnum|soimoistdept|soimoistdepb|soilmoistsensordepth|soilmoistsensorkind|obssoimoiststat|obssoimoist|obsgrsoimoist|soimoistten|siteobsiidref|sitesmiid
    @end
    @begin sitesoiltemp
    seqnum|soitempdep|soiltempsensorkind|soitemp|siteobsiidref|sitestiid
    @end
    @begin sitetext
    seqnum|recdate|recauthor|sitetextkind|textcat|textsubcat|textentry|siteiidref|sitetextiid
    @end
    @begin transect
    utransectid|tsectauth|tsectkind|tsectselmeth|tsectdelinsize|tsectdir|tsectcertstatus|tsectdbiidref|tsectiid
    @end
    @begin transecttext
    seqnum|recdate|recauthor|transecttextkind|textcat|textsubcat|textentry|tsectiidref|transecttextiid
    @end
    @begin pediagfeatures
    peiidref|seqnum|featdept|featdepb|featthick_l|featthick_r|featthick_h|featkind|recwlupdated|recuseriidref|pediagfeatiid
    @end
    @begin pefmp
    peiidref|seqnum|fmpname|fmpvalue|fmpunits|recwlupdated|recuseriidref|pefmpiid
    @end
    @begin pedon
    siteobsiidref|upedonid|pedrecorigin|descname|taxonname|taxonname_s|localphase|taxclname|taxclname_s|taxonkind|taxonkind_s|pedontype|pedonpurpose|pedonunit|labdatadescflag|relexpsize|relexpuom|earthcovkind1|earthcovkind2|erocl|labsourceid|pedlabsampnum|tsectiidref|tsectstopnum|tsectinterval|rcapointnumber|soilreplicatenumber|azimuthfromplotcenter|distancefromplotcenter|rectangularplotlinenumber|distancefrombaseline|pedodermclass|pedodermcovind|biolcrusttypedom|biolcrusttypesecond|physcrustsubtype|crustdevcl|rangevegcanopytypedom|rangevegcanopytypesec|forestoverstoryvegtype|forestunderstoryvegtype|forestgroundcovvegtypedom|forestgroundcovvegtypesec|agronomicfeature|otherfeaturedescription|currentcropname|littercoverpct|residuedescription|pedonhydricrating|pecertstatus|peqcstatus|peqastatus|saspipelengthtot|saspipelengthext|saspipelengthunfilled|sascoresettlement|sascorelength|sascorestoragesite|sasexposurebegin|sasexposureend|pedbiidref|grpiidref|objwlupdated|objuseriidref|recwlupdated|recuseriidref|peiid
    36165|94IL111028|Converted from PDP 3.x|JAD, DEC|Rodman|3||Sandy-skeletal, mixed, mesic Typic Hapludolls|1||||Full pedon description||No|||||Class 1|||||||||||||0||||||||||||||||No||||||||||||139|1298|4/6/2012 11:42:51 AM|1216|4/6/2012 11:40:56 AM|1216|36186
    @end
    @begin perestrictions
    peiidref|seqnum|resdept|resdepb|resthk_l|resthk_r|resthk_h|reskind|reshard|recwlupdated|recuseriidref|perestrictiid
    @end
    @begin sitesurffrags
    seqnum|sfragcov|distrocks|sfragkind|sfragsize_l|sfragsize_r|sfragsize_h|sfragshp|sfraground|sfraghard|siteobsiidref|sitesurffragsiid
    @end
    @begin petaxhistfmmin
    pedtaxhistoryiidref|seqnum|minorder|taxminalogy|recwlupdated|recuseriidref|petaxfmminiid
    449102||1|mixed|||32434
    @end
    @begin petxhistfmother
    pedtaxhistoryiidref|seqnum|taxfamother|recwlupdated|recuseriidref|petaxfoiid
    @end
    @begin petaxhistmoistcl
    pedtaxhistoryiidref|seqnum|taxmoistcl|recwlupdated|recuseriidref|petaxmciid
    449102||Udic|||33763
    @end
    @begin petext
    peiidref|seqnum|recdate|recauthor|pedontextkind|textcat|textsubcat|textentry|recwlupdated|recuseriidref|petextiid
    @end
    @begin phcemagent
    phiidref|seqnum|ruprescem|recwlupdated|recuseriidref|phcemagentiid
    @end
    @begin phcolor
    phiidref|seqnum|colorpct|colorhue|colorvalue|colorchroma|colorphysst|colormoistst|recwlupdated|recuseriidref|phcoloriid
    166637|1||10YR|3|1||Moist|||220346
    166637|2||10YR|4|2||Dry|||220347
    166638|2|50|10YR|4|3||Moist|||220335
    166638|1|50|10YR|3|3||Moist|||220348
    166639|1||10YR|4|4||Moist|||220336
    @end
    @begin phconccolor
    phconceniidref|seqnum|colorpct|colorhue|colorvalue|colorchroma|colormoistst|recwlupdated|recuseriidref|phconcencoloriid
    @end
    @begin phconcs
    phiidref|seqnum|concpct|concsize|conccntrst|conchardness|concshape|conckind|conclocation|concboundary|recwlupdated|recuseriidref|phconceniid
    @end
    @begin phdesgnsuffix
    phiidref|seqnum|desgnsuffix|recwlupdated|recuseriidref|phdesgnsfxiid
    @end
    @begin phfeatures
    phiidref|seqnum|horfeatkind|horfeatvtpct_l|horfeatvtpct_r|horfeatvtpct_h|horfeatlapct_l|horfeatlapct_r|horfeatlapct_h|recwlupdated|recuseriidref|phfeatsiid
    @end
    @begin phfeatcolor
    phfeatsiidref|seqnum|colorpct|colorhue|colorvalue|colorchroma|colormoistst|recwlupdated|recuseriidref|phfeatcoloriid
    @end
    @begin phfmp
    phiidref|seqnum|fmpname|fmpvalue|fmpunits|recwlupdated|recuseriidref|phfmpiid
    @end
    @begin phfrags
    phiidref|seqnum|fragvol|fragweight|fragsize_l|fragsize_r|fragsize_h|fragkind|fragshp|fraground|fraghard|fragestmethod|recwlupdated|recuseriidref|phfragsiid
    166637|1|17.0||2|39|75||||||||26160
    166638|1|25.0||2|39|75||||||||26161
    166639|1|50.0||2|39|75||||||||26162
    @end
    @begin phmottles
    phiidref|seqnum|mottlepct|mottlesize|mottlecntrst|colorhue|colorvalue|colorchroma|mottleshape|colormoistst|mottleloc|recwlupdated|recuseriidref|phmottlesiid
    @end
    @begin phpores
    phiidref|seqnum|poreqty|poreqtyclass|poresize|porecont|poreshp|recwlupdated|recuseriidref|phporesiid
    @end
    @begin phpvsf
    phiidref|seqnum|pvsfpct|pvsfkind|pvsfdistinct|pvsfcont|pvsflocation|recwlupdated|recuseriidref|phpvsfiid
    166638|1|50|Organic stains|Distinct||On faces of peds|||57799
    @end
    @begin phpvsfcolor
    phpvsfiidref|seqnum|colorpct|colorhue|colorvalue|colorchroma|colormoistst|recwlupdated|recuseriidref|phpvsfcoloriid
    57799|||10YR|3|2||||33932
    @end
    @begin phrdxfeatures
    phiidref|seqnum|rdxfeatpct|rdxfeatsize|rdxfeatcntrst|rdxfeathardness|rdxfeatshape|rdxfeatkind|rdxfeatlocation|rdxfeatboundary|recwlupdated|recuseriidref|phrdxfiid
    @end
    @begin phroots
    phiidref|seqnum|rootsquantity|rootsquantityclass|rootssize|rootslocation|recwlupdated|recuseriidref|phrootsiid
    166637|1|14.0||Very fine and fine||||52228
    166638|1|4.0||Very fine||||52241
    166639|1|2.0||Very fine||||51616
    @end
    @begin phsample
    phiidref|seqnum|labsampnum|fldsampid|layerdepthtop|layerdepthbottom|numberofbulksampbags|numberofbulkdensityclods|numberofnaturalfabricclods|numberofothersamples|recwlupdated|recuseriidref|phlabsampiid
    @end
    @begin phstructure
    phiidref|seqnum|structgrade|structsize|structtype|structid|structpartsto|recwlupdated|recuseriidref|phstructureiid
    166637|2|Strong|Fine and medium|Granular|||||176463
    166638|2|Weak|Fine|Granular|||||176464
    166639|2|||Single grain|||||176465
    @end
    @begin phtext
    phiidref|seqnum|recdate|recauthor|phorizontextkind|textcat|textsubcat|textentry|recwlupdated|recuseriidref|phtextiid
    @end
    @begin phtexture
    phiidref|seqnum|texcl|lieutex|recwlupdated|recuseriidref|phtiid
    166637|1|Loam||||167685
    166638|1|Loam||||167624
    166639|1|Sand||||167625
    166639|2|Loamy sand||||167763
    @end
    @begin phtexturemod
    phtiidref|seqnum|texmod|recwlupdated|recuseriidref|phtexmodiid
    167685||Gravelly|||8304
    167624||Gravelly|||8295
    167625||Very gravelly|||8296
    167763||Very gravelly|||8310
    @end
    @begin phorizon
    peiidref|seqnum|hzdept|hzdepb|hzthk_l|hzthk_r|hzthk_h|obsmethod|hzname|hzname_s|desgndisc|desgnmaster|desgnmasterprime|desgnvert|texture|texture_s|stratextsflag|claytotest|claycarbest|silttotest|sandtotest|fragvoltot|horcolorvflag|obssoimoiststat|rupresblkmst|rupresblkdry|rupresblkcem|rupresplate|mannerfailure|stickiness|plasticity|toughclass|penetrres|penetorient|ksatpedon|ksatstddev|ksatrepnum|horzpermclass|obsinfiltrationrate|phfield|phdetermeth|effclass|efflocation|effagent|carbdevstagefe|carbdevstagecf|mneffclass|mneffagent|reactadipyridyl|dipyridylpct|dipyridylloc|excavdifcl|soilodor|soilodorintensity|rmonosulfidep|bounddistinct|boundtopo|horzvoltotpct_l|horzvoltotpct_r|horzvoltotpct_h|horzlatareapct_l|horzlatareapct_r|horzlatareapct_h|dspcomplayerid|aashtocl|unifiedcl|recwlupdated|recuseriidref|phiid
    36186|1|0|28|||||A||||||GR-L|1|0||||||0||Friable|||||||||||||||7.2|Hellige-Truog||||||||||||||0|Clear|Wavy||||||||||||166637
    36186|2|28|36|||||Bw||||||GR-L|1|0||||||0||Friable|||||||||||||||7.8|Hellige-Truog|Strongly effervescent|||||||||||||0|Abrupt|Wavy||||||||||||166638
    36186|3|36|152|||||C||||||GRV-S GRV-LS|1|0||||||0||Loose|||||||||||||||8.0|Hellige-Truog|Strongly effervescent|||||||||||||0||||||||||||||166639
    @end
    @begin petaxhistory
    peiidref|seqnum|classdate|classtype|classifier|taxonname|localphase|taxonkind|seriesstatus|taxclname|taxclname_s|taxorder|taxsuborder|taxgrtgroup|taxsubgrp|taxpartsize|taxpartsizemod|taxceactcl|taxreaction|taxtempcl|taxmoistscl|taxtempregime|taxfamhahatmatcl|soiltaxedition|psctopdepth|pscbotdepth|osdtypelocflag|recwlupdated|recuseriidref|petaxhistoryiid
    36186||10/14/1994 12:00:00 AM|Sampled as||Rodman|||||||||||||||||||||0|8/1/2012 2:00:30 PM||273950
    36186||4/6/2012 11:42:51 AM|Correlated||Rodman||||Sandy-skeletal, mixed, mesic Typic Hapludolls|1|Mollisols|Udolls|Hapludolls|Typic Hapludolls|sandy-skeletal||||mesic||mesic||tenth edition|||0|4/6/2012 11:40:56 AM|1216|449102
    @end
    @begin pepenetrationresistance
    peiidref|seqnum|penetrometerdepth|obssoimoiststat|penetrometertiptype|penetrometerspringtype|penetorient|penetrometerreading1|penetrometerreading2|penetrometerreading3|penetrometerreading4|datacollector|recwlupdated|recuseriidref|pepenetrometeriid
    @end
    @begin pehydricfieldindicator
    peiidref|seqnum|hydricsoilfieldindicator|recwlupdated|recuseriidref|pehydricfieldindiid
    @end
    @begin pesoilstability
    peiidref|seqnum|soilstabilitydepth|samplecollector|datacollector|testdate|soilstabilityclass1|soilstabilityclass2|soilstabilityclass3|soilstabilityclasspredom|soilhydrophobicind1|soilhydrophobicind2|soilhydrophobicind3|recwlupdated|recuseriidref|pesoilstabilityiid
    @end
    @begin peinfiltrationsummary
    peiidref|seqnum|testdate|datacollector|infiltrationmean|infiltrationstddev|infiltrationtestmethod|recwlupdated|recuseriidref|pedoninfilsumiid
    @end
    @begin peinfiltrationchdata
    peinfilconstheadiidref|infiltrationrunnum|waterdrop|deltatime|infiltrationmeasured|steadystateflag|recwlupdated|recuseriidref|peinfilchdataiid
    @end
    @begin peinfiltrationch
    peinfilsumiidref|testdate|repnum|infiltrationmeasured|infiltrationringconfig|ringinsertiondepth|ringradius|waterponddepth|mariottebottleradius|notes|recwlupdated|recuseriidref|peinfilconstheadiid
    @end
    @begin peinfiltrationfhdata
    peinfilfallheadiidref|infiltrationrunnum|deltatime|infiltrationwatervolume|recwlupdated|recuseriidref|pedoninfilfhdataiid
    @end
    @begin peinfiltrationfh
    peinfilsumiidref|testdate|repnum|infiltrationmeasured|infiltrationringconfig|ringinsertiondepth|ringradius|notes|recwlupdated|recuseriidref|peinfilfallheadiid
    @end
    @begin phlabresults
    phiidref|seqnum|sampledepthtop|sampledepthbottom|sampleid|datacollector|claytotmeasured|claycarbmeasured|silttotmeasured|siltfinemeasured|siltcomeasured|sandtotmeasured|sandtotmethod|sandvcmeasured|sandcomeasured|sandmedmeasured|sandfinemeasured|sandvfmeasured|sandvfmethod|textureclfieldlab|fiberrubbedpct|fiberunrubbedpct|ph1to1h2o|ph01mcacl2|phnaf|phoxidized|phdeltah2o2|liquidlimitmeasured|plasticlimitmeasured|pi|atterbergsampcond|cole|esttotpotacidityetpa|camgmeh2|potassiummeh2|camgsatpaste|extractaciditykcl|basesatmeh2|cec7|cec82|ecec|phosphatephos|nitratenitrogen|ecmeasured|ecdeterminemeth|ec15|caco3equivmeasured|gypsumequiv|sodium|sar|gypsumreq|humiccolor|fulviccolor|humicfulviccolor|alummeasured|pyrophoshue|pyrophosvalue|pyrophoschroma|melanicindex|recwlupdated|recuseriidref|phlabresultiid
    @end
    @begin phhydrometeranalysis
    phlabresultiidref|seqnum|testdate|hydrosamplewt|hydroshmpconc|hydroblankread|hydromethod|obsgrsoimoist|recwlupdated|recuseriidref|phhydromanalysisiid
    @end
    @begin phcoledata
    phlabresultiidref|seqnum|repnum|phcolereading|phcolemethod|recwlupdated|recuseriidref|phcoledataiid
    @end
    @begin phgrcountsummary
    phlabresultiidref|seqnum|phgrcountquartz|phgrcountmica|phgrcountglass|phgrcountglasscoated|phgrcountglassagg|phgrcountother|recwlupdated|recuseriidref|phgrcountsumiid
    @end
    @begin phcracks
    phiidref|seqnum|crackfreq|crackkind|crackdepth|crackwidth|crackextabove|crackextbelow|recwlupdated|recuseriidref|phcracksiid
    @end
    @begin phdb
    phiidref|seqnum|bddepthtop|bddepthbottom|bdmethod|datacollector|samplevolfieldmoist|totalsamplewtfm|totalsamplewtairdry|coarsefragwtfm|coarsefragwtairdry|coarsefragdensity|coarsefragvolmeasured|subsamplewtairdry|subsamplewtod|obsgrsoimoist|obsgrsoimoist_s|obsgravsoilmoistfe|obsgravsoilmoistfe_s|bdfieldmoistfineearth|bdfieldmoistwhole|bdovendrywhole|bdovendrywhole_s|bdovendryfineearth|bdovendryfineearth_s|bdsatiated|recwlupdated|recuseriidref|phbulkdensityiid
    @end
    @begin phdbcore
    phbulkdensityiidref|sampletubelength|unfilledtubelength|unfilledtubelength_s|coresamplelength|coresamplelength_s|sampletubediameter|coresamplevolume|coresamplevolume_s|recwlupdated|recuseriidref|phbulkdencoreiid
    @end
    @begin phdbcorereading
    phbulkdencoreiidref|bulkdensitytubeheadspace|recwlupdated|recuseriidref|phbdcorereadingiid
    @end
    @begin siteassocsoi
    seqnum|assocsoi|siteiidref|siteassocsoiiid
    @end
    @begin phksatringdata
    peksatringiidref|ksatreadingnum|waterdrop|deltatime|sathydcondmeasured|steadystateflag|recwlupdated|recuseriidref|peksatringdataiid
    @end
    @begin phksatring
    phksatsumiidref|repnum|testdate|sathydcondrepmean|sathydcondrepstd|sathydcondclass|ringconfiguration|ringinsertiondepth|ringradius|waterponddepth|mariottebottleradius|texturestructurecat|notes|recwlupdated|recuseriidref|phksatringiid
    @end
    @begin phksatamoozedata
    peksatamoozeiidref|ksatreadingnum|waterdrop|deltatime|outflowchamberconvfact|sathydcondmeasured|steadystateflag|recwlupdated|recuseriidref|peksatamoozedataiid
    @end
    @begin phksatamoozemeter
    phksatsumiidref|repnum|testdate|sathydcondrepmean|sathydcondrepstd|sathydcondclass|boreholedepth|boreholeradius|boreholewaterlevelinit|boreholewaterlevelfinal|notes|recwlupdated|recuseriidref|phksatamoozemeteriid
    @end
    @begin phksatsummary
    phiidref|seqnum|testdate|datacollector|sathydcondmean|sathydcondstd|sathydcondmethod|recwlupdated|recuseriidref|pedonksatsummaryiid
    @end
    @begin phhydrometerdata
    phhydromanalysisiidref|hydroreadingnum|deltatime|hydrotemp|hydroreading|recwlupdated|recuseriidref|phhydrometerdataiid
    @end
    @begin phhuarts
    phiidref|seqnum|huartvol|huartsize_l|huartsize_r|huartsize_h|huartkind|huartco|huartshp|huartrnd|huartpen|huartsafety|huartper|recwlupdated|recuseriidref|phhuartiid
    @end
    @begin phgrcountdata
    phgrcountsumiidref|testdate|repnum|phgrcounttotal|phgrcountquartz|phgrcountmica|phgrcountglass|phgrcountglasscoated|phgrcountglassagg|phgrcountother|recwlupdated|recuseriidref|phgrcountiid
    @end
    @begin phdbcompliantcavity
    phbulkdensityiidref|bulkdensitycavitydiameter|bulkdensitycavitylength|bulkdensitycavitywidth|bulkdensitycavityinitvol|bulkdensitycavityinitvol_s|bulkdensitycavityfinalvol|bulkdensitycavityfinalvol_s|cavityavedepthpredig|cavityavedepthpostdig|bulkdensitycavitysampvol|bulkdensitycavitysampvol_s|recwlupdated|recuseriidref|phbulkdencavityiid
    @end
    @begin phdbscoopreading
    phbulkdenscoopiidref|scoopheadspace|recwlupdated|recuseriidref|phbulkdenscoopreadiid
    @end
    @begin phdbscoop
    phbulkdensityiidref|scooplength|scoopwidth|scoopdepthtotal|scoopvolume|scoopvolume_s|scoopdepthunfilled|scoopdepthunfilled_s|scoopsamplevolume|scoopsamplevolume_s|recwlupdated|recuseriidref|phbulkdenscoopiid
    @end
    @begin sitebedrock
    seqnum|bedrockorder|geogroup|geoform|geomember|bedrckdepth|bedrckkind|bedrckhardness|bedrckfractint|bedrckweather|bedrckstrike|bedrckdip_l|bedrckdip_h|siteiidref|sitebedrockiid
    @end
    @begin siteecositehistory
    ecositecorrdate|classifier|ecositeiidref|siteiidref|siteecositehistoryiid
    @end
    @begin siteiristubedata
    siteobsiidref|iristubeid|topdepthevaluated|bottomdepthevaluated|dateinstalled|dateremoved|ironpctremoved|reducedsoilflag|irisimagefilename|recwlupdated|recuseriidref|siteiristubedataiid
    @end
    @begin siteothvegclass
    siteiidref|seqnum|ovegcliidref|recwlupdated|recuseriidref|siteovegcliid
    @end
    @begin soiltempmonitordata
    soilmonitordataiidref|sensorid|soiltempsensordepth|soiltempsensorkind|soiltempdailymin|soiltempdailyave|soiltempdailymax|notes|recwlupdated|recuseriidref|soiltempmonitordataiid
    @end
    @begin soilmoistmonitordata
    soilmonitordataiidref|sensorid|soilmoistsensordepth|soilmoistsensorkind|soilmoistvoldailymin|soilmoistvoldailyave|soilmoistvoldailymax|notes|recwlupdated|recuseriidref|soilmoistmonitordataiid
    @end
    @begin soilmonitordata
    peiidref|stationid|obsdate|dailyprecipmeasured|airtempmin|airtempave|airtempmax|airtempsensorheight|notes|recwlupdated|recuseriidref|soilmonitordataiid
    @end
    @begin transectestcomposition
    seqnum|compname|localphase|comppct|slope_l|slope_h|tsectiidref|tsectestcompiid
    @end
    @begin phredoxfcolor
    phrdxfiidref|seqnum|colorpct|colorhue|colorvalue|colorchroma|colormoistst|recwlupdated|recuseriidref|phrdxfcoloriid
    @end
    </div>
    </div>

    </div>
    </form>
    </body>
    </html> """

    try:

        if numOfPedonStrings > 1:
            tab = "\t\t"
        else:
            tab = "\t"

        """----------------------------------- Open a network object --------------------------------"""
        ''' Open a network object using the URL with the search string already concatenated.
            As soon as the url is opened it needs to be read otherwise there will be a socket
            error raised.  Experienced this when the url was being opened before the above
            dictionary was created.  Bizarre'''

        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=' + pedonList
        requestStartTime = tic()

        try:
            theReport = urlopen(URL).readlines()
        except:
            try:
                AddMsgAndPrint(tab + "2nd attempt at requesting data - 10 second pause")
                time.sleep(15)
                theReport = urlopen(URL).readlines()
            except:
                try:
                    AddMsgAndPrint(tab + "3rd attempt at requesting data - 30 second pause")
                    time.sleep(30)
                    theReport = urlopen(URL).readlines()

                except URLError, e:
                    if hasattr(e, 'reason'):
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\tURL Error: " + str(e.reason), 2)

                    elif hasattr(e, 'code'):
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\t" + e.msg + " (errorcode " + str(e.code) + ")", 2)

                    return False

                except socket.timeout, e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tServer Timeout Error", 2)
                    return False

                except socket.error, e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                    return False

                except httplib.BadStatusLine:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                    return False

        AddMsgAndPrint(tab + "Network Request Time: " + toc(requestStartTime))

        invalidTable = 0    # represents tables that don't correspond with the GDB
        invalidRecord = 0   # represents records that were not added
        validRecord = 0

        bHeader = False         # flag indicating if value is html junk
        currentTable = ""       # The table found in the report
        numOfFields = ""        # The number of fields a specific table should contain
        partialValue = ""       # variable containing part of a value that is not complete
        originalValue = ""      # variable containing the original incomplete value
        bPartialValue = False   # flag indicating if value is incomplete; append next record

        """ ------------------- Begin Adding data from URL into a dictionary of lists ---------------"""
        # iterate through the lines in the report
        arcpy.SetProgressor("step", "Reading NASIS Report: 'WEB_AnalysisPC_MAIN_URL_EXPORT'", 0, len(theReport),1)

        memoryStartTime = tic()
        for theValue in theReport:

            theValue = theValue.strip() # remove whitespace characters

            # represents the start of valid table
            if theValue.find('@begin') > -1:
                theTable = theValue[theValue.find('@') + 7:]  ## Isolate the table
                numOfFields = tableFldDict[theTable]

                # Check if the table name exists in the list of dictionaries
                # if so, set the currentTable variable and bHeader
                if pedonGDBtables.has_key(theTable):
                    currentTable = theTable
                    bHeader = True  ## Next line will be the header

                else:
                    AddMsgAndPrint("\t" + theTable + " Does not exist in the FGDB schema!  Figure this out Jason Nemecek!",2)
                    invalidTable += 1

            # end of the previous table has been reached; reset currentTable
            elif theValue.find('@end') > -1:
                currentTable = ""
                bHeader = False

            # represents header line; skip this line
            elif bHeader:
                bHeader = False

            # this is a valid record that should be collected
            elif not bHeader and currentTable:
                numOfValues = len(theValue.split('|'))

                # Add the record to its designated list within the dictionary
                # Do not remove the double quotes b/c doing so converts the object
                # to a list which increases its object size.  Remove quotes before
                # inserting into table

                # this should represent the 2nd half of a valid value
                if bPartialValue:
                    partialValue += theValue  # append this record to the previous record

                    # This value completed the previous value
                    if len(partialValue.split('|')) == numOfFields:
                        pedonGDBtables[currentTable].append(partialValue)
                        validRecord += 1
                        bPartialValue = False
                        partialValue,originalValue = "",""

                    # appending this value still falls short of number of possible fields
                    # add another record; this would be the 3rd record appended and may
                    # exceed number of values.
                    elif len(partialValue.split('|')) < numOfFields:
                        arcpy.SetProgressorPosition()
                        continue

                    # appending this value exceeded the number of possible fields
                    else:
                        AddMsgAndPrint("\t\tIncorrectly formatted Record Found in " + currentTable + " table:",2)
                        AddMsgAndPrint("\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(len(partialValue.split('|'))),2)
                        AddMsgAndPrint("\t\t\tOriginal Record: " + originalValue,2)
                        AddMsgAndPrint("\t\t\tAppended Record: " + partialValue,2)
                        invalidRecord += 1
                        bPartialValue = False
                        partialValue,originalValue = ""

                # number of values do not equal the number of fields in the corresponding tables
                elif numOfValues != numOfFields:

                    # number of values exceed the number of fields; Big Error
                    if numOfValues > numOfFields:
                        AddMsgAndPrint("\n\t\tIncorrectly formatted Record Found in " + currentTable + " table:",2)
                        AddMsgAndPrint("\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(numOfValues),2)
                        AddMsgAndPrint("\t\t\tRecord: " + theValue,2)
                        invalidRecord += 1

                    # number of values falls short of the number of correct fields
                    else:
                        partialValue,originalValue = theValue,theValue
                        bPartialValue = True

                else:
                    pedonGDBtables[currentTable].append(theValue)
                    validRecord += 1
                    bPartialValue = False
                    partialValue = ""

            elif theValue.find("ERROR") > -1:
                AddMsgAndPrint("\n\t\t" + theValue[theValue.find("ERROR"):],2)
                return False

            else:
                invalidRecord += 1

            arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()

        #AddMsgAndPrint(tab + "Storing Data into Memory: " + toc(memoryStartTime))

        if not validRecord:
            AddMsgAndPrint("\t\tThere were no valid records captured from NASIS request",2)
            AddMsgAndPrint(str(URL))
            return False

        # Report any invalid tables found in report; This should take care of itself as Jason perfects the report.
        if invalidTable and invalidRecord:
            AddMsgAndPrint("\t\tThere were " + splitThousands(invalidTable) + " invalid table(s) included in the report with " + splitThousands(invalidRecord) + " invalid record(s)",1)

        # Report any invalid records found in report; There are 27 html lines reserved for headers and footers
        if invalidRecord > 28:
            AddMsgAndPrint("\t\tThere were " + splitThousands(invalidRecord) + " invalid record(s) not captured",1)

        return True

    except URLError, e:
        if hasattr(e, 'reason'):
            AddMsgAndPrint(tab + "URL Error: " + str(e.reason), 2)

        elif hasattr(e, 'code'):
            AddMsgAndPrint(tab + e.msg + " (errorcode " + str(e.code) + ")", 2)

        return False

    except socket.timeout, e:
        AddMsgAndPrint(tab + "Server Timeout Error", 2)
        return False

    except socket.error, e:
        AddMsgAndPrint(tab + "NASIS Reports Website connection failure", 2)
        return False

    except httplib.BadStatusLine:
        AddMsgAndPrint(tab + "NASIS Reports Website connection failure", 2)
        return False

    except:
        errorMsg()
        return False

## ================================================================================================================
def importPedonData(tblAliases,verbose=False):
    """ This function will purge the contents from the pedonGDBtables dictionary which contains all of the pedon
        data into the pedon FGDB.  Depending on the number of pedons in the user's AOI, this function will be
        used multiple times.  The pedonGDBtables dictionary could possilbly allocate all of the computer's
        memory so a fail-save was built in to make sure a memory exception error wasn't encountered.  This
        function is invoked when approximately 40,000 pedons have been retrieved from the server and stored in \
        memory."""

    try:

        if verbose: AddMsgAndPrint("\nImporting Pedon Data into FGDB")
        arcpy.SetProgressorLabel("Importing Pedon Data into FGDB")

        # use the tblAliases so that tables are imported in alphabetical order
        if bAliasName:
            tblKeys = tblAliases.keys()
            maxCharTable = max([len(table) for table in tblKeys]) + 1
            maxCharAlias = max([len(value[1]) for value in tblAliases.items()])

            firstTab = (maxCharTable - len("Table Physical Name")) * " "
            headerName = "\n\tTable Physical Name" + firstTab + "Table Alias Name"
            if verbose: AddMsgAndPrint(headerName,0)
            if verbose: AddMsgAndPrint("\t" + len(headerName) * "=",0)

        else:
            maxCharTable = max([len(table) for table in tblKeys]) + 1
            tblKeys = pedonGDBtables.keys()

        tblKeys.sort()

        """ ---------------------------------------------------"""
        arcpy.SetProgressor("step","Importing Pedon Data into FGDB",0,len(tblKeys),1)
        for table in tblKeys:

            arcpy.SetProgressorLabel("Importing Pedon Data into FGDB table: " + table)
            arcpy.SetProgressorPosition()

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            # Capture the alias name of the table
            if bAliasName:
                aliasName = tblAliases[table]

            # Strictly for standardizing reporting
            firstTab = (maxCharTable - len(table)) * " "

            # check if list contains records to be added
            if len(pedonGDBtables[table]):

                numOfRowsAdded = 0
                GDBtable = pedonFGDB + os.sep + table # FGDB Pyhsical table path

                """ -------------------------------- Collect field information -----------------------"""
                ''' For the current table, get the field length if the field is a string.  I do this b/c
                the actual value may exceed the field length and error out as has happened in SSURGO.  If
##                the value does exceed the field length then the value will be truncated to the max length
                of the field '''

                # Put all the field names in a list
                fieldList = arcpy.Describe(GDBtable).fields
                nameOfFields = []
                fldLengths = []

                for field in fieldList:

                    # Skip Object ID field Shape field (only for pedon)
                    if not field.type.lower() in ("oid","geometry"):
                        nameOfFields.append(field.name)

                        if field.type.lower() == "string":
                            fldLengths.append(field.length)
                        else:
                            fldLengths.append(0)

                # Add a new field at the end called 'labsampleIndicator' to indicate whether
                # record is a LAB pedon. Addd XY token to list
                if table == 'pedon':

##                    labField = 'labsampleIndicator'
##                    arcpy.AddField_management(GDBtable,'labsampleIndicator','TEXT','#','#',3,'Lab Sample Indicator','#','#','#')
##                    nameOfFields.append(labField)

                    # Pedon feature class will have X,Y geometry added; Add XY token to list
                    nameOfFields.append('SHAPE@XY')
                    fldLengths.append(0)  # X coord
                    fldLengths.append(0)  # Y coord

##                    peiidFld = [f.name for f in arcpy.ListFields(table,'peiid')][0]
##                    peiidIndex = nameOfFields.index(peiidFld)

                """ -------------------------------- Insert Rows ------------------------------------------
                    Iterate through every value from a specific table in the pedonGDBtables dictary
                    and add it to the appropriate FGDB table  Truncate the value if it exceeds the
                    max number of characters.  Set the value to 'None' if it is an empty string."""

                # Initiate the insert cursor object using all of the fields
                cursor = arcpy.da.InsertCursor(GDBtable,nameOfFields)
                recNum = 0

                # '"S1962WI025001","43","15","9","North","89","7","56","West",,"Dane County, Wisconsin. 100 yards south of road."'
                for rec in pedonGDBtables[table]:

                    newRow = list()  # list containing the values that will populate a new row
                    fldNo = 0        # list position to reference the field lengths in order to compare

                    for value in rec.replace('"','').split('|'):

                        value = value.strip()
                        fldLen = fldLengths[fldNo]

                        if value == '':   ## Empty String
                            value = None

                        elif fldLen > 0:  ## record is a string, truncate it
                            value = value[0:fldLen]

                        else:             ## record is a number, keep it
                            value = value

                        newRow.append(value)
                        fldNo += 1

                    # Add XY coordinates to the pedon point feature class.
                    if table == 'pedon':
                        try:
                            xValue = float(newRow[-1])  # Long
                            yValue = float(newRow[-2])  # Lat
                        except:
                            xValue = 0.00
                            yValue = 90.0

                        # remove the X,Y coords from the newRow list b/c X,Y
                        # fields don't exist in the pedon Table
                        newRow = newRow[:-2]

                        newRow.append((xValue,yValue))
                        del xValue,yValue

##                    """ -----------------------------------Pedon Feature Class-------------------------
##                        The X,Y coordinates need to come from the site table.
##                        pedon ---> siteobs ---> site
##                        1) Link to the siteobs table using the siteobsiidref field
##                        2) Get the siteiid from the siteobs table
##                        3) Retrieve the X,Y coords from site table"""
##
##                    if table == 'pedon':
##
##                        # Primary key from 'Siteobs' table that links to Pedon Table
##                        siteobsiid = rec.split('|')[0] # <-- represents siteobsiidref key
##                        siteiid = ""
##
##                        # iterate through the siteobs values looking for a siteobsiid match
##                        # ['|6/24/1991 12:00:00 AM|Actual Site Observation Date||2|||||||||||||||||0|||||||||0|0|0||||||||||||||||10873|10818']
##                        for v in pedonGDBtables.get('siteobs'):
##                            if v.split('|')[-1] == siteobsiid:
##                                siteiid = v.split('|')[-2]
##
##                        if siteiid:
##                            for v in pedonGDBtables.get('site'):
##                                if v.split('|')[-1] == siteiid:
##                                    try:
##                                        xValue = float(v.split('|')[-6])
##                                        yValue = float(v.split('|')[-7])
##                                    except:
##                                        xValue = 0.00
##                                        yValue = 90.0
##
##                        else:
##                            AddMsgAndPrint("\tsiteiid value not found for siteobs value: " + str(siteobsiid),2)
##
##                    newRow.append((xValue,yValue))

                    try:
                        cursor.insertRow(newRow)
                        numOfRowsAdded += 1;recNum += 1

                    except:
                        AddMsgAndPrint("\n\tError in: " + table + " table",2)

                        if not len(nameOfFields) == len([rec.split('|')][0]):
                            AddMsgAndPrint("\tNumber of fields in table: " + str(len(nameOfFields)),2)
                            AddMsgAndPrint("\tNumber of fields in report: " + str(len([rec.split('|')][0])),2)

                        AddMsgAndPrint("\tRecord Values: " + str(newRow),2)

                        errorMsg()
                        break

                    del newRow,fldNo

                # Report the # of records added to the table
                tableRecords = int(arcpy.GetCount_management(GDBtable).getOutput(0))

                if bAliasName:
                    secondTab = (maxCharAlias - len(aliasName)) * " "
                    if verbose: AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: " + splitThousands(tableRecords),1)
                    #if verbose: AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: " + splitThousands(numOfRowsAdded),1)
                else:
                    if verbose: AddMsgAndPrint("\t" + table + firstTab + " Records Added: " + splitThousands(tableRecords),1)

                del numOfRowsAdded,GDBtable,fieldList,nameOfFields,fldLengths,cursor,tableRecords

            # Table had no records; still print it out
            else:
                if bAliasName:
                    secondTab = (maxCharAlias - len(aliasName)) * " "
                    if verbose: AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: 0",1)
                else:
                    if verbose: AddMsgAndPrint("\t" + table + firstTab + " Records Added: 0",1)

        #Resets the progressor back to its initial state
        arcpy.ResetProgressor()

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (importPedonData)", 2)
        print "\nRec: " + rec
        print "\nfldNo: " + str(fldNo)
        print "\nLength of nameOfFields: " + str(len(nameOfFields))
        print "\nLength of fldLengths: " + str(len(fldLengths))

        errorMsg()
        return False

## ================================================================================================================
def getObjectSize(obj, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}
    """

    try:
        # lamda function to iterate through a dictionary
        dict_handler = lambda d: chain.from_iterable(d.items())

    #     Use the following lines if you want to determine the size for ANY object
    ##    all_handlers = {tuple: iter,
    ##                    list: iter,
    ##                    deque: iter,
    ##                    dict: dict_handler,
    ##                    set: iter,
    ##                    frozenset: iter,
    ##                   }

        # Limit the focus to just dictionaries since that is the only thing I will pass
        all_handlers = {dict: dict_handler}

        all_handlers.update(handlers)     # user handlers take precedence
        seen = set()                      # unique list of Object's memory ID
        default_size = getsizeof(0)       # estimate sizeof object without __sizeof__; a dict will always be 140 bytes

        def sizeof(obj):

            if id(obj) in seen:       # do not double count the same object's memory ID
                return 0

            seen.add(id(obj))
            s = getsizeof(obj, default_size)

            if verbose:
                print(s, type(obj), repr(obj))

            # iterate through all itemized objects (tuple,list) 'all_handlers' including their content
            for typ, handler in all_handlers.items():

                # check if the object is associated with the type at hand.  i.e. if the current
                # type is dict then check if the object 'o' is a dict. ({'a': 1, 'c': 3, 'b': 2, 'e': 'a string of chars', 'd': [4, 5, 6, 7]})
                # if True, go thru and add the bytes for each eleement
                if isinstance(obj, typ):
                    s += sum(map(sizeof, handler(obj)))   # Iterates through this function
                    break

            return s

        byteSize = sizeof(obj)

        if byteSize < 1024:
            return splitThousands(byteSize) + " bytes"
        elif byteSize > 1023 and byteSize < 1048576:
            return splitThousands(round((byteSize / 1024.0),1)) + " KB"
        elif byteSize > 1048575 and byteSize < 1073741824:
            return splitThousands(round((byteSize / (1024*1024.0)),1)) + " MB"
        elif byteSize > 1073741823:
            return splitThousands(round(byteSize / (1024*1024*1024.0),1)) + " GB"

    except:
        errorMsg()
        pass

#===================================================================================================================================
""" ----------------------------------------My Notes -------------------------------------------------"""

""" --------------- Column Headers
Column order
1.	Row_Number2,
2.	upedonid,
3.	peiid,
4.	pedlabsampnum,
5.	longstddecimaldegrees ,
6.	latstddecimaldegrees
                    ----------------------"""

""" 1st Report """
# Used to get a number of pedons that are within a bounding box
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_ANALYSIS_PC_PEDON_NUMBER_SUM&lat1=43&lat2=45&long1=-90&long2=-88

""" 2nd Report """
# Used to get a list of peiid which will be passed over to the 2nd report0
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&lat1=43&lat2=45&long1=-90&long2=-88

""" 3rd Report """
# This report will contain pedon information to be parsed into a FGDB.

# Raw URL
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=TEST_sub_pedon_pc_6.1_phorizon&pedonid_list=    OLD one
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=    NEW one

# Sample complete URL with pedonIDs:
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=36186,59976,60464,60465,101219,102867,106105,106106
#===================================================================================================================================


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy, socket, httplib, time, base64
from arcpy import env
from urllib2 import urlopen, URLError, HTTPError
from sys import getsizeof, stderr
from itertools import chain
from collections import deque

if __name__ == '__main__':

    try:

        GDBname = arcpy.GetParameter(0)
        outputFolder = arcpy.GetParameterAsText(1)
        question = arcpy.GetParameterAsText(2)

        GDBname = 'OnePedon'
        outputFolder = r'C:\Temp'
        question = 'dylanbeaudette'

        if not base64.b64encode(question) == r'ZHlsYW5iZWF1ZGV0dGU=':
            AddMsgAndPrint("\n\nYou do not have permission to execute this tool",2)
            exit()

        """ ------------------------------------------------------------------------ Set Scratch Workspace -------------------------------------------------------------------------------------"""
##        scratchWS = setScratchWorkspace()
##        arcpy.env.scratchWorkspace = scratchWS
##
##        if not scratchWS:
##            AddMsgAndPrint("\n Failed to scratch workspace; Try setting it manually",2)
##            exit()

        """ -------------------------------------------------- Get a list of PedonIDs that are within the bounding box from NASIS -----------------------------------------------------------------
            ---------------------------------------------------- Uses the 'WEB_EXPORT_PEDON_BOX_COUNT' NASIS report --------------------------------------------------------------------------"""
        # ['10851', '10852', '10853', '10854']
        pedonDict = getListOfAllPedonIDs()
        exit()

        ##pedonidList = pedonidList[0:10000]
        ##pedonidList = ['10851', '10852', '10853', '10854']
        ##pedonidList = [(line.rstrip('\n')).split(',') for line in open(inputTextFile)].pop()

        totalPedons = len(pedonidList)
        AddMsgAndPrint("\n" + splitThousands(totalPedons) + " pedons will be downloaded from NASIS")

        """ ------------------------------------------------------Create New File Geodatabaes and get Table Aliases for printing -------------------------------------------------------------------
            Create a new FGDB using a pre-established XML workspace schema.  All tables will be empty
            and relationships established.  A dictionary of empty lists will be created as a placeholder
            for the values from the XML report.  The name and quantity of lists will be the same as the FGDB"""

        pedonFGDB = createPedonFGDB()
        #pedonFGDB = os.path.join(outputFolder,GDBname + ".gdb")

        if not pedonFGDB:
            AddMsgAndPrint("\nFailed to Initiate Empty Pedon File Geodatabase.  Error in createPedonFGDB() function. Exiting!",2)
            exit()

        # Acquire Aliases.  This is only used for printing purposes
        tblAliases = dict()
        bAliasName = True

        if not getTableAliases(pedonFGDB):
            AddMsgAndPrint("\nCould not retrieve alias names from \'MetadataTable\'",1)
            bAliasName = False

        """ ------------------------------------------------------Create dictionary with all of the NASIS 7.3 tables  -------------------------------------------------------------------
            Create a new dictionary called pedonGDBtables that will contain every table in the newly created
            pedonFGDB above as a key.  Individual records of tables will be added as values to the table keys.
            These values will be in the form of lists.  This dictionary will be populated using the results of
            the WEB_AnalysisPC_MAIN_URL_EXPORT NASIS report.  Much faster than opening and closing cursors."""

        pedonGDBtables = createEmptyDictOfTables()

        """ --------------------------------------------------- Create a dictionary of number of fields per table -----------------------------------------------------------------------
            Create a dictionary that will contain table:number of fields in order
            to double check that the values from the web report are correct
            this was added b/c there were text fields that were getting disconnected in the report
            and being read as 2 lines -- Jason couldn't address this issue in NASIS """

        tableFldDict = createTableFieldLookuup()

        """ ------------------------------------------ Get Site, Pedon, and Pedon Horizon information from NASIS -------------------------------------------------------------------------
        ----------------------------------------------- Uses the 'WEB_AnalysisPC_MAIN_URL_EXPORT' NASIS report ---------------------------------------------------------------------------
        In order to request pedon information, the pedonIDs need to be split up into manageable
        lists of about 265 pedons due to URL limitations.  Submit these individual lists of pedon
        to the server --------------------------------------------------------------------------------------------------------------------------------------------------------------------"""

        # Parse pedonIDs into lists containing about 265 pedons
        listOfPedonStrings,numOfPedonStrings = parsePedonsIntoLists()

        if numOfPedonStrings > 1:
            AddMsgAndPrint("\nDue to URL limitations there will be " + splitThousands(len(listOfPedonStrings))+ " seperate requests to NASIS:",1)
        else:
            AddMsgAndPrint("\n")

        i = 1                                         # represents the request number
        j = 0                                         # number of Pedons that are in memory;gets reset once dumped into FGDB
        k = 0                                         # number of total pedons that have been requested thus far

        badStrings = list()                           # list containing lists of pedons that failed
        failedAttempts = 0                            # Number of failed attempts to request data. It does NOT account for the
                                                      # multiple attempts within the getPedonHorizon function.

        """ --------- iterate through groups of pedonIDs to retrieve their data ------------ """
        for pedonString in listOfPedonStrings:

            numOfPedonsInPedonString = len(pedonString.split(','))
            j+=numOfPedonsInPedonString
            k+=numOfPedonsInPedonString

            """ Strictly for formatting print message"""
            if numOfPedonStrings > 2:
                AddMsgAndPrint("\tRequest " + splitThousands(i) + " of " + splitThousands(numOfPedonStrings) + " for " + str(len(pedonString.split(','))) + " pedons",0)
                arcpy.SetProgressorLabel("Request " + splitThousands(i) + " of " + splitThousands(numOfPedonStrings) + " for " + str(len(pedonString.split(','))) + " pedons")
            else:
                AddMsgAndPrint("Retrieving pedon data from NASIS for " + str(len(pedonString.split(','))) + " pedons.",0)
                arcpy.SetProgressorLabel("Retrieving pedon data from NASIS for " + str(len(pedonString.split(','))) + " pedons.")

            """ Submit string of pedons to server to get pedon information """
            if not getPedonHorizon(pedonString):
                AddMsgAndPrint("\tFailed to receive pedon horizon info from NASIS",2)
                badStrings += pedonString
                k-=numOfPedonsInPedonString
                failedAttempts+=1

            #AddMsgAndPrint("\t\tCurrent Size of pedonGDBtables dictionary: " + getObjectSize(pedonGDBtables, verbose=False),0)

            """ Import pedons from memory to the FGDB after about 40000 pedons have been requested to avoid Memory Errors"""
            if j > 40000  or i == numOfPedonStrings:

                # Only print if number of pedons exceed 40,000
                if not i == numOfPedonStrings:
                    AddMsgAndPrint("\n\tUnloading pedon data into FGDB to avoid memory issues. Current size: " + str(getObjectSize(pedonGDBtables, verbose=False)) + " -- Number of Pedons: " + splitThousands(j) ,1)

                # Import Pedon Information into Pedon FGDB
                if len(pedonGDBtables['pedon']):
                    if not importPedonData(tblAliases,verbose=(True if i==numOfPedonStrings else False)):
                        exit()

                    del pedonGDBtables

                    # recreate pedonGDBtables dictionary only if the requests are not done
                    if not i == numOfPedonStrings:
                        pedonGDBtables = createEmptyDictOfTables()
                        j=0
            i+=1

        """ ------------------------------------ Report Summary of results -----------------------------------"""
        pedonTable = os.path.join(pedonFGDB,'pedon')
        pedonCount = int(arcpy.GetCount_management(pedonTable).getOutput(0))

        # Text file that will be created with pedonIDs that did not get collected
        errorFile = outputFolder + os.sep + os.path.basename(pedonFGDB).split('.')[0] + "_error.txt"

        if totalPedons == pedonCount:
            AddMsgAndPrint("\n\nSuccessfully downloaded " + splitThousands(totalPedons) + " pedons from NASIS",0)
        else:
            difference = totalPedons - pedonCount
            AddMsgAndPrint("\n\nDownloaded " + splitThousands(pedonCount) + " from NASIS",2)
            AddMsgAndPrint("\tFailed to download " + splitThousands(difference) + " pedons from NASIS:",2)

            downloadedPedons = [str(row[0]) for row in arcpy.da.SearchCursor(pedonTable,'peiid')]
            missingPedons = str(list(set(pedonList) - set(downloadedPedons))).replace('[','').replace(']','').replace('\'','')

            f = open(errorFile,'a+')
            if os.stat(errorFile).st_size == 0:
                f.write(str(missingPedons))
            else:
                f.write("," + str(missingPedons))
            f.close()

            if difference < 20:
                AddMsgAndPrint("\t\t" + missingPedons)

            AddMsgAndPrint("\n\tThe Missing Pedons have been written to " + errorFile + " files",2)

        """ ---------------------------Add Pedon Feature Class to ArcMap Session if available ------------------"""
        try:
            mxd = arcpy.mapping.MapDocument("CURRENT")
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            lyr = os.path.join(pedonFGDB,'pedon')
            newLayer = arcpy.mapping.Layer(lyr)
            arcpy.mapping.AddLayer(df, newLayer, "TOP")
            AddMsgAndPrint("\nAdded the pedon feature class to your ArcMap Session",0)
        except:
            pass

        AddMsgAndPrint("\n")

    except MemoryError:
        AddMsgAndPrint("\n\nOut of Memory Genius! --- " + str(sys.getsizeof(pedonGDBtables)),2)
        exit()

    except:
        errorMsg()
