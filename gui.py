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

	return width, height

# Returns a `scale w:h` string for ffmpeg cli
# H and W are EVEN
def getAspectRatio( w, h ):
	w = w * 2 # total , including alpha too 
	if( w <= 720 and h <= 720 ):
		return f"scale={w - (w%2)}:{h - (h%2)}"
	
	ar = w / h

	if( w <= h ):
		# set h to 720 and calc w
		h = 720
		w = int(ar * h)
	else: # w < h
		# set w to 720 and calc w
		w = 720
		h = int(w / ar)
	return f"scale={w - (w%2)}:{h - (h%2)}"

def runScript(rgbFileName, alphaFileName, outputFileName):
	w, h = findVideoResolution(rgbFileName) # assuming dimens of rgb == alpha
	print(w, h)
	scale_var = getAspectRatio(w, h)
	print(scale_var)
	script = f'ffmpeg -an -i "{rgbFileName}" -i "{alphaFileName}" -filter_complex "[0:v][1:v]hstack=inputs=2[n];[n]fps=fps=30[k];[k]{scale_var}" -c:v libx264 -pix_fmt yuv420p -movflags +faststart -profile:v baseline -level 3.0 "{outputFileName}" -y'
	# script = f'ffmpeg -an -i "{fileName}" -filter_complex "[0:v]alphaextract[a]; [0:v][a]hstack=inputs=2[n];[n]fps=fps=30[k];[k]{scale_var}"  -c:v libx264 -pix_fmt yuv420p -movflags +faststart -profile:v baseline -level 3.0 "{outputFileName}" -y'
	print(script)
	os.system(script)


class MainWidget(QMainWindow):
	def __init__(self):
		super().__init__()

		self.selectedFilesRGB = []
		self.selectedFilesAlpha = []
		self.saveLocation = ""

		### window attrs
		self.setWindowTitle("Shutter-lib GUI")
		self.resize(300, 300)
		# self.setAcceptDrops(True)
		wid = QWidget(self)
		self.setCentralWidget(wid)
		layout = QVBoxLayout()
		wid.setLayout(layout)
		###

		### H-box for RGB/Alpha diff
		hBoxRA = QGroupBox()
		hBoxRALayout = QHBoxLayout()

		#### V-box for RGB column
		vBox0 = QGroupBox()
		vBoxLayout0 = QVBoxLayout()

		##### button select RGB
		self.buttonRGB = QPushButton('Select RGB file(s)', self)
		self.buttonRGB.setToolTip('Select RGB file for conversion')
		self.buttonRGB.clicked.connect(self.on_clickRGB)
		vBoxLayout0.addWidget(self.buttonRGB)
		#####

		##### textview says "selected Dir RGB"
		self.labelSelectRGB = QLabel('', self)
		self.labelSelectRGB.setText("Selected RGB Files:")
		self.labelSelectRGB.setAlignment(Qt.AlignCenter)
		vBoxLayout0.addWidget(self.labelSelectRGB)
		#####

		##### filename-RGB textview
		self.twRGB = QLabel('Selected RGB files', self)
		self.twRGB.setText("No files selected")
		self.twRGB.setAlignment(Qt.AlignCenter)
		vBoxLayout0.addWidget(self.twRGB)
		#####

		vBox0.setLayout(vBoxLayout0)
		####

		#### V-box for Alpha column
		vBox1 = QGroupBox()
		vBoxLayout1 = QVBoxLayout()

		##### button select Alpha
		self.buttonAlpha = QPushButton('Select Alpha file(s)', self)
		self.buttonAlpha.setToolTip('Select Alpha file for conversion')
		self.buttonAlpha.clicked.connect(self.on_clickAlpha)
		vBoxLayout1.addWidget(self.buttonAlpha)
		#####

		##### textview says "selected Dir Alpha"
		self.labelSelectAlpha = QLabel('', self)
		self.labelSelectAlpha.setText("Selected Alpha Files:")
		self.labelSelectAlpha.setAlignment(Qt.AlignCenter)
		vBoxLayout1.addWidget(self.labelSelectAlpha)
		#####

		##### filename-Alpha textview
		self.twAlpha = QLabel('Selected RGB files', self)
		self.twAlpha.setText("No files selected")
		self.twAlpha.setAlignment(Qt.AlignCenter)
		vBoxLayout1.addWidget(self.twAlpha)
		#####

		vBox1.setLayout(vBoxLayout1)
		####

		hBoxRALayout.addWidget(vBox0)
		hBoxRALayout.addWidget(vBox1)
		hBoxRA.setLayout(hBoxRALayout)

		layout.addWidget(hBoxRA)

		### horizontal layout (Output)
		horizontalGroupBox = QGroupBox()
		h_layout = QHBoxLayout()

		#### textview says "outupt Dir"
		self.labelOutx = QLabel('', self)
		self.labelOutx.setText("Output directory:")
		self.labelOutx.setAlignment(Qt.AlignCenter)
		h_layout.addWidget(self.labelOutx)
		####

		#### out-file dir textview
		self.labelOut = QLabel('This is label', self)
		self.labelOut.setText("No output directory selected")
		self.labelOut.setAlignment(Qt.AlignCenter)
		h_layout.addWidget(self.labelOut)
		####

		horizontalGroupBox.setLayout(h_layout)
		layout.addWidget(horizontalGroupBox)
		###

		### load save file or create
		try:
			with open( getLocationsFile() ,'r' ) as F:
				self.updateSaveLocation( json.load(F)['last'] )
				# self.labelOut.setText( json.load(F)['last'] )
		except:
			with open( getLocationsFile() ,'w' ) as F:
				json.dump({'last' : getDefaultStorageLocation()} ,F)
			# self.labelOut.setText('No save location selected')
			self.updateSaveLocation( getDefaultStorageLocation() )
		###

		### out-file dir select
		self.outputDir = QPushButton('Select output dir', self)
		self.outputDir.clicked.connect(self.on_click_dir)
		layout.addWidget(self.outputDir)
		###

		### run button
		self.buttonRGB_run = QPushButton('Run', self)
		self.buttonRGB_run.setToolTip('Run Script')
		self.buttonRGB_run.setStyleSheet("QPushButton {background-color:#48A14D; border-radius: 4px; min-height: 22px;}")
		self.buttonRGB_run.clicked.connect(self.run_script)
		layout.addWidget(self.buttonRGB_run)
		###
		
	# select file onClick (RGB)
	@pyqtSlot()
	def on_clickRGB(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		open_loc = getDefaultStorageLocation()

		fileName, _ = QFileDialog.getOpenFileNames(self,"Select RGB files", open_loc,"All Files (*);;Video Files (*.mov)", options=options)
		if fileName:
			print(fileName)
			self.selectedFilesRGB = fileName
			self.setFilename(self.twRGB, fileName)

	# select file onClick (Alpha)
	@pyqtSlot()
	def on_clickAlpha(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		open_loc = getDefaultStorageLocation()

		fileName, _ = QFileDialog.getOpenFileNames(self,"Select Alpha files", open_loc,"All Files (*);;Video Files (*.mov)", options=options)
		if fileName:
			print(fileName)
			self.selectedFilesAlpha = fileName
			self.setFilename(self.twAlpha, fileName)

	# download location onClick
	@pyqtSlot()
	def on_click_dir(self):
		dir = self.saveLocation

		dirName = QFileDialog().getExistingDirectory(self, 'Select an directory to save files' ,dir)
		if dirName:
			print(dirName)
			self.updateSaveLocation(dirName) ## here too

	@pyqtSlot()
	def run_script(self):
		outputDir = self.saveLocation

		self.buttonRGB_run.setStyleSheet("QPushButton {background-color:#B33F40; border-radius: 4px; min-height: 22px;}")
		self.buttonRGB_run.setText(f"Running...")
		self.buttonRGB_run.repaint()
		self.buttonRGB_run.setEnabled(False)

		for fileRGB ,fileAlpha in zip(self.selectedFilesRGB, self.selectedFilesAlpha):
			newFileName = outputDir + f"/{fileRGB.split('/')[-1].replace('.' ,'_')}_converted_mp4.mp4"
			runScript(fileRGB ,fileAlpha , newFileName)

		with open( getLocationsFile() ,'w' ) as F:
			json.dump({'last' : outputDir} ,F)

		self.buttonRGB_run.setText("Run Again")
		self.buttonRGB_run.setStyleSheet("QPushButton {background-color:#48A14D; border-radius: 4px; min-height: 22px;}")
		self.buttonRGB_run.repaint()
		self.buttonRGB_run.setEnabled(True)

	# def dragEnterEvent(self, event):
	# 	if event.mimeData().hasUrls():
	# 		event.accept()
	# 	else:
	# 		event.ignore()

	# def dropEvent(self, event):
	# 	files = [u.toLocalFile() for u in event.mimeData().urls()]
	# 	for f in files:
	# 		print(f)
	# 	self.setFilename(files)

	def updateSaveLocation(self, loc):
		self.labelOut.setText(loc)
		self.saveLocation = loc


	def setFilename(self ,view, names):
		# self.selectedFiles = names
		text = "\n".join([i.split('/')[-1] for i in names])
		view.setText(text)
		view.adjustSize()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	ui = MainWidget()
	ui.show()
	sys.exit(app.exec_())
