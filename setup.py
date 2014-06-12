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
        'django>=1.6',
        'django-class-based-auth-views>=0.2',
        'django-piston==0.4.2',
        'germanium==0.1.3',
        'django-block-snippets==0.0.9',
        'python-dateutil>=2.2',
        'pytz',
        'django-apptemplates',
        'Unidecode>=0.04.16',
        'factory-boy>=2.3.1',
        'django-project-info==0.2.4',
    ],
    dependency_links=[
        'https://github.com/matllubos/django-piston/tarball/0.4.2#egg=django-piston-0.4.2',
        'https://github.com/matllubos/django-block-snippets/tarball/0.0.9#egg=django-block-snippets-0.0.9',
        'https://github.com/LukasRychtecky/germanium/tarball/0.1.3#egg=germanium-0.1.3',
        'https://github.com/lukasrychtecky/django-project-info/tarball/0.2.4#egg=django-project-info-0.2.4'
    ],
    zip_safe=False
)
