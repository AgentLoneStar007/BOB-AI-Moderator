# Imports
import os

with open('requirements.txt', 'a+') as requirements:
    fileContents = requirements.read()
    packages = input('Enter package name(s), comma-separated: ')
    packages = packages.strip()
    packages = packages.split(',')
    if fileContents[:-1] != '\n':
        requirements.write('\n')
    for x in packages:
        os.system(f'pip install {x}')
        requirements.write(f'{x}\n')
    requirements.close()
