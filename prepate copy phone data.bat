@echo off
adb shell run-as gazetracking.lmu.com.eyetracking_map_webview "rm -r .Fabric;"
adb shell run-as com.google.firebase.codelab.friendlychat "rm -r .Fabric;"
adb shell run-as com.lmu.gazetracking.eyetrackinggallery "rm -r .Fabric;"
adb shell run-as gazetracking.lmu.com.eyetacking_accuracy_testing "rm -r .Fabric;"
