# ExifEdit

ExifEdit is a Python-based app that allows you to browse your computer directory, select images, and modify the filename and "Date taken" EXIF field. This app is useful for giving images from different cameras a similar filename format that contains information such as the date taken, camera maker and model, and portions of the original filename.

The app uses the following dependencies:
* PySide6
* Pillow
* exif
* Send2Trash
* PyInstaller (optional)

## Installation

1. Clone the repository\
`git clone https://github.com/artjvl/ExifEdit.git`
2. Install the required libraries\
`pip3 install -r requirements.txt`
3. Optionally, install PyInstaller\
`pip3 install pyinstaller`
4. Run the app\
`python3 main.py`

Note: If you want to create a one-file executable, use PyInstaller with\
`pyinstaller --onefile --noconsole main.py`

This will create a single executable file `dist/main.exe`, which can be run on any computer without the need to install Python or any libraries.

## Usage
1. Launch the app by running python `main.py` (or run the executable `main.exe`).
2. Browse your computer's file directory using the file explorer on the left panel.
3. Select one or more images from the selected directory in the center panel.
4. Define a filename format in terms of placeholders for various EXIF elements and/or portions of the original filename.\
Example: original filename "DSC0137" with format `[YYYY][MM][DD]-[hh][mm][ss]_[MAK]-[MOD]_[FRMI:DSC]` results in filename "20230422-231542_SONY-ILCE-7C_DSC0137.JPG".
5. Change the "Date taken" EXIF field relative to the original date/time or to a specific date/time.
6. Click "Modify files" to modify the selected files with the new "Date taken" and filename.


## Contributing
If you'd like to contribute to this project, please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License.