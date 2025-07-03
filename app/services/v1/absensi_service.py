from deepface import DeepFace
import shutil

async def verify_face(img1, img2):
    with open(img1, "wb") as buffer:
        shutil.copyfileobj(img1.file, buffer)
    with open(img2, "wb") as buffer:
        shutil.copyfileobj(img2.file, buffer)
        
    result = DeepFace.verify("temp1.jpg", "temp2.jpg", enforce_detection=False)
    return result