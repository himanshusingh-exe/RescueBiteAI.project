
import torch
from transformers import (
    AutoImageProcessor,
    AutoModelForImageClassification
)
from PIL import Image

MODEL_NAME = "nateraw/vit-base-food101"

print("Loading international food recognition model...")

processor = AutoImageProcessor.from_pretrained(MODEL_NAME)

model = AutoModelForImageClassification.from_pretrained(
    MODEL_NAME
)

model.eval()

print("International food model loaded successfully!")


def recognize_international_food(image_path):
    try:
        image = Image.open(image_path).convert("RGB")

        inputs = processor(
            images=image,
            return_tensors="pt"
        )

        with torch.no_grad():
            outputs = model(**inputs)

        probabilities = torch.softmax(
            outputs.logits, dim=1
        )[0]

        top_predictions = torch.topk(
            probabilities, k=5
        )

        results = []

        for score, index in zip(
            top_predictions.values,
            top_predictions.indices
        ):
            results.append({
                "food": model.config.id2label[index.item()],
                "confidence": round(score.item() * 100, 2)
            })

        return {
            "success": True,
            "food_type": "International",
            "predictions": results
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }
