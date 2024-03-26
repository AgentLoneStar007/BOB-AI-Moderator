# Imports
import discord
from discord.ext import commands
from utils.logger import Log, LogAndPrint
import os
from shutil import rmtree
from pathlib import Path
import requests
from time import time
from PIL import Image, ImageSequence, UnidentifiedImageError
import cairosvg
from transformers import pipeline
import cv2
from pytesseract import image_to_string


# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()

# TODO: Add a background tasks that cleans the download folder, with a system that prevents deleting a
#  folder that's being actively used.


class ImageScanner(commands.Cog, description="Everything relating to the NSFW image detection system."):
    def __init__(self, bot) -> None:
        self.bot = bot

        # Load the image detection model using a high-level pipeline
        self.model = pipeline("image-classification", model="Falconsai/nsfw_image_detection")

        # Vars
        self.detection_gate: float = 0.1
        self.image_file_types: set = {".svg", ".ico", ".jpg", ".webp", ".jpeg", ".hdr", ".bmp", ".dds", ".gif", ".cur",
                                      ".psd", ".tiff", ".tga", ".avif", ".rgb", ".xpim", ".heic", ".ppm", ".rgba",
                                      ".exr", ".jfif", ".wbmp", ".pgm", ".xbm", ".jp2", ".pcx", ".jbg", ".heif", ".map",
                                      ".pdb", ".picon", ".pnm", ".jpe", ".jif", ".jps", ".pbm", ".g3", ".yuv", ".pict",
                                      ".ras", ".pal", ".g4", ".pcd", ".sixel", ".rgf", ".sgi", ".six", ".mng", ".jbig",
                                      ".xv", ".xwd", ".fts", ".vips", ".ipl", ".pct", ".hrz", ".pfm", ".pam", ".uyvy",
                                      ".otb", ".mtv", ".viff", ".fax", ".pgx", ".sun", ".palm", ".rgbo", ".jfi", ".png"}

        return

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return logandprint.logCogLoad(self.__class__.__name__)

    # TODO: Switch to using FFMpeg to convert images to PNG. FFMpeg has much more support, and should be much more
    #  capable of converting images to a PNG, which is guaranteed to be compatible with PIL.
    async def scanImage(self,
                        guild_id: int,
                        image_url: str = "",
                        message: discord.Message = None,
                        avatar: discord.Member.avatar = None,
                        banner: discord.Asset = None
                        ) -> bool:
        """
        Scans an image or images, depending on whether `image_url`, `message_attachments`, or `avatar`
        is used. (Only one can be used, however.)

        :param guild_id: The Discord ID of the guild where the function is being used.
        :param image_url: The URL to an image.
        :param message: A Discord message object, which attachments can be pulled from.
        :param avatar: A Discord avatar asset.
        :param banner: A Discord banner asset.
        :returns: True if the given image is NSFW. False otherwise.
        :raises ValueError: If neither nor more than one argument is given. Only one can be used.
        :raises discord.NotFound: If a guild with the given ID couldn't be found.
        :raises requests.RequestException: If an image couldn't be downloaded for scanning.
        :raises PIL.UnidentifiedImageError: If the image cannot be opened. Mainly for debug purposes.
        """

        # Fetch the guild
        guild: discord.Guild = self.bot.get_guild(guild_id)

        # Throw an error and stop the function if the guild is not found
        if not guild:
            # TODO: Test the following exception, as it could not work at all
            raise discord.NotFound(f"Could not find the guild with id \"{guild_id}!\"")

        # Prevent usage of more than one argument
        used_arguments: int = sum(1 for arg in (image_url, message, avatar, banner) if arg is not None) > 1
        if used_arguments > 1:
            raise ValueError(f"Only one argument can be used for the scanImage() function, but {used_arguments}"
                             "were provided.")

        # Cleanup
        del used_arguments

        # And prevent using no arguments
        if not any([image_url, message, avatar, banner]):
            raise ValueError("At least one argument must be used for the scanImage() function, but none were"
                             "provided.")

        # Vars
        folder_name: str = ""

        if image_url:
            # Create a unique ID for the folder's name
            timestamp: int = int(time())
            random_int: str = os.urandom(4).hex()
            folder_name = f"{timestamp}{random_int}"
            del timestamp, random_int

            # Create the folder in the downloads directory
            Path(f"downloads/{guild_id}/{folder_name}").mkdir(parents=True, exist_ok=True)

            full_dir_path: str = f"downloads/{guild_id}/{folder_name}/"

            try:
                # Download the image
                response = requests.get(image_url, stream=True)
                response.raise_for_status()  # Raise an error if the response isn't 200 (OK)

                # Get the path that the image will be downloaded to
                image_path: str = f"{full_dir_path}/{os.path.basename(image_url)}"

                # Write the image to the folder
                with open(image_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                    file.close()

                logandprint.debug(f"Downloaded image {os.path.basename(image_url)} for scanning.", source='d')

            # Handle if the image couldn't be downloaded
            except Exception as error:
                # Yes, this is technically counter-intuitive, but it gives more information to the existing error.
                raise requests.RequestException("Failed to download an image for scanning with the following error: "
                                                f"{error}")

            # Path to handle gifs
            if image_path.endswith(".gif"):
                # Create a list of all the results of the images to be used later
                results: list = [float]
                # Open the image object
                img = ImageSequence.Iterator(Image.open(image_path))

                # Save each frame of the GIF to the folder
                i: int = 0
                for frame in img:
                    frame = frame.convert("RGB")
                    frame.save(f"{full_dir_path}/frame_{i + 1}.png")
                    i += 1

                # Cleanup
                del i

                # Scan each image in the folder
                for png_image in os.listdir(full_dir_path):
                    # Prevent scanning the pre-existing GIF as well
                    if not png_image.endswith(".png"):
                        continue
                    image = Image.open(f"{full_dir_path}/{png_image}")
                    # And append each result to the results list
                    results.append(float(self.model(image)[1]["score"]))

                # Check to see if any of the results are too high
                for result in results:
                    if result >= self.detection_gate:
                        return True

            # Path to handle SVGs
            elif image_path.endswith(".svg"):
                # Convert the SVG to a PNG
                with open(image_path, 'rb') as svg_file, open(f"{full_dir_path}/temp_image.png", 'wb') as file:
                    cairosvg.svg2png(file_obj=svg_file, write_to=file)

                # Open the PNG as an object
                img = Image.open(f"{full_dir_path}/temp_image.png")

                # Scan it and see if it's above the detection gate
                if float(self.model(img)[1]["score"]) >= self.detection_gate:
                    return True

            # Basic path to handle all other file extensions
            else:
                # The following is in a try/except block, so I can get the error output from PIL. This allows me to
                # add more support for different image types in the future.
                try:
                    img = Image.open(image_path)
                except Exception as error:
                    raise UnidentifiedImageError("Failed to open an image for scanning with the following error: "
                                                 f"{error}")

                # Scan the image and see if it's above the detection gate
                if float(self.model(img)[1]["score"]) >= self.detection_gate:
                    return True

        elif message:
            # Make the folder's name the ID of the message
            folder_name = str(message.id)

            # Create the folder in the downloads directory
            Path(f"downloads/{guild_id}/{folder_name}").mkdir(parents=True, exist_ok=True)

            full_dir_path: str = f"downloads/{guild_id}/{folder_name}/"

            for attachment in message.attachments:
                # The spaghetti code below gets the file extension and checks if it's an image
                if os.path.splitext(attachment.filename)[1] in self.image_file_types:
                    # Download the attachment using Discord.py's save() function
                    await attachment.save(Path(f"{full_dir_path}/{attachment.filename}"))

                    logandprint.debug(f"Downloaded image {attachment.filename} for scanning.",
                                      source='d')

            # Get every image saved to the folder
            for image in os.listdir(full_dir_path):
                image_path: str = f"{full_dir_path}/{image}"

                # Path to handle gifs
                if image_path.endswith(".gif"):
                    # Create a list of all the results of the images to be used later
                    results: list = [float]
                    # Open the image object
                    img = ImageSequence.Iterator(Image.open(image_path))

                    # Save each frame of the GIF to the folder
                    i: int = 0
                    for frame in img:
                        frame = frame.convert("RGB")
                        frame.save(f"{full_dir_path}/frame_{i + 1}.png")
                        i += 1

                    # Cleanup
                    del i

                    # Scan each image in the folder
                    for png_image in os.listdir(full_dir_path):
                        # Prevent scanning the pre-existing GIF as well
                        if not png_image.endswith(".png"):
                            continue
                        image = Image.open(f"{full_dir_path}/{png_image}")
                        # And append each result to the results list
                        results.append(float(self.model(image)[1]["score"]))

                    # Check to see if any of the results are too high
                    for result in results:
                        if result >= self.detection_gate:
                            return True

                # Path to handle SVGs
                elif image_path.endswith(".svg"):
                    # Convert the SVG to a PNG
                    with open(image_path, 'rb') as svg_file, open(f"{full_dir_path}/temp_image.png", 'wb') as file:
                        cairosvg.svg2png(file_obj=svg_file, write_to=file)

                    # Open the PNG as an object
                    img = Image.open(f"{full_dir_path}/temp_image.png")

                    # Scan it and see if it's above the detection gate
                    if float(self.model(img)[1]["score"]) >= self.detection_gate:
                        return True

                # Basic path to handle all other file extensions
                else:
                    # The following is in a try/except block, so I can get the error output from PIL. This allows me to
                    # add more support for different image types in the future.
                    try:
                        img = Image.open(image_path)
                    except Exception as error:
                        raise UnidentifiedImageError(
                            f"Failed to open an image for scanning with the following error: {error}")

                    # Scan the image and see if it's above the detection gate
                    if float(self.model(img)[1]["score"]) >= self.detection_gate:
                        return True

        elif avatar:
            # Create a unique ID for the folder's name
            timestamp: int = int(time())
            random_int: str = os.urandom(4).hex()
            folder_name = f"{timestamp}{random_int}"
            del timestamp, random_int

            # Create the folder in the downloads directory
            Path(f"downloads/{guild_id}/{folder_name}").mkdir(parents=True, exist_ok=True)

            full_dir_path: str = f"downloads/{guild_id}/{folder_name}/"

            # Download the avatar
            await avatar.save(Path(f"{full_dir_path}/{os.path.basename(avatar.url)}"))

            logandprint.debug(f"Downloaded avatar {os.path.basename(avatar.url)} for scanning.",
                              source='d')

            # Get the path of the image
            image_path: str = f"{full_dir_path}/{os.path.basename(avatar.url)}"

            # Path to handle gifs
            if image_path.endswith(".gif"):
                # Create a list of all the results of the images to be used later
                results: list = [float]
                # Open the image object
                img = ImageSequence.Iterator(Image.open(image_path))

                # Save each frame of the GIF to the folder
                i: int = 0
                for frame in img:
                    frame = frame.convert("RGB")
                    frame.save(f"{full_dir_path}/frame_{i + 1}.png")
                    i += 1

                # Cleanup
                del i

                # Scan each image in the folder
                for png_image in os.listdir(full_dir_path):
                    # Prevent scanning the pre-existing GIF as well
                    if not png_image.endswith(".png"):
                        continue
                    image = Image.open(f"{full_dir_path}/{png_image}")
                    # And append each result to the results list
                    results.append(float(self.model(image)[1]["score"]))

                # Check to see if any of the results are too high
                for result in results:
                    if result >= self.detection_gate:
                        return True

            # All other media types for an Avatar asset should be PNG, but either way this path should be able to
            # handle them without error
            else:
                # The following is in a try/except block, so I can get the error output from PIL. This allows me to
                # add more support for different image types in the future.
                try:
                    img = Image.open(image_path)
                except Exception as error:
                    raise UnidentifiedImageError(
                         f"Failed to open an image for scanning with the following error: {error}")

                # Scan the image and see if it's above the detection gate
                if float(self.model(img)[1]["score"]) >= self.detection_gate:
                    return True

        elif banner:
            # Create a unique ID for the folder's name
            timestamp: int = int(time())
            random_int: str = os.urandom(4).hex()
            folder_name = f"{timestamp}{random_int}"
            del timestamp, random_int

            # Create the folder in the downloads directory
            Path(f"downloads/{guild_id}/{folder_name}").mkdir(parents=True, exist_ok=True)

            full_dir_path: str = f"downloads/{guild_id}/{folder_name}/"

            # Download the avatar
            await banner.save(Path(f"{full_dir_path}/{os.path.basename(avatar.url)}"))

            logandprint.debug(f"Downloaded avatar {os.path.basename(avatar.url)} for scanning.",
                              source='d')

            # Get the path of the image
            image_path: str = f"{full_dir_path}/{os.path.basename(avatar.url)}"

            # Path to handle gifs
            if image_path.endswith(".gif"):
                # Create a list of all the results of the images to be used later
                results: list = [float]
                # Open the image object
                img = ImageSequence.Iterator(Image.open(image_path))

                # Save each frame of the GIF to the folder
                i: int = 0
                for frame in img:
                    frame = frame.convert("RGB")
                    frame.save(f"{full_dir_path}/frame_{i + 1}.png")
                    i += 1

                # Cleanup
                del i

                # Scan each image in the folder
                for png_image in os.listdir(full_dir_path):
                    # Prevent scanning the pre-existing GIF as well
                    if not png_image.endswith(".png"):
                        continue
                    image = Image.open(f"{full_dir_path}/{png_image}")
                    # And append each result to the results list
                    results.append(float(self.model(image)[1]["score"]))

                # Check to see if any of the results are too high
                for result in results:
                    if result >= self.detection_gate:
                        return True

            # All other media types for an Avatar asset should be PNG, but either way this path should be able to
            # handle them without error
            else:
                # The following is in a try/except block, so I can get the error output from PIL. This allows me to
                # add more support for different image types in the future.
                try:
                    img = Image.open(image_path)
                except Exception as error:
                    raise UnidentifiedImageError(
                         f"Failed to open an image for scanning with the following error: {error}")

                # Scan the image and see if it's above the detection gate
                if float(self.model(img)[1]["score"]) >= self.detection_gate:
                    return True

        # Delete the directory if it exists
        if folder_name:
            rmtree(f"downloads/{guild_id}/{folder_name}")

        # Return false if the media is OK
        return False

    async def imageToText(self) -> None:
        ...
        #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Perform OCR using Tesseract
        #text = image_to_string(gray)


async def setup(bot) -> None:
    return await bot.add_cog(ImageScanner(bot))
