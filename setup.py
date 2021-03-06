from setuptools import setup

setup(
    name='aState',
    version='0.7',
    author='James Reed',
    author_email='jdreed1954@hotmail.com',
    description='aState create and modifies A records in public hosted zones.',
    license='GPLv3+',
    packages=['aState'],
    include_package_data=True,
    url='https://github.com/reed54/route53',
    install_requires=[
        'click',
        'boto3'
    ],
    entry_points='''
        [console_scripts]
        aState=aState.aState:cli
    ''',
)
