import os
import numpy as np
from deepface import DeepFace
from PIL import Image
import io
import base64
import cv2
from typing import Optional, Tuple
import tempfile

class FaceRecognitionService:
    def __init__(self):
        self.model_name = "VGG-Face"  # You can also use: "Facenet", "OpenFace", "DeepFace", "DeepID", "Dlib", "ArcFace"
        self.distance_metric = "cosine"
        self.threshold = 0.4  # Adjust this threshold based on your needs

    def extract_face_encoding(self, image_data: bytes) -> Optional[np.ndarray]:
        try:
            # Create a temporary file to save the image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name

            # Extract face embedding using DeepFace
            embedding = DeepFace.represent(
                img_path=temp_file_path,
                model_name=self.model_name,
                enforce_detection=True
            )

            # Clean up the temporary file
            os.unlink(temp_file_path)

            return np.array(embedding)
        except Exception as e:
            print(f"Error in face encoding extraction: {str(e)}")
            return None

    def verify_face(self, stored_encoding: bytes, new_image_data: bytes) -> Tuple[bool, float]:
        try:
            # Create temporary files for both images
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file1, \
                 tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file2:
                
                # Write stored encoding to temp file
                temp_file1.write(stored_encoding)
                # Write new image to temp file
                temp_file2.write(new_image_data)

                # Verify faces using DeepFace
                result = DeepFace.verify(
                    img1_path=temp_file1.name,
                    img2_path=temp_file2.name,
                    model_name=self.model_name,
                    distance_metric=self.distance_metric,
                    enforce_detection=True
                )

                # Clean up temporary files
                os.unlink(temp_file1.name)
                os.unlink(temp_file2.name)

                verified = result["verified"]
                distance = result["distance"]

                return verified, distance
        except Exception as e:
            print(f"Error in face verification: {str(e)}")
            return False, float('inf')

    @staticmethod
    def preprocess_image(image_data: bytes) -> bytes:
        """Preprocess image for better face detection"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Convert to RGB (DeepFace expects RGB)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Resize if image is too large
            max_size = 800
            height, width = img_rgb.shape[:2]
            if height > max_size or width > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img_rgb = cv2.resize(img_rgb, (new_width, new_height))

            # Convert back to bytes
            is_success, buffer = cv2.imencode(".jpg", img_rgb)
            if is_success:
                return buffer.tobytes()
            return image_data
        except Exception as e:
            print(f"Error in image preprocessing: {str(e)}")
            return image_data 