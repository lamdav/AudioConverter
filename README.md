# AudioConverter
A simple CLI to convert a directory of audio files from  one format
to another. This CLI sits ontop of `pydub` and `ffmpeg`

## Motivation
I have some old music in a lossless format. Now that I am constantly
jumping between computers, I wanted it to be converted in
a more universal format such as `mp3` so that I can play it with
the simplest of players. I also wanted to avoid having
to stream my music on cloud platforms. Upon a cursory and naive scan
on the web, I found that existing scripts are defunct (again cursory)
or was not as simple as I would like it to be. I did not want to download
a GUI for a one time use or upload a directory of music online to have it
be converted on some server and download it again either. Instead, I wrote
this quick CLI to do it for me.

## Setup
### Install `ffmpeg`
Go follow the `pydub`
[tutorial](https://github.com/jiaaro/pydub#getting-ffmpeg-set-up)
on how to set up `ffmpeg` on the various platforms.

## Usage
```shell
audioconvert [--verbose/-v] convert INPUT_DIRECTORY OUTPUT_DIRECTORY [--output-format/-o TARGET_FORMAT]
```
This will recursively search the `INPUT_DIRECTORY` for files with music
extensions. Each file found will then be converted to the `TARGET_FORMAT` and
placed in the `OUTPUT_DIRECTORY` with the same name but updated extension.

The `--verbose/-v` flag must be provided before the `convert` command. This
will enable debugging logs and allow you to monitor progress.

## Accepted Formats
Due to not being super savvy with audio formats, I hard coded the extensions
that are searched for in the `INPUT_DIRECTORY` and acceptable `TARGET_FORMAT`.
Here is a list of formats I thought were popular:
- .mp3
- .flac
- .aiff
- .mp4
- .m4a
