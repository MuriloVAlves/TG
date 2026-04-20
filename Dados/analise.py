import matplotlib.pyplot as plt
import pandas as pd
import os

# Get data files
dataDocuments = []
for k in os.listdir('./'):
    if ".txt" in k:
        dataDocuments.append(k)

# Split values
crescentData = []
decrescentData = []
for doc in dataDocuments:
    firstLine = True
    with open(f'./{doc}','r') as file:
        for sentidoCD in range(2):
            xData = []
            yData = []
            line = file.readline()
            dataBlock = line.split(';')[:-1]
            for d in dataBlock:
                usefulData = d.replace('PWM: ','').replace('RPM: ','').split(' | ')
                xData.append(float(usefulData[0]))
                yData.append(float(usefulData[1]))
            if firstLine:
                crescentData.append([xData,yData])
            else:
                decrescentData.append([xData,yData])
            firstLine = False

# Plot all graphs
for i in range(2):
    if i == 0:
        data = crescentData
        graphTitle = "Curva RPM X DC Sentido Crescente"
        tableName = "_CRESC"
    else:
        data = decrescentData
        graphTitle = "Curva RPM X DC Sentido Decrescente"
        tableName = "_DECRESC"
    for i in range(len(data)):
        plt.plot(data[i][0],data[i][1],label=dataDocuments[i].replace('.txt','').replace('_',' '))
        df = pd.DataFrame(list(zip(data[i][0], data[i][1])), columns=['PWM', 'RPM'])
        df.to_excel(f"./CONVERSAO_{dataDocuments[i].replace('.txt','')+tableName}.xlsx")
    # Contagem de índices de motores
    plt.grid(visible=True)
    plt.legend()
    plt.title(graphTitle)
    plt.show()