from flask import Flask, render_template, request
import math

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            product_name = request.form["product_name"].strip()
            selling_price = float(request.form["selling_price"])
            fixed_cost = float(request.form["fixed_cost"])

            ingredients = []
            names = request.form.getlist("name")
            available_qtys = request.form.getlist("available_qty")
            cost_per_units = request.form.getlist("cost_per_unit")
            required_per_units = request.form.getlist("required_per_unit")

            for i in range(len(names)):
                name = names[i].strip()
                available_qty = float(available_qtys[i])
                cost_per_unit = float(cost_per_units[i])
                required_per_unit = float(required_per_units[i])
                ingredients.append({
                    "name": name,
                    "available_qty": available_qty,
                    "cost_per_unit": cost_per_unit,
                    "required_per_unit": required_per_unit,
                })

            max_units = min(
                (ing["available_qty"] // ing["required_per_unit"] if ing["required_per_unit"] > 0 else float("inf"))
                for ing in ingredients
            )
            max_units = int(max_units)

            ingredient_summaries = []
            raw_total = 0

            for ing in ingredients:
                total_used = ing["required_per_unit"] * max_units
                remaining_qty = ing["available_qty"] - total_used
                total_cost = ing["cost_per_unit"] * total_used
                raw_total += total_cost
                ingredient_summaries.append({
                    "name": ing["name"],
                    "required_per_unit": ing["required_per_unit"],
                    "total_used": round(total_used, 2),
                    "total_cost": round(total_cost, 2),
                    "remaining_qty": round(remaining_qty, 2)
                })

            cost_per_unit = raw_total / max_units if max_units else 0
            revenue = max_units * selling_price
            profit = revenue - raw_total
            contribution_margin = selling_price - cost_per_unit
            break_even_units = math.ceil(fixed_cost / contribution_margin) if contribution_margin > 0 else float("inf")

            return render_template(
                "result.html",
                product_name=product_name,
                max_units=max_units,
                total_cost=raw_total,
                cost_per_unit=cost_per_unit,
                revenue=revenue,
                profit=profit,
                break_even_units=break_even_units,
                ingredients=ingredient_summaries,
                raw_total=round(raw_total, 2)
            )
        except Exception as e:
            return "Invalid input detected. Please use numeric values only."

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=False)
