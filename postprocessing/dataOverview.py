import os
import sys
import csv

if len(sys.argv) != 2:
    print("Please provide the overall directory name as an argument")
    sys.exit(0)
else:
    directory = sys.argv[1]

fileCount = 0
errorRates = []
problemRates = []
accuracies = []

for filename in os.listdir(directory):

    currentLastRow = ''
    if filename != ".DS_Store":
        try:
            with open(directory + "/" + filename + '/out/log.csv', mode='r') as csvinput:
                csv_reader = csv.reader(csvinput, delimiter=',')
                fileCount += 1

                for row in csv_reader:
                    currentLastRow = row

                errorRates.append(currentLastRow[4])
                problemRates.append(currentLastRow[7])

        except:
            pass

    if 'Acc' in filename:
        with open(directory + "/" + filename + '/out/accuracy.csv', mode='r') as csvinput:
            csv_reader = csv.reader(csvinput, delimiter=',')

            for row in csv_reader:
                currentLastRow = row

            accuracies.append(currentLastRow[9])


avgErrorRate = reduce(lambda x, y: float(x) + float(y), errorRates) / len(errorRates)
avgProblemRate = reduce(lambda x, y: float(x) + float(y), problemRates) / len(problemRates)
avgAccuracy = reduce(lambda x, y: float(x) + float(y), accuracies) / len(accuracies)

with open(directory + '/overview.csv', mode='a') as csvoutput:
    csv_writer = csv.writer(csvoutput, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(['Participant Count', 'Avg error rate', 'Avg problem rate', 'Avg gaze deviation (degree)'])
    csv_writer.writerow([fileCount/4,avgErrorRate, avgProblemRate, avgAccuracy])
