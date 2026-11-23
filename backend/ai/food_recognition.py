
from transformers import pipeline
from PIL import Image

# Load pretrained food/image recognition model
print("Loading AI food recognition model...")

food_classifier = pipeline(
    "image-classification",
    model="google/vit-base-patch16-224"
)

print("Food recognition model loaded successfully!")


def recognize_food(image_path):
    """
    Recognize food items from an uploaded image.
    Returns the top 5 predictions.
    """

    try:
        image = Image.open(image_path).convert("RGB")

        predictions = food_classifier(image)

        results = []

        for prediction in predictions[:5]:
            results.append({
                "food": prediction["label"],
                "confidence": round(
                    prediction["score"] * 100, 2
                )
            })

        return {
            "success": True,
            "predictions": results
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }
