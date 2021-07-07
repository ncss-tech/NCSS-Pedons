#-------------------------------------------------------------------------------
# Name:        NASISpedons-Create_FGDBshema_fromNASIS_Metadata.py
# Purpose:     This script will take in a table that contains the metadata schema
#              for all of the NASIS pedon objects and their child tables and create
#              an FGDB and their corresponding tables and fields.  The table is
#              manually created from the NASIS report:
#              WEB_NREPO-Style_Metadata_Tabs_Cols_Pedon_Tools.html
#              https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_NREPO-Style_Metadata_Tabs_Cols-Pedon-Tools&system_name=NASIS%207.3.3&metadata_name=METADATA%202.0.2&domain_name=Current%20NASIS/SSURGO%20Domains
#              The contents of the html report were copied into an excel
#              spreadsheet and then converted to a FGDB table.  The 'TabHelp'
#              field was deleted but should be re-introduced and used to populate
#              Metadata fields and descriptions
#
# Author:      Adolfo.Diaz (Python Script)
# Author:      Jason Nemecek (NASIS report)
#
# Created:     7/27/2018
# Last Modified: 7/27/2018
# Copyright:   (c) Adolfo.Diaz 2016
#-------------------------------------------------------------------------------

## ===================================================================================
class ExitError(Exception):
    pass

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
            arcpy.AddError(msg)

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
from arcpy import env

if __name__ == '__main__':

    try:
        # Table produced from NASIS report: WEB_NREPO-Style_Metadata_Tabs_Cols-Pedon-Tools
        # Hyperlink:
        # https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_NREPO-Style_Metadata_Tabs_Cols-Pedon-Tools&system_name=NASIS%207.3.3&metadata_name=METADATA%202.0.2&domain_name=Current%20NASIS/SSURGO%20Domains
        # HTML results are copied into NASIS_Pedons_Table_Field_Aliases.xls spreadsheet and exported
        # to FGDB table

        schemaTable = r'E:\python_scripts\GitHub\NASIS-Pedons\Metadata_Tables.gdb\NASIS_Pedons_Table_Field_Schema_7_3_3'

        # Empty FGDB
        pedonGDB = r'C:\python_scripts\GitHub\NASIS-Pedons\NasisPedonsTemplate_NEW.gdb'

        """ --------------------------------- Collect schema tables and fields -------------------------"""
        tableName = 2
        tableAlias = 3
        fieldSequence = 4
        fieldName = 6
        fieldAlias = 7
        fieldType = 8
        fieldPhysicalType = 9
        fieldNull = 10
        fieldSize = 11

        arcpy.env.workspace = pedonGDB
        currentTable = ""

        for row in arcpy.da.SearchCursor(schemaTable,'*',sql_clause=(None, 'ORDER BY Table_Physical_Name,Default_Sequence')):

            # --------------------------------------------------- Table does NOT EXIST - Create Table
            if not currentTable == row[tableName]:
                currentTable = row[tableName]

                if currentTable == 'pedon':
                    AddMsgAndPrint("\nCreating Feature Class: " + currentTable + " - " + row[tableAlias])
                    # Create the GCS WGS84 spatial reference and datum name using the factory code
                    spatialRef = arcpy.SpatialReference(4326)
                    arcpy.CreateFeatureclass_management(pedonGDB, "pedon", "POINT", "#", "DISABLED", "DISABLED", spatialRef)

                else:
                    AddMsgAndPrint("\nCreating Table: " + currentTable + " - " + row[tableAlias])
                    arcpy.CreateTable_management(pedonGDB, currentTable)

                # Add Alias Name to new table or feature class
                arcpy.AlterAliasName(pedonGDB + os.sep + currentTable, row[tableAlias])

            # --------------------------------------------------- Table does EXIST - Add fields to table
            #print('\tAdding field: {0} - {1} - {2} - {3} - {4}'.format(row[fieldName], row[fieldAlias], row[fieldType], row[fieldSize], row[fieldSequence]))
            AddMsgAndPrint('\tAdding field: {0} - {1}'.format(row[fieldName], row[fieldAlias]))
            arcFieldLength = '#'

            if row[fieldType] in ('Boolean', 'Choice', 'File Reference', 'Hyperlink', 'Narrative Text', 'String'):
                arcFieldType = 'TEXT'
                arcFieldLength = row[fieldSize]
            elif row[fieldType] == 'Date/Time':
                arcFieldType = 'DATE'
            elif row[fieldType] == 'Float':
                arcFieldType = 'FLOAT'
            elif row[fieldType] == 'Integer':
                if row[fieldPhysicalType] == 'Int':
                    arcFieldType = 'LONG'
                else:
                    arcFieldType = 'SHORT'
            else:
                AddMsgAndPrint("\t" + row[fieldType] + " was not accounted for. Defaulting to 'TEXT'",2)
                arcFieldType = 'TEXT'

            # ---------------------------------------------- Determine NULLABLE
            if row[fieldNull] == 'no':
                arcFieldNull = 'NULLABLE'
            else:
                arcFieldNull = 'NON_NULLABLE'

            arcpy.AddField_management(currentTable, row[fieldName], arcFieldType, '#', '#', arcFieldLength, row[fieldAlias], arcFieldNull, 'REQUIRED', '#')


    except:
        errorMsg()