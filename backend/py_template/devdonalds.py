from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}

# helper function to clear cookbook
@app.route('/clear', methods=['POST'])
def clear():
    cookbook.clear()
    return 'cleared', 200

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	recipeName = re.sub('[-_]', ' ', recipeName)
	recipeName = re.sub(' +', ' ', recipeName)
	recipeName = re.sub('[^a-zA-Z ]', '', recipeName)
	recipeName = ' '.join(word.capitalize() for word in recipeName.split())
	if len(recipeName) <= 0:
		return None
	return recipeName


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	recipe_name = data['name']
	recipe_type = data['type']

	if recipe_name in cookbook:
		return 'entry name is not unique', 400

	if recipe_type == 'recipe':
		seen = set()

		for item in data['requiredItems']:
			if item['name'] in seen:
				return 'requiredItems can only have one element per name', 400
			seen.add(item['name'])
        
		cookbook[recipe_name] = {
            'type': 'recipe',
            'name': recipe_name,
            'requiredItems': data['requiredItems']
        }
	elif recipe_type == 'ingredient':
		if data['cookTime'] < 0:
			return 'cookTime must be greater or equal to 0', 400
	
		cookbook[recipe_name] = {
            'type': 'ingredient',
            'name': recipe_name,
            'cookTime': data['cookTime']
        }
	else:
		return 'entry type must be either "recipe" or "ingredient"', 400

	return '', 200


# [TASK 3] ====================================================================
# Helper function to recursively get ingredients
def get_ingredients(recipe, required_items, mult):
	for item in required_items:
		if item['name'] not in cookbook:
			return 'ingredient not in cookbook', 400
		
		if cookbook[item['name']]['type'] == 'recipe':
			msg, status = get_ingredients(recipe, cookbook[item['name']]['requiredItems'], mult * item['quantity'])
			if status != 200:
				return msg, status
		else:
			recipe['cookTime'] += cookbook[item['name']]['cookTime'] * item['quantity'] * mult
			recipe['ingredients'][item['name']] = recipe['ingredients'].get(item['name'], 0) + item['quantity'] * mult

	return None, 200

# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	recipe_name = request.args.get('name')

	if recipe_name not in cookbook:
		return 'recipe not found', 400
	if cookbook[recipe_name]['type'] != 'recipe':
		return 'name is not a recipe name', 400
	
	recipe =  {
		'name': recipe_name,
		'cookTime': 0,
		'ingredients': {}
	}

	msg, status = get_ingredients(recipe, cookbook[recipe_name]['requiredItems'], 1)
	if status != 200:
		return msg, status
	recipe['ingredients'] = [
		{
			'name': name,
			'quantity': quantity
		}
		for name, quantity in recipe['ingredients'].items()
	]

	return jsonify(recipe), 200


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
