import os
import time
import cv2
import numpy as np
import pyvirtualcam
import sounddevice as sd
import wave
import subprocess

def clear_log():
    open("log.txt", "w").close()
    print("\n🧹 Log cleared!\n")

def log_message(message):
    with open("log.txt", "a") as log_file:
        log_file.write(message + "\n")
    print(message)

def extract_audio(video_path):
    audio_path = video_path.replace(".mp4", ".wav")
    if not os.path.exists(audio_path):
        log_message("🔄 Extracting audio from video...")
        cmd = f'ffmpeg -i "{video_path}" -q:a 0 -map a "{audio_path}" -y'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_path

def play_audio(audio_path):
    try:
        wf = wave.open(audio_path, "rb")
    except FileNotFoundError:
        log_message("❌ Error: Audio file not found.")
        return
    samplerate, channels = wf.getframerate(), wf.getnchannels()
    def callback(outdata, frames, time, status):
        data = wf.readframes(frames)
        if len(data) < frames * channels * np.dtype(np.int16).itemsize:
            wf.rewind()
            data = wf.readframes(frames)
        outdata[:] = np.frombuffer(data, dtype=np.int16).reshape(-1, channels)
    with sd.OutputStream(callback=callback, samplerate=samplerate, channels=channels, dtype=np.int16):
        while True:
            time.sleep(1)

def start_stream(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        log_message("❌ Error: Failed to open video.")
        return
    fps, width, height = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    audio_path = extract_audio(video_path)
    log_message(f"📹 Starting virtual camera with resolution {width}x{height} @ {fps} FPS")
    with pyvirtualcam.Camera(width, height, fps=fps) as cam:
        log_message(f"✅ Virtual Camera Active: {cam.device}")
        log_message("🎤 Virtual Mic Active")
        start_time = time.time()
        last_log_time = start_time
        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cam.send(frame)
            cam.sleep_until_next_frame()
            if time.time() - last_log_time >= 10:
                log_message("⏱️ 10 seconds passed...")
                last_log_time = time.time()
try:
    while True:
        print("\n1. Choose video\n2. Start live stream\n3. Clear log\n4. Exit")
        choice = input("Enter choice: ")
        if choice == "1":
            video_path = input("Enter video path: ").strip()
            if os.path.exists(video_path):
                log_message(f"🎬 Video selected: {video_path}")
            else:
                log_message("❌ Error: Video file not found.")
        elif choice == "2":
            if 'video_path' in locals():
                start_stream(video_path)
            else:
                log_message("⚠️ Please choose a video first!")
        elif choice == "3":
            clear_log()
        elif choice == "4":
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice, try again.")
except KeyboardInterrupt:
    print("\n👋 Exiting...")
