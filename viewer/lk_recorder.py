#------------------------------------------------------------------------------
# Recording example. Data is recorded to binary files. See simple player for
# how to extract recorded data.
# Press space to start recording.
# Press stop to stop recording.
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
path = './data'

# Unpack to viewable formats (e.g., encoded video to mp4)
unpack = False

# Ports to record
ports = [
    #hl2ss.StreamPort.RM_VLC_LEFTFRONT,
    #hl2ss.StreamPort.RM_VLC_LEFTLEFT,
    #hl2ss.StreamPort.RM_VLC_RIGHTFRONT,
    #hl2ss.StreamPort.RM_VLC_RIGHTRIGHT,
    #hl2ss.StreamPort.RM_DEPTH_AHAT,
    #hl2ss.StreamPort.RM_DEPTH_LONGTHROW,
    #hl2ss.StreamPort.RM_IMU_ACCELEROMETER,
    #hl2ss.StreamPort.RM_IMU_GYROSCOPE,
    #hl2ss.StreamPort.RM_IMU_MAGNETOMETER,
    hl2ss.StreamPort.PERSONAL_VIDEO,
    hl2ss.StreamPort.MICROPHONE,
    #hl2ss.StreamPort.SPATIAL_INPUT,
    #hl2ss.StreamPort.EXTENDED_EYE_TRACKER,
    # hl2ss.StreamPort.EXTENDED_AUDIO,
    ]

# PV parameters
pv_width     = 760
pv_height    = 428
pv_framerate = 30

# EET parameters
eet_fps = 30 # 30, 60, 90

# Maximum number of frames in buffer
buffer_elements = 300

#------------------------------------------------------------------------------

if __name__ == '__main__':
    if ((hl2ss.StreamPort.RM_DEPTH_LONGTHROW in ports) and (hl2ss.StreamPort.RM_DEPTH_AHAT in ports)):
        print('Error: Simultaneous RM Depth Long Throw and RM Depth AHAT streaming is not supported. See known issues at https://github.com/jdibenes/hl2ss.')
        quit()

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

    # Start PV Subsystem if PV is selected ------------------------------------
    if (hl2ss.StreamPort.PERSONAL_VIDEO in ports):
        hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)

    # Start receivers ---------------------------------------------------------
    
    # Create a producer (thread or process) --> (generates data) --> (puts it into a buffer)
    producer = hl2ss_mp.producer()
    
    # Configure producer "receiver ports" for a specific port and a specific receiver type.
    
    # producer.configure(hl2ss.StreamPort.RM_VLC_LEFTFRONT, hl2ss_lnm.rx_rm_vlc(host, hl2ss.StreamPort.RM_VLC_LEFTFRONT, decoded=False))
    # producer.configure(hl2ss.StreamPort.RM_VLC_LEFTLEFT, hl2ss_lnm.rx_rm_vlc(host, hl2ss.StreamPort.RM_VLC_LEFTLEFT, decoded=False))
    # producer.configure(hl2ss.StreamPort.RM_VLC_RIGHTFRONT, hl2ss_lnm.rx_rm_vlc(host, hl2ss.StreamPort.RM_VLC_RIGHTFRONT, decoded=False))
    # producer.configure(hl2ss.StreamPort.RM_VLC_RIGHTRIGHT, hl2ss_lnm.rx_rm_vlc(host, hl2ss.StreamPort.RM_VLC_RIGHTRIGHT, decoded=False))
    # producer.configure(hl2ss.StreamPort.RM_DEPTH_AHAT, hl2ss_lnm.rx_rm_depth_ahat(host, hl2ss.StreamPort.RM_DEPTH_AHAT, decoded=False))
    # producer.configure(hl2ss.StreamPort.RM_DEPTH_LONGTHROW, hl2ss_lnm.rx_rm_depth_longthrow(host, hl2ss.StreamPort.RM_DEPTH_LONGTHROW, decoded=False))
    # producer.configure(hl2ss.StreamPort.RM_IMU_ACCELEROMETER, hl2ss_lnm.rx_rm_imu(host, hl2ss.StreamPort.RM_IMU_ACCELEROMETER))
    # producer.configure(hl2ss.StreamPort.RM_IMU_GYROSCOPE, hl2ss_lnm.rx_rm_imu(host, hl2ss.StreamPort.RM_IMU_GYROSCOPE))
    # producer.configure(hl2ss.StreamPort.RM_IMU_MAGNETOMETER, hl2ss_lnm.rx_rm_imu(host, hl2ss.StreamPort.RM_IMU_MAGNETOMETER))
    producer.configure(hl2ss.StreamPort.PERSONAL_VIDEO, hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, width=pv_width, height=pv_height, framerate=pv_framerate, decoded_format=None))
    producer.configure(hl2ss.StreamPort.MICROPHONE, hl2ss_lnm.rx_microphone(host, hl2ss.StreamPort.MICROPHONE, decoded=False))
    # producer.configure(hl2ss.StreamPort.SPATIAL_INPUT, hl2ss_lnm.rx_si(host, hl2ss.StreamPort.SPATIAL_INPUT))
    # producer.configure(hl2ss.StreamPort.EXTENDED_EYE_TRACKER, hl2ss_lnm.rx_eet(host, hl2ss.StreamPort.EXTENDED_EYE_TRACKER, fps=eet_fps))
    # producer.configure(hl2ss.StreamPort.EXTENDED_AUDIO, hl2ss_lnm.rx_extended_audio(host, hl2ss.StreamPort.EXTENDED_AUDIO, decoded=False))

    for port in ports:
        # Configure producer "producer" for a specific port, to be a "module" with parameters "receiver" and "buffer length"
        # a "module" here means something that has
        
        # # source_wires / interface_source --> These are to interface between interconnect and source
        
        # # interconnect_wires / interface_interconnect --> These are to interface between interconnect and source
        
        # # source(receiver, source_wires, interconnect_wires) <--> In its own process (needs to be started)
        # # # A source acts as a producer / as a component that generates data : initiating the data flow into the system.
        # # # This could be reading from a file, receiving network packets, or any other data-generating process.
        
        # # interconnect(buffer_size, source_wires, interconnect_wires) <--> In its own process (needs to be started)
        # # # the mechanisms or pathways through which data flows between different components or threads in a multithreaded system.
        # # # This can include shared memory, message passing, or any other method of data exchange that facilitates 
        # # # communication between threads or modules.
        
        producer.initialize(port, buffer_elements)
        
        # Starts the producer's producer = the module
        # This starts the module's / producer's "Interconnect" and "Source" processes, for EACH PORT
        
        producer.start(port)

    # Wait for keyboard start signal ---------------------------------------------------
    print('Press space to start recording...')
    start_event.wait
    print('Preparing...')

    # Start writers -----------------------------------------------------------
    filenames = {port : os.path.join(path, f'{hl2ss.get_port_name(port)}.bin') for port in ports}
    
    # for port in ports, create a dict of writer processes for producers.
    # These write to a specific filename for a specific producer (collection of sources and interconnects) and port (to find a specific source and interconnect), with a specifc user name
    # They have:
    
    # # a mp.Event() stop event to stop eventually stop writing
    
    # # a writer created from the receiver : hl2ss_io.create_wr_from_rx(filename, producer.get_receiver(port), user)
    
    # # a sink process : hl2ss_mp.consumer().create_sink(producer, port, mp.Manager(), ...)
    # # # A sink is the endpoint in a data processing pipeline where the data is ultimately consumed or stored.
    # # # In a multithreading scenario, a sink could be a file writer, a network transmitter...
    
    # # # # This sink is created inside a consumer object for some reason : and There it is attached to the producer
    # # # # sink_wires = _create_interface_sink(manager.Queue(), manager.Queue(), sink_semaphore)
    # # # # sink = _create_sink(sink_wires, producer._get_interface(port))
    # # # # producer._attach_sink(port, sink_wires)
    
    # # # The sink can do these things
    # # # # get_nearest
    # # # # get_frame_stamp
    # # # # get_most_recent_frame
    # # # # get_buffered_frame
    # # # # It always makes sure to manage the semaphore to makesure multiple processes aren't using same interconnect at the same time
    # # # # it uses the interconnect to communicate what is going on
    # # # # 
    # # # # sink in and sink out are both manager.Queue() ==> Shared queue.Queue objects created by the mp.Manager and return a proxy for it.
    # # # # mp.Manager() returns A subclass of BaseManager which can be used for the synchronization of processes.
    # # # # Its methods create and return Proxy Objects for a number of commonly used data types to be synchronized across processes.
    # # # # 
    
    # # self._sync_period = hl2ss_lnm.get_sync_period(self._wr)
    
    writers = {port : hl2ss_utilities.wr_process_producer(filenames[port], producer, port, 'hl2ss LK recorder'.encode()) for port in ports}
    
    for port in ports:
        # Start writer process
        writers[port].start()

    # Wait for stop signal ----------------------------------------------------
    print('Recording started.')
    print('Press esc to stop recording...')
    stop_event.wait()
    print('Stopping...')

    # Stop writers and receivers ----------------------------------------------
    for port in ports:
        writers[port].stop() # Set stop

    for port in ports:
        writers[port].join() # Wait for stop end

    for port in ports:
        producer.stop(port)

    # Stop PV Subsystem if PV is selected -------------------------------------
    if (hl2ss.StreamPort.PERSONAL_VIDEO in ports):
        hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)

    # Stop keyboard events ----------------------------------------------------
    listener.join()

    # Quit if binaries are not to be unpacked ---------------------------------
    if (not unpack):
        quit()

    print('Unpacking binaries (may take several minutes)...')

    # Unpack encoded video streams to a single MP4 file -----------------------
    ports_to_mp4 = [
        hl2ss.StreamPort.PERSONAL_VIDEO,
        hl2ss.StreamPort.MICROPHONE,
        hl2ss.StreamPort.EXTENDED_AUDIO,
        hl2ss.StreamPort.RM_VLC_LEFTFRONT,
        hl2ss.StreamPort.RM_VLC_LEFTLEFT,
        hl2ss.StreamPort.RM_VLC_RIGHTFRONT,
        hl2ss.StreamPort.RM_VLC_RIGHTRIGHT,
        hl2ss.StreamPort.RM_DEPTH_AHAT,        
    ]

    mp4_input_filenames = [filenames[port] for port in ports_to_mp4 if (port in ports)]
    mp4_output_filename = os.path.join(path, 'video.mp4')

    if (len(mp4_input_filenames) > 0):
        hl2ss_utilities.unpack_to_mp4(mp4_input_filenames, mp4_output_filename)

    # Unpack RM Depth Long Throw to a tar file containing Depth and AB PNGs ---
    if (hl2ss.StreamPort.RM_DEPTH_LONGTHROW in ports):
        hl2ss_utilities.unpack_to_png(filenames[hl2ss.StreamPort.RM_DEPTH_LONGTHROW], os.path.join(path, 'long_throw.tar'))

    # Unpack stream metadata and numeric payloads to csv ----------------------
    # This might be nice to do anyways.
    for port in ports:
        input_filename = filenames[port]
        output_filename = input_filename[:input_filename.rfind('.bin')] + '.csv'
        hl2ss_utilities.unpack_to_csv(input_filename, output_filename)

