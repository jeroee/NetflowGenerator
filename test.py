from pyspark import SparkContext, SparkConf, SparkFiles
from pyspark.sql import Row, SQLContext
import numpy as np

conf = SparkConf().setAppName("trying").setMaster("local[*]")
sc = SparkContext(conf=conf)
sqlContext = SQLContext(sc)

columns=['name','age','cca','weight']
name=['tom','alan','david','simon']
age=[9,3,2,14]
cca=['basketball','soccer','hockey','badminton']
weight=[30,40,50,60]

matrix1 = np.array([name,age,cca,weight])
print(matrix1)
matrix2 = matrix1.transpose()
print(matrix2)

rdd = sc.parallelize(matrix2)
rdd = rdd.map(lambda x: Row(
    name = str(x[0]),
    age = int(x[1]),
    cca = str(x[2]),
    weight= int(x[3]))
)

df = sqlContext.createDataFrame(rdd)
df.show()
df.printSchema()
df=df.select('name','age','weight','cca')
df.show()