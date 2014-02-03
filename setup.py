from setuptools import setup, find_packages

from is_core import get_version

setup(
    name='django-is-core',
    version=get_version(),
    description="Information systems core.",
    keywords='django, admin, infromation systems, REST',
    author='Lubos Matl',
    author_email='matllubos@gmail.com',
    url='https://github.com/matllubos/django-is-core',
    license='LGPL',
    package_dir={'is_core': 'is_core'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU LESSER GENERAL PUBLIC LICENSE (LGPL)',
        'Natural Language :: Czech',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=[
        'django==1.6',
        'django-class-based-auth-views==0.2'
    ],
    zip_safe=False
)