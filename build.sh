###
 # @Date: 2021-06-24 19:11:10
 # @LastEditors: recar
 # @LastEditTime: 2021-06-24 19:11:36
### 

python setup.py sdist bdist_wheel
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
