# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import time, datetime, os, subprocess
import shutil
import maya.cmds as cmds

from os import listdir
from os.path import isfile, join

import tank
from tank import Hook
from tank import TankError

import sgtk
from sgtk.platform import Application


#from shotgun import Shotgun

class PublishHook(Hook):
	"""
	Single hook that implements publish functionality for secondary tasks
	"""    
	def execute(self, tasks, work_template, comment, thumbnail_path, sg_task, primary_task, primary_publish_path, progress_cb, **kwargs):
		"""
		Main hook entry point
		:param tasks:                   List of secondary tasks to be published.  Each task is a 
										dictionary containing the following keys:
										{
											item:   Dictionary
													This is the item returned by the scan hook 
													{   
														name:           String
														description:    String
														type:           String
														other_params:   Dictionary
													}
												   
											output: Dictionary
													This is the output as defined in the configuration - the 
													primary output will always be named 'primary' 
													{
														name:             String
														publish_template: template
														tank_type:        String
													}
										}
						
		:param work_template:           template
										This is the template defined in the config that
										represents the current work file
			   
		:param comment:                 String
										The comment provided for the publish
						
		:param thumbnail:               Path string
										The default thumbnail provided for the publish
						
		:param sg_task:                 Dictionary (shotgun entity description)
										The shotgun task to use for the publish    
						
		:param primary_publish_path:    Path string
										This is the path of the primary published file as returned
										by the primary publish hook
						
		:param progress_cb:             Function
										A progress callback to log progress during pre-publish.  Call:
										
											progress_cb(percentage, msg)
											 
										to report progress to the UI
						
		:param primary_task:            The primary task that was published by the primary publish hook.  Passed
										in here for reference.  This is a dictionary in the same format as the
										secondary tasks above.
		
		:returns:                       A list of any tasks that had problems that need to be reported 
										in the UI.  Each item in the list should be a dictionary containing 
										the following keys:
										{
											task:   Dictionary
													This is the task that was passed into the hook and
													should not be modified
													{
														item:...
														output:...
													}
													
											errors: List
													A list of error messages (strings) to report    
										}
		"""
		def FindFirstImageOfSequence(FolderPath):
			ImgsList=[]
			for file in (os.listdir(FolderPath)):
				SeqImgName = str.split(str(file),".")[1]
				ImgsList.append(SeqImgName)
			First_elmnt=ImgsList[0]
			return First_elmnt
			
		def FindFirstImageOfSequence(FolderPath):
			ImgsList=[]
			for file in (os.listdir(FolderPath)):
				if file.endswith(".png"):
					SeqImgName = str.split(str(file),".")[1]
					ImgsList.append(int(SeqImgName))
				First_elmnt=ImgsList[0]
			return First_elmnt

		def FindLastImageOfSequence(FolderPath):
			ImgsList=[]
			for file in (os.listdir(FolderPath)):
				if file.endswith(".png"):
					SeqImgName = str.split(str(file),".")[1]
					ImgsList.append(int(SeqImgName))
				Last_elmnt=ImgsList[-1]
			return Last_elmnt
			
		def FindLengthOfSequence(FolderPath):
			ImgsList=[]
			for file in (os.listdir(FolderPath)):
				if file.endswith(".png"):
					SeqImgName = str.split(str(file),".")[1]
					ImgsList.append(int(SeqImgName))
				Length_seq=len(ImgsList)
			return Length_seq
			
		def MakeListOfSequence(FolderPath):
			ImgsList=[]
			for file in (os.listdir(FolderPath)):
				if file.endswith(".png"):
					SeqImgName = str.split(str(file),".")[1]
					ImgsList.append(int(SeqImgName))
			return ImgsList

		def FindMissingFramesFromSequence(SequenceSet,inputStart,inputEnd):
			# my_list= list(range( int(FindFirstImageOfSequence(os.path.dirname(RenderPath)))	, int(FindLastImageOfSequence(os.path.dirname(RenderPath)))	 ))
			my_list= list(range( inputStart, inputEnd))
			MissingFrames =  set(my_list)-set(SequenceSet)
			return sorted(MissingFrames)
			
		def combineAudioFiles(fileList,output):
			#fileList = str.replace(fileList,"\\","/")
			rootPath = str.split(str(fileList)[0],"\\q")[0]
			print rootPath
			audioFilePresent = False
			audioFile = open(rootPath+'tmpAudioList.txt', 'w')
			for wav in fileList:
				if os.path.exists(wav):
					audioFilePresent = True
					print wav
					shotPath = str.split(str(wav),"Sequences")[1]
					audioFile.write("file '" +shotPath)
					audioFile.write('\r\n')
				else:
					print("AUDIO FILE NOT FOUND :  " + str(wav))
					results.append({"task":"audio stuff", "errors":("AUDIO FILE NOT FOUND :  " + str(wav))})
			audioFile.close()
			if audioFilePresent:
				value = subprocess.call('W:/WG/WTD_Code/trunk/wtd/pipeline/resources/ffmpeg/bin/ffmpeg.exe -f concat -i '+rootPath+'tmpAudioList.txt -c copy '+output)
				print value

	
		wtd_fw = self.load_framework("tk-framework-wtd_v0.x.x")
		ffmpeg = wtd_fw.import_module("pipeline.ffmpeg")
		# ffmpeg.test()
		
		shots = cmds.ls(type="shot")
		shotCams = []
		unUsedCams = []

		for sht in shots:
			shotCam = cmds.shot(sht, q=True, currentCamera=True)
			shotCams += [shotCam]
			#print shotCam

		pbShots = []
		CutInList = []
		# these booleans can be used for 
		noOverscan = False
		resetCutIn = False

		# template stuff...
		tk = tank.tank_from_path("W:/RTS/Tank/config")
		scenePath = cmds.file(q=True,sceneName=True)
		scene_template = tk.template_from_path(scenePath)
		flds = scene_template.get_fields(scenePath)
		flds['width'] = 1724
		flds['height'] = 936
		pb_template = tk.templates["maya_seq_playblast_publish"]
		pbArea_template = tk.templates["maya_seq_playblast_publish_area"]
		audio_template = tk.templates["shot_audio"]

		# get extra shot info through shotgun
		fields = ['id']
		sequence_id = self.parent.shotgun.find('Sequence',[['code', 'is',flds['Sequence'] ]], fields)[0]['id']
		fields = ['id', 'code', 'sg_asset_type','sg_cut_order','sg_cut_in','sg_cut_out']
		filters = [['sg_sequence', 'is', {'type':'Sequence','id':sequence_id}]]
		assets= self.parent.shotgun.find("Shot",filters,fields)
		results = []

		for task in tasks:
			item = task["item"]
			output = task["output"]
			errors = []
			
			#get shots from scan scene
			if item["type"] == "shot":
				shotTask = [item["name"]][0]
				pbShots += [shotTask]
			# get corresponding cut in values from shotgun
				for sht in assets:
					shot_from_shotgun = str.split(sht['code'],"_")[1]
					if shot_from_shotgun == shotTask:
						CutInList += [sht['sg_cut_in']]
			
			# set extra settings
			if item["type"] == "setting":
				if item["name"]=="overscan":
					noOverscan = True
				if item["name"]=="set Cut in":
					resetCutIn = True

			# if there is anything to report then add to result
			if len(errors) > 0:
				# add result:
				results.append({"task":task, "errors":errors})
			 
		print("corresponing Shot numbers = " + str(pbShots))
		print("cut in list = " + str(CutInList))

		# temporarily hide cams and curves
		visPan = cmds.getPanel(visiblePanels=True)
		modPan = cmds.getPanel(type="modelPanel")
		for pan in visPan:
			if pan in modPan:
				modPan = pan
		crvVis = cmds.modelEditor(modPan,q=True, nurbsCurves=True)
		camVis = cmds.modelEditor(modPan,q=True, cameras=True)
		cmds.modelEditor(modPan,e=True, nurbsCurves=False)
		cmds.modelEditor(modPan,e=True, cameras=False)
		cmds.modelEditor(modPan,e=True,displayAppearance="smoothShaded")
		
		# audio stuff
		stepVersion = flds['version']
		# audioList = []
		# for sht in shots:
			# flds['Shot'] = (flds['Sequence']+"_"+sht)
			# flds['version'] = 1 #temporary set version to 1 for soundfiles ...
			# audioList += [audio_template.apply_fields(flds)]
		# flds['Shot'] = flds['Sequence']
		# audioOutput = pbArea_template.apply_fields(flds)+"/"+flds['Sequence']+"_"+flds['Step']+".wav"
		# combineAudioFiles(audioList,audioOutput)
		flds['version'] = stepVersion #set version back

		j = 0
		RenderPath = ""
		for pbShot in pbShots:
			CutIn = CutInList[j]
			j += 1
			
			sequenceName = flds ['Sequence']
			shotName = pbShot
			
			# ... correct this in the templates?
			flds['Shot'] = flds['Sequence']

			#get camera name from sequence shot 
			shotCam = cmds.shot(pbShot, q=True, currentCamera=True)

			overscanValue = cmds.getAttr(shotCam+".overscan")
			if noOverscan:
				cmds.setAttr(shotCam+".overscan", 1)
				print (shotCam+"  overscan is set to 1")
			
			# make outputPaths from templates
			pbPath = pb_template.apply_fields(flds)
			RenderPath = pbPath
			pbPath = str.split(str(pbPath),".")[0]

			# report progress:
			progress_cb(0, "Publishing", task)

			shotStart = cmds.shot(pbShot,q=True,sequenceStartTime=True)
			shotEnd = cmds.shot(pbShot,q=True,sequenceEndTime=True)
			progress_cb(25, "Making playblast %s" %pbShot)
			# cmds.playblast(indexFromZero=False,filename=(pbPath),fmt="iff",compression="png",wh=(flds['width'], flds['height']),startTime=shotStart,endTime=shotEnd,sequenceTime=1,forceOverwrite=True, clearCache=1,showOrnaments=0,percent=100,offScreen=True,viewer=False,useTraxSounds=True)
			progress_cb(50, "Placing Slates %s" %pbShot)
			
			cmds.setAttr(shotCam+".overscan", overscanValue)
			Film = "Richard the Stork"
			#GET CURRENT DATE
			today = datetime.date.today()
			todaystr = today.isoformat()
			#Get USER
			USER = sgtk.util.get_current_user(tk)
			# os.environ.get('FFMPEG_PATH')
			# os.getenv('KEY_THAT_MIGHT_EXIST', default_value)
			
			# ffmpegPath =os.environ.get('FFMPEG_PATH')
			ffmpegPath =r"%FFMPEG_PATH%\ffmpeg"
			ffmpegPath =r'"C:\Program Files\ffmpeg\bin\ffmpeg"'
			
			"""
				Adding Slates to playblast files
			"""
			for i in range(int(shotStart),int(shotEnd)+1):
				FirstPartName = RenderPath.split( '%04d' )[0]
				EndPartName = RenderPath.split( '%04d' )[-1]
				ImageFullName= FirstPartName + '%04d' % i + EndPartName
				ffmpeg.ffmpegMakingSlates(inputFilePath= ImageFullName, outputFilePath= ImageFullName, topleft = flds ['Sequence']+"_"+flds['Step']+"_v"+str('%03d' % (flds['version'])), topmiddle = Film, topright = str(int(CutIn))+"-"+str('%04d' %(i-int(shotStart)+CutIn))+"-"+str('%04d' %(int(shotEnd)-int(shotStart)+CutIn))+"  "+str('%04d' %(i-int(shotStart)))+"-"+str('%04d' %(int(shotEnd)-int(shotStart))), bottomleft = shotName, bottommiddle = USER['name'], bottomright = todaystr , ffmpegPath =ffmpegPath, font = "C:/Windows/Fonts/arial.ttf"  )
			
		sequenceTest= MakeListOfSequence(os.path.dirname(RenderPath))
		FistImg= int(FindFirstImageOfSequence(os.path.dirname(RenderPath))) 
		LastImg= int(FindLastImageOfSequence(os.path.dirname(RenderPath)))

		FramesMissingList= FindMissingFramesFromSequence( sequenceTest , FistImg, LastImg )
		
		# for n in FramesMissingList:
			# os.system('%s -f lavfi -i color=c=black:s="%s" -vframes 1 "%s"' %(ffmpegPath,(str(flds['width'])+"x"+ str(flds['height'])),FirstPartName+str('%04d' % n)+".png"))
		
		"""
			Copy empty frames
		"""
		blackFrame = False
		blackFrameName = ""
		for n in FramesMissingList:
			if blackFrame == False:
				blackFrameName = FirstPartName+str('%04d' % n)+".png"
				value = subprocess.call('%s -f lavfi -i color=c=black:s="%s" -vframes 1 "%s"' %(ffmpegPath,(str(flds['width'])+"x"+ str(flds['height'])),FirstPartName+str('%04d' % n)+".png"))
				print '%s -f lavfi -i color=c=black:s="%s" -vframes 1 "%s"' %(ffmpegPath,(str(flds['width'])+"x"+ str(flds['height'])),FirstPartName+str('%04d' % n)+".png")
				blackFrame = True
			
			newFrameName = FirstPartName+str('%04d' % n)+".png"
			if blackFrameName != newFrameName:
				shutil.copy2(blackFrameName, newFrameName)	

		FirstImageNumber= FindFirstImageOfSequence(os.path.dirname(RenderPath))
		FirstImageNumberSecond= FirstImageNumber/24
		
		maya_seq_playblast_publish_mov_template = tk.templates["maya_seq_playblast_publish_mov"]
		maya_seq_pbst_pbsh_mov_path = maya_seq_playblast_publish_mov_template.apply_fields(flds)

		maya_seq_playblast_review_mp4_template = tk.templates["maya_seq_playblast_review_mp4"]
		maya_seq_pbst_rev_mp4_path = maya_seq_playblast_review_mp4_template.apply_fields(flds)
		
		if not os.path.exists(os.path.dirname(maya_seq_pbst_pbsh_mov_path)):
			os.makedirs(os.path.dirname(maya_seq_pbst_pbsh_mov_path))
		
		if not os.path.exists(os.path.dirname(maya_seq_pbst_rev_mp4_path)):
			os.makedirs(os.path.dirname(maya_seq_pbst_rev_mp4_path))
		"""
			SEQUENCE MOV and MP4 Creation
		"""
		# os.system('%s -start_number "%s" -i "%s" -vcodec libx264  -r 25 "%s" -y' %(ffmpegPath,FirstImageNumber,RenderPath, maya_seq_pbst_pbsh_mov_path ))
		# os.system('%s -start_number "%s" -i "%s" -vcodec libx264  -r 25 "%s" -y' %(ffmpegPath,FirstImageNumber,RenderPath, maya_seq_pbst_rev_mp4_path ))
		print "Making mov and mp4: \n", maya_seq_pbst_pbsh_mov_path, ' --- ', maya_seq_pbst_rev_mp4_path
		print ffmpeg.ffmpegMakingMovie(inputFilePath=RenderPath, outputFilePath=maya_seq_pbst_pbsh_mov_path, audioPath="", start_frame=FirstImageNumber, framerate=24 , encodeOptions='libx264',ffmpegPath=ffmpegPath)
		print ffmpeg.ffmpegMakingMovie(inputFilePath=RenderPath, outputFilePath=maya_seq_pbst_rev_mp4_path, audioPath="", start_frame=FirstImageNumber, framerate=24 , encodeOptions='libx264',ffmpegPath=ffmpegPath)

		
		# if set cam and curve visibility back to original values
		cmds.modelEditor(modPan,e=True, nurbsCurves=crvVis)
		cmds.modelEditor(modPan,e=True, cameras=camVis)
		
		# ----------------------------------------------
		# UPLOAD QUICKTIME
		# ----------------------------------------------	
			
		SERVER_PATH = 'https://rts.shotgunstudio.com'
		SCRIPT_USER = 'AutomateStatus_TD'
		SCRIPT_KEY = '8119086c65905c39a5fd8bb2ad872a9887a60bb955550a8d23ca6c01a4d649fb'

		sg = sgtk.api.shotgun.Shotgun(SERVER_PATH, SCRIPT_USER, SCRIPT_KEY)

		data = {'project': {'type':'Project','id':66},
				'entity': {'type':'Sequence', 'id':int(sequence_id)},
				'code': flds ['Sequence']+"_"+flds['Step']+"_v"+str('%03d' % (flds['version'])),
				'sg_path_to_frames':os.path.dirname(RenderPath),
				'sg_path_to_movie':maya_seq_pbst_pbsh_mov_path
				}

		result = sg.create('Version', data)
		executed = sg.upload("Version",result['id'],maya_seq_pbst_rev_mp4_path,'sg_uploaded_movie')
		print executed
		
		# print "TODO : make mov of whole sequence with audio"
		return results

