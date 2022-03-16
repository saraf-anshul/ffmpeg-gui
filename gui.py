#!/usr/bin/env python

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox, QFrame, QRadioButton
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
def getAspectRatio( w, h, SIZE = 720):
	w = w * 2 # total , including alpha too 
	if( w <= SIZE and h <= SIZE ):
		return f"scale={w - (w%2)}:{h - (h%2)}"
	
	ar = w / h

	if( w <= h ):
		# set h to SIZE and calc w
		h = SIZE
		w = int(ar * h)
	else: # w < h
		# set w to SIZE and calc w
		w = SIZE
		h = int(w / ar)
	return f"scale={w - (w%2)}:{h - (h%2)}"

def runScript(rgbFileName, alphaFileName, outputFileName, SIZE = 720):
	w, h = findVideoResolution(rgbFileName) # assuming dimens of rgb == alpha
	# print(w, h, SIZE)
	scale_var = getAspectRatio(w, h, SIZE)
	script = f'ffmpeg -an -i "{rgbFileName}" -i "{alphaFileName}" -filter_complex "[0:v][1:v]hstack=inputs=2[n];[n]fps=fps=30[k];[k]{scale_var}" -c:v libx264 -pix_fmt yuv420p -movflags +faststart -profile:v baseline -level 3.0 "{outputFileName}" -y'
	# print(script)
	os.system(script)

class FileInfoAndSelectorBox(QWidget):
	def __init__(self, type):
		super().__init__()

		self.selectedFiles = []

		self.setAcceptDrops(True)

		#### V-box for column
		vBoxLayout0 = QVBoxLayout(self)

		##### button select
		self.button = QPushButton(f'Select {type} file(s)', self)
		self.button.setToolTip(f'Select {type} file for conversion')
		self.button.clicked.connect(self.on_click_select)
		vBoxLayout0.addWidget(self.button)
		#####

		##### textview says "selected Dir"
		self.labelSelect = QLabel('', self)
		self.labelSelect.setText(f"Selected {type} Files:")
		self.labelSelect.setAlignment(Qt.AlignCenter)
		vBoxLayout0.addWidget(self.labelSelect)
		#####

		##### filename textview
		self.twFlies = QLabel(f'Selected {type} files', self)
		self.twFlies.setText(f"No {type} files selected")
		self.twFlies.setAlignment(Qt.AlignCenter)
		vBoxLayout0.addWidget(self.twFlies)
		#####


	# select file onClick
	@pyqtSlot()
	def on_click_select(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		open_loc = getDefaultStorageLocation()

		fileName, _ = QFileDialog.getOpenFileNames(self,"Select input files", open_loc,"All Files (*);;Video Files (*.mov)", options=options)
		if fileName:
			print(fileName)
			self.selectedFiles = fileName
			self.setFilename(self.twFlies, fileName)

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		files = [u.toLocalFile() for u in event.mimeData().urls()]
		for f in files:
			print(f)
		self.selectedFiles = files
		self.setFilename(self.twFlies , files)

	def setFilename(self ,view, names):
		text = "\n".join([i.split('/')[-1] for i in names])
		view.setText(text)
		view.adjustSize()


class CustomRadioButtonGroup(QWidget):
	def __init__(self):
		super().__init__()

		self.resolution = 720

		layout = QHBoxLayout(self)

		label = QLabel('Output video resolution :')
		layout.addWidget(label)

		vBox = QGroupBox()
		vLayout = QVBoxLayout()

		### Radio button for output res selection
		self.rBtn720 = QRadioButton("720p")
		self.rBtn720.setChecked(True)
		self.rBtn1080 = QRadioButton("1080p")
		self.rBtn720.toggled.connect(self.on_click_r_btn)
		self.rBtn1080.toggled.connect(self.on_click_r_btn)

		vLayout.addWidget(self.rBtn720)
		vLayout.addWidget(self.rBtn1080)

		vBox.setLayout(vLayout)
		layout.addWidget(vBox)
		###

	@pyqtSlot()
	def on_click_r_btn(self):
		radioBtn = self.sender()
		self.resolution = int(radioBtn.text()[:-1])
		# print( f"Quality set to {radioBtn.text()[:-1]}" )


class MainWidget(QMainWindow):
	def __init__(self):
		super().__init__()

		self.saveLocation = ""

		### window attrs
		self.setWindowTitle("Shutter-lib GUI")
		self.resize(300, 300)
		wid = QWidget(self)
		self.setCentralWidget(wid)
		layout = QVBoxLayout()
		wid.setLayout(layout)
		###

		### H-box for RGB/Alpha diff
		hBoxRA = QGroupBox()
		hBoxRALayout = QHBoxLayout()

		self.rgbLayout = FileInfoAndSelectorBox("RGB")
		self.alphaLayout = FileInfoAndSelectorBox("Alpha")

		hBoxRALayout.addWidget(self.rgbLayout)
		hBoxRALayout.addWidget(self.alphaLayout)
		hBoxRA.setLayout(hBoxRALayout)

		layout.addWidget(hBoxRA)
		###

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
		except:
			with open( getLocationsFile() ,'w' ) as F:
				json.dump({'last' : getDefaultStorageLocation()} ,F)
			self.updateSaveLocation( getDefaultStorageLocation() )
		###

		### out-file dir select
		self.outputDir = QPushButton('Select output dir', self)
		self.outputDir.clicked.connect(self.on_click_dir)
		layout.addWidget(self.outputDir)
		###

		### Radio Group for 1080, 720p selection
		self.radioGroup = CustomRadioButtonGroup()
		layout.addWidget(self.radioGroup)
		###

		### run button
		self.button_run = QPushButton('Run', self)
		self.button_run.setToolTip('Run Script')
		self.button_run.setStyleSheet("QPushButton {background-color:#48A14D; border-radius: 4px; min-height: 22px;}")
		self.button_run.clicked.connect(self.run_script)
		layout.addWidget(self.button_run)
		###

	# download location onClick
	@pyqtSlot()
	def on_click_dir(self):
		dir = self.saveLocation

		dirName = QFileDialog().getExistingDirectory(self, 'Select an directory to save files' ,dir)
		if dirName:
			print(dirName)
			self.updateSaveLocation(dirName)

	@pyqtSlot()
	def run_script(self):
		outputDir = self.saveLocation
		res = self.radioGroup.resolution

		self.button_run.setStyleSheet("QPushButton {background-color:#B33F40; border-radius: 4px; min-height: 22px;}")
		self.button_run.setText(f"Running...")
		self.button_run.repaint()
		self.button_run.setEnabled(False)

		for fileRGB ,fileAlpha in zip(self.rgbLayout.selectedFiles, self.alphaLayout.selectedFiles):
			newFileName = outputDir + f"/{fileRGB.split('/')[-1].replace('.' ,'_')}_converted_{res}_mp4.mp4"
			runScript(fileRGB ,fileAlpha, newFileName, res)

		with open( getLocationsFile() ,'w' ) as F:
			json.dump({'last' : outputDir} ,F)

		self.button_run.setText("Run Again")
		self.button_run.setStyleSheet("QPushButton {background-color:#48A14D; border-radius: 4px; min-height: 22px;}")
		self.button_run.repaint()
		self.button_run.setEnabled(True)

	def updateSaveLocation(self, loc):
		self.labelOut.setText(loc)
		self.saveLocation = loc


if __name__ == '__main__':
	app = QApplication(sys.argv)
	ui = MainWidget()
	ui.show()
	sys.exit(app.exec_())
