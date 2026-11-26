
from combined_food_recognition import recognize_food

image_path = input("Enter the full path of your food image: ")

result = recognize_food(image_path)

if result["success"]:
    print("\n========== RESCUEBITE AI FOOD RECOGNITION ==========")

    print("\nBEST PREDICTION:")
    print("Food:", result["food"])
    print("Confidence:", str(result["confidence"]) + "%")
    print("Model Used:", result["model_used"])

    print("\nINDIAN FOOD PREDICTIONS:")
    for item in result["indian_predictions"]:
        print(f'{item["food"]}: {item["confidence"]}%')

    print("\nINTERNATIONAL FOOD PREDICTIONS:")
    for item in result["international_predictions"]:
        print(f'{item["food"]}: {item["confidence"]}%')

else:
    print("Error:", result["error"])
