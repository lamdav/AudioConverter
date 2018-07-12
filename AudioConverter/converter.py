import pathlib
import click
from pydub import AudioSegment
from multiprocessing import Pool

AUDIO_EXTENSIONS = ['.mp3', '.flac', '.aiff', '.mp4', '.m4a']


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable Verbose Logging')
@click.pass_context
def cli(context, verbose):
    """
    AudioConverter CLI
    """
    config = {'verbose': verbose}
    context.obj = {
        'config': config
    }


@cli.command()
@click.argument('input_directory', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--output-format', '-o', type=click.Choice(AUDIO_EXTENSIONS),
              default='.mp3', help='Target output format')
@click.pass_context
def convert(context, input_directory, output_directory, output_format):
    """
    Convert Input Directory Audio to Output Directory Audio
    """
    config = get_config(context)

    info('Starting conversion of {}.'.format(input_directory))

    input_path = pathlib.Path(input_directory)
    output_path = pathlib.Path(output_directory)

    verbose('Input : {}'.format(input_path.as_posix()), config['verbose'])
    verbose('Output: {}'.format(output_path.as_posix()), config['verbose'])

    if not input_path.is_dir():
        error('Input path {} is not an existing directory'.format(input_path.as_posix()))
        exit(1)
    if output_path.is_file():
        error('Output path {} is not a directory'.format(output_path.as_posix()))
        exit(1)

    if not output_path.exists():
        verbose('Creating output directory {}'.format(output_path.as_posix()),
                config['verbose'])
        output_path.mkdir(exist_ok=True)

    audio_files = []
    for input_file in input_path.iterdir():
        if input_file.is_file() and input_file.suffix.lower() in AUDIO_EXTENSIONS:
            audio_files.append(input_file)
        elif input_file.is_dir()
    audio_files = [x for x in input_path.iterdir() if x.is_file() and x.suffix.lower() in AUDIO_EXTENSIONS]
    audio_files = list(map(lambda x: {
                                'output_format': output_format,
                                'verbose': config['verbose'],
                                'output_path': output_path,
                                'file_path': x
                           }, audio_files))
    with Pool(processes=5) as worker:
        worker.map(converter, audio_files)

    success('See {} for converted audio.'.format(output_directory))


def converter(audio_datum):
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
    # Conversion specific data
    output_format = audio_datum['output_format'][1:]
    output_path = audio_datum['output_path']
    verbose_flag = audio_datum['verbose']

    # File specific data
    audio_file = audio_datum['file_path']
    audio_name = audio_file.name[:audio_file.name.rfind('.')]
    converted_name = '{}.{}'.format(audio_name, output_format)

    verbose('Converting {} to {}'.format(audio_name, output_format),
            verbose_flag)
    audio = AudioSegment.from_file(audio_file.as_posix(),
                                   audio_file.suffix[1:])
    output_name = output_path.joinpath(converted_name)
    audio.export(output_name.as_posix(),
                 format=output_format,
                 bitrate='192k')

    verbose('{} converted'.format(audio_name), verbose_flag)


def get_config(context):
    """
    Fetch the config dictionary from the click.Context.
    """
    return context.obj['config']


def success(message):
    """
    Display a success message in green.
    """
    display('[ SUCCESS ] {}'.format(message), 'green')


def info(message):
    """
    Display an info message in blue.
    """
    display('[ INFO    ] {}'.format(message), 'blue')


def verbose(message, verbose_flag):
    """
    Display a verbose message in cyan.
    """
    if verbose_flag:
        display('[ DEBUG   ] {}'.format(message), 'cyan')


def error(message):
    """
    Display an error message in red.
    """
    display('[ ERROR   ] {}'.format(message), 'red')


def display(formatted_message, color):
    """
    Style a formatted_message message with the given color
    and print it.
    """
    click.secho(formatted_message, fg=color)
