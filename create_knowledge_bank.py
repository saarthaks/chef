import json
import os
import csv

class Ingredient:

    def __init__(self, quantity, unit, name):
        self.quantity = quantity
        self.unit = unit
        self.name = name
        

class Recipe:
    def __init__(self, name, cooking_time, total_calories, grams_carbs, grams_fat, grams_protein):
        self.name = name
        self.cooking_time = cooking_time
        self.total_calories = total_calories
        self.grams_carbs = grams_carbs
        self.grams_fat = grams_fat
        self.grams_protein = grams_protein
        self.ingredients = []
    
    def add_ingredient(self, ingredient):
        self.ingredients.append(ingredient)

def parse_recipe_file(filepath):
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)  # Read the first row with recipe details

        # Create a Recipe object
        recipe = Recipe(name=header[0], cooking_time=int(header[1]),
                        total_calories=int(header[2]), grams_carbs=float(header[3]),
                        grams_fat=float(header[4]), grams_protein=float(header[5]))

        # Add ingredients to the Recipe object
        for row in reader:
            if row:  # Ensure the row isn't empty
                ingredient = Ingredient(quantity=float(row[0]), unit=row[1], name=row[2])
                recipe.add_ingredient(ingredient)

    return recipe

def gather_ingredients(recipes_folder):
    ingredients = set()
    for filename in os.listdir(recipes_folder):
        if filename.endswith('.csv'):
            recipe_path = os.path.join(recipes_folder, filename)
            recipe = parse_recipe_file(recipe_path)
            for ingredient in recipe.ingredients:
                if ingredient.name == 'southwest spice blend':
                    print(recipe.name)
                ingredients.add(ingredient.name)
    return ingredients


def input_ingredient_data(ingredient):
    shelf_life = input(f"Enter the shelf life for {ingredient} (or 'q' to finish): ")
    if shelf_life == 'q':
        return None, False

    quantity = input(f"Enter a purchase quantity for {ingredient} (or 'q' to finish): ")
    if quantity == 'q':
        return None, False
    
    unit = input("Enter the unit: ")
    increment = {"quantity": int(quantity), "unit": str(unit)}

    return {"shelf_life": int(shelf_life), "increment": increment}, True

def load_existing_knowledge_bank(knowledge_bank_file):
    try:
        with open(knowledge_bank_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def create_knowledge_bank(recipes_folder, knowledge_bank_file):
    ingredients = gather_ingredients(recipes_folder)
    knowledge_bank = load_existing_knowledge_bank(knowledge_bank_file)

    # Only prompt for ingredients not already in the knowledge bank
    new_ingredients = ingredients - knowledge_bank.keys()
    print(sorted(list(new_ingredients)))
    print(len(new_ingredients))
    for ingredient in new_ingredients:
        data, continue_input = input_ingredient_data(ingredient)
        if continue_input:
            knowledge_bank[ingredient] = data
        else:
            break

    with open(knowledge_bank_file, 'w') as f:
        json.dump(knowledge_bank, f, indent=4)

if __name__ == '__main__':
    recipes_folder = 'app/cookbook'  # Update with the actual path
    knowledge_bank_file = 'app/knowledge_bank.json'  # Update with the desired path
    create_knowledge_bank(recipes_folder, knowledge_bank_file)