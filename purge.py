
import pandas as pd 

# convert data/walmart.json to csv using pandas
df = pd.read_json("data/walmart.json")

# only keep label column
df = df[['label']]
# remove , and terminating space from label
df['label'] = df['label'].str.strip()
# remove last character if it is a comma
df['label'] = df['label'].str.rstrip(',')
df['label'] = df['label'].str.replace(r'(Select for details|Rollback|Save|save).*|\$\d+(\.\d+)?', '', regex=True)
df['label'] = df['label'].str.replace(r', , \.|, \.|, $|, ,  . $', '', regex=True)
df['label'] = df['label'].str.replace(r', , lb\. \.$', '', regex=True)
df['label'] = df['label'].str.replace(r', , lb\. \.$|, \d+ for  or \d+(\.\d+)? each \.$', '', regex=True)
df['label'] = df['label'].str.replace(r', \d+ for  or \d+(\.\d+)? each \.$', '', regex=True)
df.to_csv("data/walmart_partial.csv", index=False)
