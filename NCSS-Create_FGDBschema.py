#-------------------------------------------------------------------------------
# Name:        NCSS-Create_FGDBschema.py
# Purpose:     This script will take in a table that contains the metadata schema,
#              D:\ESRI_stuff\python_scripts\GitHub\NASIS-Pedons\Metadata_Tables.gdb\NCSS_Lab_Table_Metadata_20191114,
#              for the NCSS Characterization Data as of 11/15/2019 and create a
#              FGDB with the corresponding tables and fields.  This schema was
#              provided by Jason Nemeeck and generated out of Miscrosoft SQL Managmeent Studio.
#
#              Jason originally provided a spreadsheet called Lab_Table_Column_Metadata_20191114.xls
#              which was converted to a FGDB Table.
#
#              This represents the new schema for the NCSS characterization pedons
#              which condenses the # of tables from 34 to 16
#
#              Future:
#                  1) Add Table Alias Names by removing spaces and capitalizing Table
#                  2) Add field Aliases
#                  3) Add domain from GitHub\NASIS-Pedons\Metadata_Tables.gdb\NCSS_Lab_Table_Domain table
#                  4) Associate domain to any field that ends with 'method'
#                  5) Establish Relationships
#
# Author:      Adolfo.Diaz (Python Script)
# Author:      Jason Nemecek (NASIS report)
#
# Created:     7/27/2018
# Last Modified: 7/27/2018
# Copyright:   (c) Adolfo.Diaz 2016
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

# ===================================================================================
def FindField(layer,chkField):
    # Check table or featureclass to see if specified field exists
    # If fully qualified name is found, return that name; otherwise return ""
    # Set workspace before calling FindField

    try:

        if arcpy.Exists(layer):

            theDesc = arcpy.Describe(layer)
            theFields = theDesc.fields
            theField = theFields[0]

            for theField in theFields:

                # Parses a fully qualified field name into its components (database, owner name, table name, and field name)
                parseList = arcpy.ParseFieldName(theField.name) # (null), (null), (null), MUKEY

                # choose the last component which would be the field name
                theFieldname = parseList.split(",")[len(parseList.split(','))-1].strip()  # MUKEY

                if theFieldname.upper() == chkField.upper():
                    return theField.name

            return False

        else:
            AddMsgAndPrint("\tInput layer not found", 0)
            return False

    except:
        errorMsg()
        return False

# =========================================================== Main Body =============================================================================
# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

if __name__ == '__main__':

    try:

        schemaTable = r'E:\python_scripts\GitHub\NCSS-Pedons---ArcGIS-Pro\Metadata_Tables.gdb\NCSS_Lab_Table_Metadata_20191114'

        # Existing Empty FGDB
        #pedonGDB = r'D:\ESRI_stuff\python_scripts\GitHub\NASIS-Pedons\NCSSLabDatabase_Schema_Template.gdb'
        pedonGDB = r'E:\python_scripts\GitHub\NCSS-Pedons---ArcGIS-Pro\Test.gdb'

        """ --------------------------------- Collect schema tables and fields -------------------------"""
        tableName = 1
        fieldName = 2
        fieldSequence = 3
        fieldType = 4
        fieldSize = 5
        fieldNull = 9
        tableAlias = tableName
        fieldAlias = fieldName

        #tableAlias = 3
        #fieldAlias = 7
        #fieldPhysicalType = 9

        arcpy.env.workspace = pedonGDB
        currentTable = ""

        tblPhysicalNameFld = 'Table_Name'     # name of field containing Physical Name of Table from the schema table
        pedonTable = 'combine_nasis_ncss'     # name of table that contains the Lat,Long and will be afeature class
        fieldSequenceFld = 'OrdinalPosition'
        currentTableFieldNames = list()

        for row in arcpy.da.SearchCursor(schemaTable,'*',sql_clause=(None, 'ORDER BY ' + tblPhysicalNameFld + ',' + fieldSequenceFld)):
            # --------------------------------------------------- Table does NOT EXIST - Create Table
            if row[tableName] == 'analyte':continue

            if not currentTable == row[tableName]:
                currentTable = row[tableName]

                # Table does exist; capture fields to compare to master list
                if arcpy.Exists(os.path.join(pedonGDB,currentTable)):
                    currentTableFieldNames = [field.name for field in arcpy.ListFields(os.path.join(pedonGDB,currentTable))]
                    tblAlias = currentTable.replace('_',' ').title()
                    arcpy.AlterAliasName(currentTable,tblAlias)
                    #AddMsgAndPrint("\n" + currentTable + " - " + row[tableAlias] + ": Already Exists!")
                    AddMsgAndPrint("\n" + currentTable + " - " + tblAlias + ": Already Exists!")

                # Create feature class for pedons
                elif currentTable == pedonTable:

                    AddMsgAndPrint("\nCreating Feature Class: " + currentTable + " - " + row[tableAlias])

                    # factory code for GCS WGS84 spatial reference
                    spatialRef = arcpy.SpatialReference(4326)
                    arcpy.CreateFeatureclass_management(pedonGDB, pedonTable, "POINT", "#", "DISABLED", "DISABLED", spatialRef)

                # Table doesn't exist; Create table
                else:
                    AddMsgAndPrint("\nCreating Table: " + currentTable + " - " + row[tableAlias])
                    arcpy.CreateTable_management(pedonGDB, currentTable)

                # Add Alias Name to new table or feature class
                arcpy.AlterAliasName(pedonGDB + os.sep + currentTable, row[tableAlias])

            # --------------------------------------------------- Add fields to new table; check fields
            #print('\tAdding field: {0} - {1} - {2} - {3} - {4}'.format(row[fieldName], row[fieldAlias], row[fieldType], row[fieldSize], row[fieldSequence]))

            if row[fieldName] in currentTableFieldNames:
               newFieldAlias =  (row[fieldName]).replace('_',' ')
               try:
                   arcpy.AlterField_management(currentTable,row[fieldName],'#',newFieldAlias)
                   AddMsgAndPrint('\tfield: {0} - {1}'.format(row[fieldName], newFieldAlias) + ' already exists')
               except:
                   AddMsgAndPrint('\tfield: {0} - {1}'.format(row[fieldName], newFieldAlias) + ' already exists')
               #AddMsgAndPrint('\tfield: {0} - {1}'.format(row[fieldName], row[fieldAlias]) + ' already exists')
               continue

            else:
                 AddMsgAndPrint('\tAdding field: {0} - {1} - {2} Table'.format(row[fieldName], row[fieldAlias],currentTable))
                 arcFieldLength = '#'

            if row[fieldType].lower() in ('bit', 'boolean', 'choice', 'file reference', 'hyperlink', 'narrative text', 'varchar', 'nvarchar', 'string', 'uniqueidentifier'):
                arcFieldType = 'TEXT'
                arcFieldLength = row[fieldSize]

                # Adjust for missing field lengths
                try:
                    int(arcFieldLength)
                except:
                    if row[fieldType].lower() == 'bit':
                        arcFieldLength = 5
                    else:
                        arcFieldLength = 100

            elif row[fieldType].lower() in ('date/time', 'datetime'):
                arcFieldType = 'DATE'
            elif row[fieldType].lower() in ('decimal', 'float', 'real'):
                arcFieldType = 'FLOAT'
            elif row[fieldType].lower() in ('int', 'integer', 'numeric', 'smallint','tinyint'):
                arcFieldType = 'LONG'
            elif row[fieldType].lower() in ('smallint','tinyint'):
                arcFieldType = 'SHORT'
            else:
                AddMsgAndPrint("\t\t" + row[fieldType] + " was not accounted for. Defaulting to 'TEXT'",1)
                arcFieldType = 'TEXT'

            # ---------------------------------------------- Determine NULLABLE
            if row[fieldNull] in ('None', 'NoneType','', None):
                arcFieldNull = 'NULLABLE'
            elif row[fieldNull].lower() in ('no'):
                arcFieldNull = 'NULLABLE'
            elif row[fieldNull].lower() in ('not null', 'none'):
                arcFieldNull = 'NON_NULLABLE'

            arcpy.AddField_management(currentTable, row[fieldName], arcFieldType, '#', '#', arcFieldLength, row[fieldAlias], arcFieldNull, 'REQUIRED', '#')


    except:
        errorMsg()