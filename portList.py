import pandas as pd


df = pd.read_csv('service-names-port-numbers.csv')
df = df['Port Number'].dropna().drop_duplicates()
df=df[df.str.contains('-')==False]
print(df)
ls =[]
for i in df:
    ls.append(int(i))

ls.remove(80)
ls.remove(443)
ls.insert(0,443)
ls.insert(0,80)
print(ls)
print(len(ls))

weights = []
weights.append(12350)
weights.append(12350)
for i in range(6175):
    weights.append(1)
print(weights)
print(len(weights))
weights = tuple(weights)
print(weights)