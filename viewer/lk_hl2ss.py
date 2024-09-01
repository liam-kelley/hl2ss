from pynput import keyboard
from queue import Empty

import os
import threading
import multiprocessing as mp
from multiprocessing.synchronize import Event
import time
import simpleaudio as sa
import wave
import numpy as np
import matplotlib.pyplot as plt
import open3d as o3d
import soundfile as sf
import cv2
import glob


import hl2ss
import hl2ss_lnm
import hl2ss_mp
import hl2ss_utilities
import hl2ss_sa
import hl2ss_io
import lk_hl2ss

def make_sure_path(filename):
    # Ensure the directory structure exists
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

#------------------------------------------------------------------------------
# process workers -------------------------------------------------------------
#------------------------------------------------------------------------------

def rec_sesh_manager(overall_script_stop_event : Event,
        session_running_flag : Event,
        interrupt_session : Event,
        stop_audio_recording : Event,
        instruction_queues : dict[str,mp.Queue],
        out_queues : dict[str,mp.Queue],
        n_recordings : int,
        room_name : str):
    '''
    Main logic behind a recording session
    '''
    
    out_queues["manager"].put("started")
    
    # Get the previous session number for this room
    previous_sessions=glob.glob(os.path.join("dataset", room_name,"session_*"))
    if any(previous_sessions):
        session_no = max([int(previous_session[-3:]) for previous_session in previous_sessions])
        formatted_session_no = f"{session_no:03}"
    else:
        session_no = -1
        formatted_session_no = f"{session_no:03}"
    
    while not overall_script_stop_event.is_set():
        # Intro message
        print("\nPlease check the following:")
        print(f"    1. Current room : {room_name}. (see --roomname argument)")
        print( "    2. Did you properly get the source position for the previous session?")
        print( "    3. Has the mesh been reset?")
        print("Waiting for instruction. Start = space, Stop = Esc, get previous src pov = L_shift\n")
        
        # Wait for instruction
        msg = instruction_queues["manager"].get()
        
        if msg == "start_rec_session":
            # New session number
            session_no += 1
            formatted_session_no = f"{session_no:03}"
            
            # Start message
            print(f"Starting new recording session n°{formatted_session_no}. n_recordings = {n_recordings}")
            
            # Start time
            session_running_flag.set()
            
            for _ in range(4):
                print("Time to get set up...")
                time.sleep(1)
        
            # Do n_recordings recordings each separated by 3 countdown beeps
            i=0
            while not interrupt_session.is_set() and i < n_recordings:
                i+=1
                # Do countdown
                print(f"Starting countdown...")
                for _ in range(5):
                    # Play audio beep 1sec
                    instruction_queues["audio_player"].put("countdown_beep")
                    # Wait for audio end
                    assert (msg := out_queues["audio_player"].get()) == "countdown_beep_done", f"Expected 'countdown_beep_done', but got {msg}"
                # Wait for beep echo to subside 
                time.sleep(1)
                
                # Define datapoint name, send it to other processes
                datapoint_name = os.path.join(room_name,f"session_{formatted_session_no}",f"time_{str(int(time.time()))}")
                
                print(f"Starting recording n°{i}...")
                # Signal to start white_blast sound
                instruction_queues["audio_player"].put("white_blast")
                # Wait for end of white_blast sound
                assert (msg := out_queues["audio_player"].get()) == "white_blast_done", f"Expected 'white_blast_done', but got {msg}"
                
                # this is here because its also used by the mesh recorder... somehow.
                # TODO make this a lot better. by making a position process, which sends the first position to the mesh.
                stop_audio_recording.clear()
                
                # Signal to record mesh and image
                for key in ["mesh_recorder","image_recorder"]:
                    instruction_queues[key].put("rec_start"+datapoint_name)
                    
                # Signal to start recording audio
                instruction_queues["audio_recorder"].put("rec_start"+datapoint_name)
                # Wait for receiver to be opened
                assert (msg := out_queues["audio_recorder"].get()) == "receiver_opened", f"Expected 'receiver_opened', but got {msg}"
                # Signal to start ESS sound
                instruction_queues["audio_player"].put("ESS")
                # Wait for end of ESS sound
                assert (msg := out_queues["audio_player"].get()) == "ESS_done", f"Expected 'ESS_done', but got {msg}"
                time.sleep(0.3)
                # Stop audio recording
                stop_audio_recording.set()
                
                # Wait for all recording processes to finish
                for key, queue in out_queues.items():
                    if key in ["mesh_recorder", "image_recorder", "audio_recorder"]:
                        assert (msg := queue.get()) == "done", f"Expected 'done', but got {msg}"
                
                print(f"Recording n°{i} is done.")
                
                # Wait 
                time.sleep(1)

            # Recording session is stopped
            stop_audio_recording.clear()
            session_running_flag.clear()
            
            # If session is interrupted, either by esc or shift, just clear
            # If no interruption, move on to getting src point of view
            if interrupt_session.is_set():
                interrupt_session.clear()
                print("Recording session interrupted.")
            else:
                instruction_queues["manager"].put("get_src_pov")
                print("Recording session stopped. Moving on to getting src position.")
        
        elif msg == "get_src_pov":
            if session_no >= 0:
                print(f"Getting src pos for recording session n°{formatted_session_no}.")
                
                session_running_flag.set()
                time.sleep(0.5)
                
                # Define datapoint name, send it to other processes
                datapoint_name = os.path.join(room_name,f"session_{formatted_session_no}",f"source_pov")
                
                print(f"Getting source pov for session {formatted_session_no}.")
                
                # Signal to start source_get_ready_warning sound
                instruction_queues["audio_player"].put("src_pov_warning")
                # Wait for end of source_get_ready_warning sound
                assert (msg := out_queues["audio_player"].get()) == "src_pov_warning_done", f"Expected 'src_pov_warning_done', but got {msg}"
                
                for _ in range(5):
                    print("Waiting...")
                    time.sleep(1)
                print("Recording!")
                
                # Signal to record mesh and image
                for key in ["mesh_recorder","image_recorder"]:
                    instruction_queues[key].put("rec_start"+datapoint_name)
                    
                # Signal to start white_blast sound
                instruction_queues["audio_player"].put("white_blast")
                # Wait for end of white_blast sound
                assert (msg := out_queues["audio_player"].get()) == "white_blast_done", f"Expected 'white_blast_done', but got {msg}"
                time.sleep(0.5)
                # Signal to start recording audio
                stop_audio_recording.clear()
                instruction_queues["audio_recorder"].put("rec_start"+datapoint_name)
                # Wait for receiver to be opened
                assert (msg := out_queues["audio_recorder"].get()) == "receiver_opened", f"Expected 'receiver_opened', but got {msg}"
                # Signal to start ESS sound
                instruction_queues["audio_player"].put("ESS")
                # Wait for end of ESS sound
                assert (msg := out_queues["audio_player"].get()) == "ESS_done", f"Expected 'ESS_done', but got {msg}"
                time.sleep(0.3)
                # Stop audio recording
                stop_audio_recording.set()
                    
                # Wait for all recording processes to finish
                for key, queue in out_queues.items():
                    if key in ["mesh_recorder", "image_recorder", "audio_recorder"]:
                        assert (msg := queue.get()) == "done", f"Expected 'done', but got {msg}"
                
                print(f"Got source pov for session {formatted_session_no}.")
                
                session_running_flag.clear()
            else:
                print("No sessions to get src pov for. Skipping.")
        
        elif msg == "stop":
            break
        else:
            print(f"Unexpected messsage in rec session manager instruction queue: {msg}")
    
    
     
    # Stop
    print("rec_session_manager_process stopped.")
    
    
def mesh_recorder(overall_script_stop_event : Event,
                stop_audio_recording : Event,
                instruction_queue : mp.Queue,
                out_queue : mp.Queue,
                si_receiver : hl2ss.rx_si,
                sm_manager : hl2ss_sa.sm_manager,
                radius : int = 2,
                visualize : bool = False):
    '''
    This will download and save a mesh for you
    '''    
    sm_manager.open()
    # The spatial mapping manager manages creating the observer.
    
    out_queue.put("started")
    
    while not overall_script_stop_event.is_set():
        msg = instruction_queue.get()
        if msg[:9] == "rec_start":
            try :
                # Get current position
                si_receiver.open()
                si_data = si_receiver.get_next_packet()
                si_receiver.close()
                si = hl2ss.unpack_si(si_data.payload)
                head_pose = si.get_head_pose()
                origin = head_pose.position
                
                # Set volume in which to get surfaces.
                volume = hl2ss.sm_bounding_volume()
                volume.add_sphere(origin, radius) # 3D sphere centered on head
                sm_manager.set_volumes(volume)
                # Get meshes within volume. sm_manager simplifies this task.
                sm_manager.get_observed_surfaces()
                meshes = sm_manager.get_meshes()
                meshes = [hl2ss_sa.sm_mesh_to_open3d_triangle_mesh(mesh) for mesh in meshes]
                
                combined_mesh = o3d.geometry.TriangleMesh()
                for mesh in meshes:
                    if len(mesh.vertices) > 0:
                        combined_mesh += mesh

                # Get datapoints
                datapoint = msg[9:]
                
                # Save combined mesh
                if len(combined_mesh.vertices) > 0:
                    obj_path=os.path.join("dataset",datapoint,"mesh",'mesh.obj')
                    make_sure_path(obj_path)
                    o3d.io.write_triangle_mesh(obj_path, combined_mesh)
                else:
                    print("Empty mesh. Skipping saving this one.")

                # Visualization
                if visualize:
                    o3d.visualization.draw_geometries(meshes, mesh_show_back_face=True)

                # Hacky average position save
                si_receiver.open()
                origin, forward, up = [], [], []
                while not stop_audio_recording.is_set():
                    si_data = si_receiver.get_next_packet()
                    si = hl2ss.unpack_si(si_data.payload)
                    head_pose = si.get_head_pose()
                    origin.append(head_pose.position)
                    forward.append(head_pose.forward)
                    up.append(head_pose.up)
                si_receiver.close()
                
                # average positions later TODO
                origin = np.asarray(origin)
                forward = np.asarray(forward)
                up = np.asarray(up)

                # Save HL2 position as .npy files
                to_save = {
                    os.path.join("dataset",datapoint,"position",'origin.npy') : origin,
                    os.path.join("dataset",datapoint,"position",'forward.npy') : forward,
                    os.path.join("dataset",datapoint,"position",'up.npy') : up,    
                }
                for path, thing in to_save.items():
                    make_sure_path(path)
                    np.save(path, thing)
                
                # write info also as text for easy reading
                txt_path = os.path.join("dataset",datapoint,"position",'info_as.txt')
                with open(txt_path, 'w') as file:
                    file.write('right = cross(up, -forward)\n'+ 'up => y, forward => -z, right => x\n')
                    file.write("origin")
                    file.write(str(origin[0]) + "\n")
                    file.write("forward")
                    file.write(str(forward[0]) + "\n")
                    file.write("up")
                    file.write(str(up[0]) + "\n")
                
                # Signal that the mesh was saved
                out_queue.put("done")
                
            except Exception as e:
                # Put the error message in the queue
                out_queue.put(f"Error in mesh recorder: {str(e)}")
                
        elif msg == "stop":
            break
        else:
            print(f"Unexpected messsage in mesh_recorder process: {msg}")
    
    sm_manager.close()
    # Stop
    print("mesh_recorder_process stopped.")
    
    
def audio_player(overall_script_stop_event : Event,
                instruction_queue : mp.Queue,
                out_queue : mp.Queue,
                mute : bool):
    '''
    This will play audio if you want it to
    '''
    folder = 'sound_fx'
    countdown_beep_wave_obj = sa.WaveObject.from_wave_file(os.path.join(folder,"countdown_beep_loud.wav"))
    ESS_wave_obj = sa.WaveObject.from_wave_file(os.path.join(folder,"ESS_x5_1second_pause.wav"))
    src_pov_warning_wave_obj = sa.WaveObject.from_wave_file(os.path.join(folder,"source_get_ready_warning.wav"))
    white_blast_wave_obj = sa.WaveObject.from_wave_file(os.path.join(folder,"white_noise_48kHz_1second.wav"))
    out_queue.put("started")
    
    while not overall_script_stop_event.is_set():
        msg = instruction_queue.get()
        
        try :
            if msg == "countdown_beep":
                print("beep!")
                if not mute:
                    play_obj = countdown_beep_wave_obj.play()
                    time.sleep(1)
                    play_obj.stop()
                out_queue.put("countdown_beep_done")
        
            elif msg == "ESS":
                print("ESS")
                if not mute:
                    play_obj = ESS_wave_obj.play()
                    play_obj.wait_done()
                out_queue.put("ESS_done")
        
            elif msg == "src_pov_warning":
                print("src_pov_warning")
                if not mute:
                    play_obj = src_pov_warning_wave_obj.play()
                    play_obj.wait_done()
                out_queue.put("src_pov_warning_done")
                
            elif msg == "white_blast":
                print("white_blast")
                if not mute:
                    play_obj = white_blast_wave_obj.play()
                    play_obj.wait_done()
                out_queue.put("white_blast_done")
                
            elif msg == "stop":
                break
            else:
                print(f"Unexpected messsage in audio_player process: {msg}")
                
        except Exception as e:
            # Put the error message in the queue
            out_queue.put(f"Error in audio_player: {str(e)}")
    
    # Stop
    print("audio_player_process stopped.")
    
    
def audio_recorder(overall_script_stop_event : Event,
                stop_audio_recording : Event,
                instruction_queue : mp.Queue,
                out_queue : mp.Queue,
                audio_receiver,
                visualize : bool = True):
    '''
    This will record 5-channel audio when asked to.
    '''
    channels = {"TOP_LEFT":hl2ss.Parameters_MICROPHONE.ARRAY_TOP_LEFT, # 0
                "TOP_CENTER":hl2ss.Parameters_MICROPHONE.ARRAY_TOP_CENTER, # 1
                "TOP_RIGHT":hl2ss.Parameters_MICROPHONE.ARRAY_TOP_RIGHT, # 2
                "BOTTOM_LEFT":hl2ss.Parameters_MICROPHONE.ARRAY_BOTTOM_LEFT, # 3
                "BOTTOM_RIGHT":hl2ss.Parameters_MICROPHONE.ARRAY_BOTTOM_RIGHT} # 4
    n_channels = hl2ss.Parameters_MICROPHONE.ARRAY_CHANNELS # 5
    sample_rate = hl2ss.Parameters_MICROPHONE.SAMPLE_RATE # 48000
    
    out_queue.put("started")
    
    while not overall_script_stop_event.is_set():
        
        msg = instruction_queue.get()
        
        if msg[:9] == "rec_start":
            try :                
                # Start audio recording
                audio_receiver.open() # open audio_receiver
                audio=[[],[],[],[],[]] # reset audio list
                data = audio_receiver.get_next_packet()
                data = audio_receiver.get_next_packet() # wait for first packets to arrive
                out_queue.put("receiver_opened") # Once connection is established signal it to manager
                while not stop_audio_recording.is_set(): # while manager tells us to record, record (until ESS is done + 1 second)
                    data = audio_receiver.get_next_packet()
                    for channel in channels.values(): 
                        payload = data.payload[0, channel::n_channels]
                        audio[channel].extend(payload)
                audio_receiver.close() # stop recording
                    
                # Save to .wav files
                datapoint = msg[9:]
                to_save = {}
                for key, channel in channels.items():
                    filename = os.path.join("dataset",datapoint,"audio",key+'.wav')
                    to_save[filename] = audio[channel]
                for path, thing in to_save.items():
                    make_sure_path(path)
                    sf.write(path, thing, sample_rate)
                
                if visualize:
                    for key, channel in channels.items():
                        plt.plot(audio[channel], label=key)
                    plt.legend()
                    plt.show()
                
                # Signal that the audio was saved
                out_queue.put("done")
            except Exception as e:
                # Put the error message in the queue
                out_queue.put(f"Error in audio_recorder: {str(e)}")  
            
        elif msg == "stop":
            break
        else:
            print(f"Unexpected messsage in audio_recorder process: {msg}")
    
    # Stop
    print("audio_recorder_process stopped.")
    
    
def image_recorder(overall_script_stop_event : Event,
                instruction_queue : mp.Queue,
                out_queue : mp.Queue,
                receiver: hl2ss.rx_pv,
                visualize : bool = False):
    '''
    This will download and save an image for you
    '''

    out_queue.put("started")
    
    while not overall_script_stop_event.is_set():
        msg = instruction_queue.get()
        if msg[:9] == "rec_start":
            try :
                # get image
                receiver.open()
                data = receiver.get_next_packet()
                receiver.close()
                
                # Save image as png
                datapoint = msg[9:]
                img_path = os.path.join("dataset",datapoint,"image",'pv.png')
                make_sure_path(img_path)
                plt.imsave(img_path, data.payload.image)

                # Save extra info just in case someone wants it
                txt_path = os.path.join("dataset",datapoint,"image",'more_info.txt')
                make_sure_path(txt_path)
                info = f'Pose at time {data.timestamp}\n'
                info += f'{str(data.pose)}\n'
                info += f'Focal length: {data.payload.focal_length}\n'
                info += f'Principal point: {data.payload.principal_point}'
                with open(txt_path, 'w') as file:
                    file.write(info)

                # visualization
                if visualize:
                    plt.imshow(data.payload.image)
                    plt.axis('off')  # Turn off axis numbers and ticks
                    plt.show()
                
                # Signal that the image was saved
                out_queue.put("done")
            except Exception as e:
                # Put the error message in the queue
                out_queue.put(f"Error in image_recorder: {str(e)}")
                
        elif msg == "stop":
            break
        else:
            print(f"Unexpected messsage in image_recorder process: {msg}")
            
    # Stop
    print("image_recorder stopped.")
