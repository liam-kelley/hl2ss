#------------------------------------------------------------------------------
# Standalone HoloLens2 Audio Recorder by Liam Kelley using hl2ss
#
# Note: This script is untested on real data because I don't have a HoloLens2 !
#
# Run the script in an anaconda shell
# ```bash
# conda activate hl2ss
# cd Documents/Work/telecom/hl2ss/viewer
# python lk_standalone_hl2_audio_recorder.py
# ```
#
# Test flags
# ```bash
# python lk_standalone_hl2_audio_recorder.py -v -t -d
# ```
#------------------------------------------------------------------------------

import argparse
import multiprocessing as mp
from multiprocessing.synchronize import Event
import os
import traceback
import glob

import matplotlib.pyplot as plt
from pynput import keyboard
import soundfile as sf
import numpy as np

import hl2ss
import hl2ss_lnm


#------------------------------------------------------------------------------
# Settings --------------------------------------------------------------------
#------------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(description='HoloLens2 Audio Recording')

    # Add arguments
    parser.add_argument('--host', type=str, default='192.168.50.61', help='HoloLens address (default: 192.168.50.61)')
    parser.add_argument('--recfolder', type=str, default='audio_data', help='Output directory (default: audio_data)')
    parser.add_argument('--recname', type=str, default='TestRecording', help='Recording name (default: TestRecording)')
    parser.add_argument('--rec_length', type=int, default=5, help='Recording length (s) (default: 5)')
    parser.add_argument('--rec_sublength', type=int, default=2, help='Recording subdivsion length (s) (default: 2)')
    parser.add_argument('--visualize', '-v', action='store_true', help='Flag to visualize the audio data (default: False)')
    parser.add_argument('--test_on_dummy_data', '-t', action='store_true', help='Flag to not open a receiver and instead use dummy data (default: False)')
    parser.add_argument('--dump_outqueues', '-d', action='store_true', help='Dump audio recorder outqueue for debug purposes (default: False)')

    # Parse arguments
    return parser.parse_args()


#------------------------------------------------------------------------------
# Utility ------------------------------------------------------
#------------------------------------------------------------------------------

def make_sure_path(filename):
    '''Ensure the directory structure exists'''
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_base_recording_path(recording_folder,recording_name):
    '''Automatically get the appropriate path based on previous sessions.'''
    
    # Get the previous session number for this room
    previous_sessions=glob.glob(os.path.join(recording_folder, recording_name,"session_*"))
    if any(previous_sessions):
        previous_session_no = max([int(previous_session[-3:]) for previous_session in previous_sessions])
    else:
        previous_session_no = -1
    
    # Get new session number
    session_no = previous_session_no + 1
    formatted_session_no = f"{session_no:03}"
    recording_path = os.path.join(recording_folder, recording_name, f"session_{formatted_session_no}")
    return recording_path

def print_args(pargs):
    print("\nParsed arguments:")
    for arg, value in vars(pargs).items():
        if isinstance(value, bool) and value:  # Check for active flags
            print(f"  {arg}")
        elif not isinstance(value, bool):  # List all non-default values
            print(f"  {arg}: {value}")


class DummyData:
    def __init__(self, payload):
        """
        A wrapper for dummy data to mimic real receiver's data structure.
        
        Args:
            payload (numpy.ndarray): Simulated payload data.
        """
        self.payload = payload


class dummy_mic_receiver():
    def __init__(self, num_channels=5, packet_size=1000):
        """
        A dummy microphone receiver for testing.
        
        Args:
            num_channels (int): Number of audio channels.
            packet_size (int): Number of samples per channel in one packet.
        """
        self.num_channels = num_channels
        self.packet_size = packet_size
    
    def open(self):
        """Simulate opening the receiver."""
        print("Dummy mic receiver opened.")

    def close(self):
        """Simulate closing the receiver."""
        print("Dummy mic receiver closed.")
    
    def get_next_packet(self):
        """
        Simulate receiving a packet of audio data.
        
        Returns:
            DummyData: Simulated data with a payload attribute.
        """
        # Create dummy payload
        payload = np.random.rand(self.num_channels, self.packet_size)
        return DummyData(payload)

#------------------------------------------------------------------------------
# Audio Recorder Process ------------------------------------------------------
#------------------------------------------------------------------------------

def audio_recorder(stop_overall_script : Event, # Informs us to close process
                stop_audio_recording : Event, # Interrupts current audio recording
                session_running : Event, # Signals that recording is underway
                instruction_queue : mp.Queue, # Used to get start or stop instructions
                out_queue : mp.Queue, # Used to communicate back with the main process
                audio_receiver, # From which we get audio samples from the headset. Samples are stored on the haedset in a buffer and are timestamped.
                rec_length : float = 5, # Total recording length
                rec_sublength : float = 2, # Recording subdivision length
                visualize : bool = True): # View audio recording.
    '''
    This will record 5-channel audio for rec_length seconds when asked to, in increments of rec_sublength seconds.
    '''
    
    # Constants
    CHANNELS = {"TOP_LEFT" : hl2ss.Parameters_MICROPHONE.ARRAY_TOP_LEFT, # 0
                "TOP_CENTER" : hl2ss.Parameters_MICROPHONE.ARRAY_TOP_CENTER, # 1
                "TOP_RIGHT" : hl2ss.Parameters_MICROPHONE.ARRAY_TOP_RIGHT, # 2
                "BOTTOM_LEFT" : hl2ss.Parameters_MICROPHONE.ARRAY_BOTTOM_LEFT, # 3
                "BOTTOM_RIGHT" : hl2ss.Parameters_MICROPHONE.ARRAY_BOTTOM_RIGHT} # 4
    N_CHANNELS = hl2ss.Parameters_MICROPHONE.ARRAY_CHANNELS # 5
    SAMPLE_RATE = hl2ss.Parameters_MICROPHONE.SAMPLE_RATE # 48000
        
    # Inform main that process correctly started
    out_queue.put("started")
    
    # While script is still running
    while not stop_overall_script.is_set():
        # Confirm that no recording session is underway
        session_running.clear()
        stop_audio_recording.clear()
        
        print("\nAudio recorder process is waiting for instruction.")
        print("Press space to start recording, esc to quit\n")
        
        # Wait / get next message in the instruction queue.
        msg = instruction_queue.get()
        
        # If recording is to start
        if msg[:9] == "rec_start":
            # 2nd half of message includes the base recording path
            base_recording_path = msg[9:]
            print("Audio recorder: Starting recording session now.")
            print(f"Audio recorder: base_recording_path = {base_recording_path}")
            
            try :
                # Confirm that session is underway
                session_running.set()
                                     
                # Open audio receiver
                audio_receiver.open()
                data = audio_receiver.get_next_packet()
                data = audio_receiver.get_next_packet() # Wait for first few packets to arrive
                PAYLOAD_LENGTH = len(data.payload[0, 0::N_CHANNELS])
                out_queue.put("receiver_opened") # Once connection is established, inform the main process

                # Loop inits and parameters
                subdivision_no = 0
                t = 0
                length = SAMPLE_RATE*rec_length
                sublength = SAMPLE_RATE*rec_sublength
                n_subdivisions = (length // sublength) + 1
                payload = None
                
                # while total recording length isn't reached and main doesn't interrupt us,
                #   record and save into subdivisions
                while subdivision_no < n_subdivisions and not stop_audio_recording.is_set():
                    print(f"Audio recorder: Recording subdivision n°{subdivision_no}. Interrupt recording with esc.")
                    
                    # init new audio subdivision
                    audio = np.zeros((N_CHANNELS, sublength))
                    # overwrite beginning with end of last packet if there is one.
                    if payload is not None: 
                        for channel_no in CHANNELS.values():
                            audio[channel_no, :t] = payload[PAYLOAD_LENGTH-t:]   
                    
                    while t < sublength and not stop_audio_recording.is_set():
                        # Get new payload data
                        data = audio_receiver.get_next_packet()
                        for channel_no in CHANNELS.values(): 
                            payload = data.payload[0, channel_no::N_CHANNELS]
                            assert PAYLOAD_LENGTH == len(payload), "Inconsistent payload length" # I'm assuming consistent payload length.
                            
                            # write it in-place into np.array
                            # min is for edge cases.
                            audio[channel_no, t : min(t + PAYLOAD_LENGTH, sublength)] = payload[:min(PAYLOAD_LENGTH, sublength - t)]                        
                            
                        t += PAYLOAD_LENGTH
                    t -= sublength
                        
                    # Save subdivision as .wav files (1 per channel)
                    wavs_to_save = {}
                    for channel_name, channel_no in CHANNELS.items():
                        filename = os.path.join(base_recording_path,f"part_{subdivision_no:03}",channel_name+'.wav')
                        wavs_to_save[filename] = audio[channel_no, :]
                    for path, wav in wavs_to_save.items():
                        make_sure_path(path)
                        sf.write(path, wav, SAMPLE_RATE)
                        print(f"Audio recorder: File saved to {path}")
                    
                    # Increment subdivision no
                    subdivision_no += 1
                    
                # stop recording
                audio_receiver.close()
                session_running.clear()
                stop_audio_recording.clear()
                    
                if visualize: # Only visualizes last subdivision
                    for key, channel_no in CHANNELS.items():
                        plt.plot(audio[channel_no], label=key)
                    plt.legend()
                    plt.show()
                
                # Signal that the audio was saved
                out_queue.put("done")
                
            except Exception as e:
                # Put the error message in the queue
                error_message = f"Error in audio_recorder: {str(e)}\n{traceback.format_exc()}"
                out_queue.put(error_message)
        elif msg == "stop":
            break
        else:
            print(f"Unexpected messsage in audio_recorder process: {msg}")
    
    # Confirm that no recording session is underway
    session_running.clear()
    
    # Stop
    print("audio_recorder_process stopped.")         

#------------------------------------------------------------------------------
# Main ------------------------------------------------------------------------
#------------------------------------------------------------------------------

if __name__ == '__main__':
    
    # Get arguments
    pargs = parse_arguments()
    
    # Welcome message
    print("\nWelcome to HoloLens2 Audio Recording !!")
    
    print_args(pargs)
    
    # Setup mic array receiver
    if not pargs.test_on_dummy_data:
        mic_array_receiver = hl2ss_lnm.rx_microphone(pargs.host, hl2ss.StreamPort.MICROPHONE, profile=hl2ss.AudioProfile.RAW, level=hl2ss.AACLevel.L5)
    else:
        mic_array_receiver = dummy_mic_receiver()


    # Setup flags
    stop_overall_script = mp.Event() # Stops entire script
    stop_audio_recording = mp.Event() # Stops current audio recording (another recording can be started again.)
    session_running = mp.Event() # Signals an audio recording is underway

    # Setup communication between main and audio recorder process (queues)
    audio_recorder_instruction_queue = mp.Queue() # Used to give orders to audio process.
    audio_recorder_out_queue = mp.Queue() # Used to receive info from audio process.

    # Setup audio recorder process
    audio_recorder_process = mp.Process(target=audio_recorder,
                                        args=(stop_overall_script,
                                            stop_audio_recording,
                                            session_running,
                                            audio_recorder_instruction_queue,
                                            audio_recorder_out_queue,
                                            mic_array_receiver,
                                            pargs.rec_length,
                                            pargs.rec_sublength,
                                            pargs.visualize))
    
    # Start audio recorder process
    audio_recorder_process.start()
    
    # Check (and wait) that process started correctly
    assert (msg := audio_recorder_out_queue.get()) == "started", f"Expected 'started' for audio_recorder_process, but got {msg}"
    
    #------------------------------------------------------------------------------
    # Keyboard Listener Process ---------------------------------------------------
    #------------------------------------------------------------------------------

    def on_press(key):
        '''
        This function runs when the keyboard listener is started and a key is pressed on the keyboard.
        '''
        # These are global because they're defined outside this on_press function
        global stop_overall_script
        global stop_audio_recording
        global session_running
        global audio_recorder_instruction_queue
        global pargs

        if not stop_overall_script.is_set():
            
            # On space press, if not currently running a session, send a message to start a specific recording.
            if key == keyboard.Key.space and not session_running.is_set():
                print("Signaling to audio_recorder to start recording session")
                # Clear previous instructions in queue
                while not audio_recorder_instruction_queue.empty(): audio_recorder_instruction_queue.get() 
                # Add new instruction in queue.
                # The base recording path is included after the start instruction so the audio process knows where to record.
                base_recording_path = get_base_recording_path(recording_folder=pargs.recfolder, recording_name=pargs.recname)
                audio_recorder_instruction_queue.put("rec_start" + base_recording_path)
            
            # On esc, either stop the session, or entire script
            elif key == keyboard.Key.esc:
                if session_running.is_set():
                    print("Recording session underway. Signaling to audio recorder to stop recording session")
                    stop_audio_recording.set()
                    # Clear previous instructions in queue
                    while not audio_recorder_instruction_queue.empty(): audio_recorder_instruction_queue.get() 
                else:
                    print("Signaling to all to stop")
                    audio_recorder_instruction_queue.put("stop")
                    stop_overall_script.set()
    
    # Start the keyboard listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    #------------------------------------------------------------------------------
    # Stop & Cleanup --------------------------------------------------------
    #------------------------------------------------------------------------------

    # Run everything until overall stop
    stop_overall_script.wait()

    # Stop the keyboard listener
    listener.stop()
    listener.join()
    print("Keyboard Listener stopped.")
    
    # Make sure all other processes are done
    audio_recorder_process.join()
    print("All processes stopped. Cheers :)")
    
    if pargs.dump_outqueues:
        # Dump audio_recorder_out_queue
        print("\naudio_recorder_out_queue dump:")
        i=0
        while not audio_recorder_out_queue.empty():
            print(f"[{i}]: ",audio_recorder_out_queue.get())
            i+=1
            