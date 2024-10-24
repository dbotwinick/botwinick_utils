# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD
import setuptools

with open("README.md", 'r') as f:
    readme_txt = f.read()

setuptools.setup(
    name="botwinick_utils",
    version="0.0.14",
    author="Drew Botwinick",
    author_email="foss@drewbotwinick.com",
    description="Assorted Utilities and platform code",
    long_description=readme_txt,
    long_description_content_type="text/markdown",
    url="https://github.com/dbotwinick/botwinick_utils",
    packages=setuptools.find_packages(),
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
