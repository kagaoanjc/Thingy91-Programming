# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import cfg
import os
import time
import csv
import sys
import re
from datetime import datetime
from os import name
import mysql.connector
import stdiomask
import logging
from func import writeToDB, checkOperator, checkSerialNumber
from pynrfjprog import HighLevel

modem_zip = cfg.fw['mdm9160']
nrf52811 = cfg.fw['fw52811']
nrf9160 = cfg.fw['fw9160']
prgMode = cfg.settings['mode']
now = datetime.now()
ROOT_DIR = os.path.abspath(os.curdir)
hourNow = int(now.strftime("%H"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('Thingy91')

operatorsDB = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="testing",
    password="testing"
)

thingy91PrgDB = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="testing",
    password="testing"
)
# define our clear function


def clear():
    # for windows
    if name == 'nt':
        os.system('cls')
        # for mac and linux(here, os.name is 'posix')
    else:
        os.system('clear')
    # print out some text


def find_verify_hex(fwPath):
    #Find the appropriate hex file to program
    if os.path.exists(fwPath):
        return fwPath
        print("File %s exists", fwPath)


def flash_IC(model):
    with HighLevel.API() as api:
        snr = api.get_connected_probes()
        jSNR = int(snr[0])
        print("Connected Jlink has SNR: %s." % jSNR)
        if len(snr)<=0:
            print("Unable to detect connected JLink")
            api.close()
            sys.exit(2)
        else:
            with HighLevel.DebugProbe(api,jSNR) as probe:
                hex_file_path = find_verify_hex(model)
                if hex_file_path is None:
                    raise Exception("Could not find FW on path, kindly check config.py")
                #Erase
                else:
                    print('Programming %s to device' % model)
                    program_options = HighLevel.ProgramOptions(
                        erase_action=HighLevel.EraseAction.ERASE_ALL,
                        reset=HighLevel.ResetAction.RESET_SYSTEM,
                        verify=HighLevel.VerifyAction.VERIFY_READ
                    )
                    status=probe.program(str(model),program_options=program_options)
                    if status is None:
                        print("Finished Programming %s to device" % model)


def flash_modem_pkg(model,verify):
    with HighLevel.API(True) as api:
        snr = api.get_connected_probes()
        jSNR = int(snr[0])
        if len(snr) <= 0:
            print("Unable to detect connected JLink debugger")
            api.close()
            sys.exit(2)
        else:
            with HighLevel.DebugProbe(api,jSNR) as probe:
                hex_file_path = find_verify_hex(model)
                if hex_file_path is None:
                    raise Exception("Could not find FW on path, kindly check config.py")
            # log.info("Establish board connection")
            # log.info(f"Flashing '{modem_zip}' to board {s}")
                else:
                    print("Flashing 9160 Modem DFU %s thru %s" % (model, jSNR))
                    print("Please wait")
                    with HighLevel.IPCDFUProbe(api, jSNR, HighLevel.CoProcessor.CP_MODEM) as probe:
                # log.info(f"Programming '{modem_zip}'")
                        probe.program(model)
                # log.info("Programming complete")
                        if verify:
                    # log.info("Verifying")
                            probe.verify(model)
                    # log.info("Verifying complete")
                        print("Flashing modem DFU complete!")
        api.close()
        # log.info(f"Completed in {time.time() - start} seconds")


def getSN():
    peerlessSN = input('Enter unit Serial Number: ')
    peerlessSN = peerlessSN.strip()
    snCheck = re.match('^[K][0-9]{11}', peerlessSN)
    if snCheck:
        return peerlessSN
    else:
        return ""


def prepareCSV():
    fileName = "Thingy91_PRG_"+now.strftime("%m_%d_%Y")+".csv"
    logPath = ROOT_DIR+"\Logs\%s" % fileName
    if os.path.exists(logPath):
        return(logPath)
    else:
        with open(logPath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["SN", "Result", "TimeStamp","Remark","TactTime","Operator","SO/PO Number","Lot Number"])


def writeLog(SN,testStatus,remark,tactime,operator,so_poNum,lotNum):
    fileName = "Thingy91_PRG_" + now.strftime("%m_%d_%Y") + ".csv"
    logPath = ROOT_DIR + "\Logs\%s" % fileName
    logTimeStamp = now.strftime("%m/%d/%Y_%H:%M:%S")
    if testStatus:
        result = "PASS"
    else:
        result = "FAIL"
    if os.path.exists(logPath):
        with open(logPath, 'a',newline='') as file:
            writer = csv.writer(file)
            writer.writerow([SN, result, logTimeStamp,remark,tactime,operator,so_poNum,lotNum])
    else:
        prepareCSV()
        with open(logPath, 'a',newline='') as file:
            writer = csv.writer(file)
            writer.writerow([SN,result,logTimeStamp,remark,tactime,operator,so_poNum,lotNum])


def cleanCSV():
    fileName = "Thingy91_PRG_" + now.strftime("%m_%d_%Y") + ".csv"
    logPath = ROOT_DIR + "\Logs\%s" % fileName
    with open(logPath) as in_file:
        with open(logPath, 'w') as out_file:
            writer = csv.writer(out_file)
            for row in csv.reader(in_file):
                if row:
                    writer.writerow(row)


def prgAction(testCx,so_poNum,lotNum,operator,SN):
    testStatus = bool(True)
    remark = "None"
    start = time.time()
    # print("Before proceeding please flip SW2 (SWD Select) to nrf91")
    # input("Press Enter key to continue")
    # if testStatus == True:
    #     try:
    #         flash_modem_pkg(modem_zip,True)
    #     except:
    #         print("Oops!", traceback.format_exc(limit=0), "occured!")
    #         print("Unit %s has failed" % SN)
    #         testStatus = testStatus and False
    #         remark = "flash_modem_pkg "+ str(traceback.format_exc(limit=0))
    #         # break
    # if testStatus == True:
    #     try:
    #         flash_IC(nrf9160,True)
    #     except:
    #         print("Oops!", traceback.format_exc(limit=0), "occured!")
    #         print("Unit %s has failed" % SN)
    #         testStatus = testStatus and False
    #         remark = "flash_IC_nrf9160 "+ str(traceback.format_exc(limit=0))
    #         # break
    #     print("Before proceeding please flip SW2 (SWD Select) to nrf52")
    #     input("Press Enter key to continue")
    # if testStatus == True:
    #     try:
    #         flash_IC(nrf52811,True)
    #     except:
    #         print("Oops!", traceback.format_exc(), "occured!")
    #         print("Unit %s has failed" % SN)
    #         testStatus = testStatus and False
    #         remark = "flash_IC_nrf52811 "+ str(traceback.format_exc(limit=0))
    #         # break
    tactTime = str(time.time() - start)
    print("Activity finished in %s seconds!" % tactTime)
    if testStatus:
        writeLog(SN, testStatus, remark.strip(),tactTime,operator,so_poNum,lotNum)
        writeToDB(testCx,SN,testStatus,remark.strip(),operator,so_poNum)
    input("Press Enter key to restart script")
    os.system('cls')
    print("Thingy91 Programming Python Script v2.0.0.0")
    print("Written by Juan Carlos Kagaoan 22/12/2020")


def prgLoop(testCx,so_poNum,lotNum,operator):
        os.system('cls')
        print("Thingy91 Programming Python Script v2.0.0.1")
        print("Written by Juan Carlos Kagaoan 22/12/2020")
        prepareCSV()
        SN = str(getSN())
        lenSN = len(SN)
        while lenSN==0:
            print('invalid Serial Number')
            SN = str(getSN())
            lenSN = len(SN)
            if lenSN > 0:
                break
        testVal = checkSerialNumber(testCx,SN)
        if testVal == 1:
            pw = stdiomask.getpass(prompt='Sorry, the unit has been tested three times already, kindly enter FA password to continue: ',mask='*')
            if pw.strip() == 'kt_prod_engr':
                print("password correct")
                input("Press Enter to Continue")
                prgAction(so_poNum, lotNum, operator,SN)
            else:
                print("Sorry, password is incorrect, restarting the software")
                input("Press Enter to Continue")
        elif testVal == 2:
            print("Unit has been programmed already!")
            input("Press Enter to Continue")

        elif testVal ==0:
            prgAction(testCx,so_poNum, lotNum, operator,SN)


def prgStart(opCx,testCx):
    employeeNumber = input("Please input your employee number: ")
    checkOp = checkOperator(opCx,employeeNumber)
    if checkOp:
        so_poNum = input("Please input SO/PO Number: ")
        lotNum = input("Please input lot Number: ")
        print("Storing info, program starting...")
        time.sleep(1)
        while True:
            prgLoop(testCx, so_poNum, lotNum, employeeNumber)
    elif checkOp is False:
        print("Sorry you are not allowed to operate this station/script")
        input("Please press enter to restart or press the close button to close this script")
    elif checkOp is None:
        print("Operator doesn't exist! Try again")
        input("Please press enter to restart or press the close button to close this script")


def main():
    while True:
        os.system('cls')
        print("Thingy91 Programming Python Script v2.0.0.1")
        print("Written by Juan Carlos Kagaoan 22/12/2020")
        prgStart(operatorsDB,thingy91PrgDB)

if __name__ == '__main__':
    main()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
