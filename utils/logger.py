# Imports
from datetime import datetime
import os

import discord

# TODO: Add error handling for when current.txt is deleted or log folder is read-only or stuff like that

# Vars
logFolder = 'logs'


# Function that, when used, will create a text file containing the name of the log file to log to during program
# lifecycle
def initLoggingUtility() -> None:
    """
    The function to initialize the logging utility. Needs to
    be run at the start of the program.

    :raises None:
    :return: None
    """

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
        """
        Logs an info type message to the current log file.

        :param message: A string of the message to be logged.
        :param source: Optional. Defaults to system. 'd' can also be used for Discord as the source.
        :returns: None
        :raises None:
        """

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
        """
        Logs a warning type message to the current log file.

        :param message: A string of the message to be logged.
        :param source: Optional. Defaults to system. 'd' can also be used for Discord as the source.
        :returns: None
        :raises None:
        """

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
        """
        Logs an error type message to the current log file.

        :param message: A string of the message to be logged.
        :param source: Optional. Defaults to system. 'd' can also be used for Discord as the source.
        :returns: None
        :raises None:
        """

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

    def fatal(self, message: str) -> None:
        """
        Logs a fatal type message to the current log file. This
        log type does not have source type because this should
        always be "System."

        :param message: A string of the message to be logged.
        :returns: None
        :raises None:
        """

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Get current file to log to
        with open('logs/current.txt', 'r') as file:
            current_log_file: str = file.read()

        with open(f'{logFolder}/{current_log_file}', 'a+') as log_file:
            log_file.write(f'{currentTime} (SYSTEM) <FATAL>: {message}\n')

        return

    def debug(self, message: str, source: str = 'S') -> None:
        """
        Logs a debug type message to the current log file.

        :param message: A string of the message to be logged.
        :param source: Optional. Defaults to system. 'd' can also be used for Discord as the source.
        :returns: None
        :raises None:
        """

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
    def logCommand(self, interaction: discord.Interaction) -> None:
        """
        A shortcut logging utility that logs usage of a command
        to the current log file as an info type.

        :param interaction: The interaction object. The command name and username can be garnered from this.
        :returns: None
        :raises None:
        """

        # Log the command
        self.info(f"@{interaction.user.name}(ID:i{interaction.user.id}) ran command \"{interaction.command.name}.\"", source='d')

        return

    def logCogLoad(self, cog_name: str) -> None:
        """
        A shortcut logging utility that logs the loading of a cog.

        :param cog_name: The name of the cog being loaded. This can be acquired in
        a cog class by using "self.__class__.__name__"
        :returns: None
        :raises None:
        """

        # Log the cog init to file (no need to specify source because it's "system" by default)
        self.info(f"Loaded cog {cog_name} successfully.")

        return


# Class/function for
class LogAndPrint:
    # Create object of Log class
    log = Log()

    def info(self, message: str, source: str = 'S') -> None:
        """
        Logs an info type message to file, and prints it to the console.

        :param message: A string of the message to be logged.
        :param source: Optional. Defaults to System("s"). "d" can also be used for Discord as the source.
        :returns: None
        :raises None:
        """

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
        """
        Logs a warning type message to file, and prints it to the console.

        :param message: A string of the message to be logged.
        :param source: Optional. Defaults to System("s"). "d" can also be used for Discord as the source.
        :returns: None
        :raises None:
        """

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
        """
        Logs an error type message to file, and prints it to the console.

        :param message: A string of the message to be logged.
        :param source: Optional. Defaults to System("s"). "d" can also be used for Discord as the source.
        :returns: None
        :raises None:
        """

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
        """
        Logs a fatal type message to file, and prints it to the console.
        This log type does not have source type because this should
        always be "System."

        :param message: A string of the message to be logged.
        :returns: None
        :raises None:
        """

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the message and log it to file
        print(f'\033[31m{currentTime} (SYSTEM) <FATAL>: {message}\033[0m')
        self.log.error(message)

        return

    def debug(self, message: str, source: str = 'S') -> None:
        """
        Logs a debug type message to file, and prints it to the console.

        :param message: A string of the message to be logged.
        :param source: Optional. Defaults to System("s"). "d" can also be used for Discord as the source.
        :returns: None
        :raises None:
        """

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

    def logCogLoad(self, cog_name: str) -> None:
        """
        A shortcut logging utility that logs and prints the loading of a cog.

        :param cog_name: The name of the cog being loaded. This can be acquired in
        a cog class by using "self.__class__.__name__"
        :returns: None
        :raises None:
        """

        # Create current time var
        now = datetime.now()
        currentTime: str = now.strftime('[%m/%d/%Y-%H:%M:%S]')

        # Print the cog load to console
        print(f'{currentTime} (SYSTEM) <INFO>: Loaded cog: {cog_name}')
        # Log the cog init to file
        self.log.info(f'Loaded cog: {cog_name}')

        return
