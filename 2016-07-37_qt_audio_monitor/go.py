from __future__ import division
from PyQt4 import QtGui,QtCore

from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range=(0,1))


import sys
import ui_main
import numpy as np
import pyqtgraph
import SWHear
import time
from PyQt4.QtCore import QObject, SIGNAL

class ExampleApp(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
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
        
    def learnSound(self, *args):
        print('max:%s' %( np.max(self.ear.fft),))
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

    def update(self):
        if not self.ear.data is None and not self.ear.fft is None:
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
            for i in range(self.ear.fft.shape[0]):
                if self.ear.fftx[i] % 100 == 0:
                    runsum+= self.ear.fft[i]
                    #print(str(self.ear.fftx[i])+' : '+str(runsum))
                    if( runsum > spike ):
                        spikept = self.ear.fftx[i]
                        spike = runsum
                    runsum = 0
                else:
                    runsum += self.ear.fft[i]
            if self.clf:
                fft = scaler.fit_transform(self.ear.fft.reshape(self.ear.fft.shape[0],1))
                fft = fft.reshape(self.ear.fft.shape[0])#back to simple array
                print('match: '+str(self.clf.predict(fft)))
            #print('spike near '+str(spikept))
            self.grFFT.plot(self.ear.fftx,self.ear.fft/self.maxFFT,pen=pen,clear=True)
            #time.sleep(13000)
        QtCore.QTimer.singleShot(1, self.update) # QUICKLY repeat

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    form.update() #start with something
    app.exec_()
    print("DONE")
