import os
import platform
import shutil
import sys

from PyInstaller.__main__ import run

if __name__ == '__main__':
    # The name of the final executable
    executable_name = 'PomodoroTimer'

    # The main Python script
    main_script = 'managed-projects/Pomodoro/pomodoro/main.py'

    # The path to the icon file (optional)
    icon_file = 'managed-projects/Pomodoro/pomodoro/prof.png'

    # The name of the application
    app_name = 'Pomodoro Timer'

    # PyInstaller options
    pyinstaller_options = [
        '--onefile',
        '--windowed',
        f'--name={executable_name}',
    ]

    if platform.system() == 'Windows':
        pyinstaller_options.append(f'--icon={icon_file}')
        pyinstaller_options.append(f'--add-data={os.path.join("managed-projects", "Pomodoro", "pomodoro", "prof.png")};.')
    elif platform.system() == 'Darwin': # macOS
        pyinstaller_options.append(f'--icon={icon_file}')
        pyinstaller_options.append(f'--add-data={os.path.join("managed-projects", "Pomodoro", "pomodoro", "prof.png")}:.')
    else: # Linux
        pyinstaller_options.append(f'--add-data={os.path.join("managed-projects", "Pomodoro", "pomodoro", "prof.png")}:.')


    # Hidden imports that PyInstaller might miss
    hidden_imports = [
        'vlc',
        'yt_dlp',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ]

    for hidden_import in hidden_imports:
        pyinstaller_options.append(f'--hidden-import={hidden_import}')

    # The full command to run PyInstaller
    command = [main_script] + pyinstaller_options

    print(f"Running PyInstaller with command: {' '.join(command)}")

    # Run PyInstaller
    run(command)

    print("\n\n")
    print("="*40)
    print("Build finished!")
    print(f"The executable should be in the 'dist' folder.")
    print("="*40)
