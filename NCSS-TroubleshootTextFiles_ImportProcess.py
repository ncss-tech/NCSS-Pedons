#-------------------------------------------------------------------------------
# Name:        NCSS-TroubleshootTextFiles_ImportProcess
# Purpose:     This script was used to troubleshoot the lab_chemical_properties
#              and lab_method_code text file during the import process.
#
# Author:      Adolfo.Diaz
#
# Created:     30/12/2019
# Copyright:   (c) Adolfo.Diaz 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ===================================================================================
def errorMsg():
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "###################  Error Message ###########"
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        #AddMsgAndPrint(theMsg,2)
        print theMsg

    except:
        #AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        print "Unhandled error in errorMsg method"
        pass

import arcpy
import csv, sys, traceback, codecs

if __name__ == '__main__':

   txtPath = r'N:\flex\Dylan\NCSS_Characterization_Database\Updated_Schema_2019\NCSS_LabData_export\lab_chemical_properties.txt'
   pedonFGDB = r'N:\flex\Dylan\NCSS_Characterization_Database\Updated_Schema_2019\Test.gdb\lab_chemical_properties'

   arcpy.env.workspace = pedonFGDB

   # Put all the field names in a list; used to initiate insertCursor object
   fieldList = arcpy.Describe(pedonFGDB).fields
   nameOfFields = []
   fldLengths = list()

   for field in fieldList:

       if field.type != "OID":
           nameOfFields.append(field.name)
           if field.type.lower() == "string":
               fldLengths.append(field.length)
           else:
               fldLengths.append(0)

   # The csv file might contain very huge fields, therefore increase the field_size_limit:
   # Exception thrown with IL177 in legend.txt.  Not sure why, only 1 record was present
   try:
       csv.field_size_limit(sys.maxsize)
   except:
       csv.field_size_limit(sys.maxint)

   # Initiate Cursor to add rows
   numOfRowsAdded = 0
   cursor = arcpy.da.InsertCursor(pedonFGDB,nameOfFields)

##   reload(sys)  # Reload does the trick!
##   sys.setdefaultencoding('ISO-8859-1')

   # counter for number of records successfully added; used for reporting
   reader = csv.reader(open(txtPath, 'rb'), delimiter='|', quotechar='"')
   #reader = csv.reader(open(txtPath, 'rb'), delimiter='|')
   #reader = csv.reader(codecs.open(txtPath, 'rb', encoding='utf-8', errors='strict'), delimiter='|', quotechar='"')

   lineNumber=0

   # Return a reader object which will iterate over lines in txtPath

   for rowInFile in reader:

       try:
           currentLine = rowInFile

           lineNumber+=1
           # Skip first record if text files contain headers
           if lineNumber==1:
              #print rowInFile; exit()
              continue

           #print 1

           newRow = list()  # list containing the values that make up a specific row
           fldNo = 0        # list position to reference the field lengths in order to compare

           #print 2
           for value in rowInFile:

               value = value.decode('ISO8859-1')\

               if value == '' or value == 'NULL':
                   value = None

               if value != None and value.startswith(" "):
                   value = value[1:len(value)]

               newRow.append(value)
               #newRow.append(value.decode('ISO8859-1'))

           #print "Inserting line #: " + str(lineNumber) + "\n"
           #try:
           cursor.insertRow(newRow)

           #print "Inserted line #: " + str(lineNumber) + "\n"

           #print 5
           numOfRowsAdded += 1
           #    print ""
           #except:
           #    pass

           #del newRow, rowInFile

           #print 6

           del currentLine, newRow,fldNo

       except:
           #pass

           print "Line Error: " + str(lineNumber)
           errorMsg()
##           exc_type, exc_value, exc_traceback = sys.exc_info()
##           print "###################  Error Message ###########"
##           theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
##           print theMsg
##           #if theMsg.find('codec') > -1:
##              #print "Codec problem"
##           print currentLine
##           print lineNumber
##           print "\n\n"
##           continue

   print "Total Lines: " + str(lineNumber)
   del cursor, reader







