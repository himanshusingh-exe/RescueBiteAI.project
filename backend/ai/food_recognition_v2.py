
import torch
from transformers import (
    AutoImageProcessor,
    AutoModelForImageClassification
)
from PIL import Image

MODEL_NAME = "Vishnu-add/finetuned-indian-food"
BASE_MODEL = "google/vit-base-patch16-224-in21k"

print("Loading Indian food recognition model...")

processor = AutoImageProcessor.from_pretrained(BASE_MODEL)

model = AutoModelForImageClassification.from_pretrained(
    MODEL_NAME
)

model.eval()

print("Indian food model loaded successfully!")


def recognize_indian_food(image_path):
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
            probabilities, k=min(5, len(probabilities))
        )

        results = []

        for score, index in zip(
            top_predictions.values,
            top_predictions.indices
        ):
            label = model.config.id2label[index.item()]

            results.append({
                "food": label,
                "confidence": round(score.item() * 100, 2)
            })

        return {
            "success": True,
            "food_type": "Indian",
            "predictions": results
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }
