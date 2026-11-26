try:
    from .food_recognition_v2 import recognize_indian_food
    from .international_food import recognize_international_food

except ImportError:
    from food_recognition_v2 import recognize_indian_food
    from international_food import recognize_international_food

def recognize_food(image_path):
    """
    Run both Indian and international food models.
    Return the prediction with the highest confidence.
    """

    indian_result = recognize_indian_food(image_path)
    international_result = recognize_international_food(image_path)

    if not indian_result["success"]:
        return indian_result

    if not international_result["success"]:
        return international_result

    indian_top = indian_result["predictions"][0]
    international_top = international_result["predictions"][0]

    if indian_top["confidence"] >= international_top["confidence"]:
        best = indian_top
        model_used = "Indian Food Model"
    else:
        best = international_top
        model_used = "International Food Model"

    return {
        "success": True,
        "food": best["food"],
        "confidence": best["confidence"],
        "model_used": model_used,
        "indian_predictions": indian_result["predictions"],
        "international_predictions": international_result["predictions"]
    }
