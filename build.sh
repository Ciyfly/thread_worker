###
 # @Date: 2021-06-24 19:11:10
 # @LastEditors: recar
 # @LastEditTime: 2021-06-24 19:11:36
### 

python3 setup.py sdist bdist_wheel
python3 -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
