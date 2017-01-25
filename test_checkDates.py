import datetime

def checkDates(dateToCheck, startMonth, endMonth, startDay=1, endDay=1, startYear=2016, endYear=2016):
    if (dateToCheck >= datetime.datetime(startYear, startMonth, startDay) and dateToCheck < datetime.datetime(endYear, endMonth, endDay)):
        return 1
# derdman: totalsurveys=5; 07:3 surveys; 08:2 surveys
# rdewey: totalsurveys=1; 01:1 surveys; 08:2 surveys
# wpeterson: totalsurveys=2; 06:1 survey; 07:3 surveys
# tlindsay: totalsurveys=1; 06:1 surveys

observersDict = {u'{CB51A3A5-1C97-4BC6-B89B-F1CC2D29ABA0}': [u'derdman_mnpower', 21, datetime.datetime(2016, 7, 19, 5, 0)],
                 u'{39AAF1CA-6ECF-453F-8D45-F2F25A74C586}': [u'derdman_mnpower', 35, datetime.datetime(2016, 8, 22, 5, 0)],
                 u'{7117B713-4677-4A15-91A7-A441B49F8C2C}': [u'derdman_mnpower', 13, datetime.datetime(2016, 7, 12, 5, 0)],
                 u'{337C054A-26B0-4FBF-A49C-753E9EB6B9D2}': [u'derdman_mnpower', 24, datetime.datetime(2016, 7, 25, 5, 0)],
                 u'{0C45EDC5-0CB5-46A1-A079-D0B9F8613EE4}': [u'rdewey_mnpower', 3, datetime.datetime(2016, 6, 22, 5, 0)],
                 u'{B2FB267C-44C0-4C98-9DE8-402666B8851D}': [u'wpeterson_mnpower', 6, datetime.datetime(2016, 6, 28, 5, 0)],
                 u'{ECB47DC6-BAB9-4DCE-8428-C7B8841A23EA}': [u'derdman_mnpower', 41, datetime.datetime(2016, 8, 24, 5, 0)],
                 u'{626C891F-2CC1-4A2A-A92C-33BD8C68E557}': [u'wpeterson_mnpower', 16, datetime.datetime(2016, 7, 12, 5, 0)],
                 u'{5FB8051A-CF96-43D6-8190-C3E138BF369C}': [u'tlindsay_mnpower', 2, datetime.datetime(2016, 6, 22, 5, 0)]}

numObserverSurveysDict = {}

# Add num surveys of 0 as default for each observer into dictionary
for key, vals in observersDict.iteritems():
    # set default values for new observer all to 0
    surveytotalsDict = {'totalsurveys': 0, '_01surveys': 0, '_02surveys': 0, '_03surveys': 0, '_04surveys': 0,
                        '_05surveys': 0, '_06surveys': 0, '_07surveys': 0, '_08surveys': 0, '_09surveys': 0,
                        '_10surveys': 0, '_11surveys': 0, '_12surveys': 0}

    numObserverSurveysDict[vals[0]] = surveytotalsDict


for observer, surveyvariables in numObserverSurveysDict.iteritems():
    #print observer, surveyvariables
    # If observer's already a key in the numObserverSurveyDict, then add 1 to totalsurvey variable
    # observersDict in format: {'rowid': ['Creator', 'objectid', 'date']}
    for vals in observersDict.itervalues():
        print vals
        if vals[0] == observer:
            # Iterate through numObserverSurveysDict vals
            myKey = numObserverSurveysDict[observer]

            # Populate the surveytotalsDict values with totals from the counts of surveys
            myKey['totalsurveys'] +=1

            # Check by date of surveys in observersDict
            # observersDict in format of: {'rowid': ['Creator', 'objectid', 'date']}
            # If survey date is (> 01/01/2016 and < 02/01/2016):

            if checkDates(dateToCheck=vals[2], startMonth=1, endMonth=2) == 1: myKey['_01surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=2, endMonth=3) == 1: myKey['_02surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=3, endMonth=4) == 1: myKey['_03surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=4, endMonth=5) == 1: myKey['_04surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=5, endMonth=6) == 1: myKey['_05surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=6, endMonth=7) == 1: myKey['_06surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=7, endMonth=8) == 1: myKey['_07surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=8, endMonth=9) == 1: myKey['_08surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=9, endMonth=10) == 1: myKey['_09surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=10, endMonth=11) == 1: myKey['_10surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=11, endMonth=12) == 1: myKey['_11surveys'] +=1
            if checkDates(dateToCheck=vals[2], startYear=2016, startMonth=12, endYear=2017, endMonth=1) == 1: myKey['_12surveys'] +=1

print(numObserverSurveysDict)
