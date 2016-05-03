from setuptools import setup, find_packages

from is_core.version import get_version

setup(
    name='django-is-core',
    version=get_version(),
    description="Information systems core.",
    keywords='django, admin, information systems, REST',
    author='Lubos Matl',
    author_email='matllubos@gmail.com',
    url='https://github.com/matllubos/django-is-core',
    license='LGPL',
    package_dir={'is_core': 'is_core'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 6 - Beta',
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
        'django>=1.8',
        'django-class-based-auth-views>=0.3',
        'django-block-snippets==0.1.1',
        'python-dateutil>=2.2',
        'pytz',
        'django-apptemplates>=1.1',
        'factory-boy>=2.5.2',
        'django-piston==django19-compatibility',
    ],
    dependency_links=[
        'https://github.com/lukasrychtecky/django-piston/tarball/django19-compatibility#egg=django-piston-django19-compatibility',
        'https://github.com/matllubos/django-chamber/tarball/0.1.11#egg=django-chamber-0.1.11',
        'https://github.com/matllubos/django-block-snippets/tarball/0.1.1#egg=django-block-snippets-0.1.1',
        'https://github.com/matllubos/django-project-info/tarball/0.2.5#egg=django-project-info-0.2.5',
    ],
    zip_safe=False
)
