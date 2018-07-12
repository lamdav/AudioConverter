# AudioConverter
A simple CLI to convert a directory of audio files from  one format
to another. This CLI sits ontop of `pydub` and `ffmpeg`

## Setup
### Install `ffmpeg`
Go follow the `pydub`
[tutorial](https://github.com/jiaaro/pydub#getting-ffmpeg-set-up)
on how to set up `ffmpeg` on the various platforms.

## Usage
```shell
λ  audioconvert -v convert INPUT_DIRECTORY OUTPUT_DIRECTORY [--output-format/-o TARGET_FORMAT]
```
