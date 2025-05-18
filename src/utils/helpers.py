import json

UNIT_CONVERSION = {
    "kg": {"g": 1000, "kg": 1, "l": 1, "ml": 1000, "pcs": 1},
    "g": {"g": 1, "kg": 0.001, "l": 0.001, "ml": 1, "pcs": 1},
    "l": {"l": 1, "ml": 1000, "kg": 1, "g": 1000, "pcs": 1},
    "ml": {"ml": 1, "l": 0.001, "kg": 0.001, "g": 1, "pcs": 1},
    "pcs": {"pcs": 1, "kg": 1, "g": 1, "l": 1, "ml": 1}
}

SAVED_INGREDIENTS_FILE = "saved_ingredients.json"

def convert_unit(value, from_unit, to_unit):
    try:
        return value * UNIT_CONVERSION[from_unit][to_unit]
    except KeyError:
        return None

def is_valid_number(value):
    try:
        return float(value) >= 0
    except ValueError:
        return False

def load_saved_ingredients():
    try:
        with open(SAVED_INGREDIENTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_ingredients_list(name, ingredients):
    saved = load_saved_ingredients()
    saved.append({'name': name, 'ingredients': ingredients})
    with open(SAVED_INGREDIENTS_FILE, 'w') as f:
        json.dump(saved, f, indent=4)

def get_ingredients_by_name(name):
    for item in load_saved_ingredients():
        if item['name'] == name:
            return item['ingredients']
    return None

def remove_ingredients_list(name):
    lists = [i for i in load_saved_ingredients() if i['name'] != name]
    with open(SAVED_INGREDIENTS_FILE, 'w') as f:
        json.dump(lists, f, indent=4)
