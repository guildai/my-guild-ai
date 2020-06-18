import setuptools

setuptools.setup(
    name="myguild",
    version="0.0.0",
    author="Guild AI",
    author_email="contact@guild.ai",
    description="Utility for my.guild.ai",
    packages=["myguild"],
    install_requires = [
        "pydiscourse",
        "pyyaml",
        "requests",
        "six",
    ],
    dependency_links = [
        "https://github.com/gar1t/pydiscourse/tarball/master#egg=pydiscourse",
    ],
    entry_points={
        "console_scripts": [
            "my-guild = myguild.__main__:main"
        ]
    }
)
