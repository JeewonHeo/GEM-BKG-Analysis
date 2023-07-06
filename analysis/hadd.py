import os
import sys


path = sys.argv[-1]

for i in os.listdir(path):
    try:
        run = int(i)
        command = f"hadd {path}/out_{run}.root {path}/{run}/*.root"
        print(command)
        os.system(command)
    except:
        print(f"{i} is not path")


# os.system(f"hadd {path}/out_359691.root {path}/359691/*.root")
# os.system(f"hadd {path}/out_359693.root {path}/359693/*.root")
# os.system(f"hadd {path}/out_359694.root {path}/359694/*.root")
