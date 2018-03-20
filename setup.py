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
    license='BSD',
    package_dir={'is_core': 'is_core'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 2 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    install_requires=[
        'django>=1.10',
        'django-class-based-auth-views==0.5druids',
        'django-pyston>=2.8.0',
        'django-block-snippets==1.0.2',
        'django-chamber>=0.4.0',
        'python-dateutil>=2.2',
        'pytz',
        'Unidecode>=0.04.16',
        'python-mimeparse==0.1.4',
        'django-ipware>=1.0.0'
    ],
    dependency_links=[
        'https://github.com/druids/django-block-snippets/tarball/1.0.2#egg=django-block-snippets-1.0.2',
        'https://github.com/druids/django-class-based-auth-views/tarball/0.5#egg=django-class-based-auth-views-0.5druids',
    ],
    zip_safe=False
)
