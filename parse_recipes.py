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

def recipe_to_dict(recipe):
    # Convert Recipe and its Ingredients to a dictionary (which is JSON-serializable)
    return {
        'name': recipe.name,
        'cooking_time': recipe.cooking_time,
        'total_calories': recipe.total_calories,
        'grams_carbs': recipe.grams_carbs,
        'grams_fat': recipe.grams_fat,
        'grams_protein': recipe.grams_protein,
        'ingredients': [
            {'quantity': ing.quantity, 'unit': ing.unit, 'name': ing.name}
            for ing in recipe.ingredients
        ]
    }

def cache_recipes(folder_path, cache_file):
    recipes = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            recipe_path = os.path.join(folder_path, filename)
            recipe = parse_recipe_file(recipe_path)
            recipes.append(recipe_to_dict(recipe))  # Convert to dict before serialization

    with open(cache_file, 'w') as f:
        json.dump(recipes, f, indent=4)

if __name__ == '__main__':
    recipes_folder = 'app/cookbook'  # Update with the actual path
    cache_file = 'app/cookbook.json'  # Update with the desired cache file path
    cache_recipes(recipes_folder, cache_file)