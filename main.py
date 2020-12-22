# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import config
import os
import time

import csv
import sys
import traceback
from datetime import datetime
from os import name

# define our clear function
def clear():
    # for windows
    if name == 'nt':
        os.system('cls')
        # for mac and linux(here, os.name is 'posix')
    else:
        os.system('clear')
    # print out some text

try:
    from..import HighLevel
except Exception:
    from pynrfjprog import HighLevel

# logging.basicConfig(level=logging.INFO)
# log = logging.getLogger('modem_update')
modem_zip = config.fw['mdm9160']
nrf52811 = config.fw['fw52811']
nrf9160 = config.fw['fw9160']
testpath = "E:\Project\Python\Thingy91_Programming\peerless-nrf9160-1.3.1-thingy91-5662-215620f-production-release.hex"
now = datetime.now()
ROOT_DIR = os.path.abspath(os.curdir)

def find_verify_hex(fwPath):
    #Find the appropriate hex file to program
    if os.path.exists(fwPath):
        return fwPath
        print("File %s exists", fwPath)

def flash_IC(model,verify):
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
    # snCheck = re.match('^[K][0-9]{11}', peerlessSN)
    if len(peerlessSN)>0:
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
            writer.writerow(["SN", "Result", "TimeStamp","Remark","TactTime"])

def writeLog(SN,testStatus,remark,tactime):
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
            writer.writerow([SN, result, logTimeStamp,remark,tactime])
    else:
        prepareCSV()
        with open(logPath, 'a',newline='') as file:
            writer = csv.writer(file)
            writer.writerow([SN,result,logTimeStamp,remark,tactime])

def cleanCSV():
    fileName = "Thingy91_PRG_" + now.strftime("%m_%d_%Y") + ".csv"
    logPath = ROOT_DIR + "\Logs\%s" % fileName
    with open(logPath) as in_file:
        with open(logPath, 'w') as out_file:
            writer = csv.writer(out_file)
            for row in csv.reader(in_file):
                if row:
                    writer.writerow(row)
def main():
    testStatus = bool(True)
    remark = "None"
    while True:
        print("Thingy91 Programming Python Script v2.0.0.0")
        print("Written by Juan Carlos Kagaoan 22/12/2020")
        prepareCSV()
        start = time.time()
        SN = str(getSN())
        lenSN = len(SN)
        while lenSN==0:
            print('invalid Serial Number')
            SN = str(getSN())
            lenSN = len(SN)
            if lenSN > 0:
                break
        print("Before proceeding please flip SW2 (SWD Select) to nrf91")
        input("Press Enter key to continue")
        if testStatus == True:
            try:
                flash_modem_pkg(modem_zip,True)
            except:
                print("Oops!", traceback.format_exc(limit=0), "occured!")
                print("Unit %s has failed" % SN)
                testStatus = testStatus and False
                remark = "flash_modem_pkg "+ str(traceback.format_exc(limit=0))
                # break
        if testStatus == True:
            try:
                flash_IC(nrf9160,True)
            except:
                print("Oops!", traceback.format_exc(limit=0), "occured!")
                print("Unit %s has failed" % SN)
                testStatus = testStatus and False
                remark = "flash_IC_nrf9160 "+ str(traceback.format_exc(limit=0))
                # break
            print("Before proceeding please flip SW2 (SWD Select) to nrf52")
            input("Press Enter key to continue")
        if testStatus == True:
            try:
                flash_IC(nrf52811,True)
            except:
                print("Oops!", traceback.format_exc(), "occured!")
                print("Unit %s has failed" % SN)
                testStatus = testStatus and False
                remark = "flash_IC_nrf52811 "+ str(traceback.format_exc(limit=0))
                # break
        tactTime = str(time.time() - start)
        print("Activity finished in %s seconds!" % tactTime)
        if testStatus:
            print("Unit %s has passed!" % SN)
        writeLog(SN, testStatus, remark.strip(),tactTime)
        input("Press Enter key to restart script")
        testStatus = bool(True)
        remark = "None"
        os.system('cls')

    # print(testStatus)
    # writeLog(SN,testStatus,remark.strip()testTime)
    # # cleanCSV()
    # input("Press Enter key to restart script")


    # flash_IC(nrf9160, True)
    # print("Before proceeding please flip SW2 (SWD Select) to nrf52")
    # input("Press Enter key to continue")
    # flash_IC(nrf52811, True)
    # print(f"Completed in {time.time() - start} seconds")
    # #parser = argparse.ArgumentParser()
    # #parser.add_argument("modem_pkg")
    # #parser.add_argument("snr")
    # #args = parser.parse_args()
    # #log.info("Modem firmware upgrade")
    # #flash_modem_pkg(args.modem_pkg, args.snr, True)


if __name__ == '__main__':
    main()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
