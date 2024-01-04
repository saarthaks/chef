from app import db
from datetime import datetime

class PantryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50))
    expiry_date = db.Column(db.DateTime, default=datetime.max)

    def __init__(self, name, quantity, unit, expiry_date=datetime.max):
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.expiry_date = expiry_date
    
    def __repr__(self):
        return f"<PantryItem {self.name}>"

class Ingredient:
    def __init__(self, quantity, unit, name):
        self.quantity = quantity
        self.unit = unit
        self.name = name

    def __add__(self, other):
        if other.unit == self.unit:
            return Ingredient(self.quantity + other.quantity, self.unit, self.name)
    
    def __radd__(self, other):
        if other.unit == self.unit:
            return Ingredient(self.quantity + other.quantity, self.unit, self.name)
    
    def __repr__(self):
        return f"<Ingredient {self.name} - {self.quantity} {self.unit}>"

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