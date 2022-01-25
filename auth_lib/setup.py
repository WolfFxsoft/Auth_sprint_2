from setuptools import setup

setup(
    name='auth_lib',
    version='0.0.1',
    description='simple function lib',
    author='Husky',
    author_email='wolf@fxsof.com',
    packages=['auth_lib',],
    install_requires=['requests==2.26.0',
                      'pyjwt==2.3.0']
)
