## Logging system by AgentLoneStar007
## https://github.com/AgentLoneStar007

# Imports
from datetime import datetime
import os


# Vars
logFolder = 'logs'


def formatInput(typeInput):
    if typeInput == 'WARN':
        return 'WARNING'
    if typeInput == 'ERR':
        return 'ERROR'
    else:
        return 'INFO'


def logsInit():
    # If there is not a logs folder, create it
    if not os.path.exists(logFolder):
        os.makedirs(logFolder)

    # Set current date var
    now = datetime.now()
    logFileTime = now.strftime('%m-%d-%Y')

    # Create some vars
    logNumber = 1
    currentLog = logFileTime + ".log"
    logFound = False

    # Loop through the log folder to see which logs exist in order to get the name
    if os.path.exists(logFolder + "/" + currentLog):
        currentLog = f"{logFileTime}_{str(logNumber)}.log"
        while not logFound:
            if not os.path.exists(logFolder + "/" + currentLog):
                logFile = currentLog
                logFound = True
            logNumber = logNumber + 1
            currentLog = f"{logFileTime}_{str(logNumber)}.log"

    if not logFound:
        logFile = logFileTime + ".log"

    with open('logs/current.txt', 'w') as file:
        file.write(logFile)
        file.close()


def log(infoType, message):
    # Create current time var
    now = datetime.now()
    currentTime = now.strftime('[%m/%d/%Y-%H:%M:%S]')

    # Get current file to log to
    with open('logs/current.txt', 'r') as file:
        logFile = file.read()

    # Format input in case something stupid was used like 'err' for error.
    infoType = infoType.upper()
    infoTypes = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
    if infoType not in infoTypes:
        infoType = formatInput(infoType)

    with open(f'{logFolder}/{logFile}', 'a+') as logFile:
        logFile.write(f'{currentTime} <{infoType}>: {message}\n')


def logCommand(user, command, channelID=None):
    # Set default message
    message = f'{user} ran command "{command}."'

    # If a channel ID is provided, log it.
    if channelID:
        message = f'{user} ran command "{command}" in channel "{channelID}."'

    # Log the command
    log('info', message)


def logCogLoad(cog):
    # Log the cog init
    log('info', f'Loaded cog {cog}.')

