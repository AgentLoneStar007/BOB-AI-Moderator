# Imports
from datetime import datetime
import os

# TODO: Add returns on functions in these miscellaneous function files

# Vars
logFolder = 'logs'


def formatInput(typeInput):
    if typeInput == 'WARN':
        return 'WARNING'
    if typeInput == 'ERR':
        return 'ERROR'
    else:
        return 'INFO'


def initLoggingUtility() -> None:
    # If there is not a logs folder, create it
    if not os.path.exists(logFolder):
        os.makedirs(logFolder)

    # Set current date var
    now: datetime = datetime.now()
    logFileTime: str = now.strftime('%m-%d-%Y')

    # Create some vars
    logNumber: int = 1
    currentLog: str = logFileTime + ".log"
    logFound: bool = False

    # Loop through the log folder to see which logs exist in order to get the name
    if os.path.exists(logFolder + "/" + currentLog):
        currentLog = f"{logFileTime}_{str(logNumber)}.log"
        while not logFound:
            if not os.path.exists(logFolder + "/" + currentLog):
                logFile: str = currentLog
                logFound = True
            logNumber = logNumber + 1
            currentLog = f"{logFileTime}_{str(logNumber)}.log"

    if not logFound:
        logFile = logFileTime + ".log"

    with open('logs/current.txt', 'w') as file:
        file.write(logFile)

    return


class Log:
    def info(self, message: str) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            log_file = file.read()
            print(type(log_file))

        with open(f'{logFolder}/{log_file}', 'a+') as logFile:
            logFile.write(f'{currentTime} <INFO>: {message}\n')

        return

    def warning(self, message: str) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            log_file: str = file.read()

        with open(f'{logFolder}/{log_file}', 'a+') as logFile:
            logFile.write(f'{currentTime} <WARNING>: {message}\n')

        return

    def error(self, message: str) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            log_file: str = file.read()

        with open(f'{logFolder}/{log_file}', 'a+') as logFile:
            logFile.write(f'{currentTime} <ERROR>: {message}\n')

        return

    def debug(self, message: str) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            log_file: str = file.read()

        with open(f'{logFolder}/{log_file}', 'a+') as logFile:
            logFile.write(f'{currentTime} <DEBUG>: {message}\n')

        return


def log(infoType, message) -> None:
    # Create current time var
    now = datetime.now()
    currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

    # Get current file to log to
    with open('logs/current.txt', 'r') as file:
        log_file: str = file.read()

    # Format input in case something stupid was used like 'err' for error.
    infoType = infoType.upper()
    infoTypes = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
    if infoType not in infoTypes:
        infoType = formatInput(infoType)

    with open(f'{logFolder}/{log_file}', 'a+') as logFile:
        logFile.write(f'{currentTime} <{infoType}>: {message}\n')


def logCommand(user, command, channelID: int = None) -> None:
    # Create object of Log class
    log = Log()

    # Set default message
    message = f'{user} ran command "{command}."'

    # If a channel ID is provided, log it.
    if channelID:
        message = f'{user} ran command "{command}" in channel "{channelID}."'

    # Log the command
    log.info(message)

    del log
    return


def logCogLoad(cog) -> None:
    # Create object of Log class
    log = Log()

    # Log the cog init
    log.info(f'Loaded cog {cog}.')
    del log

    return
