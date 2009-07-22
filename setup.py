#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup


setup(name='jessica',
      version='0.1',
      description='WSGI that interacts with RabbitMQ',
      author='Yoan Blanc',
      author_email='yoan@dosimple.ch',
      license='BSD',
      url='http://github.com/greut/jessica',
      packages=['jessica'],
      install_requires=['amqplib',
                        'txamqp'],
      test_suite='tests',
      tests_require=['mock', 'WebTest'])
