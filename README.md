# Pomodoro Timer Pro

This is a professional Pomodoro timer with YouTube audio and video integration.

## Features

- Customizable work and break intervals
- YouTube audio and video playback
- Modern GUI interface
- VLC media player integration
- Persistent configuration settings

## Installation

1.  **Install Python:** Make sure you have Python 3.10 or newer installed.
2.  **Install VLC:** Install the latest version of VLC media player. Make sure to install the version that matches your system architecture (64-bit or 32-bit).
3.  **Clone the repository:**
    ```
    git clone https://github.com/Z124415-JACK-TAYLOR-GORMAN/pomodoro-timer-pro.git
    cd pomodoro-timer-pro
    ```
4.  **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```

## Usage

To run the application, execute the following command:

```
python pomodoro/main.py
```

## Building from Source

You can build the application into a single executable file for your operating system.

### Windows

1.  **Set up your Windows environment:**
    *   Install Python for Windows from the official website.
    *   Install VLC for Windows. Make sure you install the 64-bit version if you are using 64-bit Python.
    *   Open a command prompt (`cmd` or `powershell`).
    *   Clone your project to your Windows machine if you haven't already.
    *   Navigate to the project directory: `cd path\to\your\project`

2.  **Install the dependencies:**
    *   Install the required Python packages using pip:
        ```
        pip install -r requirements.txt
        ```

3.  **Run the build script:**
    *   Execute the `build.py` script:
        ```
        python build.py
        ```

4.  **Find the executable:**
    *   After the build process is complete, you will find the executable file in the `dist` folder within your project directory. It should be named `PomodoroTimer.exe`.

### macOS

1.  **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```
2.  **Run the build script:**
    ```
    python build.py
    ```
3.  The executable will be in the `dist` folder.

### Linux

1.  **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```
2.  **Run the build script:**
    ```
    python build.py
    ```
3.  The executable will be in the `dist` folder.