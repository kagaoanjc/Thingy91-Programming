import cfg
from datetime import datetime
now = datetime.now()
customerCode = cfg.settings['customerCode']
stationCode = cfg.settings['stationCode']
productCode = cfg.settings['productCode']
hourNow = now.strftime("%H")
if 7 <= int(hourNow) <= 18:
    shift = "A"
else:
    shift = "B"

def writeToDB(connector,SN,testStatus,remark,operator,so_poNum):
    logTimeStamp = now.strftime("%Y-%m-%d %H:%M:%S")
    dbName1 = customerCode + '.' + productCode + "_" + stationCode
    dbName2 = customerCode + "." + productCode + "_main_copy"
    dutcursor = connector.cursor()
    if testStatus:
        result = "1"
    else:
        result = "0"
    testRep = getDUTTestRep(connector,SN)
    if testRep < 0:
        sqlCommandTable = "INSERT INTO "+ dbName1 +" (`serial_num`,`po_num`,`operator_en`,`shift`,`date_time`,`test_rep`,`remarks`,`status`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        valTable = (SN,so_poNum,operator,shift,logTimeStamp,str(1),remark,result)
        dutcursor.execute(sqlCommandTable, valTable)
        connector.commit()
        sqlCommandMain = "INSERT INTO " + dbName2+" (`serial_num`,`po_num`,`progtest`) VALUES(%s,%s,%s)"
        valMain = (SN,so_poNum,result)
        dutcursor.execute(sqlCommandMain, valMain)
        connector.commit()
    elif testRep == 0:
        sqlCommandTable = "INSERT INTO "+ dbName1 +" (`serial_num`,`po_num`,`operator_en`,`shift`,`date_time`,`test_rep`,`remarks`,`status`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        valTable =  (SN, so_poNum, operator, shift, logTimeStamp, str(testRep), remark, result)
        sqlCommandMain = "UPDATE " + dbName2+" SET progtest = '1' WHERE serial_num = '" + SN+"'"
        dutcursor.execute(sqlCommandTable,valTable)
        dutcursor.execute(sqlCommandMain)
    elif testRep > 0:
        newSN = SN+'_'+str(testRep)
        newTestRep = testRep+1
        sqlCommandUpdate = "UPDATE " + dbName1+" SET serial_num = '"+newSN+"' WHERE serial_num ='"+SN+"'"
        sqlCommandTable = "INSERT INTO "+ dbName1 +" (`serial_num`,`po_num`,`operator_en`,`shift`,`date_time`,`test_rep`,`remarks`,`status`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        valTable = (SN,so_poNum,operator,shift,logTimeStamp,str(newTestRep),remark,result)
        sqlCommandMain = "UPDATE " + dbName2+" SET progtest = '"+result+"' WHERE serial_num ='"+SN+"'"
        dutcursor.execute(sqlCommandUpdate)
        connector.commit()
        dutcursor.execute(sqlCommandTable,valTable)
        connector.commit()
        dutcursor.execute(sqlCommandMain)
        connector.commit()
        
def checkOperator(connector,employeeNumber):
    enNumStr = str(employeeNumber)
    opcursor = connector.cursor()
    opcursor.execute("SELECT process FROM operators.main WHERE operator_en = %s", (enNumStr,))
    listProcess = opcursor.fetchone()
    if listProcess is None:
        return None
    else:
        for x in listProcess:
            newList = x.split(",")
        for y in newList:
            if str(y) == "all" or str(y) == "test" or str(y) == "fct":
                return True
        return False

def checkSerialNumber(connector,dutSN):
    dutSNStr = str(dutSN)
    tableStat=getStatusProgtest(connector,dutSNStr)
    mainTableStat=(getStatusProgtestMain(connector,dutSNStr))
    testRepStat=(getDUTTestRepStatus(connector,dutSNStr))
    if (testRepStat>0) and not(mainTableStat) and not(tableStat):
            return int(1)
    elif (mainTableStat and tableStat):
            return int(2)
    else:
        return int(0)

def getStatusProgtestMain(connector,dutSN):
    dutSNStr = str(dutSN)
    dutcursor = connector.cursor()
    dbName = customerCode+"."+productCode+"_main_copy"
    sqlCommand = "SELECT progtest FROM %s WHERE serial_num = '%s'" % (dbName, dutSNStr)
    dutcursor.execute(sqlCommand)
    check = dutcursor.fetchone()
    if check is None:
        return False
    else:
        for x in check:
            if x==0:
                return False
            elif x>0:
                return True

def getStatusProgtest(connector,dutSN):
    dutSNStr = str(dutSN)
    dutcursor = connector.cursor()
    dbName = customerCode+'.'+productCode+"_"+stationCode
    sqlCommand = "SELECT status FROM %s WHERE serial_num = '%s'" %(dbName,dutSNStr)
    dutcursor.execute(sqlCommand)
    check = dutcursor.fetchone()
    if check is None:
        return False
    else:
        for x in check:
            if x == 0:
                return False
            elif x>0:
                return True
def getDUTTestRepStatus(connector,dutSN):
    dutSNStr = str(dutSN)
    dutcursor = connector.cursor()
    dbName = customerCode + '.' + productCode + "_" + stationCode
    sqlCommand = "SELECT test_rep FROM %s WHERE serial_num = '%s'" % (dbName, dutSNStr)
    dutcursor.execute(sqlCommand)
    check = dutcursor.fetchone()
    if check is None:
        return False
    else:
        for x in check:
            if x >= 3:
                return False
            elif x < 3:
                return True

def getDUTTestRep(connector,dutSN):
    dutSNStr = str(dutSN)
    dutcursor = connector.cursor()
    dbName = customerCode + '.' + productCode + "_" + stationCode
    sqlCommand = "SELECT test_rep FROM %s WHERE serial_num = '%s'" % (dbName, dutSNStr)
    dutcursor.execute(sqlCommand)
    check = dutcursor.fetchone()
    if check is None:
        return -1
    else:
        for x in check:
            return int(x)