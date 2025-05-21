from bs4 import BeautifulSoup
import requests
import pandas as pd      

html = requests.get("https://gravitas.acr.org/ACPortal/Index").text
soup = BeautifulSoup(html, "lxml")

records = []

# iterate over each row
for tr in soup.select("table tr"):
    # grab only the direct <td> children
    tds = tr.find_all("td", recursive=False)
    if len(tds) < 5:
        continue            # skip invalid rows

    scenario_id = tds[1].get_text(strip=True)   # 2nd <td>
    sex         = tds[3].get_text(strip=True)   # 4th <td>
    age         = tds[4].get_text(strip=True)   # 5th <td> RE-CHECK LATER

    if scenario_id:          # skip blank rows?
        records.append({
            "scenario_id": scenario_id,
            "sex": sex,
            "age": age
        })

df = pd.DataFrame(records)

# TEST
#df = pd.DataFrame(records)
#print(df.head())

df_acr = pd.read_csv('acr_scenarios.csv')
df_ssa = df
df_ssa['scenario_id'] = df_ssa['scenario_id'].astype(int)


#main
df_new = df_acr.merge(df_ssa, how='left', on='scenario_id')

#reorder the columns
new_order = ['variant','scenario_id','scenario','age','sex','procedure','adult_rrl','peds_rrl','appropriateness_category']
df_ordered = df_new[new_order]

#save to csv
df_ordered.to_csv('acr_scenarios_complete_ordered.csv',index=False)