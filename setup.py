from setuptools import setup, find_packages

from is_core import get_version

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
        'django-piston==0.3.3',
        'germanium==0.0.2',
        'django-block-snippets==0.0.2',
    ],
    dependency_links=[
        'https://github.com/matllubos/django-piston/tarball/master#egg=django-piston-0.3.3',
        'https://github.com/matllubos/django-block-snippets/tarball/0.0.2#egg=django-block-snippets-0.0.2',
        'https://github.com/LukasRychtecky/germanium/tarball/0.0.2#egg=germanium-0.0.2',
    ],
    zip_safe=False
)
