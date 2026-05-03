# Smart Helmet Traffic System  
### IoT Project

---

## Overview

This project presents a smart traffic system aimed at improving road safety for motorcycle riders.

The system detects whether riders are wearing helmets and reacts accordingly.  
Instead of only identifying unsafe situations, it actively changes the traffic light behavior to emphasize safety violations.

---

## Project Goal

The main goal of this project is to reduce head injuries and fatalities among motorcycle riders.

This is achieved by:
- detecting riders without helmets  
- responding immediately  
- encouraging safer behavior  

---

## System Architecture

The system is divided into two main components:

### Raspberry Pi  
Responsible for:
- capturing images using a camera  
- sending data to the server  
- controlling the traffic light LEDs  
- displaying warning messages on an OLED screen  

### Computer (Server)  
Responsible for:
- analyzing images  
- detecting motorcycles, riders and helmets  
- making decisions based on the analysis  

---

## System Flow

1. The Raspberry Pi captures an image.  
2. The image is sent to the server.  
3. The server processes the image and detects motorcycles, riders, and helmets.  
4. A decision is made based on the detection results.  

If a rider without a helmet is detected:  
- the traffic light switches to red  
- a warning is displayed on the OLED screen  

If all riders wear helmets or no motorcycle is detected:  
- the traffic light operates normally  

5. The results are displayed on the computer.  
6. The data is stored in Firebase for tracking.

---

## Project Structure

### Computer (Server)

| File | Description |
|------|------------|
| main.py | Starts the server |
| server.py | Handles requests and processing |
| model_logic.py | Detection logic |
| preview_display.py | Visualization |
| firebase_connection.py | Firebase integration |
| uploads/ | Stores incoming images |

---

### Raspberry Pi

| File | Description |
|------|------------|
| main.py | Main system controller |
| camera.py | Image capture |
| server_connection.py | Communication with server |
| traffic_light.py | Traffic light control |
| OLED.py | Warning display |
| photo/ | Captured images |

---

## Technologies Used

- Python – main programming language  
- YOLOv8 – used for detecting motorcycles, riders and helmets  
- Flask – used for communication between Raspberry Pi and server  
- Firebase Firestore – used for storing results  
- Raspberry Pi GPIO – used to control the traffic light  
- OLED display (ST7735) – used to display warning messages  
- PiCamera (Picamera2) – used for capturing images  
- Tkinter – used for displaying results on the computer  

---

## Running the Project

Start the server (computer):

    python src/main.py

Run the Raspberry Pi system:

    python main.py

---

## Notes

- Firebase is used for storing results  
- Running the full system requires valid Firebase credentials  

---

## Summary

This project demonstrates how combining IoT and computer vision can improve road safety.

By moving from passive detection to active response, the system provides a practical approach to reducing motorcycle-related injuries.