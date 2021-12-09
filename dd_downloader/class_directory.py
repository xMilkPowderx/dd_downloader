from importlib.util import spec_from_file_location, module_from_spec
import pathlib, os

found = False

scanner_types = {}

"""
Returns a dictionary containing references to all of the loaded Scanner classes. Used when the user would like to create a new scanner, and a list of choices needs to be presented.
"""
def get_scanner_types():
	if (not found):
		load()
	return scanner_types

"""
The purpose of load() is to dynamically load all modules inside the scanner_types directory. This ensures that the Scanner and Scan model objects are recognized by Django, and get initialized in the database.
"""
def load():
	global found
	current_dir = str(pathlib.Path(__file__).resolve().parent)
	scanner_types_dir = os.path.join(current_dir, 'scanner_types')
	for scanner_name in os.listdir(scanner_types_dir):
		# Only check inside sub-folders, for files that are the same name as the sub-folder's name.
		scanner_dir = os.path.join(scanner_types_dir, scanner_name)
		if os.path.isdir(scanner_dir):
			try:
				path = os.path.join(scanner_dir,scanner_name+'.py')
				spec = spec_from_file_location(scanner_name, path)
				module = module_from_spec(spec)
				spec.loader.exec_module(module)

				scanner_types[scanner_name] = {
					'scanner': getattr(module,scanner_name+'_Scanner'),
					'scan': getattr(module,scanner_name+'_Scan'),
				}
			except Exception as e:
				print(f"Couldn't load module {scanner_name} at {scanner_dir}")
	found = True
	print('Dynamic classes finished loading!')
