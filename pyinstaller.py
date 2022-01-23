import PyInstaller.__main__

PyInstaller.__main__.run(
    [
        "awsdsc/main.py",
        "--onefile",
        "--name",
        "awsdsc",
        "--clean",
    ]
)
