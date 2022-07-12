import pandas as pd
from matplotlib import pyplot as plt



#Importing just the North ports data set containing information from 2015-2020 which came from 
#PORT0400(https://www.gov.uk/government/statistical-data-sets/port-and-domestic-waterborne-freight-statistics-port)
path = r'Y:\Freight\18. Brexit impacts on freight\2. Port0400\PORT0400 North Ports 2015-2020.xlsx'
#Reading in the imported  data
data = pd.read_excel(path)

#Some of the data isn't useful to me at this point so I've removed it. (cargo code and cargo name)
usefuldata = data[['Port', 'Year', 'Region', 'Direction', 'Value (Thousands)']]


#Inward EU data for just the North Ports
eu_in = usefuldata[(usefuldata['Direction'] == 'Inwards')  & (usefuldata['Region'] == 
                                                             'European Union traffic')]
#Splitting the data up just into the important data  this being port year and value
eu_in1 = eu_in[['Port','Year','Value (Thousands)']]
#Summing the tonnage values to figure out the top 10
eu_in_grouped = eu_in1.groupby('Port')

for key, group in eu_in_grouped:
    plt.title('Total tonnage to North ports from EU countries')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label= key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("North Ports/EU Inward.png")

#Creating a summed data set so that a percentage drop can be obtained for each year
EU_in_summed_val = eu_in1.groupby(['Port' , 'Year']).sum()
    





#Outward EU data just for the north ports
eu_out = usefuldata[(usefuldata['Direction'] == 'Outwards')  & (usefuldata['Region'] == 
                                                               'European Union traffic')]
eu_out1 = eu_out[['Port','Year','Value (Thousands)']]
eu_out_grouped = eu_out1.groupby('Port')

plt.figure()
for key, group in eu_out_grouped:
    plt.title('Total tonnage from North Ports to EU countries')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("North Ports/EU Outward.png")
 
#Creating a summed data set so that a percentage drop can be obtained for each year
EU_out_summed_val = eu_out1.groupby(['Port' , 'Year']).sum()








#Inward Non EU data just for the north ports
non_eu_in = usefuldata[(usefuldata['Direction'] == 'Inwards')  & (usefuldata['Region'] == 
                                                                'Non-EU Foreign traffic')]
non_eu_in1 = non_eu_in[['Port','Year','Value (Thousands)']]
non_eu_in_grouped = non_eu_in1.groupby('Port')

plt.figure()
for key, group in non_eu_in_grouped:
    plt.title('Total tonnage to North ports from Non EU countries')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("North Ports/Non EU Inward.png")

#Creating a summed data set so that a percentage drop can be obtained for each year
Non_EU_in_summed_val = non_eu_in1.groupby(['Port' , 'Year']).sum()







#Outward Non EU data just for the north ports
non_eu_out = usefuldata[(usefuldata['Direction'] == 'Outwards')  & (usefuldata['Region'] == 
                                                                  'Non-EU Foreign traffic')]
non_eu_out1 = non_eu_out[['Port','Year','Value (Thousands)']]
non_eu_out_grouped = non_eu_out1.groupby('Port')


plt.figure()
for key, group in non_eu_out_grouped:
    plt.title('Total tonnage from North ports to EU countries')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("North Ports/Non EU Outward.png")

#Creating a summed data set so that a percentage drop can be obtained for each year
Non_EU_out_summed_val = non_eu_out1.groupby(['Port' , 'Year']).sum()







#Inward domestic for the north ports
domestic_in = usefuldata[(usefuldata['Direction'] == 'Inwards')  & (usefuldata['Region'] == 
                                                             'Domestic traffic')]
domestic_in1 = domestic_in[['Port','Year','Value (Thousands)']]
domestic_in_grouped = domestic_in1.groupby('Port')

plt.figure()
for key, group in domestic_in_grouped:
    plt.title('Total Tonnage from other UK ports from 2015 to 2020')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("North Ports/Domestic Inward.png")



#Creating a summed data set so that a percentage drop can be obtained for each year
Domestic_in_summed_val = domestic_in1.groupby(['Port' , 'Year']).sum()




#Outward domestic for the north ports
domestic_out = usefuldata[(usefuldata['Direction'] == 'Outwards')  & (usefuldata['Region'] == 
                                                             'Domestic traffic')]
domestic_out1 = domestic_out[['Port','Year','Value (Thousands)']]
domestic_out_grouped = domestic_out1.groupby('Port')


plt.figure()
for key, group in domestic_out_grouped:
    plt.title('Total Tonnage to other UK ports from 2015 to 2020')
    group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
    plt.legend(loc='best')
    plt.grid()
    plt.ylabel('Tonnage (Thousands)')
    plt.savefig("North Ports/Domestic Outward.png")
    
#Creating a summed data set so that a percentage drop can be obtained for each year
Domestic_out_summed_val = domestic_out1.groupby(['Port' , 'Year']).sum()    
