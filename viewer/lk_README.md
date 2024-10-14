# lk multimodal dataset capture script usage

This README explains how to setup and use my scripts.

These include:

- viewer/lk_multimodal_dataset_capture.py : The main script to run a recording session.
- viewer/lk_hl2ss.py : mp.Processes for recording the streamed mesh, playing audio on the speaker, recording streamed audio, recording streamed images, and managing a recording session.
- viewer/lk_basic_audio_recorder.py : A minimal audio recorder example.
- viewer/lk_basic_audio_player.py : A minimal audio player example.

---

## 🚧 Initial setup

### Setup your Laptop

On the laptop, clone this repository, and install the required libraries in a hl2ss conda env.

```bash
conda create -n hl2ss python=3.9
y
conda activate hl2ss
python -m pip install numpy==1.26.4 open3d pynput opencv-python av simpleaudio soundfile pyaudio
```

You can test your open3d installation like this.

```bash
python
import open3d as o3d
mesh = o3d.geometry.TriangleMesh.create_sphere()
mesh.compute_vertex_normals()
o3d.visualization.draw(mesh, raw_mode=True)
```

### Setup your HoloLens

1. On your HoloLens, Update your HoloLens: Settings -> Update & Security -> Windows Update.
2. On your HoloLens, Enable developer mode: Settings -> Update & Security -> For developers -> Use developer features.
3. On your HoloLens, Enable device portal: Settings -> Update & Security -> For developers -> Device Portal.
4. Enable research mode on your HoloLens via the device portal: Refer to the Enabling Research Mode section in [HoloLens Research Mode](https://docs.microsoft.com/en-us/windows/mixed-reality/develop/advanced-concepts/research-mode). Please note that enabling Research Mode on the HoloLens increases battery usage.
5. On your HoloLens, open Microsoft Edge and navigate to the jdibenes/hl2ss repository, releases section. Then, download the hl2ss release 1.0.33.0 appxbundle "hl2ss_1.0.33.0_arm64.appxbundle". Then Open the appxbundle on your HoloLens and tap Install.

### Setup your recording cart

The recording cart I used had:

- a wifi router with an ethernet cable
- a small high quality speaker (TODO make it have an adjustable height and angle)
- a usb audio interface
- a laptop, the laptop charger
- an extension cable with the speaker and laptop plugged in.

---

## 📐 Recording session setup in a new room

Once you've finished the initial setup, you can setup a recording session in a new room.
Do the following in every new room.

### Session setup - On mobile recording cart

1. Plug in extension cord
2. Plug in ethernet
3. Turn on speaker
4. Wait for wifi router to boot up

### Session setup - On HoloLens2

1. Check that the HoloLens is connected to the wifi router.
2. Open **hl2ss** app
3. Check the HoloLens IP address (readable in the high left corner of your view inside the app).
4. Open settings > System > Holograms

### Session setup - On pc

1. Make sure audio will be coming through the speaker.
2. Make sure PC volume is at 40/100, and audio interface volume is 50%. (TODO calibrate better).
3. **Change the room name in the following code to the current room.**
4. Make sure the IP address argument (--host) is the same as the one in the hl2ss app.
5. Run in a new anaconda Prompt on your windows or linux laptop:

```bash
conda activate hl2ss
cd Documents/Work/telecom/hl2ss/viewer
python lk_multimodal_dataset_capture.py --roomname "1A242" --nrec 6 --host 192.168.50.61
```

Or just the script if you’re already there

```bash
python lk_multimodal_dataset_capture.py --roomname "1A242" --nrec 6 --host 192.168.50.61
```

---

## 🎦 Recording protocol

### Recording protocol - On HoloLens2

1. Reset mesh before starting

### Recording protocol - On pc

1. Start script if needed (see above).
2. Tell HL2 guy to reset his mesh (remove all holograms)
3. Press space when ready

### Recording protocol - Recording procedure

1. Walk and look around during 10 second countdown. This is when you're building the mesh. (TODO: pictures could be taken during this process, eventually.)
2. When countdown ends, a blast of white noise is played. Stop moving now!
3. Stay still and silent during the Exponential Sine Sweeps.

The sweeps get recorded by the HoloLens' 5 microphones. The currently built room mesh, along with the pictures from the Personal Video camera, research mode cameras and longthrow depth camera are captured at the very beginning of the sweeps. Head position is averaged over the entire duration of the sweeps.

4. Repeat 1 through 3 until the final end sound happens.
5. Quickly place the headset onto speaker to localize it + get the final mesh + get some sweeps + pictures from the point of view of the speaker.

If you weren't quick enough and missed step 5, no worries! You can press l_shift to start step 5 again for the latest session.
