@echo off
adb shell "mkdir /sdcard/phoneData"

adb shell run-as gazetracking.lmu.com.eyetracking_map_webview "rm -r files/.Fabric;"
adb shell run-as com.google.firebase.codelab.friendlychat "rm -r files/.Fabric;"
adb shell run-as com.lmu.gazetracking.eyetrackinggallery "rm -r files/.Fabric;"
adb shell run-as gazetracking.lmu.com.eyetacking_accuracy_testing "rm -r files/.Fabric;"

adb shell run-as gazetracking.lmu.com.eyetracking_map_webview "cp -r ./files /sdcard/phoneData/map"
adb shell run-as com.google.firebase.codelab.friendlychat "cp -r ./files /sdcard/phoneData/chat"
adb shell run-as com.lmu.gazetracking.eyetrackinggallery "cp -r ./files /sdcard/phoneData/gallery"
adb shell run-as gazetracking.lmu.com.eyetacking_accuracy_testing "cp -r ./files /sdcard/phoneData/accuracy"

adb pull /sdcard/phoneData
adb -d shell "rm -r /sdcard/phoneData"

pause
