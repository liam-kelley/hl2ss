#------------------------------------------------------------------------------
# Audio Player example. Plays audio data recorded using basic audio recorder.
#------------------------------------------------------------------------------

import os
import hl2ss
import hl2ss_io
import pyaudio # python -m pip install pyaudio

# Settings --------------------------------------------------------------------

# Directory containing the recorded data
path = './audio_data'

# Adjusted Audio settings (Modify these based on your actual format) -----------
FORMAT = pyaudio.paInt16  # Assuming 16-bit audio format, adjust if needed
CHANNELS = 1              # Assuming mono, change to 2 if stereo
RATE = 16000              # Assuming 16 kHz sample rate, adjust if needed
CHUNK = 1024              # Size of the audio buffer, you can tweak this

# Initialize PyAudio ----------------------------------------------------------
p = pyaudio.PyAudio()

# Open PyAudio stream ---------------------------------------------------------
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True)

# Open bin file ---------------------------------------------------------------
port = hl2ss.StreamPort.MICROPHONE
filename = os.path.join(path, f'{hl2ss.get_port_name(port)}.bin')

# Stream type is detected automatically (Thank you hl2ss)
reader = hl2ss_io.create_rd(filename, hl2ss.ChunkSize.SINGLE_TRANSFER)
reader.open()

# Debug: Check what kind of data is being read --------------------------------
first_packet = reader.get_next_packet()
print(f"First packet type: {type(first_packet)}")
print(f"First packet size: {len(first_packet.payload)} bytes")

# Check if the payload is bytes (raw audio data)
if isinstance(first_packet.payload, bytes):
    print("Payload seems to be raw audio data")
else:
    print("Payload is not raw audio. You may need to decode it.")

# Stream and play audio in real-time ------------------------------------------
while True:
    data = reader.get_next_packet()  # Get next audio packet
    if data is None:
        break  # End of file

    # Play raw audio data if it's in bytes format (assuming raw PCM audio)
    stream.write(data.payload)

# Close the stream and resources ----------------------------------------------
stream.stop_stream()
stream.close()
p.terminate()

# Close the bin file ----------------------------------------------------------
reader.close()
