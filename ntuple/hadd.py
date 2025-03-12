import os
import sys


path = sys.argv[-1]

fill_lst = [
"fill_10190",
"fill_10226",
"fill_8220",
"fill_8456",
"fill_8754",
"fill_9573",
"fill_9606",
"fill_9877",
]
fill_lst = ['fill_9606']
for fill in fill_lst:
    path = f"results/{fill}"
    for i in os.listdir(path):
        try:
            run = int(i)
            command = f"hadd {path}/out_{run}.root {path}/{run}/*.root"
            print(command)
            os.system(command)
        except:
            print(f"{i} is not a path")
