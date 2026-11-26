
from food_recognition_v2 import recognize_indian_food

image_path = input("Enter the full path of your food image: ")

result = recognize_indian_food(image_path)

if result["success"]:
    print("\n--- INDIAN FOOD RECOGNITION RESULTS ---")

    for item in result["predictions"]:
        print(f'{item["food"]}: {item["confidence"]}%')
else:
    print("Error:", result["error"])
