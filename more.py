from roboflow import Roboflow
rf = Roboflow(api_key="W891m34roeYw16CyrlO4")
project = rf.workspace("detect-images").project("lawn-and-grass")
version = project.version(21)
dataset = version.download("yolov8")

from ultralytics import YOLO

model = YOLO('yolov8n-seg.pt')

model.train(
    data=f"{dataset.location}/data.yaml", 
    epochs=50, 
    imgsz=320,     
    device='mps', 
    workers=2,     
    batch=8        
)