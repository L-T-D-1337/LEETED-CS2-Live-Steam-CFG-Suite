from pathlib import Path
import os,sys,subprocess
os.chdir(Path(__file__).resolve().parent)
for args in [['build.py','out/rebuilt'],['check_inputs.py','out/rebuilt/LEETED_Gesamtansicht.cfg.txt','out/rebuilt/input_tests.json'],['verify.py','out/rebuilt'],['test_combinations.py','out/rebuilt'],['analyze.py','out/rebuilt']]:
 subprocess.run([sys.executable,*args],check=True)
print('Offline rebuild and static checks completed: out/rebuilt')
