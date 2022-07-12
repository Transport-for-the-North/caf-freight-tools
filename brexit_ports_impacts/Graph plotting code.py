import pandas as pd
from matplotlib import pyplot as plt


#Importing the large data set containing information from 2015-2020 which came from 
#PORT0400(https://www.gov.uk/government/statistical-data-sets/port-and-domestic-waterborne-freight-statistics-port)
path = r'Y:\Freight\18. Brexit impacts on freight\2. Port0400\Data from PORT0400 from 2015-2020.xlsx'
#Reading in the imported  data
data = pd.read_excel(path)

#Some of the data isn't useful to me at this point so I've removed it. (cargo code and cargo name)
usefuldata = data[['Port', 'Year', 'Region', 'Direction', 'Value (Thousands)']]



#Splitting up the data even more into 6 different data sets so that i can use the data  to plot graphs  later
#Only interested in the Data from EU and Non-EU sources as the goal is to find  how  brexit affected these
#The process is the same for all 6 data sets so only the first has been commented.


#Inward EU data
eu_in = usefuldata[(usefuldata['Direction'] == 'Inwards')  & (usefuldata['Region'] == 
                                                             'European Union traffic')]
#Splitting the data up just into the important data  this being port year and value
eu_in1 = eu_in[['Port','Year','Value (Thousands)']]
#Now that I have only the important data  I need to group up all data from each port in the same year data up 
#, sum the values and then finally plot the results. As the results together were hard to interpret  I plotted
# all of the ports individually so that individual trends could be seen.
eu_in_grouped = eu_in1.groupby('Port')

for key, group in eu_in_grouped:
    plt.figure()
    plt.title('Total Tonnage into the UK from the EU from 2015 to 2020')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("Inward EU graphs/{}.png".format(key))
    


#Outward EU data
eu_out = usefuldata[(usefuldata['Direction'] == 'Outwards')  & (usefuldata['Region'] == 
                                                               'European Union traffic')]
eu_out1 = eu_out[['Port','Year','Value (Thousands)']]
eu_out_grouped = eu_out1.groupby('Port')

for key, group in eu_out_grouped:
    plt.figure()
    plt.title('Total Tonnage out of the UK from the EU from 2015 to 2020')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("Outward EU graphs/{}.png".format(key))
 




#Inward Non EU data
non_eu_in = usefuldata[(usefuldata['Direction'] == 'Inwards')  & (usefuldata['Region'] == 
                                                                'Non-EU Foreign traffic')]
non_eu_in1 = non_eu_in[['Port','Year','Value (Thousands)']]
non_eu_in_grouped = non_eu_in1.groupby('Port')

for key, group in non_eu_in_grouped:
    plt.figure()
    plt.title('Total Tonnage into the UK from Non EU Countries from 2015 to 2020')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("Inward Non EU graphs/{}.png".format(key))



#Outward Non EU data
non_eu_out = usefuldata[(usefuldata['Direction'] == 'Outwards')  & (usefuldata['Region'] == 
                                                                  'Non-EU Foreign traffic')]
non_eu_out1 = non_eu_out[['Port','Year','Value (Thousands)']]
non_eu_out_grouped = non_eu_out1.groupby('Port')

for key, group in non_eu_out_grouped:
    plt.figure()
    plt.title('Total Tonnage out of the UK to Non EU Countries from 2015 to 2020')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("Outward Non EU graphs/{}.png".format(key))



#Final work is to look at the UK freight transfer on a domestic level 

#Inward domestic
domestic_in = usefuldata[(usefuldata['Direction'] == 'Inwards')  & (usefuldata['Region'] == 
                                                             'Domestic traffic')]
domestic_in1 = domestic_in[['Port','Year','Value (Thousands)']]
domestic_in_grouped = domestic_in1.groupby('Port')

for key, group in domestic_in_grouped:
    plt.figure()
    plt.title('Total Tonnage from other UK ports from 2015 to 2020')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("Inward Domestic graphs/{}.png".format(key))




#Outward domestic
domestic_out = usefuldata[(usefuldata['Direction'] == 'Outwards')  & (usefuldata['Region'] == 
                                                             'Domestic traffic')]
domestic_out1 = domestic_out[['Port','Year','Value (Thousands)']]
domestic_out_grouped = domestic_out1.groupby('Port')

for key, group in domestic_out_grouped:
    plt.figure()
    plt.title('Total Tonnage to other UK ports from 2015 to 2020')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("Outward Domestic graphs/{}.png".format(key))







