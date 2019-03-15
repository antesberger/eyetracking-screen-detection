import os
import sys
import csv

if len(sys.argv) != 2:
    print("Please provide the overall directory name as an argument")
    sys.exit(0)
else:
    directory = sys.argv[1]

for filename in os.listdir(directory):
    print(filename)

    currentLastRow = ''
    if filename != ".DS_Store":
        try:
            with open(directory + "/" + filename + '/out/log.csv', mode='r') as csvinput:
                csv_reader = csv.reader(csvinput, delimiter=',')

                for row in csv_reader:
                    currentLastRow = row

                with open(directory + '/overview.csv', mode='a') as csvoutput:
                    csv_writer = csv.writer(csvoutput, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    csv_writer.writerow([filename, currentLastRow[0], currentLastRow[1], currentLastRow[2], currentLastRow[3], currentLastRow[4], currentLastRow[5], currentLastRow[6], currentLastRow[7]])

        except:
            pass
