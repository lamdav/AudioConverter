import datetime
import os
import pathlib
import sys
from multiprocessing import Pool
from typing import Optional, Sequence

import click
from pydub import AudioSegment

AUDIO_EXTENSIONS = [
    ".aiff",
    ".flac",
    ".m4a",
    ".mp3",
    ".mp4",
    ".wav",
    ".ogg",
]
AUDIO_EXTENSIONS_SET = set(AUDIO_EXTENSIONS)
CODEC = [
    "pcm_mulaw",
]
CODEC_SET = set(CODEC)


class Logger(object):
    def success(self, message: str):
        """
        Display a success message in green.
        """
        self.display("[ SUCCESS ] {}".format(message), "green")

    def info(self, message: str):
        """
        Display an info message in blue.
        """
        self.display("[ INFO    ] {}".format(message), "blue")

    def verbose(self, message: str, verbose_flag: bool):
        """
        Display a verbose message in cyan.
        """
        if verbose_flag:
            self.display("[ DEBUG   ] {}".format(message), "cyan")

    def error(self, message: str):
        """
        Display an error message in red.
        """
        self.display("[ ERROR   ] {}".format(message), "red")

    @staticmethod
    def display(formatted_message, color):
        """
        Style a formatted_message message with the given color
        and print it.
        """
        click.secho(formatted_message, fg=color)


class Config(object):
    """
    CLI global configurations
    """

    __slots__ = ["verbose", "logger"]

    def __init__(self, verbose: bool):
        self.verbose = verbose
        self.logger = Logger()


class ConversionJob(object):
    """
    Details related to audio conversion jobs
    """

    __slots__ = [
        "output_format",
        "codec",
        "verbose",
        "output_path",
        "file_path",
        "logger",
    ]

    def __init__(
        self,
        output_format: str,
        codec: Optional[str],
        verbose: bool,
        output_path: pathlib.Path,
        file_path: pathlib.Path,
        logger: Optional[Logger] = None,
    ):
        self.output_format = output_format
        self.codec = codec
        self.verbose = verbose
        self.output_path = output_path
        self.file_path = file_path
        self.logger = logger if logger is not None else Logger()


@click.group()
@click.version_option()
@click.option("--verbose", "-v", type=bool, is_flag=True, help="Enable Verbose Logging")
@click.pass_context
def cli(context: click.Context, verbose: bool):
    """
    AudioConverter CLI
    """
    context.obj = Config(verbose)


@cli.command()
@click.argument(
    "input_directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
)
@click.argument(
    "output_directory", type=click.Path(file_okay=False, dir_okay=True, path_type=str)
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(AUDIO_EXTENSIONS),
    default=".mp3",
    help="Target output format",
)
@click.option(
    "--codec",
    "-c",
    type=click.Choice(CODEC),
    default=None,
    help="Codec to covert to",
)
@click.option(
    "--workers", "-w", type=int, default=5, help="Number of worker processes to run"
)
@click.option(
    "--after",
    "-d",
    help="Convert files created or modified after this date (ISO 8601 format or POSIX timestamp)"
)
@click.pass_obj
def convert(
    config: Config,
    input_directory: str,
    output_directory: str,
    output_format: str,
    codec: Optional[str],
    workers: int,
    after: Optional[str]
):
    """
    Convert Input Directory Audio to Output Directory Audio
    """
    logger = config.logger
    logger.info("Starting conversion of {}.".format(input_directory))

    input_path = pathlib.Path(input_directory)
    output_path = pathlib.Path(output_directory)

    logger.verbose("Input : {}".format(input_path.as_posix()), config.verbose)
    logger.verbose("Output: {}".format(output_path.as_posix()), config.verbose)
    logger.verbose("Workers: {}".format(workers), config.verbose)

    after_date = None
    if after is not None:
        if after.isnumeric():
            after_date = datetime.datetime.fromtimestamp(after)
        else:
            try:
                after_date = datetime.datetime.fromisoformat(after)
            except:
                logger.error("Unable to parse after date option. This must be given in ISO 8601 format or as a POSIX timestamp (seconds since 1970-01-01).")
                sys.exit(1)
        logger.verbose("After date: {}".format(after_date), config.verbose)

    if not output_path.exists():
        logger.verbose(
            "Creating output directory {}".format(output_path.as_posix()),
            config.verbose,
        )
        output_path.mkdir(exist_ok=True)

    audio_files = get_audio_files(input_path, after_date)
    audio_files = [
        ConversionJob(
            output_format=output_format,
            codec=codec,
            verbose=config.verbose,
            output_path=output_path,
            file_path=file_path,
            logger=logger,
        )
        for file_path in audio_files
    ]
    with Pool(processes=workers) as worker:
        worker.map(converter, audio_files)

    logger.success("See {} for converted audio.".format(output_path.as_posix()))


def get_audio_files(input_path: pathlib.Path, after_date: Optional[datetime.datetime]=None) -> Sequence[pathlib.Path]:
    """
    Recursively get audio files within the input_path.
    If after_date is specified, only include files created or modified after this date.
    """
    audio_files = []
    for input_file in input_path.iterdir():
        if input_file.is_file() and should_convert_file(input_file, after_date):
            audio_files.append(input_file)
        elif input_file.is_dir() and not input_file.is_symlink():
            audio_files.extend(get_audio_files(input_file, after_date))
    return audio_files

def should_convert_file(input_file: pathlib.Path, after_date: Optional[datetime.datetime]=None) -> bool:
    """
    Check if a given file should be converted
    """
    if not input_file.suffix.lower() in AUDIO_EXTENSIONS_SET:
        # Wrong file type
        return False
    if after_date is not None:
        # Check file date
        file_stats = os.stat(input_file)
        file_date = datetime.datetime.fromtimestamp(max(file_stats.st_ctime, file_stats.st_mtime))
        if file_date <= after_date:
            return False
    return True

def converter(conversion_job: ConversionJob):
    """
    Multiprocessing worker function.
    Expects audio_datum to have keys:
        output_format - String of the form '.mp3' (must include '.' prefix)
        verbose - Boolean of verbose mode logging
        output_path - Path object of the output directory location
        file_path - Path object of the file to be converted

    Converts the audio file_path to the desired output_format of the same name
    in the output_path.
    """
    logger = conversion_job.logger

    # Conversion specific data
    output_format = conversion_job.output_format[1:]  # ignore "." prefix
    output_path = conversion_job.output_path
    verbose_flag = conversion_job.verbose
    codec = conversion_job.codec

    # File specific data
    audio_file = conversion_job.file_path
    audio_name = audio_file.name[: audio_file.name.rfind(".")]
    converted_name = "{}.{}".format(audio_name, output_format)

    logger.verbose(
        "Converting {} to {}".format(audio_name, output_format), verbose_flag
    )
    audio = AudioSegment.from_file(audio_file.as_posix(), audio_file.suffix[1:])
    output_name = output_path.joinpath(converted_name)
    parameters = get_parameters(output_format, codec)

    audio.export(
        output_name.as_posix(),
        format=output_format,
        bitrate="192k",
        codec=codec,
        parameters=parameters,
    )

    logger.verbose("{} converted".format(audio_name), verbose_flag)


def get_parameters(output_format: str, codec: Optional[str]) -> Optional[Sequence[str]]:
    if codec == "pcm_mulaw":
        return ["-ar", "8000"]
    return None
