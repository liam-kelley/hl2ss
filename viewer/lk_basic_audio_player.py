#------------------------------------------------------------------------------
# Audio Player example. Plays audio data recorded using basic audio recorder.
# 
# Note: This script is untested because I don't have a HoloLens2 !
#------------------------------------------------------------------------------

import os
import hl2ss
import hl2ss_io
import pyaudio # python -m pip install pyaudio

#------------------------------------------------------------------------------
# Settings --------------------------------------------------------------------
#------------------------------------------------------------------------------

# Directory containing the recorded data
path = './audio_data'

# Audio settings
FORMAT = pyaudio.paInt16  # 16-bit audio format (Might need to check this)
N_CHANNELS = hl2ss.Parameters_MICROPHONE.ARRAY_CHANNELS # 5
RATE = hl2ss.Parameters_MICROPHONE.SAMPLE_RATE # 48 kHz

channels = {"TOP_LEFT":hl2ss.Parameters_MICROPHONE.ARRAY_TOP_LEFT, # 0
            "TOP_CENTER":hl2ss.Parameters_MICROPHONE.ARRAY_TOP_CENTER, # 1
            "TOP_RIGHT":hl2ss.Parameters_MICROPHONE.ARRAY_TOP_RIGHT, # 2
            "BOTTOM_LEFT":hl2ss.Parameters_MICROPHONE.ARRAY_BOTTOM_LEFT, # 3
            "BOTTOM_RIGHT":hl2ss.Parameters_MICROPHONE.ARRAY_BOTTOM_RIGHT} # 4

# Choose a specific channel to stream 
selected_channel = channels["TOP_CENTER"]

#------------------------------------------------------------------------------
# Read Audio ------------------------------------------------------------------
#------------------------------------------------------------------------------

# Initialize PyAudio ----------------------------------------------------------
p = pyaudio.PyAudio()

# Open PyAudio stream ---------------------------------------------------------
stream = p.open(format=FORMAT,
                channels=1, # This basic streamer only plays mono.
                rate=RATE,
                output=True)

# Open bin file ---------------------------------------------------------------
port = hl2ss.StreamPort.MICROPHONE
filename = os.path.join(path, f'{hl2ss.get_port_name(port)}.bin')

# Stream type to read is detected automatically (Thank you hl2ss)
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

    # Extract the payload for the selected channel
    channel_payload = data.payload[0, selected_channel::N_CHANNELS]
    
    # Play the selected channel's audio data
    stream.write(channel_payload)

# Close the stream and resources ----------------------------------------------
stream.stop_stream()
stream.close()
p.terminate()

# Close the bin file ----------------------------------------------------------
reader.close()
