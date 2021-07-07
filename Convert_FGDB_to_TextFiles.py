#-------------------------------------------------------------------------------
# Name:        Convert_FGDB_to_TextFiles.py
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     08/22/2017
# Copyright:   2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# This tool will convert File Geodatabase tables and independent feature classes to
# text files to a user-defined output folder.
# The output text files can be delimited in either Comma Separated Value (CSV) or
# Pipe delimited.  Field names will be written in the first row of each output file.
# The filename extension for CSV format will be .csv.  The filename extension for pipe
# delimited  format will be .txt

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

## ===================================================================================
def convertTablesToCSV(GDB):

    try:
        env.workspace = GDB

        # List containing all tables from input FGDB
        tablesToConvert = [table for table in arcpy.ListTables()]

        # Add indpendent feature classes to list above
        for fc in arcpy.ListFeatureClasses():
            tablesToConvert.append(fc)

        numOfTablesToConvert = len(tablesToConvert)

        if bPipeDelimitted:
            ext = ".txt"
        else:
            ext = ".csv"

        if numOfTablesToConvert:
            AddMsgAndPrint("\n")

            # Itereate through tables and feature classes
            for table in tablesToConvert:

                try:
                    # record count
                    numOfRows = int(arcpy.GetCount_management(table).getOutput(0))
                    fieldNames = [f.name for f in arcpy.ListFields(table)]

                    finalFile = outputFolder + os.sep + table + ext

                    # Delete final file if it exists.
                    if arcpy.Exists(finalFile):
                        arcpy.Delete_management(finalFile)

                    # Produce CSV files
                    if not bPipeDelimitted:
                        arcpy.SetProgressorLabel("Converting " + table + " to CSV file Number of records: " + splitThousands(numOfRows))
                        arcpy.TableToTable_conversion(table,outputFolder, table + ext)
                        AddMsgAndPrint("Successfully converted " + table + " to CSV file.  Number of records: " + splitThousands(numOfRows))

                    # Produce pipe delimitted files, which requires a temp file to be written
                    else:
                        import pandas as pd
                        tempTable = table + "Temp.csv"
                        tempTablePath = outputFolder + os.sep + tempTable

                        if arcpy.Exists(tempTablePath):
                            arcpy.Delete_management(tempTablePath)

                        arcpy.SetProgressorLabel("Converting " + table + " to temp CSV file - Number of records: " + splitThousands(numOfRows))
                        arcpy.TableToTable_conversion(table,outputFolder,tempTable)

                        # read inputfile in a dataframe
                        df = pd.read_csv(tempTablePath)

                        # write dataframe df to the outputfile with pipe delimited
                        df.to_csv(finalFile, sep = '|', index=False)
                        AddMsgAndPrint("Successfully converted " + table + " to pipe delimited text file.  Number of records: " + splitThousands(numOfRows))

##                        # file needs to be opened in Universal mode otherwise an error is thrown:
##                        # new-line character seen in unquoted field - do you need to open the file in
##                        # universal-newline mode
##                        with open(outputFolder + os.sep + tempTable,'rU') as csvFile:
##                            #csvReader = csv.reader(open(csvFile, 'rU'), dialect=csv.excel_tab)
##                            arcpy.SetProgressorLabel("Writing " + table + " records to pipe delimited text file ")
##
##                            csvReader = csv.reader(csvFile)
##                            with open(finalFile,"wb") as csvResult:
##
##
##                                csvWrite = csv.writer(csvResult,delimiter='|',quotechar='"')
##
##                                try:
##                                    for row in csvReader:
##                                        csvWrite.writerow(row[1:])
##                                        arcpy.SetProgressorPosition()
##                                except:
##                                    AddMsgAndPrint("\tHad to increase csv field size")
##                                    csv.field_size_limit(sys.maxsize)
##                                    for row in csvReader:
##                                        csvWrite.writerow(row[1:])
##                                    arcpy.SetProgressorPosition()

                        arcpy.ResetProgressor()
                        arcpy.Delete_management(tempTablePath)

                except:
                    AddMsgAndPrint("\nUnable to properly convert " + table,2)
                    errorMsg()

        # No Tables or feature classes to convert
        else:
            AddMsgAndPrint("No Tables or Feature Classes found to convert",2)

        AddMsgAndPrint("\n")

    except:
        errorMsg()
        AddMsgAndPrint("\nUnable to get table information from: " + GDB,2)
        exit()


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy,csv
from arcpy import env

if __name__ == '__main__':

    inputGDB = arcpy.GetParameter(0)
    outputFolder = arcpy.GetParameterAsText(1)
    bPipeDelimitted = arcpy.GetParameter(2)    # Boolean True or False

    arcpy.env.overwriteOutput = True
    arcpy.env.parallelProcessingFactor = "100%"
    #inputGDB = r'E:\All_Pedons\NASIS_Pedons\NASIS_Pedons_20180415.gdb'
    #outputFolder = r'E:\All_Pedons\NASIS_Pedons\CSV_files_20180415'

    convertTablesToCSV(inputGDB)
