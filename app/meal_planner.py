import json
import copy
import math
from datetime import datetime, timedelta
import random


from app.models import Ingredient

def standardize_units(name, quantity, unit):
    # assume standard unit is 4 oz == 4 fl oz == 1 unit (of tomato, zucchini, lime, etc.)
    if unit == 'unit':
        return Ingredient(quantity, 'stan', name)
    elif unit == 'oz':
        return Ingredient(quantity/4, 'stan', name)
    elif unit == 'lb':
        return Ingredient(quantity*16/4, 'stan', name)
    elif unit == 'cup':
        return Ingredient(quantity*8/4, 'stan', name)
    elif unit == 'tbsp':
        return Ingredient(quantity/2/4, 'stan', name)
    elif unit == 'tsp':
        return Ingredient(quantity/6/4, 'stan', name)
    elif unit == 'ml':
        return Ingredient(quantity/30/4, 'stan', name)
    elif unit == 'clove':
        return Ingredient(quantity/10, 'stan', name)
    else:
        raise NotImplementedError(f'Unit {unit} for item {name} not converted!')

def to_purchase_unit(quantity, purchase_unit):
    if purchase_unit == 'unit':
        return quantity
    elif purchase_unit == 'oz':
        return quantity*4
    elif purchase_unit == 'lb':
        return quantity*4/16
    elif purchase_unit == 'cup':
        return quantity*4/8
    elif purchase_unit == 'tbsp':
        return quantity*4*2
    elif purchase_unit == 'tsp':
        return quantity*4*6
    elif purchase_unit == 'ml':
        return quantity*4*30
    elif purchase_unit == 'clove':
        return quantity*10
    else:
        raise NotImplementedError(f'Unit {purchase_unit} not converted!')

def load_all_recipes(path):
    with open(path, 'r') as f:
        recipes = json.load(f)
    
    for recipe in recipes:
        ingredients = []
        for item in recipe['ingredients']:
            ingredients.append(standardize_units(item['name'], item['quantity'], item['unit']))
        recipe['ingredients'] = ingredients
    return recipes

def load_digital_pantry(pantry_items):
    # Create a deep copy of the pantry items to manipulate separately from the database
    copied_pantry = {}
    for item in pantry_items:
        ingredient = standardize_units(item.name, item.quantity, item.unit)
        copied_pantry[item.name] = {'quantity': ingredient.quantity, 'unit': ingredient.unit, 'expiry_date': item.expiry_date}
        # copied_pantry.append(PantryItem(item.name, ingredient.quantity, ingredient.unit, item.expiry_date))

    return copied_pantry

def load_knowledge_bank(path):
    with open(path, 'r') as f:
        knowledge_bank = json.load(f)

    return knowledge_bank

def generate_shopping_list(meal_plan, digital_pantry, knowledge_bank):

    # aggregate the ingredients in the meal plan
    ingredients = {}
    for recipe in meal_plan:
        for ingredient in recipe['ingredients']:
            if ingredient.name not in ingredients:
                ingredients[ingredient.name] = ingredient
            else:
                ingredients[ingredient.name] = ingredients[ingredient.name] + ingredient

    # create shopping list and update pantry
    shopping_list = {}
    new_pantry = copy.deepcopy(digital_pantry)
    for name in ingredients:
        if name in digital_pantry:
            purchase_amt = max(0, ingredients[name].quantity-digital_pantry[name]['quantity'])
            new_pantry[name]['quantity'] = max(0, digital_pantry[name]['quantity'] - ingredients[name].quantity)                
        else:
            purchase_amt = ingredients[name].quantity
        
        if purchase_amt > 0:
            increment = knowledge_bank[name]['increment']
            increment_quantity = increment['quantity']
            increment_unit = increment['unit']
            shelf_life = knowledge_bank[name]['shelf_life']

            reqd_amt = to_purchase_unit(purchase_amt, increment_unit)
            purchase_ct = int(math.ceil(round(reqd_amt / increment_quantity, 3)))
            shopping_list[name] = {'count': purchase_ct, 'increment': increment}

            remaining_amt = standardize_units(name, max(0, purchase_ct*increment_quantity - reqd_amt), increment_unit).quantity
            new_pantry[name] = {'quantity': remaining_amt, 'unit': 'stan', 'expiry_date': datetime.now() + timedelta(7*shelf_life)}
    
    return shopping_list, new_pantry

def calculate_wastage_cost(new_pantry):

    # calculate how much food goes to waste in the pantry over the next two weeks
    wastage = 0
    now = datetime.now()
    for name in new_pantry:
        if (new_pantry[name]['expiry_date'] - now).days < 15 and new_pantry[name]['quantity'] > 0:
            wastage += new_pantry[name]['quantity']
    return wastage
        
def calculate_pantry_change_cost(old_pantry, new_pantry):
    initial_mass = 0
    for name in old_pantry:
        initial_mass += old_pantry[name]['quantity']
    
    final_mass = 0
    for name in new_pantry:
        final_mass += new_pantry[name]['quantity']
    
    return (final_mass - initial_mass)

def calculate_cost(digital_pantry, new_pantry, wastage_weight, pantry_change_weight):
    
    wastage_cost = calculate_wastage_cost(new_pantry)
    pantry_change_cost = calculate_pantry_change_cost(digital_pantry, new_pantry)
    total_cost = (wastage_weight * wastage_cost) + (pantry_change_weight * pantry_change_cost)
    return total_cost

def prune_pantry(future_pantry):
    # remove items from future pantry if their quantity is 0
    pruned_pantry = {}
    for name in future_pantry:
        if future_pantry[name]['quantity'] > 0:
            pruned_pantry[name] = future_pantry[name]

    return pruned_pantry

def generate_meal_plan(all_recipes, digital_pantry, knowledge_bank, iterations, wastage_weight, pantry_change_weight, num_meals=6):

    all_recipe_dict = {recipe['name']: recipe for recipe in all_recipes}

    # current_plan = random.sample(all_recipes, num_meals)[:]
    current_plan = random.sample(range(all_recipes), num_meals)[:]
    current_shopping_list, current_pantry = generate_shopping_list([all_recipes[i] for i in current_plan], digital_pantry, knowledge_bank)
    current_cost = calculate_cost(digital_pantry, current_pantry, wastage_weight, pantry_change_weight)

    for _ in range(iterations):
        # the following swap does not allow repeats
        new_plan = current_plan[:]
        idx = random.randint(0, 5)
        all_recipes_copy = set(range(len(all_recipes))).difference(set(new_plan))

        new_plan[idx] = random.choice(list(all_recipes_copy))

        # the following swap allows repeats
        # new_plan = current_plan[:]
        # new_plan[random.randint(0, num_meals-1)] = random.choice(all_recipes)
        new_shopping_list, new_pantry = generate_shopping_list([all_recipes[i] for i in new_plan], digital_pantry, knowledge_bank)

        new_cost = calculate_cost(digital_pantry, new_pantry, wastage_weight, pantry_change_weight)

        # If the new plan has a lower cost, accept the swap
        if new_cost < current_cost:
            current_plan = new_plan
            current_cost = new_cost
            current_shopping_list = new_shopping_list
            current_pantry = new_pantry

    current_pantry = prune_pantry(current_pantry)
    return [all_recipes[i] for i in current_plan], round(current_cost,1), current_shopping_list, current_pantry
