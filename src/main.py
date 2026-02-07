from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import json
import os

app = FastAPI()

class WeightEntry(BaseModel):
  weight: float
  date: str | None = None


weight_log = "./data/weight.json"

@app.post("/add_weight")
async def add_weight(entry: WeightEntry):

  # 99% of my entries with be automatic, entry.date is in case of uploading past weights
  date = entry.date or datetime.now().strftime("%Y-%m-%d")

  weight = entry.weight
  if os.path.exists(weight_log):
    with open(weight_log, "r") as f:
      data = json.load(f)

  else:
    data = []

  data.append({"weight": weight, "date":date})

  with open(weight_log, "w") as f:
    json.dump(data, f)


  return {"status": "success", "updated_weight": weight}
