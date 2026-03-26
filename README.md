# Low-Cost Seed Bombing Quadcopter Drone for AI-Assisted Vegetation Propagation

-

## Project motive
The focus of this project is to develop an affordable, scalable way to propagate vegetation in rural areas that current aerial seed-bombing companies struggle to reach. While companies like Airseed and Droneseed use large industrial drones with huge capacity, their high costs and limited drone supply limit how widely and quickly they can distribute seeds. Since this project utilizes low-cost, easily repairable components, this design has the capability to allow for broader adoption across underserved or poorer communities, expanding access to ecological preservation technologies.

Another big focus of this project is to integrate AI vision into this drone and be able to identify which areas have healthy and unhealthy vegetation, involving a lightweight custom segmentation and then just straight hsv analyzation architecture

-

## How to use
Buy a 3D printer to print out all of the STL files, and then download this repo. You will have to install of the dependencies, most important being ultralytics, yolov8, and torch.
Screw together the parts with m3 screws as shown in the master assembly, and then attach the ESP32 below with installed code and preferrably an OV5640 camera.

-

## Technologies used:
Drone design: Onshape, Creality Print
Physical build: Speedybee F405, 22.2v 2200mAh battery, Sunnysky v3506
AI vision: pytorch, YOLOv8
ESP32 code: C++, Arduino IDE

-

## CAD files
All STL files are in the DRONESTLFILES folder, and the public Onshape link is here: https://cad.onshape.com/documents/4d949e733ae3224fbe4bc38b/w/46edb2449a469d3a34608bfa/e/87cf866c0849984a1ade0323
All of the design was done by me! 

-
