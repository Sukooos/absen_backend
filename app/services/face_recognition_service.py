import os
import numpy as np
from deepface import DeepFace
from PIL import Image
import io
import base64
import cv2
import tempfile
from typing import Optional, Tuple, Union, List
import uuid

from app.core.config import settings
from app.core.logger import logger


class FaceRecognitionService:
    """Service for face recognition operations"""
    
    def __init__(self):
        self.model_name = settings.FACE_RECOGNITION_MODEL
        self.distance_metric = settings.FACE_DISTANCE_METRIC
        self.threshold = settings.FACE_THRESHOLD
        self.enforce_detection = True
        
    def process_face_image(self, base64_image: str) -> Optional[bytes]:
        """Process face image from base64 string and extract face encoding"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image)
            
            # Preprocess the image
            processed_image = self.preprocess_image(image_data)
            
            # Extract face encoding
            face_encoding = self.extract_face_encoding(processed_image)
            
            if face_encoding is None:
                logger.warning("No face detected in the image")
                return None
                
            return face_encoding.tobytes()
        except Exception as e:
            logger.error(f"Error processing face image: {str(e)}")
            raise

    def extract_face_encoding(self, image_data: bytes) -> Optional[np.ndarray]:
        """Extract face encoding from image data"""
        try:
            # Create a temporary file to save the image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name

            try:
                # Extract face embedding using DeepFace
                embedding = DeepFace.represent(
                    img_path=temp_file_path,
                    model_name=self.model_name,
                    enforce_detection=self.enforce_detection
                )
                
                # Convert to numpy array if not already
                if not isinstance(embedding, np.ndarray):
                    embedding = np.array(embedding)
                    
                return embedding
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error in face encoding extraction: {str(e)}")
            return None

    def verify_face(self, stored_encoding: bytes, new_image_data: bytes) -> Tuple[bool, float]:
        """Verify a face against a stored encoding"""
        try:
            # Create temporary files for both images
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file1, \
                 tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file2:
                
                # Convert stored encoding back to numpy array
                stored_array = np.frombuffer(stored_encoding, dtype=np.float32)
                
                # Save the stored encoding to a temporary file
                np.save(temp_file1.name, stored_array)
                temp_file1_path = temp_file1.name
                
                # Save the new image to a temporary file
                temp_file2.write(new_image_data)
                temp_file2_path = temp_file2.name

            try:
                # Extract embedding from new image
                new_embedding = DeepFace.represent(
                    img_path=temp_file2_path,
                    model_name=self.model_name,
                    enforce_detection=self.enforce_detection
                )
                
                # Calculate distance between embeddings
                if self.distance_metric == "cosine":
                    distance = self.cosine_distance(stored_array, new_embedding)
                else:
                    # Use DeepFace's built-in verification
                    result = DeepFace.verify(
                        img1_path=temp_file1_path,
                        img2_path=temp_file2_path,
                        model_name=self.model_name,
                        distance_metric=self.distance_metric,
                        enforce_detection=self.enforce_detection
                    )
                    distance = result.get("distance", float('inf'))
                
                # Determine if it's a match based on threshold
                is_match = distance <= self.threshold
                
                # Calculate confidence score (0-100%)
                confidence = max(0, min(100, 100 * (1 - distance / self.threshold)))
                
                return is_match, confidence
            finally:
                # Clean up temporary files
                for path in [temp_file1_path, temp_file2_path]:
                    if os.path.exists(path):
                        os.unlink(path)
                        
        except Exception as e:
            logger.error(f"Error in face verification: {str(e)}")
            return False, 0.0

    def verify_face_from_base64(self, stored_encoding: bytes, base64_image: str) -> Tuple[bool, float]:
        """Verify a face from base64 image against a stored encoding"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image)
            
            # Preprocess the image
            processed_image = self.preprocess_image(image_data)
            
            # Verify face
            return self.verify_face(stored_encoding, processed_image)
        except Exception as e:
            logger.error(f"Error in face verification from base64: {str(e)}")
            return False, 0.0

    def preprocess_image(self, image_data: bytes) -> bytes:
        """Preprocess image for better face detection"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error("Failed to decode image")
                return image_data

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

            # Apply some basic image enhancements
            # Adjust brightness and contrast if needed
            alpha = 1.2  # Contrast control (1.0 means no change)
            beta = 10    # Brightness control (0 means no change)
            img_rgb = cv2.convertScaleAbs(img_rgb, alpha=alpha, beta=beta)

            # Convert back to bytes
            is_success, buffer = cv2.imencode(".jpg", img_rgb)
            if is_success:
                return buffer.tobytes()
            return image_data
        except Exception as e:
            logger.error(f"Error in image preprocessing: {str(e)}")
            return image_data
    
    @staticmethod
    def cosine_distance(vector1: np.ndarray, vector2: np.ndarray) -> float:
        """Calculate cosine distance between two vectors"""
        if vector1 is None or vector2 is None:
            return float('inf')
            
        vector1 = vector1.flatten()
        vector2 = vector2.flatten()
        
        dot_product = np.dot(vector1, vector2)
        norm_product = np.linalg.norm(vector1) * np.linalg.norm(vector2)
        
        if norm_product == 0:
            return float('inf')
            
        similarity = dot_product / norm_product
        # Convert similarity to distance (0 = identical, 2 = completely different)
        distance = 1 - similarity
        
        return distance 