import argparse
import os
import json
import copy

parser = argparse.ArgumentParser()
parser.add_argument('filepath', metavar = 'F', type = str, nargs = 1, help = 'File path of Rust code') 
args = parser.parse_args()

storageJSONFileName = './content.json'

try:
	rustFilePath = str(*args.filepath)
	errorCode = os.system(f'rustc -Z ast-json {rustFilePath} > {storageJSONFileName}')
	
	if errorCode != 0:
		raise

	file = open(storageJSONFileName, 'r')

	parseTree = json.loads(file.read())

	os.system(f'rm {storageJSONFileName}')

	file = open(rustFilePath, 'r')
	rustContent = file.read()
	rustContentList = rustContent.split('\n')

except:
	raise OSError

class UnsafeNotification:

	# Returns spanning line and line content in a tuple
	def computeSpanningLine(self):
		tempLo = self.lo
		for i in range(len(rustContentList)):

			if tempLo > len(rustContentList[i]):
				tempLo -= (len(rustContentList[i]) + 1) # This 1 is for the newline character

			else:
				return i+1


class UnsafeTrigger(UnsafeNotification):
	'''
	Error Types :
	(1) Union field accessing
	(2) Dereferencing raw pointer
	(3) Called an external script
	(4) Read or wrote to static mutable
	'''
	def __init__(self, errorType, wasSafelyAccessed, lo, hi):

		errorDefinitionDict = {1: 'Union field accessing', 2: 'Raw pointer dereferencing', 3: 'External Script Call', 4: 'Static Mutable R/W', 5: 'Unsafe Function Call'}

		self.errorDefinition = errorDefinitionDict[errorType]
		self.wasSafelyAccessed = wasSafelyAccessed
		self.lo = lo
		self.hi = hi


	def __repr__(self):
		lineNumber = self.computeSpanningLine()
		prefix = 'Declared || ' if self.wasSafelyAccessed else 'Undeclared || '
		return f'{prefix} {self.errorDefinition} on line {lineNumber}:\n\t{rustContentList[lineNumber-1]}'

	__str__ = __repr__



class UnsafetyMarker(UnsafeNotification):

	def __init__(self, lo = None, hi = None):
		self.lo = lo
		self.hi = hi

	def __repr__(self):

		lineNumber = self.computeSpanningLine()
		return f'Unnecessary unsafety declaration starting on line {lineNumber}:\n\t{rustContentList[lineNumber-1]}'

	__str__ = __repr__



class Literal:
	def __init__(self):
		pass

	def __repr__(self):
		return 'Lit'

	__str__ = __repr__

class Union:
	def __init__(self, fields):
		self.fields = fields

	def __repr__(self):
		return f'|{self.fields}|'

	__str__ = __repr__

class Struct:
	def __init__(self, fields):
		parsedFields = {}
		i = 0
		while i < len(fields):
			parsedFields.update({fields[i]: fields[i+1]})
			i += 2

		self.fields = parsedFields

	def __repr__(self):
		return f'/{self.fields}/'

	__str__ = __repr__

class RawPointer:
	def __init__(self, pointingTo):
		self.pointingTo = pointingTo

	def __repr__(self):
		return f'>{self.pointingTo}<'

	__str__ = __repr__	


class Static:
	def __init__(self, content, isMutable):
		self.content = content
		self.isMutable = isMutable

	def __repr__(self):
		mutability = "Mut" if self.isMutable else "Immut"
		return f'>{mutability}: {self.content}<'

	__str__ = __repr__	


# Outdated
def reduceParseTree(tree):
	if isinstance(tree, dict):
		for elem in ['span', 'id', 'suffix', 'tokens', 'is_placeholder', 'vis', 'attrs']:
			if elem in tree.keys():
				del tree[elem]

		for key in tree.keys():
			reduceParseTree(tree[key])

	elif isinstance(tree, list):
		for i in range(len(tree)):
			reduceParseTree(tree[i])


def computeSafety(tree):

	innerParseTree = tree['module']['items']

	globalVariables = {}

	# Check if is a static macro declaration
	treeIndex = 2
	while True:

		tempInnerTree = innerParseTree[treeIndex]['kind']['fields']

		# Static constant
		if 'Not' in tempInnerTree:
			staticName = innerParseTree[treeIndex]['ident']['name']
			globalVariables[staticName] = Static(Literal(), False)

		# Static mutable
		elif 'Mut' in tempInnerTree:
			staticName = innerParseTree[treeIndex]['ident']['name']
			globalVariables[staticName] = Static(Literal(), True)

		else:
			break

		treeIndex += 1

	unsafeFunctions = set()

	for indivFuncTree in innerParseTree[treeIndex: len(innerParseTree)]:
		funcName = indivFuncTree['ident']['name']

		# Add all names of unsafe functions to unsafeFunctions set
		if indivFuncTree['kind']['fields'][1]['header']['unsafety'] != 'No': 
			unsafeFunctions.add(funcName)

	for indivFuncTree in innerParseTree[treeIndex: len(innerParseTree)]:

		funcName = indivFuncTree['ident']['name']

		isDeclaredUnsafe = funcName in unsafeFunctions
		currFuncParser = FunctionParser(indivFuncTree, isDeclaredUnsafe, globalVariables, unsafeFunctions)
		output = currFuncParser.isFunctionSafe()

		print(f'Function "{funcName}": \n')

		if output:
			for block in output:
				for line in block:
					print(f'\t{line}\n\n')

		else:
			print('\tNo unsafe usage detected\n\n')


class FunctionParser:
	typeToError = {Union: 1, RawPointer: 2, Static: 4}

	def __init__(self, funcTree, isDeclaredUnsafe, globalVariables, unsafeFunctions):
		self.declaredDataTypes = {}

		self.variables = globalVariables
		self.functionDeclaredUnsafe = isDeclaredUnsafe
		self.unsafeFunctions = unsafeFunctions

		self.funcTree = funcTree

		self.characterRange = None
		self.unsafeReferenceOccurredInBranch = False


	# If variant = semi -> Function call
	# 			 = local -> variable assignment
	#			 = Item -> Declaration
	#			 = Call -> Function argument

	def recDrill(self, subTree, isDeclaredUnsafe = False, declaredUnsafeInCurrentLevel = False):
		if subTree:
			if isinstance(subTree, dict):

				keys = list(subTree.keys())

				currKey = keys[0]
				for specialCase in ['span', 'rules', 'variant']:
					if specialCase in keys:
						currKey = specialCase
						break
				
				drilledTree = subTree[currKey]

				del subTree[currKey]

				if len(keys) == 1 and declaredUnsafeInCurrentLevel and not self.unsafeReferenceOccurredInBranch:
					unsafeDeclarationInSafeBlockError = [UnsafetyMarker(*self.characterRange)] 
				
				else:
					unsafeDeclarationInSafeBlockError = []
				
				if currKey == 'span':
					self.characterRange = (drilledTree['lo'], drilledTree['hi'])

				elif currKey == 'rules':
					if 'variant' in drilledTree and drilledTree['variant'] == 'Unsafe':
						return self.recDrill(subTree, True, True)

				elif currKey == 'variant':
						
					# Data type declaration
					if drilledTree == 'Item':

						newDataType = self.parseDeclaration(subTree)

						if newDataType[1] == 'Union':
							self.declaredDataTypes[newDataType[0]] = Union(newDataType[2::2])

						elif newDataType[1] == 'Struct':
							self.declaredDataTypes[newDataType[0]] = Struct(newDataType[2:])

						# An unsafe foreign script is being called
						elif 'ForeignMod' in newDataType:	
							self.unsafeReferenceOccurredInBranch = True

							return errorReturn(isDeclaredUnsafe, 3, *self.characterRange)


						# Static variable is being defined
						elif newDataType[1] == 'Static':
							self.variables[newDataType[0]] = Static(newDataType[2], True if newDataType[-1] == 'Mut' else False)


					# Variable assignment
					elif drilledTree == 'Local' or drilledTree == 'Assign':
						temp = copy.deepcopy(subTree)
						content = self.parseAssignment(subTree)

						# If len(content) == 1, variable has been assigned to a literal
						if len(content) == 1:

							# Check if writing to a static mutable
							if content[0] in self.variables:
								value = self.variables[content[0]]

								if isinstance(value, Static) and value.isMutable:
								
									self.unsafeReferenceOccurredInBranch = True
									return errorReturn(isDeclaredUnsafe, 4, *self.characterRange)

							self.variables[content[0]] = Literal()

						else:
							# Checks if statement is instantation or assignment
							isInstantiation = self.isInstantiation(temp)

							if isInstantiation:
								variableName, customDataType, *parameters = content

								# Pushes tags like 'Ptr' and 'Deref' to the end of content
								moveKeyworkToBack(content)
								actualValue = self.isIndexingSafe(content, datatype = customDataType)


							else:
								variableName, *parameters = content

								# Pushes tags like 'Ptr' and 'Deref' to the end of content
								moveKeyworkToBack(content)
								actualValue = self.isIndexingSafe(content)


							# Indexing has been revealed as unsafe
							if actualValue in self.typeToError:

								self.unsafeReferenceOccurredInBranch = True
								return errorReturn(isDeclaredUnsafe, self.typeToError[actualValue], *self.characterRange)


							if isInstantiation:

								assignmentType = self.declaredDataTypes[customDataType]
								self.variables[variableName] = self.declaredDataTypes[customDataType]


							else:

								# Raw pointer assignment
								if content[-1] == 'Ptr':
									self.variables[variableName] = RawPointer(actualValue)

								else:
									# Assignment is properly indexed into, so assign variable
									self.variables[variableName] = actualValue


					# Function call has been made
					elif drilledTree == 'Call':
						funcName, *content = self.parseFunctionArguments(subTree)

						# Check if function is unsafe
						if funcName in self.unsafeFunctions:
							self.unsafeReferenceOccurredInBranch = True
							return errorReturn(isDeclaredUnsafe, 5, *self.characterRange)


						# Function name is the first argument
						splitList = splitContent(content, self.variables)

						# Check each argument and ensure they are properly indexed into
						for argumentList in splitList:
							actualValue = self.isIndexingSafe(argumentList)

							if actualValue in self.typeToError:

								self.unsafeReferenceOccurredInBranch = True
								return errorReturn(isDeclaredUnsafe, self.typeToError[actualValue], *self.characterRange)



				return self.recDrill(drilledTree, isDeclaredUnsafe) + self.recDrill(subTree, isDeclaredUnsafe, declaredUnsafeInCurrentLevel) + unsafeDeclarationInSafeBlockError

			elif isinstance(subTree, list):

				return self.recDrill(subTree[0], isDeclaredUnsafe) + self.recDrill(subTree[1:], isDeclaredUnsafe)

		return []


	# Checks safety of forward indexing into a variable
	# Returns tuple of (content accessed, if was accessed safely)
	# Unsafely accessed content should be the datatype of its cause
	def isIndexingSafe(self, content, datatype = None,):
		currentVariable = content[0] 

		# Assignment
		if not datatype:

			for parsingItem in content:

				# Check type of assignment variable
				if parsingItem in self.variables:

					currentVariable = self.variables[parsingItem]

					if isinstance(currentVariable, Static) and currentVariable.isMutable:
						return Static


				# IDK what this block does...
				elif parsingItem in self.declaredDataTypes:
					currentVariable = self.declaredDataTypes[parsingItem]


				elif isinstance(currentVariable, Struct):
					currentVariable = currentVariable.fields[parsingItem] 
					if currentVariable in self.declaredDataTypes:
						currentVariable = self.declaredDataTypes[currentVariable]

				# If code enters here, union is being accessed
				elif isinstance(currentVariable, Union) and parsingItem in currentVariable.fields:
					return Union

				# If code enters here, rawpointer is being dereferenced
				elif parsingItem == 'Deref':
					return RawPointer

			return currentVariable


		# Instantation
		else:

			for parsingItem in content:

				if parsingItem in self.declaredDataTypes[datatype].fields:
					pass

				# Check type of assignment variable
				elif parsingItem in self.variables:

					currentVariable = self.variables[parsingItem]

					if isinstance(currentVariable, Static) and currentVariable.isMutable:
						return Static


				elif isinstance(currentVariable, Union) and parsingItem in currentVariable.fields:
					return Union

				# If code enters here, rawpointer is being dereferenced
				elif parsingItem == 'Deref':
					return RawPointer

				else:
					currentVariable = parsingItem

			return None





	# Will return information about declaration in the form 
	# [custom name of data type, Formal data type, first parameter name, first parameter type, second & etc]
	def parseDeclaration(self, subTree, variantFound = False):
		if subTree:
			if isinstance(subTree, dict):

				keys = list(subTree.keys())
				currKey = keys[0]

				for specialCase in ['variant', 'indent']:
					if specialCase in keys:
						currKey = specialCase
						break

				drilledTree = subTree[currKey]
				del subTree[currKey]

				if currKey == 'variant' and not variantFound:
					return [drilledTree] + self.parseDeclaration(subTree, True)
				elif currKey == 'ident':
					return [drilledTree['name']] + self.parseDeclaration(subTree, variantFound)

				return self.parseDeclaration(drilledTree, variantFound) + self.parseDeclaration(subTree, variantFound)

			elif isinstance(subTree, list):
				return self.parseDeclaration(subTree[0], variantFound) + self.parseDeclaration(subTree[1:], variantFound)

			# Pull out the mutability
			elif isinstance(subTree, str) and subTree == "Mut":
				return ['Mut'] 

		return []


	# Will return information about assignment in the form 
	# [variable name, custom name of data type, parameter input]
	def parseAssignment(self, subTree):
		if subTree:
			if isinstance(subTree, dict):

				keys = list(subTree.keys())
				currKey = keys[0]

				for specialCase in ['name']:
					if specialCase in keys:
						currKey = specialCase
						break

				drilledTree = subTree[currKey]
				del subTree[currKey]

				if currKey == 'name':
					return [drilledTree] + self.parseAssignment(subTree)

				# Pull out the pointers
				elif currKey == 'variant' and drilledTree == 'Ptr':
					return ['Ptr']

				return self.parseAssignment(drilledTree) + self.parseAssignment(subTree)

			elif isinstance(subTree, list):
				return self.parseAssignment(subTree[0]) + self.parseAssignment(subTree[1:])

			# Pull out the dereferencing
			elif isinstance(subTree, str) and subTree == "Deref":
				return ['Deref'] 

		return []

	# Pulls out function arguments in a list for further inspection
	def parseFunctionArguments(self, subTree):
		if subTree:
			if isinstance(subTree, dict):

				keys = list(subTree.keys())
				currKey = keys[0]

				for specialCase in ['name']:
					if specialCase in keys:
						currKey = specialCase
						break

				drilledTree = subTree[currKey]
				del subTree[currKey]

				if currKey == 'name':
					return [drilledTree] + self.parseFunctionArguments(subTree)

				return self.parseFunctionArguments(drilledTree) + self.parseFunctionArguments(subTree)

			elif isinstance(subTree, list):
				return self.parseFunctionArguments(subTree[0]) + self.parseFunctionArguments(subTree[1:])

			# Pull out the dereferencing
			elif isinstance(subTree, str) and subTree == "Deref":
				return ['Deref'] 

		return []		


	# Tells if a line is an instantation of an data type or rather just a plain assignment
	def isInstantiation(self, subTree):
		if subTree:
			if isinstance(subTree, dict):

				keys = list(subTree.keys())
				currKey = keys[0]

				drilledTree = subTree[currKey]
				del subTree[currKey]

				if currKey == 'name':
					if isinstance(drilledTree, str) and drilledTree in self.declaredDataTypes:
						return True

				return self.isInstantiation(drilledTree) or self.isInstantiation(subTree)

			elif isinstance(subTree, list):
				return self.isInstantiation(subTree[0]) or self.isInstantiation(subTree[1:])

		return False

	
	# Scans each function using recDrill to find all safety violations made. Returns each violation in a list.
	def isFunctionSafe(self):
		functionSafetyObservations = []

		for topLevelCodeTree in self.funcTree['kind']['fields'][3]['stmts']:
			self.unsafeReferenceOccurredInBranch = False

			if (observationMade := self.recDrill(topLevelCodeTree, self.functionDeclaredUnsafe)):
				functionSafetyObservations.append(observationMade)

		return functionSafetyObservations


# Dissects a list into sublists, split between each word in a dictionary
def splitContent(content, variableDict):
	splitList = []
	currentIter = []
	for element in content:
		if element in variableDict and currentIter:
			splitList.append(currentIter)
			currentIter = []

		currentIter.append(element)
	
	if currentIter:
		splitList.append(currentIter)

	return splitList

# Scans list for keywords and places them at the end of the list
def moveKeyworkToBack(inputList):
	keywords = ['Deref', 'Ptr']

	iterations = len(inputList)
	i = 0

	while i < iterations:
		if inputList[i] in keywords:
			inputList.append(inputList.pop(i))
			iterations -= 1
		
		else:
			i += 1

	return inputList

def errorReturn(isDeclaredUnsafe, errorType, lo, hi):
	return [UnsafeTrigger(errorType, isDeclaredUnsafe, lo, hi)]

computeSafety(parseTree)


