#-------------------------------------------------------------------------------
# Name:        NCSS-ImportNCSSTextFiles_into_FGDB
#
# Author:      Adolfo.Diaz
#              This tool will import NCSS Soil Characterization pedon records
#              from existing text files.  These text files were exported by Jason Nemecek.
#              and include the following 17 pipe delimitted ascii tables:
#                 - analyte.txt
#                 - combine_nasis_ncss.txt
#                 - lab_analysis_prodcedure.txt
#                 - lab_area.txt
#                 - lab_calculations_including_estimates_and_default_values.txt
#                 - lab_chemical_properties.txt
#                 - lab_major_and_trace_elements_and_oxides.txt
#                 - lab_method_code.txt
#                 - lab_mineralogy_glass_count.txt
#                 - lab_physical_properties.txt
#                 - lab_webmap.txt
#                 - lab_xray_and_thermal.txt
#                 - layer.txt
#                 - pedon.txt
#                 - preparation.txt
#                 - rosetta.txt
#                 - site.txt
#              The tool will import the above text files into an existing empty FGDB with
#              the appropriate tabular schema produced from the 'create_Schema_from_NCSS_Lab_Table_Metadata.py'
#              The tool takes in 3 parameters:
#                  1) directory path of text files
#                  2) directory where FGDB will be created
#                  3) Name of FGDB
#              The tool will error out if there is a discrepancy between the FGDB
#              schema and the import files.  The names have to match exactly.
#              There were several temporary adjustments that needed to be made:
#                  1) Webmap table was manually imported using catalog and not the script
#                  2) analyte table schemas do not match.
#
#
# Created:     14/11/2019
# ArcGIS Desktop 7.3


#-------------------------------------------------------------------------------

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print(msg)

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

        if theMsg.find("exit") > -1:
            AddMsgAndPrint("\n\n")
            pass
        else:
            AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

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
def createPedonFGDB():
    """This Function will create a new File Geodatabase using a pre-established XML workspace
       schema.  All Tables will be empty and should correspond to incoming text files.
       Relationships will also be pre-established.
       Return false if XML workspace document is missing OR an existing FGDB with the user-defined
       name already exists and cannot be deleted OR an unhandled error is encountered.
       Return the path to the new Pedon File Geodatabase if everything executes correctly."""

    try:
        AddMsgAndPrint("\nCreating File Geodatabase")
        arcpy.SetProgressorLabel("Creating File Geodatabase")

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "Create_NCSSLabDatabase_Schema_XMLWorkspace.xml"
        localPedonDB = os.path.dirname(sys.argv[0]) + os.sep + "NCSSLabDatabase_Schema_Template.gdb"

        # Return false if pedon fGDB template is not found
        if not arcpy.Exists(localPedonDB):
            AddMsgAndPrint("\t" + os.path.basename(localPedonDB) + " FGDB template was not found!",2)
            return False

        newPedonDB = os.path.join(outputFolder,DBname + ".gdb")

        if arcpy.Exists(newPedonDB):
            try:
                arcpy.Delete_management(newPedonDB)
                AddMsgAndPrint("\t" + DBname + ".gdb already exists. Deleting and re-creating pedon database\n",1)
            except:
                AddMsgAndPrint("\t" + DBname + ".gdb already exists. Failed to delete\n",2)
                return False

        # copy template over to new location
        AddMsgAndPrint("\tCreating " + DBname + ".gdb with NCSS Characterization Data V.XXXXX")
        arcpy.Copy_management(localPedonDB,newPedonDB)

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

        arcpy.UncompressFileGeodatabaseData_management(newPedonDB)
        AddMsgAndPrint("\tSuccessfully created: " + DBname + ".gdb")

        return newPedonDB

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        return False

## ================================================================================================================
def importTabularData(DB,pedonTables):
    # Description
    # This function will import the lab data .csv files into the lab data spatial database.
    # Return False if error occurs, true otherwise.

    # Parameters:
    # DB - The absolute path to the spatial database that will be used to import the .csv files
    # pedonTables - A python list of the tables within the pedon database along with feature classes.
    #               This list will be used to iterate through the tables and corresponding .csv files
    #               and import the data into

    try:
        arcpy.env.workspace = DB
        AddMsgAndPrint("\nImporting Tabular Data")

        # List of missing .csv files
        missingCSVFile = list()

        longField = 'longitude_decimal_degrees'
        latFileld = 'latitude_decimal_degrees'

        # For each item in sorted keys
        for DBtable in sorted(pedonTables):

            #if DBtable != 'lab_area':continue
            #if DBtable != 'lab_chemical_properties':continue
            #if not DBtable in ('combine_nasis_ncss'):continue

            # Absolute path to text file
            txtPath = os.path.join(textFilePath,DBtable + ".txt")

            if os.path.exists(txtPath):

                # Continue if the text file contains values. Not Empty file
                if os.path.getsize(txtPath) > 0:

                    # Put all the field names and their associated field lengths in a list;
                    # used to initiate insertCursor object
                    fieldList = arcpy.Describe(DBtable).fields
                    nameOfFields = []
                    fldLengths = list()

                    for field in fieldList:

                        # record is an X,Y LAB pedon. Addd XY token to list
                        if DBtable == pedonFC and field == 'Shape':

                            # Pedon feature class will have X,Y geometry added; Add XY token to list
                            nameOfFields.append('SHAPE@XY')
                            fldLengths.append(0)  # X coord
                            fldLengths.append(0)  # Y coord
                            continue

                        if field.type != "OID":
                            nameOfFields.append(field.name)
                            if field.type.lower() == "string":
                                fldLengths.append(field.length)
                            else:
                                fldLengths.append(0)

                    del fieldList, field
                    #print("------------------- Number of fields: " + str(len(nameOfFields)))
                    #print(nameOfFields)

                    # The csv file might contain very huge fields, therefore increase the field_size_limit:
                    # Exception thrown with IL177 in legend.txt.  Not sure why, only 1 record was present
##                  Python 3.x doesn't like either one.  Test without.
##                    try:
##                        csv.field_size_limit(sys.maxsize)
##                    except:
##                        csv.field_size_limit(sys.maxint)

                    # Number of records in the SSURGO text file
                    textFileRecords = sum(1 for row in csv.reader(open(txtPath, 'r'), delimiter='|', quotechar='"'))

                    # Subtract header from total records
                    if fileContainHeaders:
                       textFileRecords = textFileRecords - 1

                    # Initiate Cursor to add rows
                    cursor = arcpy.da.InsertCursor(DBtable,nameOfFields)

                    # counter for number of records successfully added; used for reporting
                    numOfRowsAdded = 0
                    reader = csv.reader(open(txtPath, 'r'), delimiter='|', quotechar='"')
                    #reader = csv.reader(codecs.open(txtPath, 'r', encoding='utf-8', errors='ignore'), delimiter='|', quotechar='"')

                    # Strictly for headers
                    lineNumber = 0
                    headerRow = ""
                    unicodeErrors = list()
                    arcpy.SetProgressor("step", "Importing Tabular data for: " + DBtable, 0, textFileRecords)

                    # Return a reader object which will iterate through records in txtPath
                    for rowInFile in reader:
                        try:
                            lineNumber+=1

                            # Skip first record if text files contain headers
                            if fileContainHeaders and lineNumber==1:
                               headerRow = rowInFile
                               continue

##                            # This is strictly temporary bc the 'combine_nasis_ncss' txt
##                            # file contained duplicate sets of records.  Use the header
##                            # row as breaking point.
##                            if DBtable in (pedonFC,'lab_chemical_properties'):
##                               try:
##                                   if rowInFile == headerRow:
##                                      print "Duplicate records found ---- Ending"
##                                      break
##                               except:
##                                   print rowInFile
##                                   print headerRow
##                                   exit()

                            """ Cannot use this snippet of code b/c some values have exceeded their field lengths
                                so now every value has to be assessed."""
                            # replace all blank values with 'None' so that the values are properly inserted
                            # into integer values otherwise insertRow fails
                            # newRow = [None if value =='' else value for value in rowInFile]

                            newRow = list()  # list containing the values that make up a specific row
                            fldNo = 0        # list position to reference the field lengths in order to compare

                            # Iterate through every value in the row and assess the value to ensure it will
                            # fit in the corresponding table.  Maybe there is a faster way of doing this?
                            for value in rowInFile:

                                # incoming strings had a variety of non-ascii symbols that could
                                # not be decoded by utf-8 including the degree symbol and the lower
                                # case beta.  Had to use the ISO8859 code set.
                                value = value.decode('ISO8859-1')

                                # Get the field length associated with this field
                                fldLen = fldLengths[fldNo]

                                # set NULL values to None
                                if value == '' or value == 'NULL':
                                    value = None

                                # If field is a string, truncate the value to the limit
                                # of the field.  Is this correct?  Should these be put in
                                # a list and then reported to user?
                                elif fldLen > 0:
                                    value = value[0:fldLen]

                                # Remove empty space if value starts with blank spaces.
                                # How do you know that 2 consecutive spaces aren't found?
                                if value != None and value.startswith(" "):
                                    value = value[1:len(value)]

                                newRow.append(value)
                                fldNo += 1

                            # Add XY coordinates to the pedon spatial layer.
                            if DBtable == pedonFC:
                                longPos = fieldList.index(longField) # index position of lat/long fields
                                latPos = fieldList.index(latFileld)

                                try:
                                    xValue = float(newRow[longPos])  # Long
                                    yValue = float(newRow[latPos])  # Lat
                                except:
                                    # The pedon did not have a lat/long;
                                    # Send it to the North Pole :)
                                    xValue = 0.00
                                    yValue = 90.0

                                newRow.insert(nameOfFields.index('Shape'),(xValue,yValue))

                            cursor.insertRow(newRow)
                            numOfRowsAdded += 1

                            arcpy.SetProgressorPosition()

                        except:
                            arcpy.SetProgressorPosition()
                            AddMsgAndPrint("Line Error: " + str(lineNumber))
                            errorMsg()

##                            exc_type, exc_value, exc_traceback = sys.exc_info()
##                            theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
##
##                            if theMsg.find('codec') > -1:
##                               unicodeErrors.append((DBtable,lineNumber,fldNo))
##                               continue
##
##                            else:
##                                AddMsgAndPrint("\n\t\tError inserting record in table: " + DBtable,2)
##                                AddMsgAndPrint("\t\t\tRecord # " + str(lineNumber),2)
##                                AddMsgAndPrint("\t\t\tValue: " + str(newRow),2)
##                                AddMsgAndPrint("\t\t\tField Number: " + str(fldNo))
##                                errorMsg()
                            continue

                    #AddMsgAndPrint("\t\t--> " + iefileName + theAlias + theRecLength + " Records Added: " + str(splitThousands(numOfRowsAdded)),0)
                    AddMsgAndPrint("\t\t--> " + DBtable + ": Records Added: " + str(splitThousands(numOfRowsAdded)),0)

                    # compare the # of rows inserted with the number of valid rows in the text file.
                    if numOfRowsAdded != textFileRecords:
                        AddMsgAndPrint("\t\t\t Incorrect # of records inserted into: " + DBtable, 2 )
                        AddMsgAndPrint("\t\t\t\t TextFile records: " + str(splitThousands(textFileRecords)),2)
                        AddMsgAndPrint("\t\t\t\t Records Inserted: " + str(splitThousands(numOfRowsAdded)),2)
                        AddMsgAndPrint("\t\t\t\t Unicode Errors: " + str(splitThousands(len(unicodeErrors))),2)
                        AddMsgAndPrint("\n\n" + str(unicodeErrors))

                    # Resets the progressor back to is initial state
                    arcpy.ResetProgressor()

                else:
                    AddMsgAndPrint("\t\t--> " + DBtable + ": Records Added: 0")

            else:
                AddMsgAndPrint("\t\t--> " + DBtable + ".csv does NOT exist.....SKIPPING ",1)
                missingCSVFile.append(DBtable)

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        errorMsg()
        return False



# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy, time, csv, codecs
from arcpy import env
from sys import getsizeof, stderr
from itertools import chain
from collections import deque

if __name__ == '__main__':

    try:

##        textFilePath = arcpy.GetParameter(0)
##        outputFolder = arcpy.GetParameterAsText(1)
##        GDBname = arcpy.GetParameterAsText(2)
##        fileContainHeaders = True

        textFilePath = r'E:\Pedons\NCSS_Characterization_Database\2019_Schema_Short'
        outputFolder = r'E:\Pedons\Temp\Import_NCSS_Testing_Short'
        DBname = 'Testing_short'
        fileContainHeaders = True

        pedonFC = 'combine_nasis_ncss'     # name of FC that contains the Lat,Long and will be afeature class

        # Step 1 - Create List of .txt files
        textFileList = [file.replace('.txt','') for file in os.listdir(textFilePath) if file.endswith('.txt')]

        # Step 2 - Create FGDB
        """ ------------------------------------------------------Create New File Geodatabaes and get Table Aliases for printing -------------------------------------------------------------------
        Create a new FGDB using a pre-established XML workspace schema.  All tables will be empty
        and relationships established.  A dictionary of empty lists will be created as a placeholder
        for the values from the XML report.  The name and quantity of lists will be the same as the FGDB"""

        pedonDB = createPedonFGDB()
        #pedonFGDB = r'N:\flex\Dylan\NCSS_Characterization_Database\Updated_Schema_2019\NCSS_Characterization_Database_newSchema2.gdb'
        arcpy.env.workspace = pedonDB

        if not pedonDB:
            AddMsgAndPrint("\nFailed to Initiate Empty Pedon File Geodatabase.  Error in createPedonFGDB() function. Exiting!",2)
            exit()

        # Step 3 - Compare .csv files to tables in the pedonDB and report any
        #          discrepancies between the two.  What should happen if discrepancies
        #          are found?  exit?
        pedonDBTables = arcpy.ListTables("*")
        for fcs in arcpy.ListFeatureClasses('*'):
            pedonDBTables.append(fcs)

        discrepancy = list(set(pedonDBTables) - set(textFileList))

        if len(discrepancy) > 0:
           AddMsgAndPrint("\nThere are " + str(len(discrepancy)) + " discrepancies between the FGDB and text files",2)
           for item in discrepancy:
               if item in pedonDBTables:
                  AddMsgAndPrint("\t\"" + item + "\" Table does not have a corresponding text file")
               else:
                  AddMsgAndPrint("\t\"" + item + "\" text file does not have a corresponding FGDB Table")
           AddMsgAndPrint("\nAll discrepancies must be addressed before continuing.....EXITING!",1)
           #exit()

        importTabularData(pedonDB,pedonDBTables)

    except MemoryError:
        AddMsgAndPrint("\n\nOut of Memory Genius! --- " + str(sys.getsizeof(pedonDBTables)),2)
        exit()

    except:
        errorMsg()