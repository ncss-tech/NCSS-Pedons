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

        if bWrite:
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

    bWrite = False

    try:
        # New pedon template schema will either be compared to the URL report or the old Pedon template
        oldPedonTemplate = r'E:\python_scripts\GitHub\NCSS-Pedons---ArcGIS-Pro\NASISPedonsFGDBTemplate.gdb'

        newPedonTemplate =  os.path.dirname(sys.argv[0]) + os.sep + 'NASISPedonsTemplate_NASIS_7_4_1.gdb'
        textFilePath = os.path.dirname(sys.argv[0]) + os.sep + "CompareSchemas_logFile.txt"

        # This is the same metadata table that is used to create the FGDB template using the NASISpedons_Create_FGDBschema_fromNASIS_Metadata.py script.
        tblColFldsDesc = r'E:\python_scripts\GitHub\NCSS-Pedons---ArcGIS-Pro\Metadata_Tables.gdb\PedonMetadataTableColDesc'
        tableName = 2
        tableAlias = 1
        fieldSequence = 5
        fieldPhysicalName = 7
        fieldAlias = 8
        fieldType = 9
        fieldNull = 11
        fieldSize = 15
        domain = 22

        tablab = 1             # Table Alias
        tabphynm = 2           # Table Physical Name
        tabhelptext = 4        # Table Description
        coldefseq = 5          # Field Sequence
        attphynm = 7           # Field Physical Name
        collab = 8             # Field Alias
        cholabtxt = 9          # Field Type
        colnotnulbool = 11     # Field Allow NULLs
        attfldsiz = 15         # Field Length
        attprec = 16           # Field Precision
        domnm = 22             # Field Domain
        aggregation = 23       # Determines whether a field needs to be disaggregated into 3 individual fields _l, _r, _h

        metadataFlds = [f.name for f in arcpy.ListFields(tblColFldsDesc)]
        oldTblColDict = dict()  # collection of table and field names {'siteobs': ['seqnum','obsdate','obsdatekind']

        """ --------------------------------- Collect OLD FGDB tables and fields -------------------------"""
        arcpy.env.workspace = oldPedonTemplate
        oldTables = arcpy.ListTables('*')
        oldTables.append(r'pedon')

        for tbl in oldTables:
            tblPath = f"{oldPedonTemplate}\{tbl}"
            flds = [f.name for f in arcpy.ListFields(tblPath)]
            flds.remove('OBJECTID')
            oldTblColDict[tbl] = flds

        if not len(oldTblColDict):
            AddMsgAndPrint("\n\nNo records returned for pedon ID: " + str(pedonID))
            exit()

        """ --------------------------------- Collect NEW FGDB tables and fields -------------------------"""
        arcpy.env.workspace = newPedonTemplate
        newPedonTemplateTables = arcpy.ListTables('*')

        if arcpy.ListFeatureClasses('pedon'):newPedonTemplateTables.append('pedon')

        # List of old tables that are missing from new template
        missingTables = list()

        """ ---------------------------- Begin the Comparison between NEW and OLD FGDB Pedon Template -----------------------------"""
        discrepancies = 0
        for oldTable in oldTblColDict.keys():

            # Skip any Metadata table
            if oldTable.find("Metadata") > -1: continue

            # Check if old table exists in new Pedon FGDB; log and continue if it doesn't
            if not oldTable in newPedonTemplateTables:
                missingTables.append(oldTable)
                continue

            else:
                newPedonTemplateTables.remove(oldTable)

            oldTableFields = [f.name for f in arcpy.ListFields(newPedonTemplate + os.sep + oldTable)]   # List of GDB table fields
            nasisFields = [value for value in oldTblColDict.get(oldTable)]                                  # List of NASIS table fields
            fieldsMissingGDB = list()                                                                     # List of NASIS fields missing from FGDB

            # remove OBJECTID from oldTableFields list
            if 'OBJECTID' in oldTableFields:
                oldTableFields.remove('OBJECTID')

            if 'SHAPE' in oldTableFields:
                oldTableFields.remove('SHAPE')

            oldTableFieldsTotal = len(oldTableFields)  # number of fields in the FGDB table
            nasisFieldsTotal = len(nasisFields)        # number of fields in the NASIS table

            if oldTableFieldsTotal == nasisFieldsTotal:
                sameNumOfFields = True
            else:
                sameNumOfFields = False

            # Check for NASIS fields missing in the GDB
            for nasisField in nasisFields:

                if not str(nasisField) in oldTableFields:
                    fieldsMissingGDB.append(nasisField)
                else:
                    oldTableFields.remove(nasisField)

            """ -----------------------------------------------Report any tabular field problems to user -------------------------------"""
            AddMsgAndPrint("\n=============================================================================================",0)
            tablePrinted = False

            if not len(fieldsMissingGDB) and not len(oldTableFields):
                AddMsgAndPrint(oldTable + " Table:",0)
                AddMsgAndPrint("\tAll NASIS report fields match FGDB")
                continue

            if len(fieldsMissingGDB):
                AddMsgAndPrint(oldTable + " Table:",2)

                AddMsgAndPrint("\tThe following fields need to be removed from the WEB_AnalysisPC_MAIN_URL_EXPORT report:",1)

                AddMsgAndPrint("\t\t" + str(fieldsMissingGDB))
                tablePrinted = True
                discrepancies += len(fieldsMissingGDB)

            if len(oldTableFields):
                if not tablePrinted:
                    AddMsgAndPrint(oldTable + " Table:",2)

                AddMsgAndPrint("\n\tThe following fields need to be added to the WEB_AnalysisPC_MAIN_URL_EXPORT report:",1)

                AddMsgAndPrint("\t\t" + str(oldTableFields))
                discrepancies += len(oldTableFields)

            # Print all of the fields in their correct format and sequence so that Jason can copy and paste directly
            # into the NASIS report; This will save Jason a ton of time.  This will only print if there are field discrepancies
            # in the table.

            whereClause = f"{metadataFlds[tableName].upper()} = \'{oldTable}\'"
            sqlPostfix = f"ORDER BY {metadataFlds[fieldSequence].upper()} ASC"
            tableFlds = list()
            with arcpy.da.SearchCursor(tblColFldsDesc,[metadataFlds[fieldPhysicalName],metadataFlds[domain]],where_clause=whereClause,sql_clause=(None,sqlPostfix)) as cursor:
                for row in cursor:
                     key = row[0]
                     if row[1] is None:
                        value = None
                     else:
                        value = '*'

                     tableFlds.append((key,value))

            #AddMsgAndPrint(f"{os.linesep}{30*'-'} FORMAT #1: LIST OF TABLE FIELDS IN PROPER SEQUENCE")
            i = 1
            j = len(tableFlds)
            for fld in tableFlds:
                if i < j:
                    AddMsgAndPrint(f"\'{fld[0]}\',")
                else:
                    AddMsgAndPrint(f"\'{fld[0]}\'.")
                i+=1


            #AddMsgAndPrint(f"{os.linesep}{30*'-'} FORMAT #2: LIST OF TABLE FIELDS IN PROPER SEQUENCE")
            i = 1
            j = len(tableFlds)
            for fld in tableFlds:
                if i < j:
                    AddMsgAndPrint(f"{fld[0]}   ,{'*' if not fld[1] == None else ''}")
                else:
                    AddMsgAndPrint(f"{fld[0]}   .{'*' if not fld[1] == None else ''}")
                i+=1

            del oldTableFields,nasisFields,oldTableFieldsTotal,nasisFieldsTotal,fieldsMissingGDB,tablePrinted

        """ ---------------------------------------------------- Report any missing tables to the user ----------------------------------"""
        if len(missingTables):
            AddMsgAndPrint(f"\n{'='*95}")
            AddMsgAndPrint("The following OLD Template Tables no longer exist in the NEW Template:",2)
            missingTables.sort()
            AddMsgAndPrint("\t" + str(missingTables))
            discrepancies += len(missingTables)

        if len(newPedonTemplateTables):
            AddMsgAndPrint(f"\n{'='*95}")
            AddMsgAndPrint(f"{'='*95}")
            AddMsgAndPrint("The following Tables have been added to the NEW Template:",2)
            newPedonTemplateTables.sort()
            AddMsgAndPrint("\t" + str(newPedonTemplateTables))
            discrepancies += len(newPedonTemplateTables)


            # ----------------------- TEMPORARY -----------------------
            #
##            bWrite = True
##            mainURLtblFile = r'E:\NCSS_Pedons\NASIS_Pedons_Metatdata_Update\WEB_AnalysisPC_MAIN_URL_EXPORT.txt'
##            with open(mainURLtblFile) as f:
##                mainURlTblList = f.readlines()
##            mainURlTblList = [f.strip('\n') for f in lines][:-1]
##
##            arcpy.env.workspace = newPedonTemplate
##            newSchemaTables = arcpy.ListTables('*')
##
##            for addtlTbl in newSchemaTables:
##                if addtlTbl in mainURlTblList or addtlTbl in newPedonTemplateTables:
##                    continue
##                else:
##                    newPedonTemplateTables.append(addtlTbl)
##
##            AddMsgAndPrint(f"\n{'='*95}")
##            AddMsgAndPrint(f"{'='*95}")
##            AddMsgAndPrint(f"The following {len(newPedonTemplateTables)} Tables have been added to the NEW Template:",2)
##            newPedonTemplateTables.sort()
##            AddMsgAndPrint("\t" + str(newPedonTemplateTables))
##            discrepancies += len(newPedonTemplateTables)

            # ----------------------- TEMPORARY END -----------------------

            # Print all of the fields in their correct format and sequence so that Jason can copy and paste directly
            # into the NASIS report; This will save Jason a ton of time.  This will only print if there are field discrepancies
            # in the table.
            for newTbl in newPedonTemplateTables:

                AddMsgAndPrint(f"{os.linesep}{'='*30} {newTbl} Table")
                whereClause = f"{metadataFlds[tableName].upper()} = \'{newTbl}\'"
                sqlPostfix = f"ORDER BY {metadataFlds[fieldSequence].upper()} ASC"
                tableFlds = list()
                with arcpy.da.SearchCursor(tblColFldsDesc,[metadataFlds[fieldPhysicalName],metadataFlds[domain]],where_clause=whereClause,sql_clause=(None,sqlPostfix)) as cursor:
                    for row in cursor:
                         key = row[0]
                         if row[1] is None:
                            value = None
                         else:
                            value = '*'

                         tableFlds.append((key,value))

                AddMsgAndPrint(f"{30*'-'} FORMAT #1: LIST OF TABLE FIELDS FOR \'{newTbl}\' IN PROPER SEQUENCE")
                i = 1
                j = len(tableFlds)
                for fld in tableFlds:
                    if i < j:
                        AddMsgAndPrint(f"\'{fld[0]}\',")
                    else:
                        AddMsgAndPrint(f"\'{fld[0]}\'.")
                    i+=1


                AddMsgAndPrint(f"{os.linesep}{30*'-'} FORMAT #2: LIST OF TABLE FIELDS FOR \'{newTbl}\' IN PROPER SEQUENCE")
                i = 1
                j = len(tableFlds)
                for fld in tableFlds:
                    if i < j:
                        AddMsgAndPrint(f"{fld[0]}   ,{'*' if not fld[1] == None else ''}")
                    else:
                        AddMsgAndPrint(f"{fld[0]}   .{'*' if not fld[1] == None else ''}")
                    i+=1

        if discrepancies:
            AddMsgAndPrint("\nTotal # of discrepancies between NASIS report and FGDB: " + str(splitThousands(discrepancies)) + "\n\n",2)
        else:
            AddMsgAndPrint("\nThere are no discrepancies between NASIS report and FGDB....CONGRATULATIONS!\n\n",0)


    except:
        errorMsg()




