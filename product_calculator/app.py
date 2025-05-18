from flask import Flask, render_template, request, send_file, session, jsonify
import math
from reportlab.lib.pagesizes import letter
import json

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Secret key for sessions

# Unit conversion rates between units
UNIT_CONVERSION = {
    "kg": {"g": 1000, "kg": 1, "l": 1, "ml": 1000, "pcs": 1},
    "g": {"g": 1, "kg": 0.001, "l": 0.001, "ml": 1, "pcs": 1},
    "l": {"l": 1, "ml": 1000, "kg": 1, "g": 1000, "pcs": 1},
    "ml": {"ml": 1, "l": 0.001, "kg": 0.001, "g": 1, "pcs": 1},
    "pcs": {"pcs": 1, "kg": 1, "g": 1, "l": 1, "ml": 1}
}

SAVED_INGREDIENTS_FILE = "saved_ingredients.json"  # File to save ingredient lists

def convert_unit(value, from_unit, to_unit):
    # Convert 'value' from 'from_unit' to 'to_unit' using conversion table
    if from_unit in UNIT_CONVERSION and to_unit in UNIT_CONVERSION[from_unit]:
        return value * UNIT_CONVERSION[from_unit][to_unit]
    else:
        return None  # Return None if conversion is not possible

def load_saved_ingredients():
    # Load saved ingredient lists from JSON file
    try:
        with open(SAVED_INGREDIENTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # Return empty list if file doesn't exist

def save_ingredients_list(name, ingredients):
    # Add a new ingredient list and save to JSON file
    saved_lists = load_saved_ingredients()
    saved_lists.append({'name': name, 'ingredients': ingredients})
    with open(SAVED_INGREDIENTS_FILE, 'w') as f:
        json.dump(saved_lists, f, indent=4)

def get_ingredients_by_name(name):
    # Retrieve ingredient list by its name
    saved_lists = load_saved_ingredients()
    for item in saved_lists:
        if item['name'] == name:
            return item['ingredients']
    return None  # Return None if not found

def remove_ingredients_list(name):
    # Remove an ingredient list by name and update JSON file
    saved_lists = load_saved_ingredients()
    updated_lists = [item for item in saved_lists if item['name'] != name]
    with open(SAVED_INGREDIENTS_FILE, 'w') as f:
        json.dump(updated_lists, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Read basic product info from form
            product_name = request.form["product_name"].strip()
            selling_price = float(request.form["selling_price"])
            fixed_cost = float(request.form["fixed_cost"])

            # Collect all ingredient-related inputs as lists
            ingredients = []
            names = request.form.getlist("name")
            available_qtys = request.form.getlist("available_qty")
            cost_per_units = request.form.getlist("cost_per_unit")
            required_per_units = request.form.getlist("required_per_unit")
            available_units = request.form.getlist("available_unit")
            required_units = request.form.getlist("required_unit")

            # Process each ingredient and prepare data structure
            for i in range(len(names)):
                name = names[i].strip()
                available_qty = float(available_qtys[i])
                cost_per_unit = float(cost_per_units[i])
                required_per_unit = float(required_per_units[i])
                available_unit = available_units[i].strip()
                required_unit = required_units[i].strip()

                # Validate and convert units if necessary
                if available_unit != required_unit:
                    converted_qty = convert_unit(available_qty, available_unit, required_unit)
                    if converted_qty is None:
                        return "Error: Incompatible units provided."

                ingredients.append({
                    "name": name,
                    "available_qty": available_qty,
                    "cost_per_unit": cost_per_unit,
                    "required_per_unit": required_per_unit,
                    "required_unit": required_unit,
                    "available_unit": available_unit,
                })
            
            # Calculate maximum units producible limited by ingredient availability
            max_units = min(
                (ing["available_qty"] // ing["required_per_unit"] if ing["required_per_unit"] > 0 else float("inf"))
                for ing in ingredients
            )
            max_units = int(max_units)

            ingredient_summaries = []
            raw_total = 0  # Sum of all ingredient costs

            # Summarize ingredient usage and costs based on max production units
            for ing in ingredients:
                converted_required_per_unit = ing["required_per_unit"]
                if ing["required_unit"] != ing["available_unit"]:
                    converted_required_per_unit = convert_unit(
                        ing["required_per_unit"],
                        ing["required_unit"],
                        ing["available_unit"]
                    )
                    if converted_required_per_unit is None:
                        return "Error: Incompatible units provided."
                
                total_used = converted_required_per_unit * max_units
                remaining_qty = ing["available_qty"] - total_used
                total_cost = ing["cost_per_unit"] * total_used  # Cost for the ingredient
                raw_total += total_cost

                ingredient_summaries.append({
                    "name": ing["name"],
                    "required_per_unit": ing["required_per_unit"],
                    "required_unit": ing["required_unit"],
                    "cost_per_unit": ing["cost_per_unit"],
                    "total_used": round(total_used, 2),
                    "total_cost": round(total_cost, 2),
                    "remaining_qty": round(remaining_qty, 2),
                    "available_unit": ing["available_unit"],
                })

            # Calculate total cost including fixed costs
            total_cost_with_fixed = raw_total + fixed_cost
            cost_per_unit = total_cost_with_fixed / max_units if max_units else 0
            revenue = max_units * selling_price
            profit = revenue - total_cost_with_fixed

            # Contribution margin used for break-even calculation
            contribution_margin = selling_price - (total_cost_with_fixed / max_units if max_units else 0)
            break_even_units = math.ceil(fixed_cost / contribution_margin) if contribution_margin > 0 else float("inf")

            # Prepare data for rendering result template
            report_data = {
                'product_name': product_name,
                'max_units': max_units,
                'total_cost': round(total_cost_with_fixed, 2),
                'cost_per_unit': round(cost_per_unit, 2),
                'revenue': round(revenue, 2),
                'profit': round(profit, 2),
                'break_even_units': break_even_units,
                'ingredients': ingredient_summaries,
                'raw_total': round(raw_total, 2),
                'selling_price': selling_price,
                'fixed_cost': fixed_cost
            }
            session['report_data'] = report_data  # Save report in session

            return render_template(
                "result.html",
                **report_data
            )
        except ValueError:
            return "Invalid input detected. Please use numeric values only."
        except Exception as e:
            return f"An error occurred: {e}"

    # For GET, load saved ingredient lists to display on the index page
    saved_ingredient_lists = load_saved_ingredients()
    return render_template("index.html", saved_lists=saved_ingredient_lists)

@app.route('/save_ingredients', methods=['POST'])
def save_ingredients():
    # Save ingredient list sent via JSON POST request
    data = request.get_json()
    name = data.get('name')
    ingredients = data.get('ingredients')
    if name and ingredients:
        save_ingredients_list(name, ingredients)
        return jsonify({'message': 'Ingredients saved successfully!'})
    return jsonify({'error': 'Invalid data'}), 400

@app.route('/get_saved_ingredients')
def get_saved_ingredients():
    # Return all saved ingredient lists as JSON
    saved_lists = load_saved_ingredients()
    return jsonify(saved_lists)

@app.route('/load_ingredients/<name>')
def load_ingredients(name):
    # Load specific saved ingredient list by name
    ingredients = get_ingredients_by_name(name)
    if ingredients:
        return jsonify(ingredients)
    return jsonify({'error': 'List not found'}), 404

@app.route('/remove_ingredients/<name>', methods=['DELETE'])
def remove_ingredients(name):
    # Remove ingredient list by name
    remove_ingredients_list(name)
    return jsonify({'message': 'List removed successfully!'})

if __name__ == "__main__":
    app.run(debug=True)
