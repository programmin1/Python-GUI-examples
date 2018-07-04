from __future__ import division
import os
from PyQt4 import QtGui,QtCore
from sklearn.externals import joblib
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range=(0,1))


import sys
import ui_main
import numpy as np
import pyqtgraph
import SWHear
import time
from PyQt4.QtCore import QObject, SIGNAL

class DetectionClass():
    def __init__(self, fname):
        """
        Class to load detector and function to run on a specific detection svm.
        """
        self.detector = joblib.load(fname)
        self.importmodule = __import__(fname.replace('.svm','')) #.py
        #Instantiate one class Runner in the file to runner.run():
        self.runner = self.importmodule.Runner() # New Runner() class... just one stored here.
        
    def predict(self,value):
        """
        Checks prediction - and sends to relevant function.
        """
        detection = self.detector.predict(value)[0]
        self.runner.run(detection)
        return detection

class ExampleApp(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
        self.plotting = True #to turn off... somehow it does not detect then.
        pyqtgraph.setConfigOption('background', 'w') #before loading widget
        super(ExampleApp, self).__init__(parent)
        self.setupUi(self)
        self.grFFT.plotItem.showGrid(True, True, 0.7)
        self.grPCM.plotItem.showGrid(True, True, 0.7)
        self.maxFFT=0
        self.maxPCM=0
        self.ear = SWHear.SWHear(rate=44100,updatesPerSecond=20)
        
        self.progressBar.setVisible(False)
        QObject.connect(self.LearnSound, SIGNAL("clicked()"), self.learnSound)
        QObject.connect(self.LearnNotSound, SIGNAL("clicked()"), self.learnNotSound)
        QObject.connect(self.Train, SIGNAL("clicked()"), self.trainAction)
        self.ear.stream_start()
        #print dir(self.progressBar)
        #KEEP learning
        self.learnArrs = []
        self.learnNotArrs = []
        self.clf = None
        self.dumps = {fname:DetectionClass(fname) for fname in os.listdir('.') if fname.endswith('.svm')}
        if not self.plotting:
            self.labelDetection.setText('No updating the display... restart with plotting on to turn on high cpu graphs.')
        
    def learnSound(self, *args):
        print('max:%s' %( np.max(self.ear.fft),))
        fft = self.ear.fft
        #The scaler works per column. adjust:
        fft = scaler.fit_transform(self.ear.fft.reshape(self.ear.fft.shape[0],1))
        fft = fft.reshape(self.ear.fft.shape[0]);
        print('max:%s' %( np.max(fft),))
        self.learnArrs.append(fft)
        self.showInfo()
        #csv = '\n'.join( [str(x) for x in self.ear.fft] )
        #with open('out.csv','w') as outputfile:
        #    outputfile.write(csv)
        
    def learnNotSound(self):
        fft = self.ear.fft
        fft = scaler.fit_transform(self.ear.fft.reshape(self.ear.fft.shape[0],1))
        fft = fft.reshape(self.ear.fft.shape[0]);
        self.learnNotArrs.append(fft)
        self.showInfo();

    def showInfo(self):
        self.status.setText('%s learn, %s noise' % (len(self.learnArrs), len(self.learnNotArrs)))

    def trainAction(self):
        self.progressBar.setVisible(True)
        import numpy
        from sklearn.svm import SVC
        clf = SVC(kernel='linear', C=3)
        #Prep data to fit...
        data = self.learnArrs + self.learnNotArrs
        category = [1]*len(self.learnArrs) + [-1]*len(self.learnNotArrs)
        clf.fit(data, category)
                
        #Get m coefficients:
        coef = clf.coef_[0]
        b = clf.intercept_[0]
        self.progressBar.setVisible(False)
        print('This is the M*X+b=0 equation...')
        print('M=%s' % (coef))
        print('b=%s' % (b))
        print('positives:')
        for p in self.learnArrs:
            print clf.predict(p)
        print('negatives:')
        for p in self.learnNotArrs:
            print clf.predict(p)
        self.clf = clf
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', 'What did I just detect?')
        if ok:
            from sklearn.externals import joblib
            joblib.dump(clf, str(text+'.svm'))
            with open(text+'.py', 'w') as out:
                out.write("""#Example code!!!
class Runner():
    def __init__(self):
        pass
        
    def run(self, found):
        pass
""")
        self.learnArrs = []
        self.learnNotArrs = []

    def update(self):
        if not self.ear.data is None and not self.ear.fft is None:
            if self.plotting:
                pcmMax=np.max(np.abs(self.ear.data))
                if pcmMax>self.maxPCM:
                    self.maxPCM=pcmMax
                    self.grPCM.plotItem.setRange(yRange=[-pcmMax,pcmMax])
                if np.max(self.ear.fft)>self.maxFFT:
                    self.maxFFT=np.max(np.abs(self.ear.fft))
                    #self.grFFT.plotItem.setRange(yRange=[0,self.maxFFT])
                    self.grFFT.plotItem.setRange(yRange=[0,1])
                self.pbLevel.setValue(1000*pcmMax/self.maxPCM)
                pen=pyqtgraph.mkPen(color='b')
                self.grPCM.plot(self.ear.datax,self.ear.data,pen=pen,clear=True)
                pen=pyqtgraph.mkPen(color='r')
            #print(self.ear.fftx.shape)
            #for i in range(self.ear.fftx.shape[0]):
            #    print(self.ear.fftx[i])
            # ^ that is just increments of 20.
            #print(self.ear.fft.shape)
            runsum = 0
            spike = 0
            spikept = 0
            #for i in range(self.ear.fft.shape[0]):
                #if self.ear.fftx[i] % 100 == 0:
                    #runsum+= self.ear.fft[i]
                    ##print(str(self.ear.fftx[i])+' : '+str(runsum))
                    #if( runsum > spike ):
                        #spikept = self.ear.fftx[i]
                        #spike = runsum
                    #runsum = 0
                #else:
                    #runsum += self.ear.fft[i]
            status = ''
            #Label if it is happening or not:
            for detector in self.dumps:
                fft = self.ear.fft
                fft = scaler.fit_transform(self.ear.fft.reshape(self.ear.fft.shape[0],1))
                fft = fft.reshape(self.ear.fft.shape[0])#back to simple array
                status+=detector.replace('.svm', ' : ')
                if self.dumps[detector].predict(fft) > 0:
                    status += 'YES'
                status+='\n'
            if self.plotting:
                self.labelDetection.setText(status)
            #print('spike near '+str(spikept))
            if self.plotting:
                self.grFFT.plot(self.ear.fftx,self.ear.fft/self.maxFFT,pen=pen,clear=True)
                QtCore.QTimer.singleShot(1, self.update) # QUICKLY repeat

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    form.update() #start with something
    app.exec_()
    print("DONE")
