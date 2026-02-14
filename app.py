import os
import runpy

for candidate in ["ScoardBoard1.py", "Scoardboard1.py"]:
    if os.path.exists(candidate):
        runpy.run_path(candidate, run_name="__main__")
        break
else:
    raise FileNotFoundError("No se encontro el archivo principal del scoreboard.")
