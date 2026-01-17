import cv2
import numpy as np
import time
from collections import deque
from gpiozero import Buzzer
from pyrf24 import RF24, RF24_PA_LOW, RF24_250KBPS

# USER CONFIG

INPUT_MODE = "video"      # "camera" or "video"
VIDEO_PATH = "pushpa.mp4" # Path to video file if INPUT_MODE is "video"

FRAME_SIZE = (640, 480) # Width, Height for processing which matches CCTV camera resolution
ACCUM_FRAMES = 8 # Number of frames to accumulate strain before decision

# BUZZER 

buzzer = Buzzer(13) # GPIO pin 18 for buzzer

def buzzer_beep(on_time, off_time, n):
    buzzer.beep(on_time, off_time, n)

# NRF24L01 SETUP (SPI)

print("[VIGIL AI] Initializing NRF24L01...")

# Initialize radio with CE pin at GPIO 25 and CSN at SPI CE0
radio = RF24(25, 100)  # (CE_PIN, SPI_BUS)

# Check if radio initialized
if not radio.begin():
    print("[ERROR] NRF24L01 hardware not responding!")
    print("Check wiring and power supply")
    exit(1)

print("[VIGIL AI] NRF24L01 initialized successfully")

# Configure radio
radio.setPALevel(RF24_PA_LOW)
radio.setDataRate(RF24_250KBPS)
radio.setChannel(76)
radio.setPayloadSize(1)

# Define the address (must match Arduino receiver)
address = [0x30, 0x30, 0x30, 0x30, 0x31]  # "00001" in ASCII
radio.openWritingPipe(bytes(address))

# Disable auto-acknowledgment for simpler one-way communication
radio.setAutoAck(False)
radio.disableDynamicPayloads()

# Stop listening (we're transmitting)
radio.stopListening()

print("[VIGIL AI] NRF24L01 configured - Ready to transmit")

def nrf_send(value):
    """
    Send a single byte value (0, 1, or 2) to the Arduino receiver
    0 = Normal, 1 = Pre-alert, 2 = Stampede
    """
    if value not in [0, 1, 2]:
        print(f"[NRF ERROR] Invalid value {value}. Must be 0, 1, or 2")
        return False
    
    # Create payload as bytes
    payload = bytes([value])
    
    # Send the data
    success = radio.write(payload)
    
    if success:
        # Uncomment below for debugging transmission
        # print(f"[NRF] Sent: {value}")
        return True
    else:
        print(f"[NRF ERROR] Failed to send: {value}")
        return False

# VIDEO SOURCE SETUP

use_camera = (INPUT_MODE == "camera") 

if use_camera:
    from picamera2 import Picamera2 
    cam = Picamera2()
    cam.configure(cam.create_video_configuration(
        main={"format": "RGB888", "size": FRAME_SIZE}
    )) 
    cam.start()
    time.sleep(1) # Camera warm-up time to prevent noisy datas which may cause false positives
    print("[VIGIL AI] Live camera started")

else:
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video file")
    print("[VIGIL AI] Video file opened")

# TEMPORAL STATE

prev_gray = None 
strain_accum = None # previous strain accumulation is none as the motion hasn't started yet
history = deque(maxlen=20) # store history of strain and energy for temporal decision
frame_id = 0

# LOW-LIGHT ENHANCEMENT

clahe = cv2.createCLAHE(2.0, (8,8)) # CLAHE Increases local contrast in low light conditions and avoids over brightening of noise.

def enhance(gray):
    return clahe.apply(gray) 

# MAIN LOOP

print("[VIGIL AI] Granular crowd model is running")

try:
    while True:

       # FRAME ACQUISITION
        if use_camera:
            frame = cam.capture_array()
        else:
            ret, frame = cap.read()
            if not ret:
                break

        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY if use_camera else cv2.COLOR_BGR2GRAY) # Convert to grayscale as pi camera output is RGB and OpenCV video file is BGR

        if np.mean(gray) < 60:
            gray = enhance(gray) 

        if prev_gray is None:
            prev_gray = gray
            continue

        # OPTICAL FLOW 
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray, None,
            0.5, 3, 15, 3, 5, 1.2, 0  # prev, next, flow, pyramid scale, levels, winsize, iterations, poly_n, poly_sigma, flags
        )

        # REMOVE BULK MOTION
        flow[...,0] -= np.median(flow[...,0]) # removes the x axis bulk motion 
        flow[...,1] -= np.median(flow[...,1]) # removes the y axis bulk motion

        fx, fy = flow[...,0], flow[...,1]

        # GRANULAR STRAIN
        shear = np.sqrt(
            np.gradient(fx, axis=0)**2 +
            np.gradient(fy, axis=1)**2
        ) # shear strain magnitude formula

        if strain_accum is None:
            strain_accum = shear.copy()
        else:
            strain_accum += shear

        frame_id += 1

        # TEMPORAL DECISION
        if frame_id % ACCUM_FRAMES == 0:
            mean_strain = float(np.mean(strain_accum))
            energy = float(np.mean(fx*fx + fy*fy))
            history.append((mean_strain, energy))
            strain_accum = None

            state = 0  # 0 Normal, 1 Pre alert, 2 Stampede

            if len(history) >= 6:
                s_old, e_old = history[0]
                s_new, e_new = history[-1]

                strain_grows = s_new > s_old
                motion_persists = e_new >= 0.8 * e_old

                if strain_grows and motion_persists:
                    state = 2
                elif strain_grows:
                    state = 1

            # ACTUATION
            if state == 2:
                buzzer_beep(5, 1, 6)
                nrf_send(2)
                label = "STAMPEDE"
            elif state == 1:
                buzzer_beep(2, 2, 6)
                nrf_send(1)
                label = "PRE-ALERT"
            else:
                nrf_send(0)
                label = "NORMAL"

            print(f"[{frame_id:05d}] {label} | strain={mean_strain:.4f} energy={energy:.4f}")

        prev_gray = gray
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n[VIGIL AI] Interrupted by user")

finally:
    if use_camera:
        cam.stop()
    else:
        cap.release()

    radio.powerDown()  # Power down the radio
    print("[VIGIL AI] Shutdown complete")
