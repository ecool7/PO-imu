## Сборка приложения для macOS

Требования: macOS (желательно той же версии или ниже, чем у друга), Xcode Command Line Tools, Python 3.9+.

### Вариант A: .app бандл (рекомендуется для отправки)
```bash
chmod +x build-mac-app.sh
./build-mac-app.sh
```
Получите `dist/IMU_Monitor.app`.

Упаковка в zip для отправки:
```bash
ditto -c -k --sequesterRsrc --keepParent dist/IMU_Monitor.app IMU_Monitor-mac.zip
```

Друг распакует и запустит `IMU_Monitor.app`. Если macOS блокирует запуск (Gatekeeper):
- Клик правой кнопкой → Открыть → Открыть
- Или: Системные настройки → Конфиденциальность и безопасность → Разрешить запуск

Подписывание/нотаризация (необязательно, снижает блокировки):
- Требуются Apple Developer ID, сертификаты. Внутри `.app` можно выполнить `codesign --deep --force --sign "Developer ID Application: ..." dist/IMU_Monitor.app` и затем нотацию через `notarytool`.

### Вариант B: Один файл (onefile)
```bash
chmod +x build-mac-onefile.sh
./build-mac-onefile.sh
```
Исполняемый файл: `dist/IMU_Monitor`. Может блокироваться Gatekeeper и запускаться дольше.

### Заметки
- Сборите на версии macOS, не выше версии у друга (обратная совместимость ограничена).
- Для PyQt5 требуется наличие Qt библиотек внутри бандла — PyInstaller включает их автоматически.
- Если приложение не стартует, проверьте логи через `Console.app` или запустите `open dist/IMU_Monitor.app --args --verbose`.

