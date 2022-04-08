#!/usr/bin/python
# coding=utf-8
'''
Date: 2021-06-24 17:56:20
LastEditors: recar
LastEditTime: 2021-06-24 19:07:01
'''
from setuptools import setup
from os import path as os_path
import sys


def is_py3():
	if sys.version > '3':
		return True
	return False
    

this_directory = os_path.abspath(os_path.dirname(__file__))
def read_file(filename):
    if is_py3():
        with open(os_path.join(this_directory, filename),'r', encoding='UTF-8') as f:
            long_description = f.read()
    else:
        with open(os_path.join(this_directory, filename), 'rb') as f:
            long_description = f.read()
    return long_description

setup(name='thread_worker',  
      version='0.1.8',
      author='recar',
      author_email='recar@recar.com',
      long_description=read_file('README.md'),
      long_description_content_type="text/markdown",
      description='thread work',
      url='https://github.com/Ciyfly/thread_work',
      packages=['thread_worker'],
      install_requires=[],
      zip_safe=False)
