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
        'django>=1.6',
        'django-class-based-auth-views>=0.3',
        'django-piston==1.2.0',
        'germanium>=0.2.7',
        'django-block-snippets==0.1.0',
        'django-chamber>=0.1.1',
        'python-dateutil>=2.2',
        'pytz',
        'django-apptemplates',
        'Unidecode>=0.04.17',
        'factory-boy>=2.5.2',
        'django-project-info==0.2.4',
        'sorl-thumbnail==12.2',
        'pillow==2.8.1'
    ],
    dependency_links=[
        'https://github.com/matllubos/django-piston/tarball/1.2.0#egg=django-piston-1.2.0',
        'https://github.com/matllubos/django-chamber/tarball/0.1.1#egg=django-chamber-0.1.1',
        'https://github.com/matllubos/django-block-snippets/tarball/0.1.0#egg=django-block-snippets-0.1.0',
        'https://github.com/LukasRychtecky/germanium/tarball/0.2.7#egg=germanium-0.2.7',
        'https://github.com/lukasrychtecky/django-project-info/tarball/0.2.4#egg=django-project-info-0.2.4'
    ],
    zip_safe=False
)
