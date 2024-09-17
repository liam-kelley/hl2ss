# lk multimodal dataset capture script usage

This read me is meant to explain how to setup and use this script.

## Initial setup

1. On the PC, clone the repository, and install the required libraries in a hl2ss conda env.
2. On the HoloLens2, download hl2ss via the github repository on microsoft edge.

## 📐 Recording setup in a new room

Do the following in every new room.

### On recording cart

1. plug in extension cord
2. plug in ethernet
3. Wait for wifi router to boot up

### On HoloLens2

1. Check that the HoloLens is connected to the wifi router.
2. Open **hl2ss** app
3. Check IP address.
4. Open settings > System > Holograms

### On pc

1. Make sure audio will be coming through the speaker.
2. Make sure PC volume is at 40/100.
3. **Change the room name in the following code to the current room.**
4. Make sure the IP address is correct.
5. Run in a new anaconda Prompt:

```bash
conda activate hl2ss
cd Documents/Work/telecom/hl2ss/viewer
python lk_multimodal_dataset_capture.py --roomname "1A242" --nrec 6 --host 192.168.50.61
```

Or just the script if you’re already there

```bash
python lk_multimodal_dataset_capture.py --roomname "1A242" --nrec 6 --host 192.168.50.61
```

## 🎦 Recording protocol

### Recording protocol - On HoloLens2

1. Reset mesh before starting

### Recording protocol - On pc

1. Start script if needed (see above).
2. Tell HL2 guy to reset his mesh (remove all holograms)
3. Press space when ready

### Recording protocol - Recording procedure

1. Walk and look around during 10 second countdown. This is when you're building the mesh. (TODO: pictures could be taken during this process, eventually.)
2. Stay very still during Exponential Sine Sweeps.
3. Repeat 1 and 2 until end sound happens.
4. Quickly place headset on speaker to localize it, get the final mesh and get some sweeps from the point of view of the speaker.

If you missed step 4, you can press l_shift to start step 4 again for the latest capture.
