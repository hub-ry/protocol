from fastapi import FastAPI
from pydantic import BaseModel
import json
import os

app = FastAPI()

class WeightEntry(BaseModel):
  weight: int

weight_log = "./data/weight.json"

@app.post("/add_weight")
async def add_weight(entry: WeightEntry):

  weight = entry.weight
  if os.path.exists(weight_log):
    with open(weight_log, "r") as f:
      data = json.load(f)

  else:
    data = []

  data.append(weight)

  with open(weight_log, "w") as f:
    json.dump(data, f)


  return {"status": "success", "updated_weight": weight}