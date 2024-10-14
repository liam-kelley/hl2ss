#------------------------------------------------------------------------------
# Basic audio recording example.
# Data is recorded to binary files.
# See basic audio player for how to extract recorded data.
# Press space to start recording.
# Press stop to stop recording.
# 
# Note: Using a "producer" might be overkill since we're only recording audio.
# Maybe a method using only the receiver could be cleaner? But this should work just fine.
# 
# Note: This script is untested because I don't have a HoloLens2 !
#------------------------------------------------------------------------------

from pynput import keyboard

import os
import threading
import hl2ss
import hl2ss_lnm
import hl2ss_mp
import hl2ss_utilities

# Settings --------------------------------------------------------------------

# HoloLens address
host = '192.168.50.61'

# Output directory
path = './audio_data'

# Maximum number of frames in buffer
buffer_elements = 300

# Port
port = hl2ss.StreamPort.MICROPHONE # Optionally, port = hl2ss.StreamPort.EXTENDED_AUDIO

#------------------------------------------------------------------------------

if __name__ == '__main__':

    # Keyboard events ---------------------------------------------------------
    start_event = threading.Event()
    stop_event = threading.Event()

    def on_press(key):
        global start_event
        global stop_event

        if (key == keyboard.Key.space):
            start_event.set()
        elif (key == keyboard.Key.esc):
            stop_event.set()

        return not stop_event.is_set()

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Start receiver ---------------------------------------------------------
    producer = hl2ss_mp.producer()
    producer.configure(hl2ss.StreamPort.MICROPHONE, hl2ss_lnm.rx_microphone(host, hl2ss.StreamPort.MICROPHONE, decoded=False))
    producer.initialize(hl2ss.StreamPort.MICROPHONE, buffer_elements)
    producer.start(hl2ss.StreamPort.MICROPHONE)

    # Wait for start signal ---------------------------------------------------
    print('Press space to start recording...')
    start_event.wait()
    print('Preparing...')

    # Start writer -----------------------------------------------------------
    filename = os.path.join(path, f'{hl2ss.get_port_name(hl2ss.StreamPort.MICROPHONE)}.bin')
    writer = hl2ss_utilities.wr_process_producer(filename, producer, hl2ss.StreamPort.MICROPHONE, 'hl2ss basic audio recorder'.encode())
    writer.start()

    # Now writing any audio received until...

    # Wait for stop signal ----------------------------------------------------
    print('Recording started.')
    print('Press esc to stop recording...')
    stop_event.wait()
    print('Stopping...')

    # Stop writers and receivers ----------------------------------------------
    writer.stop()
    writer.join()
    producer.stop(hl2ss.StreamPort.MICROPHONE)

    # Stop keyboard events ----------------------------------------------------
    listener.join()
