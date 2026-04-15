from setuptools import setup, find_packages

setup(
    name='ariel',
    version='1.0.0',
    description='Live Mermaid diagram viewer',
    py_modules=['ariel'],
    package_data={'': ['templates/*.html']},
    data_files=[('templates', ['templates/index.html'])],
    include_package_data=True,
    install_requires=[
        'Flask>=2.3.0',
        'Werkzeug>=2.3.0',
    ],
    entry_points={
        'console_scripts': [
            'ariel=ariel:main',
        ],
    },
    python_requires='>=3.9',
)
