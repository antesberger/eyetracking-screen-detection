# eyetracking-smartphone-mapping
This is a tool to map eye tracking data optained with the Tobii Pro Glasses 2 to a mobile screen. The screen is recognised by four markers each fixed to one of the screen's corners. Output is a video just containing the phone's screen and coordinates relative to it.

### Examples
* study setup: https://youtu.be/G8e6BhmDbmE
* source video recorded with the Tobii Eyetracker: https://youtu.be/Faa2i5FKkCA
* application in android app: https://youtu.be/LDF4DCDZavQ
* visualizing accuracy: https://youtu.be/pgOZUwNd2pg

### Aruco Marker Positioning
The markers to be used are located in the /markers directory. Currently the tracking file is configured to look for the markers with id=0, id=1 and id=3.

### Calibration
Before starting the data collection it is suggested to run the calibration script. This removes any distortions introduced by the camera of the Eye Tracker. Copy and paste the results into the processing.py script. Plese overwrite the contents of the three variables ```self.dist```, ```self.cameraMatrix```, and ```self.mtx``` with your own contents.

### Usage
The /scripts directory contains two start scripts one for windows and one for the mac. When running one of them you will be asked to provide a particiapant name and a task. This referrs to a specific study run with this toolkit but also serves as an example on how to integrate this project into a data collection workflow.

### Postprocessing
In this directory you will find some script to merge, clean and process the obtained data.
* gazePointVideo.py: Draw the gazePoint into a processed video. See above for an example.
* galleryMapper: To be used with the gallery app (https://github.com/antesberger/eyetracking-gallery-task). Attaches the filename corresponding the the gaze points target image to an output csv file

## Install dependencies
* python version 2.7
* ```pip install opencv_python```
* ```pip install opencv-contrib-python```
* ```pip install pip setuptools```
* ```pip install tobii_research```
