from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from app.models import PantryItem
from app.meal_planner import load_all_recipes, load_digital_pantry, load_knowledge_bank, generate_meal_plan, to_purchase_unit, generate_shopping_list, prune_pantry
import json
import os
from datetime import datetime

@app.route('/')
def index():
    # items = PantryItem.query.all()
    items = PantryItem.query.order_by(PantryItem.expiry_date.asc()).all()
    return render_template('index.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = float(request.form.get('quantity'))
        unit = request.form.get('unit')
        non_perishable = request.form.get('non_perishable') == 'on'

        # Create a new PantryItem object
        if non_perishable:
            new_item = PantryItem(name=name, quantity=quantity, unit=unit)  # Expiry date defaults to 'infinity'
        else:
            expiry_str = request.form.get('expiry_date')
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            new_item = PantryItem(name=name, quantity=quantity, unit=unit, expiry_date=expiry_date)

        # Add to the database session and commit
        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_item.html')

@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
def update_item(item_id):
    item = PantryItem.query.get_or_404(item_id)

    if request.method == 'POST':
        new_quantity = float(request.form.get('quantity'))

        if new_quantity <= 0:
            # If the quantity is 0 or less, remove the item
            db.session.delete(item)
        else:
            # Otherwise, update the item details
            item.name = request.form.get('name')
            item.quantity = new_quantity
            item.unit = request.form.get('unit')
            expiry_str = request.form.get('expiry_date')
            if expiry_str and expiry_str != datetime.max:
                item.expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            else:
                item.expiry_date = datetime.max

        # Commit changes to the database
        db.session.commit()

        # Redirect back to the home page
        return redirect(url_for('index'))

    # Render the update_item template if the request is GET
    return render_template('update_item.html', item=item)

@app.route('/remove/<int:item_id>', methods=['POST'])
def remove_item(item_id):
    item = PantryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/recipes')
def show_recipes():
    basedir = os.path.abspath(os.path.dirname(__file__))
    cookbook_path = os.path.join(basedir, 'cookbook.json')
    with open(cookbook_path, 'r') as f:  # Update with the actual path
        cached_recipes = json.load(f)
    return render_template('recipes.html', recipes=cached_recipes)

@app.route('/meal_plans')
def show_meal_plans():
    basedir = os.path.abspath(os.path.dirname(__file__))
    cookbook_path = os.path.join(basedir, 'cookbook.json')
    kb_path = os.path.join(basedir, 'knowledge_bank.json')
    all_recipes = load_all_recipes(cookbook_path)
    digital_pantry = load_digital_pantry(PantryItem.query.all())
    knowledge_bank = load_knowledge_bank(kb_path)

    iteration_limit = 100

    if len(digital_pantry) == 0:
        wastage_weight = 1
        pantry_weight = 0
    else:
        wastage_weight = 0.75
        pantry_weight = 0.25

    meal_plans = []
    for _ in range(5):
        plan, cost, shop_list, new_pantry = generate_meal_plan(all_recipes, 
                                                               digital_pantry, 
                                                               knowledge_bank, 
                                                               iteration_limit, 
                                                               wastage_weight, 
                                                               pantry_weight)
        recipe_names = [recipe['name'] for recipe in plan]
        meal_plans.append({'plan': plan, 'cost': cost, 'recipes': recipe_names, 'shopping_list': shop_list, 'new_pantry': new_pantry})

    now = datetime.now()
    return render_template('meal_plans.html', meal_plans=meal_plans, now=now)


@app.route('/stage_meal_plan', methods=['POST'])
def stage_meal_plan():
    data = request.get_json()
    recipe_names = data.get('recipeNames')

    basedir = os.path.abspath(os.path.dirname(__file__))
    mealplan_path = os.path.join(basedir, 'staged_meal_plan.json')

    if recipe_names:
        # Save the list of recipe names to a file
        data = {'recipes': recipe_names, 'executed': False}
        with open(mealplan_path, 'w') as f:
            json.dump(data, f)

        return jsonify(success=True, message="Meal plan staged successfully.")

    return jsonify(success=False, message="No recipe names provided.")

@app.route('/current_meal_plan')
def current_meal_plan():
    basedir = os.path.abspath(os.path.dirname(__file__))
    cookbook_path = os.path.join(basedir, 'cookbook.json')
    kb_path = os.path.join(basedir, 'knowledge_bank.json')
    all_recipes = load_all_recipes(cookbook_path)
    digital_pantry = load_digital_pantry(PantryItem.query.all())
    knowledge_bank = load_knowledge_bank(kb_path)
    mealplan_path = os.path.join(basedir, 'staged_meal_plan.json')
    try:
        with open(mealplan_path, 'r') as f:
            data = json.load(f)
            recipe_names = set(data.get('recipes'))
            executed = data.get('executed')
        if len(recipe_names) == 0:
            raise FileNotFoundError

        selected_recipes = [recipe for recipe in all_recipes if recipe['name'] in recipe_names]
        if executed:
            shopping_list = None
            new_pantry = None
        else:        
            shopping_list, new_pantry = generate_shopping_list(selected_recipes, digital_pantry, knowledge_bank)
            new_pantry = prune_pantry(new_pantry)
        staged_plan = {'plan': selected_recipes, 'recipes': recipe_names, 'shopping_list': shopping_list, 'new_pantry': new_pantry}
    
    except (FileNotFoundError, json.JSONDecodeError):
        print('No meal plan staged.')
        staged_plan = None  # Handle the case where no plan is staged

    now = datetime.now()
    return render_template('current_meal_plan.html', meal_plan=staged_plan, now=now)

@app.route('/execute_staged_plan', methods=['POST'])
def execute_staged_plan():
    try:
        basedir = os.path.abspath(os.path.dirname(__file__))
        cookbook_path = os.path.join(basedir, 'cookbook.json')
        kb_path = os.path.join(basedir, 'knowledge_bank.json')
        all_recipes = load_all_recipes(cookbook_path)
        digital_pantry = load_digital_pantry(PantryItem.query.all())
        knowledge_bank = load_knowledge_bank(kb_path)
        mealplan_path = os.path.join(basedir, 'staged_meal_plan.json')
        with open(mealplan_path, 'r') as f:
            data = json.load(f)
            recipe_names = set(data.get('recipes'))

        selected_recipes = [recipe for recipe in all_recipes if recipe['name'] in recipe_names]
        # Assuming your generate_shopping_list function returns the new pantry state
        _, new_pantry_state = generate_shopping_list(selected_recipes, digital_pantry, knowledge_bank)
        new_pantry_state = prune_pantry(new_pantry_state)

        # Update the digital pantry in the database
        for name, item in new_pantry_state.items():
            purchase_unit = knowledge_bank[name]['increment']['unit']
            rem_quantity = to_purchase_unit(item['quantity'], purchase_unit)
            pantry_item = PantryItem.query.filter_by(name=name).first()
            if pantry_item:

                pantry_item.quantity = rem_quantity
                pantry_item.unit = purchase_unit
                # Update other fields like expiry_date if necessary
            else:
                # Handle the case where the item doesn't exist (e.g., create a new PantryItem)
                new_item = PantryItem(name=name, quantity=rem_quantity, unit=purchase_unit, expiry_date=item['expiry_date'])
                db.session.add(new_item)

        db.session.commit()

        # Remove or empty the staged_meal_plan.json file to indicate no plan is staged
        data['executed'] = True
        with open(mealplan_path, 'w') as f:
            json.dump(data, f)

        return jsonify(success=True, message="Meal plan executed successfully and pantry updated.")

    except Exception as e:
        return jsonify(success=False, message=str(e))