# import sys
# from datetime import datetime
# print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
# print("脚本名称：",sys.argv[0])
# print("第一个参数：",sys.argv[1])
# print("第二个参数：",sys.argv[2])

# import source
# print(source.hello())
import pandas as pd
import numpy as np
data = {"A": [1, 2, 3], "B": [4, 5, 6]}
df = pd.DataFrame(data)
print(df)