# Low-Cost Seed Bombing Quadcopter Drone for AI-Assisted Vegetation Propagation

-

## Project motive
The focus of this project is to develop an affordable, scalable way to propagate vegetation in rural areas that current aerial seed-bombing companies struggle to reach. While companies like Airseed and Droneseed use large industrial drones with huge capacity, their high costs and limited drone supply limit how widely and quickly they can distribute seeds. Since this project utilizes low-cost, easily repairable components, this design has the capability to allow for broader adoption across underserved or poorer communities, expanding access to ecological preservation technologies.

Another big focus of this project is to integrate AI vision into this drone and be able to identify which areas have healthy and unhealthy vegetation, involving a lightweight custom segmentation and then just straight hsv analyzation architecture

-

## How to use
Buy a 3D printer to print out all of the STL files, and then download this repo. You will have to install of the dependencies, most important being ultralytics, yolov8, and torch.
Screw together the parts with m3 screws as shown in the master assembly, and then attach the ESP32 below with installed code and preferrably an OV5640 camera.

Reason for rejection second time was because they wanted me to deploy the AI segmentation bit, but instead im showing a video demo because:
This part of the project was designed as a real-time computer vision pipeline using OpenCV and YOLOv8 and pyrotch
It relies on direct camera access (In the actual project it is supposed to be using the ESP32 but the computer camera is more clear for a demo), multithreaded frame capture, and needs to be very close to the GPU for performance
Rewriting all of this into a browser compatible demo would take an enormous amount of time again that is out of the scope of this project, and performance would absolutely nosedive

In order to run this on your own machine, download all of the files except for more.py, pvp.py, macro.py, denouncement.py, and the demo files i need to deelte those later not used in this project
Download pytorch, ultralytics, YOLOv8, and any other python libraries that you dont have, and then run esp32_segment.py

There's also a video demo
https://www.youtube.com/watch?v=I8bLy9_4kpg&feature=youtu.be

Also arduino ide code is in there now

-

## Technologies used:
Drone design: Onshape, Creality Print
Physical build: Speedybee F405, 22.2v 2200mAh battery, Sunnysky v3506
AI vision: pytorch, YOLOv8
ESP32 code: C++, Arduino IDE

-

## CAD files
All STL files are in this public Onshape document, link: https://cad.onshape.com/documents/4d949e733ae3224fbe4bc38b/w/46edb2449a469d3a34608bfa/e/87cf866c0849984a1ade0323
All of the design was done by me! 

-
