#!/usr/bin/env python

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot ,Qt
import sys, os
import subprocess, shlex
import json

def getLocationsFile():
	return os.path.join(os.path.expanduser('~'), "Documents/locations.json")

def getDefaultStorageLocation():
	return os.path.join(os.path.expanduser('~'), "Downloads/")

# function to find the resolution of the input video file
def findVideoResolution(pathToInputVideo):
	cmd = "ffprobe -v quiet -print_format json -show_streams"
	args = shlex.split(cmd)
	args.append(pathToInputVideo)
	# run the ffprobe process, decode stdout into utf-8 & convert to JSON
	ffprobeOutput = subprocess.check_output(args).decode('utf-8')
	ffprobeOutput = json.loads(ffprobeOutput)

	# find height and width
	height = ffprobeOutput['streams'][0]['height']
	width = ffprobeOutput['streams'][0]['width']

	return height, width

# returns a `scale w:h` string for ffmpeg
def getAspectRatio( w, h ):
	w = w * 2 # seperate alpha 
	if( w <= 720 and h <= 720 ):
		f"scale={w}:{h}"
	
	ar = w / h
	
	if( w <= h ):
		# set h to 720 and calc w
		h = 720
		w = int(ar * h)
	else: # w < h
		# set w to 720 and calc w
		w = 720
		h = int(w / ar)
	return f"scale={w}:{h}"


def runScript(fileName, outputFileName):
	# bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
	
	# videoconvetor = os.path.abspath(os.path.join(bundle_dir,'videoconvetor.sh'))

	# os.system(f"chmod +x {videoconvetor}")
	w, h = findVideoResolution(fileName)
	scale_var = getAspectRatio(w, h)
	script = f'ffmpeg -an -i {fileName} -filter_complex "[0:v]alphaextract[a]; [0:v][a]hstack=inputs=2[n];[n]fps=fps=30[k];[k]{scale_var}"  -c:v libx264 -pix_fmt yuv420p -movflags +faststart -profile:v baseline -level 3.0 {outputFileName} -y'
	print(script)
	os.system(script)


class MainWidget(QMainWindow):
	def __init__(self):
		super().__init__()

		self.selectedFiles = [] # file locations

		# window attrs
		self.setWindowTitle("Drag and Drop")
		self.resize(300, 300)
		self.setAcceptDrops(True)
		wid = QWidget(self)
		self.setCentralWidget(wid)
		layout = QVBoxLayout()
		wid.setLayout(layout)	

		# button select
		self.button = QPushButton('Select file(s)', self)
		self.button.setToolTip('Select file for conversion')
		self.button.clicked.connect(self.on_click)
		layout.addWidget(self.button)


		# horizontal layout (Selected)

		self.horizontalGroupBox0 = QGroupBox()
		h_layout0 = QHBoxLayout()

		# textview says "selected Dir"
		self.labelOuty = QLabel('', self)
		self.labelOuty.setText("Selected Files:")
		self.labelOuty.setAlignment(Qt.AlignCenter)
		h_layout0.addWidget(self.labelOuty)

		# filename textview
		self.label = QLabel('Selected files', self)
		self.label.setText("No files selected")
		self.label.setAlignment(Qt.AlignCenter)
		h_layout0.addWidget(self.label)

		self.horizontalGroupBox0.setLayout(h_layout0)
		layout.addWidget(self.horizontalGroupBox0)



		# horizontal layout (Output)
		#### horizontal box
		self.horizontalGroupBox = QGroupBox()
		h_layout = QHBoxLayout()

		# textview says "outupt Dir"
		self.labelOutx = QLabel('', self)
		self.labelOutx.setText("Output directory:")
		self.labelOutx.setAlignment(Qt.AlignCenter)
		h_layout.addWidget(self.labelOutx)

		# out-file dir textview
		self.labelOut = QLabel('This is label', self)
		self.labelOut.setText("No output directory selected")
		self.labelOut.setAlignment(Qt.AlignCenter)
		h_layout.addWidget(self.labelOut)

		self.horizontalGroupBox.setLayout(h_layout)
		layout.addWidget(self.horizontalGroupBox)

		try:
			with open( getLocationsFile() ,'r' ) as F:
				self.labelOut.setText( json.load(F)['last'] )
		except:
			with open( getLocationsFile() ,'w' ) as F:
				json.dump({'last' : getDefaultStorageLocation()} ,F)
			self.labelOut.setText('No save location selected')

		###



		# out-file dir select
		self.outputDir = QPushButton('Select output dir', self)
		self.outputDir.clicked.connect(self.on_click_dir)
		layout.addWidget(self.outputDir)

		# run button
		self.button_run = QPushButton('Run', self)
		self.button_run.setToolTip('Run Script1')
		self.button_run.setStyleSheet("QPushButton {background-color:#48A14D; border-radius: 4px; min-height: 22px;}")
		self.button_run.clicked.connect(self.run_script)
		layout.addWidget(self.button_run)
		
	@pyqtSlot()
	def on_click(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		open_loc = ""

		fileName, _ = QFileDialog.getOpenFileNames(self,"Select files", open_loc,"All Files (*);;Video Files (*.mp4)", options=options)
		if fileName:
			print(fileName)
			self.setFilename(fileName)

	@pyqtSlot()
	def on_click_dir(self):
		dir = "/"
		if(os.path.isdir(self.labelOut.text())):
			dir = self.labelOut.text()

		dirName = QFileDialog().getExistingDirectory(self, 'Select an directory' ,dir)
		if dirName:
			print(dirName)
			self.labelOut.setText(dirName)

	@pyqtSlot()
	def run_script(self):
		outputDir = self.labelOut.text()

		self.button_run.setStyleSheet("QPushButton {background-color:#B33F40; border-radius: 4px; min-height: 22px;}")
		for idx ,file in enumerate(self.selectedFiles):
			self.button_run.setText(f"Running... {idx + 1}")
			newFileName = outputDir + f"/{file.split('/')[-1].replace('.' ,'_')}_converted_mp4.mp4"
			runScript(file , newFileName)

		with open( getLocationsFile() ,'w' ) as F:
			json.dump({'last' : outputDir} ,F)

		self.button_run.setText("Run Again")
		self.button_run.setStyleSheet("QPushButton {background-color:#48A14D; border-radius: 4px; min-height: 22px;}")

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		files = [u.toLocalFile() for u in event.mimeData().urls()]
		for f in files:
			print(f)
		self.setFilename(files)

	def setFilename(self ,names):
		self.selectedFiles = names
		text = "\n".join([i.split('/')[-1] for i in names])
		self.label.setText(text)
		self.label.adjustSize()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	ui = MainWidget()
	ui.show()
	sys.exit(app.exec_())
