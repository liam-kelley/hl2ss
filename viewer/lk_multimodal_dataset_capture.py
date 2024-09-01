#------------------------------------------------------------------------------
# Liam Kelley's Multimodal Mesh-Audio-Image HL2 recording session
#------------------------------------------------------------------------------

from pynput import keyboard
import multiprocessing as mp
import argparse

import hl2ss
import hl2ss_lnm
import hl2ss_mp
import hl2ss_utilities
import hl2ss_sa
import hl2ss_io
import lk_hl2ss

### Initial setup
# Get HoloLens IP
# Allow developper mode
# Download and install hl2ss from their github

### MESH RESET
# 1. Open settings > System > Holograms
# 2. Remove all holograms

### OPTIONAL 
# 1. Go to https://192.168.50.61
# 2. Check that the mesh is reset

#------------------------------------------------------------------------------
# Settings --------------------------------------------------------------------
#------------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(description='lk multimodal dataset capture')

    # Add arguments
    parser.add_argument('--mute', type=bool, default=False, help='Flag to mute the audio (default: True)')
    parser.add_argument('--visualize', type=bool, default=False, help='Flag to visualize the data (default: False)')
    parser.add_argument('--roomname', type=str, default='LiamsOffice', help='Name of the room (default: LiamsOffice)')
    parser.add_argument('--host', type=str, default='192.168.50.61', help='HoloLens address (default: 192.168.50.61)')
    parser.add_argument('--nrec', type=int, default=5, help='Number of consecutive recordings in a rec sesh (default: 5)')

    # Parse arguments
    return parser.parse_args()

# Recorded channels
channels = [
    "PERSONAL_VIDEO",
    "MICROPHONE",
    "SPATIAL_INPUT",
    "SPATIAL_MAPPING",
]

# PV parameters
pv_width     = 760
pv_height    = 428
pv_framerate = 30

# Spatial_Mapping manager parameters
tpcm = 500 # triangles per cubic meter
threads = 2
radius = 2

# # EET parameters (currently unused)
# eet_fps = 30 # 30, 60, 90 

if __name__ == '__main__':
    
    pargs = parse_arguments()
    
    print("\nWelcome to lk multimodal dataset capture !!")
    
    #------------------------------------------------------------------------------
    # HL2 Setup -------------------------------------------------------------------
    #------------------------------------------------------------------------------
    
    # Checks for compatible channels
    if ("RM_DEPTH_LONGTHROW" in channels) and ("RM_DEPTH_AHAT" in channels):
        print('Error: Simultaneous RM Depth Long Throw and RM Depth AHAT streaming is not supported. See known issues at https://github.com/jdibenes/hl2ss.')
        quit()
    if ("SPATIAL_MAPPING" in channels) and not ("SPATIAL_INPUT" in channels):
        print('Error: Spatial Mapping requires Spatial Input.')
        quit()

    # Channel correspondance (receivers)
    receivers = {
        "RM_VLC_LEFTFRONT" : hl2ss_lnm.rx_rm_vlc(pargs.host, hl2ss.StreamPort.RM_VLC_LEFTFRONT, decoded=True),
        "RM_VLC_LEFTLEFT" : hl2ss_lnm.rx_rm_vlc(pargs.host, hl2ss.StreamPort.RM_VLC_LEFTLEFT, decoded=True),
        "RM_VLC_RIGHTFRONT" : hl2ss_lnm.rx_rm_vlc(pargs.host, hl2ss.StreamPort.RM_VLC_RIGHTFRONT, decoded=True),
        "RM_VLC_RIGHTRIGHT" : hl2ss_lnm.rx_rm_vlc(pargs.host, hl2ss.StreamPort.RM_VLC_RIGHTRIGHT, decoded=True),
        # "RM_DEPTH_AHAT" : hl2ss_lnm.rx_rm_depth_ahat(pargs.host, hl2ss.StreamPort.RM_DEPTH_AHAT, decoded=True),
        "RM_DEPTH_LONGTHROW" : hl2ss_lnm.rx_rm_depth_longthrow(pargs.host, hl2ss.StreamPort.RM_DEPTH_LONGTHROW, decoded=True),
        # "RM_IMU_ACCELEROMETER" : hl2ss_lnm.rx_rm_imu(pargs.host, hl2ss.StreamPort.RM_IMU_ACCELEROMETER),
        # "RM_IMU_GYROSCOPE" : hl2ss_lnm.rx_rm_imu(pargs.host, hl2ss.StreamPort.RM_IMU_GYROSCOPE),
        # "RM_IMU_MAGNETOMETER" : hl2ss_lnm.rx_rm_imu(pargs.host, hl2ss.StreamPort.RM_IMU_MAGNETOMETER),
        "PERSONAL_VIDEO" : hl2ss_lnm.rx_pv(pargs.host, hl2ss.StreamPort.PERSONAL_VIDEO, width=pv_width, height=pv_height,
                                            framerate=pv_framerate, decoded_format = 'rgb24', mode = hl2ss.StreamMode.MODE_1), # Stream mode 1 includes camera pose, 0 doesn't
        "MICROPHONE" : hl2ss_lnm.rx_microphone(pargs.host, hl2ss.StreamPort.MICROPHONE, profile=hl2ss.AudioProfile.RAW, level=hl2ss.AACLevel.L5), # Miicrophone Array
        "SPATIAL_INPUT" : hl2ss_lnm.rx_si(pargs.host, hl2ss.StreamPort.SPATIAL_INPUT),
        # "EXTENDED_EYE_TRACKER" : hl2ss_lnm.rx_eet(pargs.host, hl2ss.StreamPort.EXTENDED_EYE_TRACKER, fps=eet_fps),
        # "EXTENDED_AUDIO" : hl2ss_lnm.rx_extended_audio(pargs.host, hl2ss.StreamPort.EXTENDED_AUDIO, decoded=False),
    }
    
    # Start PV Subsystem if PV is selected
    if ("PERSONAL_VIDEO" in channels):
        hl2ss_lnm.start_subsystem_pv(pargs.host, hl2ss.StreamPort.PERSONAL_VIDEO)

    # Start Spatial mapping manager if selected
    if "SPATIAL_MAPPING" in channels:
        sm_manager = hl2ss_sa.sm_manager(pargs.host, tpcm, threads)
        
    #------------------------------------------------------------------------------
    # Process setup ---------------------------------------------------------------
    #------------------------------------------------------------------------------
    
    # Used to stop everything
    overall_script_stop_event = mp.Event()
    session_running_flag = mp.Event()
    interrupt_session = mp.Event()
    stop_audio_recording = mp.Event()
    si_receiver_already_open_flag = mp.Event()
    
    names=["audio_player", "audio_recorder", "mesh_recorder", "image_recorder","manager"]
    instruction_queues={}
    for name in names:
        instruction_queues[name] = mp.Queue()
    out_queues={}
    for name in names:
        out_queues[name] = mp.Queue()
        
    # Manager process
    rec_session_manager_process = mp.Process(target=lk_hl2ss.rec_sesh_manager,
                                    args=(overall_script_stop_event,
                                        session_running_flag,
                                        interrupt_session,
                                        stop_audio_recording,
                                        instruction_queues,
                                        out_queues,
                                        pargs.nrec,
                                        pargs.roomname))
    
    # Mesh process
    mesh_recorder_process = mp.Process(target=lk_hl2ss.mesh_recorder,
                                        args=(overall_script_stop_event,
                                              stop_audio_recording,
                                            instruction_queues["mesh_recorder"],
                                            out_queues["mesh_recorder"],
                                            receivers["SPATIAL_INPUT"],
                                            sm_manager,
                                            radius,
                                            pargs.visualize))
    # Audio process
    audio_player_process = mp.Process(target=lk_hl2ss.audio_player,
                                        args=(overall_script_stop_event,
                                            instruction_queues["audio_player"],
                                            out_queues["audio_player"],
                                            pargs.mute))
    audio_recorder_process = mp.Process(target=lk_hl2ss.audio_recorder,
                                        args=(overall_script_stop_event,
                                            stop_audio_recording,
                                            instruction_queues["audio_recorder"],
                                            out_queues["audio_recorder"],
                                            receivers["MICROPHONE"],
                                            pargs.visualize))
    # Image process
    image_recorder_process = mp.Process(target=lk_hl2ss.image_recorder,
                                        args=(overall_script_stop_event,
                                            instruction_queues["image_recorder"],
                                            out_queues["image_recorder"],
                                            receivers["PERSONAL_VIDEO"],
                                            pargs.visualize))
    
    # Start all processes
    processes = [mesh_recorder_process, audio_player_process,
                audio_recorder_process, image_recorder_process,
                rec_session_manager_process]
    for process in processes:
        process.start()

    # Check all inits
    for key, queue in out_queues.items():
        assert (msg := queue.get()) == "started", f"Expected 'started' for {key}, but got {msg}"

    #------------------------------------------------------------------------------
    # Start / stop  via Keyboard Manager ------------------------------------------
    #------------------------------------------------------------------------------

    def on_press(key):
        '''
        This function runs when a key is pressed on the keyboard.
        When space is pressed, and no process is yet created, a new process (and stop event) is created.
        This process is to manage the recording.
        
        When esc is pressed, and there is an active process, the stop event is set.
        The process will hear this, and should stop itself cleanly.
        
        The keys can then be pressed again to start new recordings.
        If there are no processes, esc can be used to quit the recording manager.
        '''
        # These are global because they're defined outside this on_press function
        global overall_script_stop_event
        global session_running_flag
        global interrupt_session
        global instruction_queues

        if not overall_script_stop_event.is_set():
            # On space, start a recording session, or do nothing
            if key == keyboard.Key.space:
                print("Signaling to manager to start recording session")
                while not instruction_queues["manager"].empty():
                    instruction_queues["manager"].get()
                instruction_queues["manager"].put("start_rec_session")
            
            # On esc, either stop the session, or keyboard manager
            elif key == keyboard.Key.esc:
                if session_running_flag.is_set():
                    print("Session underway. Signaling to manager to stop recording session")
                    interrupt_session.set()
                    while not instruction_queues["manager"].empty():
                        instruction_queues["manager"].get()
                else:
                    print("Signaling to all to stop")
                    for queue in instruction_queues.values():
                        queue.put("stop")
                    overall_script_stop_event.set()
            
            elif key == keyboard.Key.shift_l:
                if session_running_flag.is_set():
                    print("Session underway. Signaling to manager to move on to getting source position")
                    interrupt_session.set()
                    while not instruction_queues["manager"].empty():
                        instruction_queues["manager"].get()
                    instruction_queues["manager"].put("get_src_pov")
                else:
                    print("Signaling to manager to get the source position for the previous session")
                    while not instruction_queues["manager"].empty():
                        instruction_queues["manager"].get()
                    instruction_queues["manager"].put("get_src_pov")
                    
                    
                    
                

    # Start the keyboard listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    #------------------------------------------------------------------------------
    # Run & Stop & Cleanup --------------------------------------------------------
    #------------------------------------------------------------------------------

    # Run everything until overall stop
    overall_script_stop_event.wait()

    # Stop the keyboard listener
    listener.stop()
    listener.join()
    print("Keyboard Listener stopped.")
    
    # Make sure all other processes are done
    for process in processes:
        process.join()
    print("All processes stopped. Cheers!")
    