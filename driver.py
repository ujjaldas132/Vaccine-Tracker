'''
author: Ujjal Das
github: ujjaldas132
date: June, 2021
<p>

'''


import requests
import sched, time
from datetime import datetime
import credentials.credentials

# User defined data
### Add your distric ids
interestedDistId = [49,50]
#Add your BOT credential here
BOT_CREDENTIALS = credentials.credentials.BOT_CRENDENTIALS
# ADD the group id
TELEGRAM_GROUP_CREDENTIAL = credentials.credentials.GROUP_ID


todayDate = datetime.now().strftime("%d-%m-%y")
header={'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"}
print(todayDate)
districtWiseCalenderBaseUrl="https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?"
# districtWiseCalenderBaseUrl="https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id=50&date=06-06-2021"
baseTelegramApiUrl="https://api.telegram.org/botADD_BOT_ID_HERE/sendMessage?chat_id=@ADD_GROUP_ID_HERE&text="
addBotIdKey="ADD_BOT_ID_HERE"
addGroupIdKey="ADD_GROUP_ID_HERE"
SESSION_DATE = "sessionDate"
MIN_AGE_LIMIT = "min_age_limit"
VACCINE_NAME = "vaccineName"
AVAILABLE_CAPACITY_DOSE1 = "available_capacity_dose1"
AVAILABLE_CAPACITY_DOSE2 = "available_capacity_dose2"
CENTER_NAME="centerName"
DISTRICT_NAME="district_name"
SESSION_DATA="session_data"

# function to get the SETU api
def getDistricWiseCalenderUrl(districId,date=todayDate):
    query="district_id="+districId + "&date=" + date
    return districtWiseCalenderBaseUrl + query
#Function to get data from apis
def getDataResponseFromCowin(districId):
    url = getDistricWiseCalenderUrl(str(districId))
    response = requests.get(url,headers=header)
    # print(response.text)
    return response


# age filter
def isAgeInScope(age):
    maxAge = 45
    return int(age)<maxAge
#Vaccine filter
def isVaccineInScope(vaccineName):
    return vaccineName!="COVISHIELD"

# availablity of dose
def isDoseAvailable(vaccineNum):
    return vaccineNum > 0


#Session filter
def isSessionInScope(sessionData):
    isInScope = isAgeInScope(sessionData[MIN_AGE_LIMIT]) & isVaccineInScope(sessionData[VACCINE_NAME]) & isDoseAvailable(int(sessionData[AVAILABLE_CAPACITY_DOSE2]))
    return isInScope


# function to process the session data
def processSessionDataJson(sessionDataJsons):
    sessionMapCollection = {}
    for sessionJson in sessionDataJsons:
        sessionMap = {}
        sessionDate = sessionJson["date"]
        minAgeLimit = sessionJson["min_age_limit"]
        vaccineName = sessionJson["vaccine"]
        availableDose1 = sessionJson["available_capacity_dose1"]
        availableDose2 = sessionJson["available_capacity_dose2"]
        sessionMap[SESSION_DATE]=sessionDate
        sessionMap[MIN_AGE_LIMIT]=minAgeLimit
        sessionMap[VACCINE_NAME] =vaccineName
        sessionMap[AVAILABLE_CAPACITY_DOSE1]=availableDose1
        sessionMap[AVAILABLE_CAPACITY_DOSE2]=availableDose2
        if (isSessionInScope(sessionMap)):
            sessionMapCollection[sessionDate]=sessionMap
    return sessionMapCollection

# function to process the center data
def processCenterData(centerDataJson):
    centerDataMapList = []
    sessiondataMaps = processSessionDataJson(centerDataJson["sessions"])
    if (sessiondataMaps == {}):
        return
    centerName = centerDataJson['name']
    districName = centerDataJson['district_name']
    for keyDate in sessiondataMaps.keys():
        centerDataMap = {}
        centerDataMap[CENTER_NAME] = centerName
        centerDataMap[DISTRICT_NAME] = districName
        centerDataMap[SESSION_DATA]=sessiondataMaps[keyDate]
        centerDataMapList.append(centerDataMap)
    return centerDataMapList

# function to construct the telegram message
def constructTheTelegramMesssage(messageMap):
    # print(messageMap)
    message = " Center Name : " + messageMap[CENTER_NAME] + "\n"
    message += "Distric Name : " + messageMap[DISTRICT_NAME] + "\n"
    message += "Vaccine Name : " + messageMap[SESSION_DATA][VACCINE_NAME] + "\n"
    message += "MIN AGE : " + str(messageMap[SESSION_DATA][MIN_AGE_LIMIT]) + "\n"
    message += "Date : " + messageMap[SESSION_DATA][SESSION_DATE] + "\n"
    message += "DOSE 1 : " + str(messageMap[SESSION_DATA][AVAILABLE_CAPACITY_DOSE1]) + "\n"
    message += "DOSE 2 : " + str(messageMap[SESSION_DATA][AVAILABLE_CAPACITY_DOSE2]) + "\n"
    return message


# function to send the message to telegram
def sendMessageToTelegram(message):
    telegramApi = baseTelegramApiUrl.replace(addBotIdKey, BOT_CREDENTIALS)
    telegramApi = telegramApi.replace(addGroupIdKey, TELEGRAM_GROUP_CREDENTIAL)
    finalUrl=telegramApi+constructTheTelegramMesssage(message)
    response = requests.get(finalUrl)
    print(response.text)


# to process the reponse
def processResponse(responseData):
    centerDataList = []
    responseJson = responseData.json()
    for centerData in responseJson["centers"]:
        centerRequiredData = processCenterData(centerData)
        if (centerRequiredData!=None):
            sendMessageToTelegram(centerRequiredData[0])
    return centerDataList


# function to start the process
def startProcess():
    requiredData = []
    for distId in interestedDistId:
        cowinDataResponse = getDataResponseFromCowin(distId)
        requiredData += processResponse(cowinDataResponse)
    # print(requiredData)


if __name__ == '__main__':
    while True:
        startProcess()
        time.sleep(30)