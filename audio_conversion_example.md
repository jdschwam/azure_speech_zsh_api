# Audio Conversion Filename Example

When the Azure Speech API script converts audio files to optimal format for speech recognition, it now includes the original format in the filename and replaces any spaces with underscores to ensure clean, consistent filenames.

## Example Conversions:

**Original files → Converted files:**
- `test.mp3` → `test_converted_from_mp3.wav`
- `audio.m4a` → `audio_converted_from_m4a.wav`
- `speech file.flac` → `speech_file_converted_from_flac.wav`
- `my recording.ogg` → `my_recording_converted_from_ogg.wav`
- `voice message.mp3` → `voice_message_converted_from_mp3.wav`

This helps identify the source format, maintains a clear audit trail of file conversions, and ensures compatibility by removing spaces from filenames.

## Usage:
```bash
# This will automatically convert the MP3 to optimal WAV format
./azure_speech_v1.sh stt samples_audio/test.mp3

# The conversion creates: samples_audio/test_converted_from_mp3.wav

# Files with spaces in names get underscores:
./azure_speech_v1.sh stt "samples_audio/voice message.mp3"
# Creates: samples_audio/voice_message_converted_from_mp3.wav
# Transcription: output/stt/transcription_20250720_123456_voice_message.txt
```

The converted files are optimized for Azure Speech Recognition:
- Sample rate: 16kHz
- Channels: Mono (1 channel)
- Format: 16-bit PCM WAV

## Important Notes:

**Audio Conversion**: Converted audio files get the new naming format with underscores and format tracking.

**Transcription Files**: The transcription output files (`.txt` and `.json`) also replace spaces with underscores for consistent, clean filenames across all outputs.
