#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     06/01/2022
# Copyright:   (c) Adolfo.Diaz 2022
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print(msg)
        #print msg

        f = open(textFilePath,'a+')
        f.write(msg + " \n")
        f.close
        del f

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
            AddMsgAndPrint(theMsg)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

import os

from urllib.error import HTTPError, URLError
from urllib.request import Request

if __name__ == '__main__':

    try:

        folder = r'N:\scratch'
        existingDir = os.listdir(folder)

        textFilePath = folder + os.sep + "Test_logFile.txt"

        i = 0

        while i < 5:
            os.mkdir(os.path.join(folder,"Test" + str(i)))
            AddMsgAndPrint(f"Creating Folder# {i}")
            #AddMsgAndPrint("Creating Folder# " + str(i))
            i+=1

    except:
        errorMsg()




