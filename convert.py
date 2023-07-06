
import pandas as pd 

# convert data/walmart.json to csv using pandas
df = pd.read_json("data/walmart.json")
df.to_csv("data/walmart.csv", index=False)
