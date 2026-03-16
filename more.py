from roboflow import Roboflow
rf = Roboflow(api_key="W891m34roeYw16CyrlO4")
project = rf.workspace("detect-images").project("lawn-and-grass")
version = project.version(21)
dataset = version.download("yolov8")

from ultralytics import YOLO

# 1. Load the nano model (best for your stream)
model = YOLO('yolov8n-seg.pt')

# 2. Start training using the path Roboflow just gave you
model.train(
    data=f"{dataset.location}/data.yaml", 
    epochs=50, 
    imgsz=320,      # Smaller is more stable
    device='mps', 
    workers=2,      # Prevents "Time limit" errors from data loading
    batch=8         # Lowers memory usage
)