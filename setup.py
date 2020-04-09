import os

from setuptools import setup, find_packages

from is_core.version import get_version


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-is-core',
    version=get_version(),
    description="Information systems core.",
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    keywords='django, admin, information systems, REST',
    author='Lubos Matl',
    author_email='matllubos@gmail.com',
    url='https://github.com/matllubos/django-is-core',
    license='BSD',
    package_dir={'is_core': 'is_core'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    install_requires=[
        'django>=2.2',
        'django-pyston~=2.10.0',
        'django-block-snippets==2.0.1',
        'django-chamber~=0.5.12',
        'python-dateutil~=2.8.0',
        'pytz~=2019.2',
        'Unidecode~=1.1.1',
        'python-mimeparse~=1.6.0',
        'django-ipware~=2.1.0',
        'import_string>=0.1.0',
    ],
    zip_safe=False
)
