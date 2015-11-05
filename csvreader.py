import csv

with open('PlantData.csv', "rU") as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		print(row['TREE_SpeciesCommonName'],row['TREE_SpeciesLatinName'], row['x'], row['y'])
