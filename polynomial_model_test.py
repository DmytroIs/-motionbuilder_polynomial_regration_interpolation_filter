import numpy as np
import csv

#reading testcase into a list of tuples from .csv
filename = "C:/Users/dmitr/Desktop/plnm_test.csv"  
output_filename = "C:/Users/dmitr/Desktop/plnm_test_calc.csv" 
data = []

with open(filename, "r") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        data.append(row)

#converting list of strings into float arrays
array_t, array_x = [float(x) for x, y in data], [float(y) for x, y in data]

#GETTING POLYNOMIAL REGRESSION COEFS TO DEGREE 4
coefs = np.polyfit(array_t, array_x, 4)

#calculated aproximated values by polynomial model
def calculate_polynomial(coefs, y):
    x = 0
    n = len(coefs)
    for i in range(n):
        x += coefs[i] * y ** (n-i-1)
    return x

array_x1 = []
for t in array_t :
    array_x1.append (calculate_polynomial(coefs,t))
    
#writing aproximated values into another .csv for desmos tests
aprx_data = zip (array_t, array_x1)

with open(output_filename, 'w', newline='') as file:
    writer = csv.writer(file)

    # Write each row to the CSV file
    for row in aprx_data:
        writer.writerow(row)
