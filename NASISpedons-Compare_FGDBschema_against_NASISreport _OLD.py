#-------------------------------------------------------------------------------
# Name:        NASISpedons_compareFGDBschema_against_NASISreport.py
# Purpose:     This script will compare the table and fields from the input FGDB
#              to the tables and fields from the 'WEB Analysis PC MAIN URL Export'
#              NASIS report that follows the NASIS 7.1 Schema.
#              It is primarily for Jason Nemecek to adjust the pedon reports so that
#              they match the an updated schema.
#
# Author:      Adolfo.Diaz
#
# Created:     04/08/2016
# Last Modified: 9/28/2016
# Copyright:   (c) Adolfo.Diaz 2018
#-------------------------------------------------------------------------------

# ==========================================================================================
# Updated  2/16/2022 - Adolfo Diaz
# The script was updated to allow comparison of schemas between 2 FGDBs rather than just
# against the the 'WEB Analysis PC MAIN URL Export' rerport.
# If there are discrepancies between tables/schemas then the fields will be printed twice
# in 2 different formats so that jason can simply copy and paste as he updates the fields
# in his report. The fields are printed in the correct sequence as well.


## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print(msg)

        try:
            f = open(textFilePath,'a+')
            f.write(msg + " \n")
            f.close
            del f
        except:
            pass

        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError(msg)

    except:
        pass

## ===================================================================================
def errorMsg():
    try:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]

        if theMsg.find("exit") > -1:
            AddMsgAndPrint("\n\n")
            pass
        else:
            AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

# ===============================================================================================================
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

# =========================================================== Main Body =============================================================================
# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from urllib.request import Request
from arcpy import env

if __name__ == '__main__':

    try:
        # New pedon template schema will either be compared to the URL report or the old Pedon template
        sampleURL = "https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=36186"
        oldPedonTemplate = r'E:\python_scripts\GitHub\NCSS-Pedons---ArcGIS-Pro\NASISPedonsFGDBTemplate.gdb'

        # True = Use NASIS URL to compare; False = Use older pedon Template FGDB
        bUseNASISurlReport = False

        newPedonTemplate =  os.path.dirname(sys.argv[0]) + os.sep + 'NASISPedonsTemplate_7_4_1.gdb'
        textFilePath = os.path.dirname(sys.argv[0]) + os.sep + "CompareSchemas_logFile.txt"

        # This is the same metadata table that is used to create the FGDB template using the NASISpedons_Create_FGDBschema_fromNASIS_Metadata.py script.
        schemaTable = r'E:\python_scripts\GitHub\NCSS-Pedons---ArcGIS-Pro\Metadata_Tables.gdb\PedonMetadataTableColDesc'
        tableName = 2
        tableAlias = 1
        fieldSequence = 5
        fieldPhysicalName = 7
        fieldAlias = 8
        fieldType = 9
        fieldNull = 11
        fieldSize = 15
        domain = 22

##        tablab = 1             # Table Alias
##        tabphynm = 2           # Table Physical Name
##        tabhelptext = 4        # Table Description
##        coldefseq = 5          # Field Sequence
##        attphynm = 7           # Field Physical Name
##        collab = 8             # Field Alias
##        cholabtxt = 9          # Field Type
##        colnotnulbool = 11     # Field Allow NULLs
##        attfldsiz = 15         # Field Length
##        attprec = 16           # Field Precision
##        domnm = 22             # Field Domain
##        aggregation = 23       # Determines whether a field needs to be disaggregated into 3 individual fields _l, _r, _h
##

        schemaFlds = [f.name for f in arcpy.ListFields(schemaTable)]

        nasisDict = dict()  # collection of table and field names {'siteobs': ['seqnum','obsdate','obsdatekind']

        if bUseNASISurlReport:
            """ --------------------------------- Parse the report to isolate the NASIS tables and fields -------------------------"""
            tempTableName = ""  # name of the current table

            theReport = urllib.request.urlopen(sampleURL).readlines()
            bFieldNameRecord = False # boolean that marks the starting point of the table and attributes.

            # iterate through the report until a valid record is found
            for theValue in theReport:

                # convert from bytes to string and remove white spaces
                theValue = theValue.decode('utf-8').strip()

                fieldNames = list()
                theValue = theValue.strip() # remove whitespace characters

                # Iterating through the report
                if bFieldNameRecord:

                    nasisDict[tempTableName] = (theValue.split('|'))
                    tempTableName = ""
                    bFieldNameRecord = False

                elif theValue.find('@begin') > -1:
                    bFieldNameRecord = True
                    tempTableName = theValue[theValue.find('@begin')+7:]

                else:
                    continue

            del bFieldNameRecord,tempTableName

        else:
            arcpy.env.workspace = oldPedonTemplate
            oldTables = arcpy.ListTables('*')
            oldTables.append(r'pedon')

            for tbl in oldTables:
                tblPath = f"{oldPedonTemplate}\{tbl}"
                flds = [f.name for f in arcpy.ListFields(tblPath)]
                flds.remove('OBJECTID')
                nasisDict[tbl] = flds

        if not len(nasisDict):
            AddMsgAndPrint("\n\nNo records returned for pedon ID: " + str(pedonID))
            exit()

        """ --------------------------------- Collect FGDB tables and fields -------------------------"""
        arcpy.env.workspace = newPedonTemplate
        newPedonTemplateTables = arcpy.ListTables('*')

        if arcpy.ListFeatureClasses('pedon'):newPedonTemplateTables.append('pedon') # Site is not a table so we will manually add it.
        missingTables = list()

        """ ---------------------------------------- Begin the Comparison between NASIS URL and FGDB -----------------------------"""
        discrepancies = 0
        for nasisTable in nasisDict.keys():

            # Skip any Metadata table
            if nasisTable.find("Metadata") > -1: continue

            # Check if NASIS table exists in Pedon FGDB; log and continue if it doesn't
            if not nasisTable in newPedonTemplateTables:
                missingTables.append(nasisTable)
                continue

            else:
                newPedonTemplateTables.remove(nasisTable)

            gdbTableFields = [f.name for f in arcpy.ListFields(newPedonTemplate + os.sep + nasisTable)]   # List of GDB table fields
            nasisFields = [value for value in nasisDict.get(nasisTable)]                          # List of NASIS table fields
            fieldsMissingGDB = list()                                                             # List of NASIS fields missing from FGDB

            # remove OBJECTID from gdbTableFields list
            if 'OBJECTID' in gdbTableFields:
                gdbTableFields.remove('OBJECTID')

            if 'SHAPE' in gdbTableFields:
                gdbTableFields.remove('SHAPE')

            gdbTableFieldsTotal = len(gdbTableFields)  # number of fields in the FGDB table
            nasisFieldsTotal = len(nasisFields)        # number of fields in the NASIS table

            if gdbTableFieldsTotal == nasisFieldsTotal:
                sameNumOfFields = True
            else:
                sameNumOfFields = False

            # Check for NASIS fields missing in the GDB
            for nasisField in nasisFields:

                if not str(nasisField) in gdbTableFields:
                    fieldsMissingGDB.append(nasisField)
                else:
                    gdbTableFields.remove(nasisField)

            """ -----------------------------------------------Report any tabular field problems to user -------------------------------"""
            AddMsgAndPrint("\n=============================================================================================",0)
            tablePrinted = False

            if not len(fieldsMissingGDB) and not len(gdbTableFields):
                AddMsgAndPrint(nasisTable + " Table:",0)
                AddMsgAndPrint("\tAll NASIS report fields match FGDB")
                continue

            #
            if len(fieldsMissingGDB):
                AddMsgAndPrint(nasisTable + " Table:",2)

                if bUseNASISurlReport:
                    AddMsgAndPrint("\tThe following NASIS report fields do NOT exist in the FGDB table:",1)
                else:
                    AddMsgAndPrint("\tThe following fields need to be removed from the WEB_AnalysisPC_MAIN_URL_EXPORT report:",1)

                AddMsgAndPrint("\t\t" + str(fieldsMissingGDB))
                tablePrinted = True
                discrepancies += len(fieldsMissingGDB)

            if len(gdbTableFields):
                if not tablePrinted:
                    AddMsgAndPrint(nasisTable + " Table:",2)

                if bUseNASISurlReport:
                    AddMsgAndPrint("\n\tThe following FGDB fields do NOT exist in the NASIS report:",1)
                else:
                    AddMsgAndPrint("\n\tThe following fields need to be added to the WEB_AnalysisPC_MAIN_URL_EXPORT report:",1)

                AddMsgAndPrint("\t\t" + str(gdbTableFields))
                discrepancies += len(gdbTableFields)

            # Print all of the fields in their correct format and sequence so that Jason can copy and paste directly
            # into the NASIS report; This will save Jason a ton of time.  This will only print if there are field discrepancies
            # in the table.

            whereClause = f"{schemaFlds[tableName].upper()} = \'{nasisTable}\'"
            sqlPostfix = f"ORDER BY {schemaFlds[fieldSequence].upper()} ASC"
            tableFlds = list()
            with arcpy.da.SearchCursor(schemaTable,[schemaFlds[fieldPhysicalName],schemaFlds[domain]],where_clause=whereClause,sql_clause=(None,sqlPostfix)) as cursor:
                for row in cursor:
                     key = row[0]
                     if row[1] is None:
                        value = None
                     else:
                        value = '*'

                     tableFlds.append((key,value))

            AddMsgAndPrint(f"{os.linesep}{30*'-'} FORMAT #1: LIST OF TABLE FIELDS IN PROPER SEQUENCE")
            i = 1
            j = len(tableFlds)
            for fld in tableFlds:
                if i < j:
                    AddMsgAndPrint(f"\'{fld[0]}\',")
                else:
                    AddMsgAndPrint(f"\'{fld[0]}\'.")
                i+=1


            AddMsgAndPrint(f"{os.linesep}{30*'-'} FORMAT #2: LIST OF TABLE FIELDS IN PROPER SEQUENCE")
            i = 1
            j = len(tableFlds)
            for fld in tableFlds:
                if i < j:
                    AddMsgAndPrint(f"{fld[0]}   ,{'*' if not fld[1] == None else ''}")
                else:
                    AddMsgAndPrint(f"{fld[0]}   .{'*' if not fld[1] == None else ''}")
                i+=1

            del gdbTableFields,nasisFields,gdbTableFieldsTotal,nasisFieldsTotal,fieldsMissingGDB,tablePrinted

        """ ---------------------------------------------------- Report any missing tables to the user ----------------------------------"""
        if len(missingTables):
            AddMsgAndPrint("\n=============================================================================================",0)
            AddMsgAndPrint("The following NASIS report Tables do NOT exist in the FGDB:",2)
            missingTables.sort()
            AddMsgAndPrint("\t" + str(missingTables))
            discrepancies += len(missingTables)

        if len(newPedonTemplateTables):
            AddMsgAndPrint("\n=============================================================================================",0)
            AddMsgAndPrint("The following FGDB Tables do NOT exist in the NASIS report:",2)
            newPedonTemplateTables.sort()
            AddMsgAndPrint("\t" + str(newPedonTemplateTables))
            discrepancies += len(newPedonTemplateTables)
        else:
            AddMsgAndPrint("\n\n")

        if discrepancies:
            AddMsgAndPrint("\nTotal # of discrepancies between NASIS report and FGDB: " + str(splitThousands(discrepancies)) + "\n\n",2)
        else:
            AddMsgAndPrint("\nThere are no discrepancies between NASIS report and FGDB....CONGRATULATIONS!\n\n",0)

        del missingTables,newPedonTemplateTables

    except:
        errorMsg()




