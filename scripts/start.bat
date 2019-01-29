@echo off
adb kill-server
adb start-server

set /p PARTICIPANT="Please enter the participants id: "
set /p TASK="Please enter the current task name (map, chat, gallery or accuracy): "

copy Nul log.txt
set CDATE=%date:~-4%-%date:~3,2%-%date:~0,2%
echo %CDATE% %TIME%: Eyetacking started  >> log.txt
adb push ./log.txt /sdcard || set errorFlag=error

IF "%TASK%"=="map" (
  set PACKAGE=gazetracking.lmu.com.eyetracking_map_webview
)

IF "%TASK%"=="chat" (
  set PACKAGE=com.google.firebase.codelab.friendlychat
)

IF "%TASK%"=="gallery" (
  set PACKAGE=com.lmu.gazetracking.eyetrackinggallery
)

IF "%TASK%"=="accuracy" (
  set PACKAGE=gazetracking.lmu.com.eyetacking_accuracy_testing
)

adb shell run-as %PACKAGE% "mkdir ./files/%PARTICIPANT%_%CDATE%" || set errorFlag=error
adb shell run-as %PACKAGE% "mv /sdcard/log.txt ./files/%PARTICIPANT%_%CDATE%" || echo can't connect to devices

del log.txt
cd \Users\biometrics\Desktop\eyetracking-smartphone-mapping-master
start python eyetracking.py %PARTICIPANT%
