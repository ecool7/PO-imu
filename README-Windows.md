## Сборка .exe на Windows

### 1) Подготовка
- Установите Python 3.9+ для Windows (с добавлением в PATH).
- Склонируйте/скопируйте проект на Windows-машину.

### 2) Быстрая сборка (скрипт)
1. Откройте PowerShell/Командную строку в корне проекта
2. Запустите:
   ```bat
   build-win.bat
   ```
3. Готовый файл: `dist/IMU_Monitor/IMU_Monitor.exe`

### 2.1) Onefile (один .exe)
Запускает приложение из одного файла .exe (дольше стартует, возможны ложные срабатывания антивируса):
```bat
build-win-onefile.bat
```
Готовый файл: `dist/IMU_Monitor.exe`

### 3) Ручная сборка (альтернатива)
```bat
py -3 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-win.txt
pyinstaller --noconfirm --clean ^
  --name IMU_Monitor ^
  --windowed ^
  --add-data "venv/Lib/site-packages/PyQt5/Qt5/bin/;PyQt5/Qt5/bin/" ^
  --add-data "venv/Lib/site-packages/PyQt5/Qt5/plugins/platforms/;PyQt5/Qt5/plugins/platforms/" ^
  --add-data "venv/Lib/site-packages/PyQt5/Qt5/plugins/styles/;PyQt5/Qt5/plugins/styles/" ^
  main.py
```

### 4) Примечания
- Если при запуске `.exe` нет окна — убедитесь, что рядом с `.exe` в папке есть каталоги `platforms`, `styles` и `Qt5` бинарники. Скрипт добавляет их автоматически.
- Антивирус может задерживать старт — добавьте исключение.
- Для отладки можно убрать `--windowed`, чтобы видеть консоль.
- Если шрифты/плагины не подхватываются, добавьте соответствующие папки через `--add-data` аналогично.
 - Для onefile на чистых системах может понадобиться Microsoft VC++ Redistributable.


