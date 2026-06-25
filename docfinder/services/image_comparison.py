"""Image Comparison Service."""
import io
import base64
import numpy as np
from PIL import Image, ImageChops

class ImageComparisonEngine:
    """Engine for comparing two images to find visual differences."""

    @staticmethod
    def compare_images(image1_bytes: bytes, image2_bytes: bytes) -> dict:
        """
        Compare two images and return similarity score and diff image.
        
        Args:
            image1_bytes: Original image bytes
            image2_bytes: Modified image bytes
            
        Returns:
            Dictionary containing similarity score and base64 diff image
        """
        try:
            img1 = Image.open(io.BytesIO(image1_bytes)).convert('RGB')
            img2 = Image.open(io.BytesIO(image2_bytes)).convert('RGB')
            
            # Ensure images are same size for comparison
            if img1.size != img2.size:
                img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
                
            # Compute difference
            diff = ImageChops.difference(img1, img2)
            
            # Calculate similarity score based on sum of differences
            diff_np = np.array(diff)
            max_diff = np.prod(diff_np.shape) * 255.0
            actual_diff = np.sum(diff_np)
            
            similarity = 100.0 - ((actual_diff / max_diff) * 100.0) if max_diff > 0 else 100.0
            
            # Highlight differences (red overlay)
            # Create a mask where difference > threshold
            threshold = 30
            mask = np.any(diff_np > threshold, axis=-1)
            
            # Create highlighted image
            highlighted = np.array(img2)
            highlighted[mask] = [255, 0, 0] # Red for differences
            
            diff_img = Image.fromarray(highlighted)
            
            # Convert to base64 for frontend
            buffered = io.BytesIO()
            diff_img.save(buffered, format="JPEG")
            diff_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            return {
                "similarity_score": round(similarity, 2),
                "diff_image_base64": f"data:image/jpeg;base64,{diff_b64}",
                "success": True,
                "overall_similarity": round(similarity, 2)
            }
        except Exception as e:
            return {
                "similarity_score": 0,
                "diff_image_base64": None,
                "success": False,
                "error": str(e)
            }
