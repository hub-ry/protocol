import io
from flask import Flask, request, jsonify
from datetime  import datetime, timezone
import json
import os
import pandas as pd
import matplotlib
# This line is CRITICAL: It tells Linux not to look for a monitor
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
# Create the Flask web server
app = Flask(__name__)

# File where all weight data is stored
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# Health check endpoint (just to see if server is running)
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "server running"})


# Endpoint to add a new weight entry
@app.route("/add_weight", methods=["POST"])
def add_weight():
    # Read JSON data sent in the request body
    data = request.get_json()

    # Make sure a weight was provided
    if data is None or "weight" not in data:
        return jsonify({"error": "No weight provided"}), 400

    # Create a new weight entry
    weight_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "weight": data["weight"]
    }

    # Load existing data if the file exists
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            all_data = json.load(f)
    else:
        all_data = []

    # Add the new entry
    all_data.append(weight_entry)

    # Save updated data back to the file
    with open(DATA_FILE, "w") as f:
        json.dump(all_data, f, indent=2)

    # Send confirmation back to the client
    return jsonify({"status": "ok", "entry": weight_entry})
# Endpoint to get all stored weight entries
@app.route("/get_weights", methods=["GET"])
def get_weights():
    # If no data file exists yet, return empty list
    if not os.path.exists(DATA_FILE):
        return jsonify({"weights": []})

# Load existing data if the file exists and isn't empty
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        try:
            with open(DATA_FILE, "r") as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            all_data = [] # If file is corrupted, start fresh
    else:
        all_data = []


@app.route("/graph")
def graph():
    if not os.path.exists(DATA_FILE):
        return "No data yet", 404

    # 1. Load data
    df = pd.read_json(DATA_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # 2. Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['weight'], marker='o', linestyle='-', color='#2ca02c')
    plt.title("Weight Tracker Progress")
    plt.grid(True, alpha=0.3)
    plt.gcf().autofmt_xdate()

    # 3. Save to a buffer (RAM) instead of a file
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close() # Keep memory clean

    return send_file(img, mimetype='image/png')
# Start the server (accessible via Tailscale)
if __name__ == "__main__":
    app.run(host="100.89.197.38", port=5002)
