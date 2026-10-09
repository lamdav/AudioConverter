import datetime
import os
import pathlib
import sys
from dataclasses import dataclass, field
from multiprocessing import Pool
from typing import Optional, Sequence
from urllib.parse import quote, unquote

import click
from pydub import AudioSegment, utils

import xml.etree.ElementTree as ET

AUDIO_EXTENSIONS = [
    ".aiff",
    ".flac",
    ".m4a",
    ".mp3",
    ".mp4",
    ".wav",
    ".ogg",
    ".opus",
]
AUDIO_EXTENSIONS_SET = set(AUDIO_EXTENSIONS)
PLAYLIST_EXTENSIONS_SET = set([".m3u", ".pls", ".xspf", ".asx"])
CODEC = [
    "pcm_mulaw",
]
CODEC_SET = set(CODEC)

ENCODED_PATH_SAFE_CHARS = '/ ()+,&';

SYNC_FILE_NAME = '.AudioConverterLastSync'


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

@dataclass
class PlaylistJob:
    """
    Details related to playlist conversion jobs
    """
    verbose: bool
    input_root: pathlib.Path
    output_root: pathlib.Path
    file_path: pathlib.Path
    file_output_path: pathlib.Path
    flatten: bool
    output_format: str = field(default=None)
    logger: Logger = field(default_factory=Logger)
    prefix: str = field(default=None)


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
@click.option("--flat", type=bool, is_flag=True, help="Flatten directory structure")
@click.pass_obj
def convert(
    config: Config,
    input_directory: str,
    output_directory: str,
    output_format: str,
    codec: Optional[str],
    workers: int,
    after: Optional[str],
    flat: bool
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

    audio_files = get_files(input_path, is_convertable_audio_file, after_date=after_date)
    audio_files = [
        ConversionJob(
            output_format=output_format,
            codec=codec,
            verbose=config.verbose,
            output_path=get_output_path(input_path, output_path, file_path, not flat),
            file_path=file_path,
            logger=logger,
        )
        for file_path in audio_files
    ]
    with Pool(processes=workers) as worker:
        worker.map(converter, audio_files)

    logger.success("See {} for converted audio.".format(output_path.as_posix()))

def get_output_path(input_path: pathlib.Path, output_path: pathlib.Path, file_path: pathlib.Path, preserve_path: bool=True):
    if not preserve_path or file_path.parts[:len(input_path.parts)] != input_path.parts:
        return output_path
    
    # Get the file_path relative to the input_path, excluding filename
    file_partial_path = file_path.parts[len(input_path.parts):-1]

    return output_path.joinpath(*file_partial_path)


def get_files(input_path: pathlib.Path, file_validator: callable, **kwargs) -> Sequence[pathlib.Path]:
    """
    Recursively get audio files within the input_path.
    If after_date is specified, only include files created or modified after this date.
    """
    audio_files = []
    for input_file in input_path.iterdir():
        if input_file.is_file() and file_validator(input_file, **kwargs):
            audio_files.append(input_file)
        elif input_file.is_dir() and not input_file.is_symlink():
            audio_files.extend(get_files(input_file, file_validator, **kwargs))
    return audio_files

def is_convertable_audio_file(input_file: pathlib.Path, after_date: Optional[datetime.datetime]=None) -> bool:
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
    output_name = output_path.joinpath(converted_name)

    if output_name.exists():
        # If the output file was last modified after the input file, assume it's up to date
        output_stats = os.stat(output_name)
        input_stats = os.stat(audio_file)
        if output_stats.st_mtime > input_stats.st_mtime:
            logger.verbose("{} already converted". format(audio_name), verbose_flag)
            return

    logger.verbose(
        "Converting {} to {}".format(audio_name, output_format), verbose_flag
    )
    audio = AudioSegment.from_file(audio_file.as_posix(), audio_file.suffix[1:])
    metadata = utils.mediainfo(audio_file.as_posix())
    parameters = get_parameters(output_format, codec)
    output_path.mkdir(parents=True, exist_ok=True)

    audio.export(
        output_name.as_posix(),
        format=output_format,
        bitrate="192k",
        codec=codec,
        parameters=parameters,
        tags=metadata['TAG']
    )

    logger.verbose("{} converted".format(audio_name), verbose_flag)


def get_parameters(output_format: str, codec: Optional[str]) -> Optional[Sequence[str]]:
    if codec == "pcm_mulaw":
        return ["-ar", "8000"]
    return None

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
    help="Assume output audio files are in this format (default: autodetect)"
)
@click.option(
    "--prefix",
    type=click.Path(file_okay=False, dir_okay=True, path_type=str),
    help="Add this prefix to all paths in output files"
)
@click.option(
    "--workers", "-w", type=int, default=5, help="Number of worker processes to run"
)
@click.option("--flat", type=bool, is_flag=True, help="Flatten directory structure")
@click.pass_obj
def playlists(
    config: Config,
    input_directory: str,
    output_directory: str,
    output_format: Optional[str],
    prefix: Optional[str],
    workers: int,
    flat: bool
):
    """
    Copy all playlists in input_directory to output_directory, with updated paths
    """
    logger = config.logger
    logger.info("Starting conversion of {}.".format(input_directory))

    input_root = pathlib.Path(input_directory)
    output_root = pathlib.Path(output_directory)

    logger.verbose("Input : {}".format(input_root.as_posix()), config.verbose)
    logger.verbose("Output: {}".format(output_root.as_posix()), config.verbose)
    logger.verbose("Workers: {}".format(workers), config.verbose)

    if not output_root.exists():
        logger.verbose(
            "Creating output directory {}".format(output_root.as_posix()),
            config.verbose,
        )
        output_root.mkdir(exist_ok=True)
    
    playlist_files = get_files(input_root, is_playlist_file)
    playlist_conversions = [
        PlaylistJob(
            verbose=config.verbose,
            input_root=input_root,
            output_root=output_root,
            file_path=file_path,
            file_output_path=get_output_path(input_root, output_root, file_path, not flat),
            flatten=flat,
            output_format=output_format,
            logger=logger,
            prefix=prefix,
        )
        for file_path in playlist_files
    ]

    with Pool(processes=workers) as worker:
        worker.map(playlist_converter, playlist_conversions)
    
    logger.success("See {} for converted playlists.".format(output_root.as_posix()))



def is_playlist_file(input_file: pathlib.Path) -> bool:
    return input_file.suffix.lower() in PLAYLIST_EXTENSIONS_SET

def playlist_converter(job: PlaylistJob):
    logger = job.logger
    suffix = job.file_path.suffix

    if suffix == ".m3u":
        playlist_converter_m3u(job)
    elif suffix == ".pls":
        playlist_converter_pls(job)
    elif suffix == ".xspf":
        playlist_converter_xspf(job)
    elif suffix == ".asx":
        playlist_converter_asx(job)

def playlist_converter_m3u(job: PlaylistJob):
    logger = job.logger
    logger.verbose("Converting M3U playlist {}".format(job.file_path), job.verbose)

    with open(job.file_output_path.joinpath(job.file_path.name), 'w') as out_playlist:
        with open(job.file_path, 'r') as in_playlist:
            for line in in_playlist:
                if line.startswith("#"):
                    # Copy comments (including EXTM3U) as-is
                    out_playlist.write(line)
                else:
                    decoded_original_path = unquote(line.strip())
                    new_path = str(find_playlist_target(decoded_original_path, job))
                    encoded_path = quote(new_path, ENCODED_PATH_SAFE_CHARS)
                    out_playlist.write(encoded_path + '\n')

def playlist_converter_pls(job: PlaylistJob):
    logger = job.logger
    logger.verbose("Converting PLS playlist {}".format(job.file_path), job.verbose)

    with open(job.file_output_path.joinpath(job.file_path.name), 'w') as out_playlist:
        with open(job.file_path, 'r') as in_playlist:
            for line in in_playlist:
                if not line.startswith("File"):
                    # Copy all non-file lines as-is
                    out_playlist.write(line)
                else:
                    key, original_path = line.strip().split("=")
                    decoded_original_path = unquote(original_path)
                    new_path = str(find_playlist_target(decoded_original_path, job))
                    encoded_path = quote(new_path, ENCODED_PATH_SAFE_CHARS)
                    out_playlist.write(key + "=" + encoded_path + '\n')

def playlist_converter_xspf(job: PlaylistJob):
    logger = job.logger
    logger.verbose("Converting XSPF playlist {}".format(job.file_path), job.verbose)

    ET.register_namespace('', "http://xspf.org/ns/0/")
    playlist_file = ET.parse(job.file_path)
    namespaces = {"": "http://xspf.org/ns/0/"}
    tracklist = playlist_file.getroot().find("trackList", namespaces)
    for track in tracklist.findall("track", namespaces):
        location = track.find("location", namespaces)
        location.text = str(find_playlist_target(location.text, job))
    
    playlist_file.write(
        job.file_output_path.joinpath(job.file_path.name),
        'utf-8',
        True,
    )

def playlist_converter_asx(job: PlaylistJob):
    logger = job.logger
    logger.verbose("Converting ASX playlist {}".format(job.file_path), job.verbose)

    playlist_file = ET.parse(job.file_path)
    for entry in playlist_file.getroot().findall("entry"):
        ref = entry.find("ref")
        ref.attrib["href"] = str(find_playlist_target(ref.attrib["href"], job))
    
    playlist_file.write(job.file_output_path.joinpath(job.file_path.name))

def find_playlist_target(original_file_path: pathlib.Path, job: PlaylistJob) -> pathlib.Path:
    """
    Find the target of a playlist item after conversion

    Expects an absolute path or a path relative to the input_root
    Replaces it with a path relative to the output root, with a prefix if specified.
    If an output format is set, the file suffix is replaced with this.
    Otherwise, we search for files with the same name in the expected location and use the first one matching a known audio format.
    If no matching file is present, the original filename is used as specified in the playlist
    """

    # TODO: Handle encoded paths for M3U and PLS files

    if original_file_path.startswith("/"):
        original_file_path = job.input_root.joinpath(original_file_path)
    
    new_directory = pathlib.Path(*original_file_path.parts[len(job.input_root.parts):-1])
    original_file_name = original_file_path.name
    new_file_path = new_directory.joinpath(original_file_path.name) # Fallback - original file name in new location
    
    if (job.output_format is None):
        possible_files = job.output_root.joinpath(new_directory).glob(original_file_path.stem + ".*")
        for f in possible_files:
            if f.suffix in AUDIO_EXTENSIONS_SET:
                new_file_path = new_directory.joinpath(original_file_name).with_suffix(f.suffix)
                break
    else:
        new_file_path = new_directory.joinpath(original_file_name).with_suffix(job.output_format)
    
    return new_file_path

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
@click.option("--flat", type=bool, is_flag=True, help="Flatten directory structure")
@click.pass_obj
@click.pass_context
def sync(
    ctx: click.Context,
    config: Config,
    input_directory: str,
    output_directory: str,
    output_format: Optional[str],
    codec: Optional[str],
    workers: int,
    flat: bool
):
    """
    Convert all files that have changed since the last sync, and update playlists

    Stores a marker file at the root of input_directory indicating the time of the last sync
    """
    logger = config.logger

    last_sync_start = None
    this_sync_start = datetime.datetime.now
    sync_file_path = pathlib.Path(input_directory).joinpath(SYNC_FILE_NAME);
    sync_file_contents = dict()

    if (sync_file_path.is_file()):
        with open(sync_file_path, 'r') as sync_file:
            for line in sync_file:
                out_dir, start = line.split(":")
                sync_file_contents[out_dir] = start
                if out_dir == output_directory:
                    last_sync_start = datetime.datetime.fromisoformat(start)
    
    if last_sync_start is None:
        logger.info("First synchronisation, all files will be converted.")
        after = None
    else:
        logger.info("Synchronising changes since {}".format(last_sync_start.strftime("%c")))
        after = last_sync_start.time()

    ctx.forward(convert, after=after)
    ctx.format(playlists)

    # After successfully completing, update the last sync start
    with open(sync_file_path, 'w') as sync_file:
        for out_dir, start in sync_file_contents.items():
            sync_file.write("{}:{}".format(out_dir, start))

