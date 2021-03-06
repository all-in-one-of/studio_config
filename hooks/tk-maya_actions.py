# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook that loads defines all the available actions, broken down by publish type. 
"""
import sgtk
import os
import json
import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
# import cProfile

HookBaseClass = sgtk.get_hook_baseclass()

def getNextAvailableNamespace(namespaceBase, startNumber = 1):
    """@brief Return the next available name space.

    @param namespaceBase Base of the namespace. (string) ex:NEMO01
    """
    for i in xrange(startNumber, 10000) :
        newNamespace = "%s_%03d" % (namespaceBase, i)
        if not pm.namespace(exists=newNamespace) :
            return newNamespace

class MayaActions(HookBaseClass):
	
	##############################################################################################################
	# public interface - to be overridden by deriving classes 
	
	def generate_actions(self, sg_publish_data, actions, ui_area):
		"""
		Returns a list of action instances for a particular publish.
		This method is called each time a user clicks a publish somewhere in the UI.
		The data returned from this hook will be used to populate the actions menu for a publish.
	
		The mapping between Publish types and actions are kept in a different place
		(in the configuration) so at the point when this hook is called, the loader app
		has already established *which* actions are appropriate for this object.
		
		The hook should return at least one action for each item passed in via the 
		actions parameter.
		
		This method needs to return detailed data for those actions, in the form of a list
		of dictionaries, each with name, params, caption and description keys.
		
		Because you are operating on a particular publish, you may tailor the output 
		(caption, tooltip etc) to contain custom information suitable for this publish.
		
		The ui_area parameter is a string and indicates where the publish is to be shown. 
		- If it will be shown in the main browsing area, "main" is passed. 
		- If it will be shown in the details area, "details" is passed.
		- If it will be shown in the history area, "history" is passed. 
		
		Please note that it is perfectly possible to create more than one action "instance" for 
		an action! You can for example do scene introspection - if the action passed in 
		is "character_attachment" you may for example scan the scene, figure out all the nodes
		where this object can be attached and return a list of action instances:
		"attach to left hand", "attach to right hand" etc. In this case, when more than 
		one object is returned for an action, use the params key to pass additional 
		data into the run_action hook.
		
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
			Shotgun data representing a publish is passed in and forwarded on to hooks
			to help them determine which actions may be applicable. This data should by convention
			contain at least the following fields:
					 
				"published_file_type",
				"tank_type"
				"name",
				"version_number",
				"image",
				"entity",
				"path",
				"description",
				"task",
				"task.Task.sg_status_list",
				"task.Task.due_date",
				"task.Task.content",
				"created_by",
				"created_at",                     # note: as a unix time stamp
				"version",                        # note: not supported on TankPublishedFile so always None
				"version.Version.sg_status_list", # (also always none for TankPublishedFile)
				"created_by.HumanUser.image"
			
			This ensures consistency for any hooks implemented by users.
		
		:param actions: List of action strings which have been defined in the app configuration.
		:param ui_area: String denoting the UI Area (see above).
		:returns List of dictionaries, each with keys name, params, caption and description
		"""
		app = self.parent
		app.log_debug("Generate actions called for UI element %s. "
					  "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data))
		
		action_instances = []
		
		if "reference" in actions:
			action_instances.append( {"name": "reference", 
									  "params": None,
									  "caption": "Create Reference", 
									  "description": "This will add the item to the scene as a standard reference."} )
									  
		if "referenceWithLocator" in actions:
			action_instances.append( {"name": "reference with locator", 
									  "params": None,
									  "caption": "Create Reference with a locator", 
									  "description": "This will add the item to the scene as a reference under a locator."} )

		if "referenceWithRtsLocator" in actions:
			action_instances.append( {"name": "reference with rtsLocator", 
									  "params": None,
									  "caption": "Create Reference with a rts specific locator", 
									  "description": "This will add the item to the scene as a reference under the custom rts locator."} )

		if "import" in actions:
			action_instances.append( {"name": "import", 
									  "params": None,
									  "caption": "Import into Scene", 
									  "description": "This will import the item into the current scene."} )

		if "importNoNs" in actions:
			action_instances.append( {"name": "import without Namespace", 
									  "params": None,
									  "caption": "Import into Scene without a namespace", 
									  "description": "This will import the item into the current scene without a namespace."} )

		if "openUntitled" in actions:
			action_instances.append( {"name": "open as untitled", 
									  "params": None,
									  "caption": "open the maya file and set it to untitled", 
									  "description": "This will open the publish and rename the scene to untitled, use in empty scenes only."} )

		if "texture_node" in actions:
			action_instances.append( {"name": "texture_node",
									  "params": None, 
									  "caption": "Create Texture Node", 
									  "description": "Creates a file texture node for the selected item.."} )
			
		if "udim_texture_node" in actions:
			# Special case handling for Mari UDIM textures as these currently only load into 
			# Maya 2015 in a nice way!
			if self._get_maya_version() >= 2015:
				action_instances.append( {"name": "udim_texture_node",
										  "params": None, 
										  "caption": "Create Texture Node", 
										  "description": "Creates a file texture node for the selected item.."} )    

		if "poslist_as_references" in actions:
			action_instances.append( {"name": "reference whole list with rtsLocator", 
									  "params": None,
									  "caption": "References from positionlist", 
									  "description": "Create the whole scene based on this positionlist (referenced)."} )

		if "poslist_update_selected" in actions:
			action_instances.append( {"name": "update position of selected locators", 
									  "params": None,
									  "caption": "Update position on selection", 
									  "description": "Reload the position of the selected locators based on this positionlist."} )

		if "poslist_update" in actions:
			action_instances.append( {"name": "update position of locators", 
									  "params": None,
									  "caption": "Update position", 
									  "description": "Reload the position of all the locators based on this positionlist."} )

		return action_instances

	def execute_action(self, name, params, sg_publish_data):
		"""
		Execute a given action. The data sent to this be method will
		represent one of the actions enumerated by the generate_actions method.
		
		:param name: Action name string representing one of the items returned by generate_actions.
		:param params: Params data, as specified by generate_actions.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		:returns: No return value expected.
		"""		
		app = self.parent
		app.log_debug("Execute action called for action %s. "
					  "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data))
		
		# resolve path
		path = self.get_publish_path(sg_publish_data)
		
		if name == "reference":
			self._create_reference(path, sg_publish_data)

		if name == "reference with locator":
			self._create_reference_with_locator(path, sg_publish_data)	

		if name == "reference with rtsLocator":
			self._create_reference_with_rtslocator(path, sg_publish_data)	
			
		if name == "import":
			self._do_import(path, sg_publish_data)
			
		if name == "import without Namespace":
			self._do_importNoNs(path, sg_publish_data)
		
		if name == "texture_node":
			self._create_texture_node(path, sg_publish_data)
			
		if name == "udim_texture_node":
			self._create_udim_texture_node(path, sg_publish_data)
		
		if name == "open as untitled":
			self._do_open_file_as_untitled(path, sg_publish_data)
			
		if name == "reference whole list with rtsLocator":
			self._create_references_from_positionlist(path, sg_publish_data)	
			
		if name == "update position of selected locators":
			self._update_selected_objects_from_positionlist(path, sg_publish_data)	
			
		if name == "update position of locators":
			# cProfile.run('self._update_objects_from_positionlist(path, sg_publish_data)')
			self._update_objects_from_positionlist(path, sg_publish_data)
						
		   
	##############################################################################################################
	# helper methods which can be subclassed in custom hooks to fine tune the behaviour of things
	
	def _create_reference(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""
		
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
		
		# make a name space out of entity name + publish name
		# e.g. bunny_upperbody           
		if self.parent.context.entity != sg_publish_data['entity']:     
			namespace = "%s" % (sg_publish_data.get("entity").get("name"))
			namespace = namespace.replace(" ", "_")
			namespace = getNextAvailableNamespace(namespace)
		elif self.parent.context.entity == sg_publish_data['entity']:
			task = sg_publish_data.get('task')
			if not task:
				raise Exception('no task linked to the published file %s' % (sg_publish_data.get('id')))
			else:
				step = self.parent.shotgun.find_one('Task', [['id','is', task['id'] ]], ['step.Step.short_name'])
				resolution = ''
				import re
				if re.match('.*(High|high|hig|HIGH).*', task.get('name')):
					resolution = 'hir'
				if re.match('.*(Layout|layout|lay).*', task.get('name')):
					resolution = 'lay'
				if re.match('.*(Low|low|LOW).*', task.get('name')):
					resolution = 'low'
				if resolution:
					namespace = "%s_%s" % (resolution, step.get('step.Step.short_name', 'NOTHING_FOUND'))
				else:
					namespace = "%s" %(step.get('step.Step.short_name', 'NOTHING_FOUND'))
				namespace = namespace.replace(" ", "_")
				#namespace = getNextAvailableNamespace(namespace)
				
		pm.system.createReference(path,  loadReferenceDepth= "all", mergeNamespacesOnClash=False, namespace=namespace)
		
	def _create_references_from_positionlist(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""
		self.assetRefList = {}
		print "Started _create_references_from_positionlist"
				
		publish_entity_type = sgtk.util.get_published_file_entity_type(self.parent.tank)
		if publish_entity_type == "PublishedFile":
			self._publish_type_field = "published_file_type"
		else:
			self._publish_type_field = "tank_type"
			
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
			
		# Prefix = sg_publish_data.get("entity")
		IdAsset = sg_publish_data.get("entity").get("id")
		NameAsset = "%s" % (sg_publish_data.get("entity").get("name"))
		TypeAsset = self.parent.shotgun.find_one('Asset', [['id','is', IdAsset ]], ['sg_asset_type'])
		
		poslist = None
		with open(path, 'r') as positionlistFile:
			lines = ""
			readFileLines = positionlistFile.readlines()
			for l in readFileLines:
				lines += l

			poslist = json.loads(lines)
		
		allLocators = cmds.ls(type = "rtsAssetRoot")
		print allLocators
		
		objectTypes = {"SET":"Set", "SUB":"Set", "PRP":"Prop", "CHR":"Character", "VHL":"Vehicle"}
		for type in poslist:
			poslistGroup = poslist[type]
			if type in objectTypes:
				longType = objectTypes[type]
				if longType == "Prop":
					print "Prop Handling"
					for obj in poslistGroup:
						if obj in allLocators:
							print "### %s already in scene! (skip file) ###" %obj
						else:
							newLocator = self.loadObjectInScene(poslistGroup[obj], longType)	
				# elif longType == "Set":
				else:
					print "%s Handling" %longType
					
	def _create_only_locators_from_positionlist(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""
		self.assetRefList = {}
		print "Started _create_references_from_positionlist"
				
		publish_entity_type = sgtk.util.get_published_file_entity_type(self.parent.tank)
		if publish_entity_type == "PublishedFile":
			self._publish_type_field = "published_file_type"
		else:
			self._publish_type_field = "tank_type"
			
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
			
		# Prefix = sg_publish_data.get("entity")
		IdAsset = sg_publish_data.get("entity").get("id")
		NameAsset = "%s" % (sg_publish_data.get("entity").get("name"))
		TypeAsset = self.parent.shotgun.find_one('Asset', [['id','is', IdAsset ]], ['sg_asset_type'])
		
		poslist = None
		with open(path, 'r') as positionlistFile:
			lines = ""
			readFileLines = positionlistFile.readlines()
			for l in readFileLines:
				lines += l

			poslist = json.loads(lines)
		
		objectTypes = {"SET":"Set", "SUB":"Set", "PRP":"Prop", "CHR":"Character", "VHL":"Vehicle"}
		for type in poslist:
			poslistGroup = poslist[type]
			if type in objectTypes:
				longType = objectTypes[type]
				if longType == "Prop":
					print "Prop Handling"
					for obj in poslistGroup:
						newLocator = self.loadObjectInScene(poslistGroup[obj], longType)	
				# elif longType == "Set":
				else:
					print "%s Handling" %longType
					
	def _update_selected_objects_from_positionlist(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""
		print "Started _update_selected_objects_from_positionlist"
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
			
		poslist = None
		with open(path, 'r') as positionlistFile:
			lines = ""
			readFileLines = positionlistFile.readlines()
			for l in readFileLines:
				lines += l

			poslist = json.loads(lines)	
			
		for type in poslist:
			poslistGroup = poslist[type]
			self.updatePosition( poslistGroup ,selectionOnly = True)
			
	def _update_objects_from_positionlist(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""
		print "Started _update_objects_from_positionlist"
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
			
		poslist = None
		with open(path, 'r') as positionlistFile:
			lines = ""
			readFileLines = positionlistFile.readlines()
			for l in readFileLines:
				lines += l

			poslist = json.loads(lines)	
			
		for type in poslist:
			poslistGroup = poslist[type]
			self.updatePosition( poslistGroup ,selectionOnly = False)
			
	def updatePosition(self,  data, selectionOnly = False):
		objectsToUpdate = None
		if selectionOnly:
			objectsToUpdate = cmds.ls(selection = selectionOnly, type = "rtsAssetRoot")
		else:
			objectsToUpdate = cmds.ls(type = "rtsAssetRoot")
			
		print objectsToUpdate
		for o in objectsToUpdate:
			if o in data:
				print "UPDATE :", o
		
	def updatePositionOfObject(self, objectName, data):
		print objectName
		print data
			
	def loadObjectInScene(self, data, type):
		# print data
		# print type
			
		asset = data["asset"]
		if not "id" in asset:
			try:
				fields = ['id', 'code']
				filters = [['code','is',asset]]
				asset = self.parent.sgtk.find("Asset",filters,fields)
			except:
				print "Error in %s" %asset
				return None
		# print asset
		resolution = data['resolution']
		if resolution == None:
			resolution = "lay"
				
		tempObj = self.findAssetPublishData(asset = asset, assetType = type, resolution = resolution)
		if tempObj == None:
			print "Object not made : %s" %asset
			return None
			
		setPosition(tempObj, data['position'], data['rotation'], data['scale'])
			
	def findAssetPublishData(self, asset, assetType, resolution = 'lay'):
		"""
		Load and refresh data.
		
		:param sg_filters: Shotgun filters to use for the search.
		:param child_folders: List of items ('folders') from the tree view. These are to be
							  added to the model in addition to the publishes, so that you get a mix
							  of folders and files.
		"""
		# first figure out which fields to get from shotgun
		publishData = None
				
		assetName = asset["code"]
		if not assetType in self.assetRefList:
			self.assetRefList[assetType]= {}
		
		if not resolution in self.assetRefList[assetType]:
			self.assetRefList[assetType][resolution] = {}

		if assetName in self.assetRefList[assetType][resolution]:
			publishData = self.assetRefList[assetType][resolution][assetName]
		else:			
			publish_filters = [['project', 'is', self.parent.context.project], ['%s.PublishedFileType.code' %self._publish_type_field,'is', 'Maya Scene'],['entity', 'is', asset],['task.Task.sg_short_name', 'is', resolution]]
			
			publish_fields = [self._publish_type_field,
							  "name",
							  "version_number",
							  "image",
							  "entity",
							  "path",
							  "description",
							  "task",
							  "task.Task.sg_status_list",
							  "task.Task.due_date",
							  "project",
							  "task.Task.content",
							  "created_by",
							  "created_at",
							  "version", # note: not supported on TankPublishedFile so always None
							  "version.Version.sg_status_list",
							  "created_by.HumanUser.image"
							  ]

			publishDataList = self.parent.shotgun.find("PublishedFile",publish_filters, publish_fields)

			if publishDataList == None or publishDataList == []:
				publishData = None
			else:
				version_number = -1
				for p in publishDataList:
					if p['version_number'] > version_number:
						version_number = p['version_number']
						publishData = p
			
			self.assetRefList[assetType][resolution][assetName] = publishData
			return None
			
		# load cached data
		locator = None
		if publishData != None:
			try:
				locator = self._create_reference_with_rtslocator(publishData['path']['local_path'], publishData)
			except:
				print "ERROR!ERROR!ERROR!ERROR!ERROR!ERROR!ERROR!ERROR!ERROR!"
		else:
			# createRtsAssetNode()
			print "TODO : Could not create :"
			print asset
			print resolution
			print type
		
		return locator
		
	def _create_reference_with_locator(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""

		# Prefix = sg_publish_data.get("entity")
		IdAsset = sg_publish_data.get("entity").get("id")
		NameAsset = "%s" % (sg_publish_data.get("entity").get("name"))
		TypeAsset = self.parent.shotgun.find_one('Asset', [['id','is', IdAsset ]], ['sg_asset_type'])
		prefix = ""
		if TypeAsset['sg_asset_type'] == 'Character':
			prefix= 'CHR_'
		if TypeAsset['sg_asset_type'] == 'Vehicle':
			prefix= 'VEH_'
		if TypeAsset['sg_asset_type'] == 'Prop':
			prefix= 'PRP_'			
		# Number = 1
		# NameLoc = prefix+NameAsset+'%03d' %(Number)

		# if cmds.objExists(NameLoc):
			# Number += 1
			# NameLoc = prefix+NameAsset+'_%03d' %(Number)
		maxNull=0
		# all = cmds.ls()
		# for i in all:
			# if "Shape" not in i and i.startswith(prefix+NameAsset):
				# numNull = i.split(prefix+NameAsset)[-1]
				# if numNull >= maxNull:
					# maxNull = int(numNull)
		all = cmds.ls(type='locator')
		for i in all:
			if i.startswith((prefix+NameAsset)):
				print "1. Start with %s in %s" %(prefix+NameAsset,i)
				numLoc = i.split((prefix+NameAsset))[-1].replace("Shape","").replace("_","")
				print numLoc
				if int(numLoc) >= maxNull:
					maxNull = int(numLoc)
					print maxNull
			elif i.find((prefix+NameAsset)) != -1:
				print "2. Found name %s in %s" %(prefix+NameAsset,i)
				
		number = maxNull+1
		namespace = NameAsset+'_%03d' %(number)
		NameLoc = prefix+namespace
			
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
		
		# make a name space out of entity name + publish name
		# e.g. bunny_upperbody           
		if self.parent.context.entity != sg_publish_data['entity']:     
			namespace = "%s" % (sg_publish_data.get("entity").get("name"))
			namespace = namespace.replace(" ", "_")
			namespace = getNextAvailableNamespace(namespace, number)
			NameLoc = prefix+namespace
		elif self.parent.context.entity == sg_publish_data['entity']:
			task = sg_publish_data.get('task')
			if not task:
				raise Exception('no task linked to the published file %s' % (sg_publish_data.get('id')))
			else:
				step = self.parent.shotgun.find_one('Task', [['id','is', task['id'] ]], ['step.Step.short_name'])
				resolution = ''
				import re
				if re.match('.*(Layout|layout|lay).*', task.get('name')):
					resolution = 'lay'
				if re.match('.*(High|high|hig|HIGH|hir).*', task.get('name')):
					resolution = 'hir'
				if re.match('.*(Low|low|LOW|lor).*', task.get('name')):
					resolution = 'low'
				if resolution:
					namespace = "%s_%s" % (resolution, step.get('step.Step.short_name', 'NOTHING_FOUND'))
				else:
					namespace = "%s" %(step.get('step.Step.short_name', 'NOTHING_FOUND'))
				namespace = namespace.replace(" ", "_")
				#namespace = getNextAvailableNamespace(namespace)
		
		cmds.spaceLocator(name=NameLoc)
				
		pm.system.createReference(path,  loadReferenceDepth= "all", mergeNamespacesOnClash=False,namespace=namespace ,gr= True, gn= "TMP" )

		for i in cmds.listRelatives("TMP",c=True):
			print i
			try:
				cmds.parent( "TMP|"+i, NameLoc)
			except:
				None
		cmds.delete("TMP")

	def _create_reference_with_rtslocator(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""
		# Prefix = sg_publish_data.get("entity")
		IdAsset = sg_publish_data.get("entity").get("id")
		NameAsset = "%s" % (sg_publish_data.get("entity").get("name"))
		TypeAsset = self.parent.shotgun.find_one('Asset', [['id','is', IdAsset ]], ['sg_asset_type'])
		prefix = ""
		if TypeAsset['sg_asset_type'] == 'Character':
			prefix= 'CHR_'
		if TypeAsset['sg_asset_type'] == 'Vehicle':
			prefix= 'VEH_'
		if TypeAsset['sg_asset_type'] == 'Prop':
			prefix= 'PRP_'			
		# Number = 1
		# NameLoc = prefix+NameAsset+'%03d' %(Number)

		# if cmds.objExists(NameLoc):
			# Number += 1
			# NameLoc = prefix+NameAsset+'_%03d' %(Number)
		maxNull=0
		# all = cmds.ls()
		# for i in all:
			# if "Shape" not in i and i.startswith(prefix+NameAsset):
				# numNull = i.split(prefix+NameAsset)[-1]
				# if numNull >= maxNull:
					# maxNull = int(numNull)
		all = cmds.ls(type="rtsAssetRoot")
		for i in all:
			if i.startswith((prefix+NameAsset)):
				# print "1. Start with %s in %s" %(prefix+NameAsset,i)
				numLoc = i.split((prefix+NameAsset))[-1].replace("Shape","").replace("_","")
				# print numLoc
				if int(numLoc) >= maxNull:
					maxNull = int(numLoc)
					# print maxNull
			elif i.find((prefix+NameAsset)) != -1:
				print "2. Found name %s in %s" %(prefix+NameAsset,i)
				
		number = maxNull+1
		namespace = NameAsset+'_%03d' %(number)
		NameLoc = prefix+namespace
			
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
		
		# make a name space out of entity name + publish name
		# e.g. bunny_upperbody           
		if self.parent.context.entity != sg_publish_data['entity']:     
			namespace = "%s" % (sg_publish_data.get("entity").get("name"))
			namespace = namespace.replace(" ", "_")
			namespace = getNextAvailableNamespace(namespace, number)
			NameLoc = prefix+namespace
		elif self.parent.context.entity == sg_publish_data['entity']:
			task = sg_publish_data.get('task')
			if not task:
				raise Exception('no task linked to the published file %s' % (sg_publish_data.get('id')))
			else:
				step = self.parent.shotgun.find_one('Task', [['id','is', task['id'] ]], ['step.Step.short_name'])
				resolution = ''
				import re
				if re.match('.*(Layout|layout|lay).*', task.get('name')):
					resolution = 'lay'
				if re.match('.*(High|high|hig|HIGH|hir).*', task.get('name')):
					resolution = 'hir'
				if re.match('.*(Low|low|LOW|lor).*', task.get('name')):
					resolution = 'low'
				if resolution:
					namespace = "%s_%s" % (resolution, step.get('step.Step.short_name', 'NOTHING_FOUND'))
				else:
					namespace = "%s" %(step.get('step.Step.short_name', 'NOTHING_FOUND'))
				namespace = namespace.replace(" ", "_")
				#namespace = getNextAvailableNamespace(namespace)
		
		# # cmds.createNode("rtsAssetRoot", name = NameLoc)
		locator = createRtsAssetNode(NameLoc, sg_publish_data)	
		
		pm.system.createReference(path,  loadReferenceDepth= "all", mergeNamespacesOnClash=False,namespace=namespace ,gr= True, gn= "TMP" )

		for i in cmds.listRelatives("TMP",c=True):
			print i
			try:
				cmds.parent( "TMP|"+i, locator)
			except:
				None
		cmds.delete("TMP")
		
		return locator

	def _do_import(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
				
		# make a name space out of entity name + publish name
		# e.g. bunny_upperbody                
		namespace = "%s %s" % (sg_publish_data.get("entity").get("name"), sg_publish_data.get("name"))
		namespace = namespace.replace(" ", "_")
		
		# perform a more or less standard maya import, putting all nodes brought in into a specific namespace
		cmds.file(path, i=True, renameAll=True, namespace=namespace, loadReferenceDepth="all", preserveReferences=True)
			
	def _do_importNoNs(self, path, sg_publish_data):
		"""
		Create a reference with the same settings Maya would use
		if you used the create settings dialog.
		
		:param path: Path to file.
		:param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
		"""
		if not os.path.exists(path):
			raise Exception("File not found on disk - '%s'" % path)
		# perform a more or less standard maya import, putting all nodes brought in into a specific namespace
		cmds.file(path, i=True, loadReferenceDepth="all", preserveReferences=True)

	def _do_open_file_as_untitled(self, path, sg_publish_data):
		"""
		opens the path and sets the session to untitled
		the maya callback is paused to not loose context
		"""
		#stop the watcher for a second, or else he will pick up the load and switch to layout
		engine = sgtk.platform.current_engine() 
		engine._MayaEngine__watcher.stop_watching()

		pm.cmds.file(path, open = True, force = True)
		pm.cmds.file(rename = "untitled")
		pm.cmds.file(rts = 1)	 

		# set scene settings
		defaultResolution = pm.PyNode("defaultResolution")
		defaultResolution.width.set(1725)
		defaultResolution.height.set(936)
		defaultResolution.deviceAspectRatio.set(1725.0/936.0)

		#start the watcher again
		engine._MayaEngine__watcher.start_watching()

	def _create_texture_node(self, path, sg_publish_data):
		"""
		Create a file texture node for a texture
		
		:param path:             Path to file.
		:param sg_publish_data:  Shotgun data dictionary with all the standard publish fields.
		:returns:                The newly created file node
		"""
		file_node = cmds.shadingNode('file', asTexture=True)
		cmds.setAttr( "%s.fileTextureName" % file_node, path, type="string" )
		return file_node

	def _create_udim_texture_node(self, path, sg_publish_data):
		"""
		Create a file texture node for a UDIM (Mari) texture
		
		:param path:             Path to file.
		:param sg_publish_data:  Shotgun data dictionary with all the standard publish fields.
		:returns:                The newly created file node
		"""
		# create the normal file node:
		file_node = self._create_texture_node(path, sg_publish_data)
		if file_node:
			# path is a UDIM sequence so set the uv tiling mode to 3 ('UDIM (Mari)')
			cmds.setAttr("%s.uvTilingMode" % file_node, 3)
			# and generate a preview:
			mel.eval("generateUvTilePreview %s" % file_node)
		return file_node
			
	def _get_maya_version(self):
		"""
		Determine and return the Maya version as an integer
		
		:returns:    The Maya major version
		"""
		if not hasattr(self, "_maya_major_version"):
			self._maya_major_version = 0
			# get the maya version string:
			maya_ver = cmds.about(version=True)
			# handle a couple of different formats: 'Maya XXXX' & 'XXXX':
			if maya_ver.startswith("Maya "):
				maya_ver = maya_ver[5:]
			# strip of any extra stuff including decimals:
			major_version_number_str = maya_ver.split(" ")[0].split(".")[0]
			if major_version_number_str and major_version_number_str.isdigit():
				self._maya_major_version = int(major_version_number_str)
		return self._maya_major_version
		
		
def setPosition(objName, pos, rot, scl):
	cmds.setAttr("%s.translateX" %objName, pos[0])
	cmds.setAttr("%s.translateY" %objName, pos[1])
	cmds.setAttr("%s.translateZ" %objName, pos[2])
	
	cmds.setAttr("%s.rotateX" %objName, rot[0])
	cmds.setAttr("%s.rotateY" %objName, rot[1])
	cmds.setAttr("%s.rotateZ" %objName, rot[2])
	
	cmds.setAttr("%s.scaleX" %objName, scl[0])
	cmds.setAttr("%s.scaleY" %objName, scl[1])
	cmds.setAttr("%s.scaleZ" %objName, scl[2])

def createRtsAssetNode(name, publishData = None):
	rtsLocator = cmds.createNode("rtsAssetRoot", name = name)
	cmds.setAttr("%s.displayHandle"%rtsLocator, True)
	
	cmds.addAttr(rtsLocator, shortName='aid', longName='asset_id', at = "long" )
	cmds.addAttr(rtsLocator, shortName='ass', longName='asset_name', dt = "string" )
	cmds.addAttr(rtsLocator, shortName='pid', longName='publish_id', at = "long" )
	cmds.addAttr(rtsLocator, shortName='pub', longName='publish_path', dt = "string" )
	# cmds.addAttr(rtsLocator, shortName='typ', longName='type', dt = "string" )
	# cmds.addAttr(rtsLocator, shortName='stp', longName='step', dt = "string" )
	cmds.addAttr(rtsLocator, shortName='tsk', longName='task', dt = "string" )
	# cmds.addAttr(rtsLocator, shortName='ver', longName='version', at = "long" )
	cmds.addAttr(rtsLocator, shortName='org', longName='origin', dt = "string" )
	cmds.addAttr(rtsLocator, shortName='vis', longName='visible', at = "bool" )
	
	if publishData != None:
		setRtsAssetNode(rtsLocator, publishData)
	
	return rtsLocator
	
def setRtsAssetNode(name, publishData):
	"""
		"published_file_type",
		"tank_type"
		"name",
		"version_number",
		"image",
		"entity",
		"path",
		"description",
		"task",
		"task.Task.sg_status_list",
		"task.Task.due_date",
		"task.Task.content",
		"created_by",
		"created_at",                     # note: as a unix time stamp
		"version",                        # note: not supported on TankPublishedFile so always None
		"version.Version.sg_status_list", # (also always none for TankPublishedFile)
		"created_by.HumanUser.image"
	"""
	
	print publishData
	cmds.setAttr("%s.asset_id"%name,publishData["entity"]["id"])
	cmds.setAttr("%s.asset_name"%name, publishData["name"],  type = "string")
	cmds.setAttr("%s.publish_id"%name,publishData["id"])
	cmds.setAttr("%s.publish_path"%name, publishData["path"]["local_path"],  type = "string")
	cmds.setAttr("%s.task"%name, publishData["task"],  type = "string")
	# cmds.setAttr("%s.version"%name, publishData["version_number"])
	# cmds.setAttr("%s.step"%name, publishData[""],  type = "string")
	# cmds.setAttr("%s.origin"%name, publishData[""],  type = "string")
	# cmds.setAttr("%s.visible"%name, publishData["visible"])
	# cmds.setAttr("%s.type"%name, publishData["tank_type"],  type = "string")
	return name
