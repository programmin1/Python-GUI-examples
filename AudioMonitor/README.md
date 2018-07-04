
# qt audio monitor

ORIGINAL PROJECT PAGE: http://www.swharden.com/wp/2016-07-31-real-time-audio-monitor-with-pyqt/

This is a minimal-case example how to get continuous PCM data from the sound card. A preliminary SWHEar class is included which can self-detect likely input devices. To manually define an input device, set it when SWHEar() is called. In most cases it will work right out of the box. If you're playing music and no microphone is detected, it will use the sound mapper and graph the audio being played.

**The buttons added allow you to train and detect sounds using simple SVM - may not work well if there is other noise than the target noise. For best results do train this in a quiet environment!**

Youtube demo: https://youtu.be/lDS9rI0o6mM

![demo](demo.gif)
