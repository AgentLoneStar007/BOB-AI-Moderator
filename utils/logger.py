# Imports
from datetime import datetime
import os

# TODO: Add error handling for when current.txt is deleted or log folder is read-only or stuff like that

# Vars
logFolder = 'logs'


# Function that, when used, will create a text file containing the name of the log file to log to during program
# lifecycle
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


# Log class, containing all the different log types
class Log:
    # For all log types, the source can either be "s" for SYSTEM or "d" for DISCORD
    def info(self, message: str, source: str = 'S') -> None:
        # Get/set source type
        if source.lower().startswith('d'):
            source = 'DISCORD'
        else:
            source = 'SYSTEM'

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            current_log_file: str = file.read()

        with open(f'{logFolder}/{current_log_file}', 'a+') as log_file:
            log_file.write(f'{currentTime} ({source}) <INFO>: {message}\n')

        return

    def warning(self, message: str, source: str = 'S') -> None:
        # Get/set source type
        if source.lower().startswith('d'):
            source = 'DISCORD'
        else:
            source = 'SYSTEM'

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            current_log_file: str = file.read()

        with open(f'{logFolder}/{current_log_file}', 'a+') as log_file:
            log_file.write(f'{currentTime} ({source}) <WARNING>: {message}\n')

        return

    def error(self, message: str, source: str = 'S') -> None:
        # Get/set source type
        if source.lower().startswith('d'):
            source = 'DISCORD'
        else:
            source = 'SYSTEM'

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            current_log_file: str = file.read()

        with open(f'{logFolder}/{current_log_file}', 'a+') as log_file:
            log_file.write(f'{currentTime} ({source}) <ERROR>: {message}\n')

        return

    def debug(self, message: str, source: str = 'S') -> None:
        # Get/set source type
        if source.lower().startswith('d'):
            source = 'DISCORD'
        else:
            source = 'SYSTEM'

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            current_log_file: str = file.read()

        with open(f'{logFolder}/{current_log_file}', 'a+') as log_file:
            log_file.write(f'{currentTime} ({source}) <DEBUG>: {message}\n')

        return

    # Currently not defining a "fatal" log function because I don't think it's required outside LogAndPrint

    # Two shortcut log functions, which will log cog loads and command usages
    def logCommand(self, user, command) -> None:
        # Log the command
        self.info(f'{user} ran command "{command}."', source='d')

        return

    def logCogLoad(self, cog) -> None:
        # Log the cog init to file (no need to specify source because it's "system" by default)
        self.info(f'Loaded cog {cog}.')

        return


# Class/function for
class LogAndPrint:
    # Create object of Log class
    log = Log()

    def info(self, message: str, source: str = 'S') -> None:
        # Get/set source type
        if source.lower().startswith('d'):
            source = 'DISCORD'
        else:
            source = 'SYSTEM'

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'{currentTime} ({source}) <INFO>: {message}')
        self.log.info(message, source=source)

        return

    def warning(self, message: str, source: str = 'S') -> None:
        # Get/set source type
        if source.lower().startswith('d'):
            source = 'DISCORD'
        else:
            source = 'SYSTEM'

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'\033[93m{currentTime} ({source}) <WARNING>: {message}\033[0m')
        self.log.warning(message, source=source)

        return

    def error(self, message: str, source: str = 'S') -> None:
        # Get/set source type
        if source.lower().startswith('d'):
            source = 'DISCORD'
        else:
            source = 'SYSTEM'

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'\033[91m{currentTime} ({source}) <ERROR>: {message}\033[0m')
        self.log.error(message, source=source)

        return

    # No need to specify source type because all fatal errors will be SYSTEM
    def fatal(self, message: str) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'\033[31m{currentTime} (SYSTEM) <FATAL>: {message}\033[0m')
        self.log.error(message)

        return

    def debug(self, message: str, source: str = 'S') -> None:
        # Get/set source type
        if source.lower().startswith('d'):
            source = 'DISCORD'
        else:
            source = 'SYSTEM'

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'\033[37m{currentTime} ({source}) <DEBUG>: {message}\033[0m')
        self.log.debug(message, source=source)

        return

    def logCogLoad(self, cog) -> None:
        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the cog load to console
        print(f'{currentTime} (SYSTEM) <INFO>: Loaded cog: {cog}')
        # Log the cog init to file
        self.log.info(f'Loaded cog: {cog}')

        return
