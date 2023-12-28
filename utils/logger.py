# Imports
from datetime import datetime
import os

# TODO: Add returns on functions in these miscellaneous function files

# Vars
logFolder = 'logs'


def formatInput(typeInput) -> str:
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
            log_file: str = file.read()

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
            logFile.write(f'\033[93m{currentTime} <WARNING>: {message}\n\033[0m')

        return

    def error(self, message: str) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            log_file: str = file.read()

        with open(f'{logFolder}/{log_file}', 'a+') as logFile:
            logFile.write(f'\033[31m{currentTime} <ERROR>: {message}\n\033[0m')

        return

    def debug(self, message: str) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            log_file: str = file.read()

        with open(f'{logFolder}/{log_file}', 'a+') as logFile:
            logFile.write(f'\033[37m{currentTime} <DEBUG>: {message}\n\033[0m')

        return

    def logCommand(self, user, command, channelID: int = None) -> None:
        # Set default message
        message = f'{user} ran command "{command}."'

        # If a channel ID is provided, log it.
        if channelID:
            message = f'{user} ran command "{command}" in channel "{channelID}."'

        # Log the command
        self.info(message)

        del message
        return

    def logCogLoad(self, cog) -> None:
        # Log the cog init to file
        self.info(f'Loaded cog {cog}.')

        return


# Class/function for
class LogAndPrint:
    # Create object of Log class
    log = Log()

    def info(self, message: str):
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'{currentTime} <INFO>: {message}')
        self.log.info(message)

    def warning(self, message: str):
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'\033[93m{currentTime} <WARNING>: {message}\033[0m')
        self.log.warning(message)

    def error(self, message: str):
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'\033[31m{currentTime} <ERROR>: {message}\033[0m')
        self.log.error(message)

    def logCogLoad(self, cog) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the cog load to console
        print(f'{currentTime} <INFO>: Loaded cog: {cog}')
        # Log the cog init to file
        self.log.info(f'Loaded cog: {cog}')

        return
