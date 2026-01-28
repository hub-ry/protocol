import pandas as pd
import matplotlib.pyplot as plt
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

def create_graph():
    # 1. Load the data
    if not os.path.exists(DATA_FILE):
        print("No data.json found. Go log some weight first!")
        return

    # 2. Read JSON into a DataFrame
    df = pd.read_json(DATA_FILE)

    if df.empty:
        print("The JSON file is empty.")
        return


    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    plt.style.use('seaborn-v0_8') # Makes it look a bit cleaner
    plt.figure(figsize=(10, 6))

    plt.plot(df['timestamp'], df['weight'], marker='o', linestyle='-', color='#2ca02c', linewidth=2)


    # 5. Labeling
    plt.title('Weight Progress', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Weight', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)


    plt.gcf().autofmt_xdate()

    plt.show()

    if __name__ == "__main__":
        create_graph()
