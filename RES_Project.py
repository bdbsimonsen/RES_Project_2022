# -*- coding: utf-8 -*-
"""
Created on Tue Nov 30 11:40:53 2021

@author: bdbsi
"""

"""
Spyder Editor

This is a temporary script file.
"""
import pypsa
import pandas as pd
import numpy
import csv
import matplotlib.pyplot as plt
from datetime import datetime

def annuity(n,r):
    """Calculate the annuity factor for an asset with lifetime n years and
    discount rate of r, e.g. annuity(20,0.05)*20 = 1.6"""

    if r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n
#%% adding generators, loads and carbon caps

network = pypsa.Network()

hours_in_2015 =pd.date_range('2015-01-01T00:00Z','2015-12-31T23:00Z', freq='H')
network.set_snapshots(hours_in_2015)

path="C:/Users/bdbsi/Desktop/University/Engineering/Renewable Energy Systems/Project/pv_optimal.csv"
path1="C:/Users/bdbsi/Desktop/University/Engineering/Renewable Energy Systems/Project/onshore_wind_1979-2017.csv"
path2='C:/Users/bdbsi/Desktop/University/Engineering/Renewable Energy Systems/Project/electricity_demand.csv'
path3='C:/Users/bdbsi/Desktop/University/Engineering/Renewable Energy Systems/Project/hydro/Hydro_Inflow_DE.csv'
path4="C:/Users/bdbsi/Desktop/University/Engineering/Renewable Energy Systems/Project/offshore_wind_1979-2017.csv"
path5='C:/Users/bdbsi/Desktop/University/Engineering/Renewable Energy Systems/Project/hydro/Hydro_Inflow_FR.csv'
path6='C:/Users/bdbsi/Desktop/University/Engineering/Renewable Energy Systems/Project/heat_demand.csv'

#GERMANY
network.add("Bus","bus_DEU")

df_demand= pd.read_csv(path2, sep=';', index_col=0)
df_demand.index = pd.to_datetime(df_demand.index) #change index to datatime
demand_DEU=df_demand['DEU']

df_heat_demand= pd.read_csv(path6, sep=';', index_col=0)
df_heat_demand.index = pd.to_datetime(df_demand.index) #change index to datatime
heat_demand_DEU=df_heat_demand['DEU']
heat_demand_DNK=df_heat_demand['DNK']
heat_demand_FRA=df_heat_demand['FRA']

network.add("Carrier", "onshorewind")
network.add("Carrier", "solar")
efficiency_OCGT = 0.39
gas_emissions= 0.19/efficiency_OCGT # in t_CO2/MWh not in t_CO2/MWh_th CO2 constraint does not work otherwise
network.add("Carrier", "gas", co2_emissions=gas_emissions)
efficiency_coal = 0.40
coal_emissions= 0.35/efficiency_coal # in t_CO2/MWh not in t_CO2/MWh_th CO2 constraint does not work otherwise
network.add("Carrier", "coal", co2_emissions=coal_emissions)
network.add("Carrier", "nuclear")
network.add("Carrier", "hydro")
network.add("Carrier", "offshorewind")

df_solar=pd.read_csv(path, sep=';', index_col=0)
df_solar.index=pd.to_datetime(df_solar.index)
solar_cf_2015=df_solar['DEU'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

df_wind=pd.read_csv(path1, sep=';', index_col=0)
df_wind.index=pd.to_datetime(df_wind.index)
wind_cf_2015=df_wind['DEU'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

df_offshorewind=pd.read_csv(path4, sep=';', index_col=0)
df_offshorewind.index=pd.to_datetime(df_offshorewind.index)
offshorewind_cf_2015=df_offshorewind['DEU'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

# add loads
network.add("Load",
            "load1",
            bus="bus_DEU",
            p_set=demand_DEU)

#demand_DEU=demand_DEU+heat_demand_DEU

capital_cost_wind=annuity(30,0.07)*910000*(1+0.033) # in €/MW
CF_wind=wind_cf_2015
network.add("Generator",
            "onshorewind",
            bus="bus_DEU",
            p_nom_extendable=True,
            carrier="onshorewind",
            p_nom_max=sum(demand_DEU)/8760, # penetration of technology=1
            capital_cost = capital_cost_wind,
            marginal_cost = 1.5,
            p_max_pu = CF_wind)

capital_cost_solar=annuity(25,0.055)*(425000+725000)*0.5*(1+0.025) # in €/MW
CF_solar=solar_cf_2015
network.add("Generator",
            "solar",
            bus="bus_DEU",
            p_nom_extendable=True,
            carrier="solar",
            #p_nom_max=2*sum(demand_DEU)/8760, # penetration of technology=2
            capital_cost = capital_cost_solar,
            marginal_cost = 0,
            p_max_pu = CF_solar)

capital_cost_OCGT = annuity(25,0.07)*560000*(1+0.033) # in €/MW
fuel_cost = 21.6 # in €/MWh_th 
marginal_cost_OCGT = fuel_cost/efficiency_OCGT # in €/MWh_el
network.add("Generator",
            "OCGT",
            bus="bus_DEU",
            p_nom_extendable=True,
            carrier="gas",
            #p_nom_max=sum(demand_DEU)/8760, # penetration of technology=1
            capital_cost = capital_cost_OCGT,
            marginal_cost = marginal_cost_OCGT)

capital_cost_coal = annuity(25,0.07)*1900000*(1+0.033) # in €/MW source: data catalogue
fuel_cost = 11.25 #in €/MWh_th
marginal_cost_coal = fuel_cost/efficiency_coal # in €/MWh_el
network.add("Generator",
            "coal",
            bus="bus_DEU",
            p_nom_extendable=True,
            carrier="coal",
            p_nom_max=0,
            capital_cost = capital_cost_coal,
            marginal_cost = marginal_cost_coal)

capital_cost_nuclear = annuity(30,0.07)*3700000*(1+0.033) #  in €/MW
fuel_cost = 11.5 # in €/MWh_th
efficiency_nuclear = 0.39
marginal_cost_nuclear = fuel_cost/efficiency_nuclear # in €/MWh_el
network.add("Generator",
            "nuclear",
            bus="bus_DEU",
            p_nom_extendable=True,
            carrier="nuclear",
            p_nom_max=0,
            capital_cost = capital_cost_nuclear,
            marginal_cost = marginal_cost_nuclear)

capital_cost_offshorewind=annuity(25,0.07)*1930000*(1+0.03) # in €/MW source:data catalogue 2020
CF_offshorewind=offshorewind_cf_2015
network.add("Generator",
            "offshorewind",
            bus="bus_DEU",
            p_nom_extendable=True,
            carrier="offshorewind",
            p_nom_max=2*sum(demand_DEU)/8760, # penetration of technology = 2. or 70000 # target for 2045 
            capital_cost = capital_cost_offshorewind,
            marginal_cost =3,
            p_max_pu = CF_offshorewind)



# add storages
df_hydro_org = pd.read_csv(path3, sep=',', index_col=0)
dict_hydro=[]
for y,(m,d,v) in df_hydro_org.iterrows():
    for h in range(24):
        dict_hydro.append({'utc_time':datetime(int(y), int(m), int(d), hour=h),'Inflow [GWh]':v/24})
df_hydro=pd.DataFrame(dict_hydro).set_index(["utc_time"])  
df_hydro2012=df_hydro[(df_hydro.index >= datetime(2015, 1, 1)) & (df_hydro.index < datetime(2016, 1, 1))]
df_hydro2012.index=pd.to_datetime(df_hydro2012.index,utc=True)  
         
CF_hydro=df_hydro2012/df_hydro2012.max()
CF_hydro=CF_hydro.squeeze()
CF_hydro=CF_hydro*1000 #convert to MW


capital_cost_hydro=annuity(80,0.07)*2000000*(0.01) # in €/MW assuming only maintanence costs
network.add("StorageUnit",
            'Hydro_Storage',
            bus='bus_DEU',
            p_nom_extendable=True,
            carrier="hydro",
            p_nom_max=11000,
            efficiency_store=0.87,
            efficiency_dispatch=0.87,
            capital_cost = capital_cost_hydro,
            inflow=CF_hydro)

network.add("Carrier","H2")

network.add("Bus","H2_DEU",carrier = "H2")

#Connect the store to the bus
network.add("Store",
      "H2_Tank",
      bus = "H2_DEU",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(20, 0.07)*8400*(1))

#Add the link "H2 Electrolysis" that transport energy from the bus_DEU (bus0) to the H2 bus (bus1)
#with 80% efficiency
network.add("Link",
      "H2_Electrolysis", 
      bus0 = "bus_DEU",
      bus1 = "H2_DEU",     
      p_nom_extendable = True,
      efficiency = 0.8,
      capital_cost = annuity(18, 0.07)*350000*(1+0.04))

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the bus_DEU (bus1)
#with 58% efficiency
network.add("Link",
      "H2_Fuel_Cell", 
      bus0 = "H2_DEU",
      bus1 = "bus_DEU",     
      p_nom_extendable = True,
      efficiency = 0.58,
      capital_cost = annuity(20, 0.07)*339000*(1+0.03)) 

network.add("Carrier","battery")

network.add("Bus","battery_DEU",carrier = "battery")

#Connect the store to the bus
network.add("Store",
      "battery_storage",
      bus = "battery_DEU",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(15, 0.07)*144600*(1))

#Add the link "battery inverter" that transport energy from the bus_DEU (bus0) to the batttery bus (bus1)
#with 80% efficiency
network.add("Link",
      "battery_inverter", 
      bus0 = "battery_DEU",
      bus1 = "bus_DEU",     
      p_nom_extendable = True,
      efficiency = 0.9,
      #p_nom_max= 5000,
      p_min_pu=-1,
      capital_cost = annuity(20, 0.07)*310000*(1+0.03))


# ADDING OTHER COUNTRIES

# DENMARK

network.add("Bus","bus_DNK")

# add loads
demand_DNK=df_demand['DNK']
network.add("Load",
            "load_DNK",
            bus="bus_DNK",
            p_set=demand_DNK)

#demand_DNK=demand_DNK+heat_demand_DNK

CF_solar_DNK=df_solar['DNK'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

CF_wind_DNK=df_wind['DNK'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

CF_offshorewind_DNK=df_offshorewind['DNK'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

capital_cost_wind=annuity(30,0.07)*910000*(1+0.033) # in €/MW
network.add("Generator",
            "onshorewind_DNK",
            bus="bus_DNK",
            p_nom_extendable=True,
            carrier="onshorewind",
            p_nom_max=sum(demand_DNK)/8760, #onshore penetration=1
            capital_cost = capital_cost_wind,
            marginal_cost = 1.5,
            p_max_pu = CF_wind_DNK)

capital_cost_solar=annuity(25,0.055)*(425000+725000)*0.5*(1+0.025) # in €/MW
network.add("Generator",
            "solar_DNK",
            bus="bus_DNK",
            p_nom_extendable=True,
            carrier="solar",
            p_nom_max=2*sum(demand_DNK)/8760, #onshore penetration=2
            capital_cost = capital_cost_solar,
            marginal_cost = 0,
            p_max_pu = CF_solar_DNK)

capital_cost_OCGT = annuity(25,0.07)*560000*(1+0.033) # in €/MW
fuel_cost = 21.6 # in €/MWh_th 
marginal_cost_OCGT = fuel_cost/efficiency_OCGT # in €/MWh_el
network.add("Generator",
            "OCGT_DNK",
            bus="bus_DNK",
            p_nom_extendable=True,
            carrier="gas",
            #p_nom_max=sum(demand_DNK)/8760, #onshore penetration=1
            capital_cost = capital_cost_OCGT,
            marginal_cost = marginal_cost_OCGT)

capital_cost_coal = annuity(25,0.07)*1900000*(1+0.033) # in €/MW source: data catalogue
fuel_cost = 11.25 #in €/MWh_th
marginal_cost_coal = fuel_cost/efficiency_coal # in €/MWh_el
network.add("Generator",
            "coal_DNK",
            bus="bus_DNK",
            p_nom_extendable=True,
            carrier="coal",
            #p_nom_max=0,
            capital_cost = capital_cost_coal,
            marginal_cost = marginal_cost_coal)

capital_cost_nuclear = annuity(30,0.07)*3700000*(1+0.033) #  in €/MW
fuel_cost = 11.5 # in €/MWh_th
efficiency_nuclear = 0.39
marginal_cost_coal = fuel_cost/efficiency_nuclear # in €/MWh_el
network.add("Generator",
            "nuclear_DNK",
            bus="bus_DNK",
            p_nom_extendable=True,
            carrier="nuclear",
            p_nom_max=0,
            capital_cost = capital_cost_nuclear,
            marginal_cost = marginal_cost_nuclear)


capital_cost_offshorewind=annuity(25,0.07)*1930000*(1+0.03) # in €/MW source:data catalogue 2020
network.add("Generator",
            "offshorewind_DNK",
            bus="bus_DNK",
            p_nom_extendable=True,
            carrier="offshorewind",
            p_nom_max= 10*sum(demand_DNK)/8760, #onshore penetration=10
            capital_cost = capital_cost_offshorewind,
            marginal_cost =3,
            p_max_pu = CF_offshorewind_DNK)


# add storages
capital_cost_hydro=annuity(80,0.07)*2000000*(1+0.01) # in €/MW source:data catalogue 2020
network.add("StorageUnit",
            'Hydro_Storage_DNK',
            bus='bus_DNK',
            p_nom_extendable=True,
            carrier="hydro",
            p_nom_max=0,
            efficiency_store=0.87,
            efficiency_dispatch=0.87,
            capital_cost = capital_cost_hydro,
            inflow=CF_hydro)


network.add("Bus","H2_DNK",carrier = "H2")

#Connect the store to the bus
network.add("Store",
      "H2_Tank_DNK",
      bus = "H2_DNK",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(20, 0.07)*8400*(1))

#Add the link "H2 Electrolysis" that transport energy from the bus_DNK (bus0) to the H2 bus (bus1)
#with 80% efficiency
network.add("Link",
      "H2_Electrolysis_DNK", 
      bus0 = "bus_DNK",
      bus1 = "H2_DNK",     
      p_nom_extendable = True,
      efficiency = 0.8,
      capital_cost = annuity(18, 0.07)*350000*(1+0.04))

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the bus_DNK (bus1)
#with 58% efficiency
network.add("Link",
      "H2_Fuel_Cell_DNK", 
      bus0 = "H2_DNK",
      bus1 = "bus_DNK",     
      p_nom_extendable = True,
      efficiency = 0.58,
      capital_cost = annuity(20, 0.07)*339000*(1+0.03)) 


network.add("Bus","battery_DNK",carrier = "battery")

#Connect the store to the bus
network.add("Store",
      "battery_storage_DNK",
      bus = "battery_DNK",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(15, 0.07)*144600*(1))

#Add the link "battery inverter" that transport energy from the bus_DNK (bus0) to the batttery bus (bus1)
#with 80% efficiency
network.add("Link",
      "battery_inverter_DNK", 
      bus0 = "battery_DNK",
      bus1 = "bus_DNK",     
      p_nom_extendable = True,
      efficiency = 0.9,
      #p_nom_max= 5000,
      p_min_pu=-1,
      capital_cost = annuity(20, 0.07)*310000*(1+0.03))

#add HVDC link between DEU and DNK

network.add("Link",
      "DEU_DNK", 
      bus0 = "bus_DEU",
      bus1 = "bus_DNK",     
      p_nom_extendable = True,
      efficiency = 1,
      p_nom_max= 0.25*sum(demand_DEU)/8760,
      p_min_pu=-1,
      #marginal_cost=1,
      capital_cost = annuity(40, 0.07)*(150000+400*100)*(1+0.02))

# FRANCE

network.add("Bus","bus_FRA")

# add loads
demand_FRA=df_demand['FRA']
network.add("Load",
            "load_FRA",
            bus="bus_FRA",
            p_set=demand_FRA)

#demand_FRA=demand_FRA+heat_demand_FRA

CF_solar_FRA=df_solar['FRA'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

CF_wind_FRA=df_wind['FRA'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

CF_offshorewind_FRA=df_offshorewind['FRA'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

capital_cost_wind=annuity(30,0.07)*910000*(1+0.033) # in €/MW
network.add("Generator",
            "onshorewind_FRA",
            bus="bus_FRA",
            p_nom_extendable=True,
            carrier="onshorewind",
            p_nom_max=sum(demand_FRA)/8760, #onshore penetration=1
            capital_cost = capital_cost_wind,
            marginal_cost = 1.5,
            p_max_pu = CF_wind_FRA)

capital_cost_solar=annuity(25,0.055)*(425000+725000)*0.5*(1+0.025) # in €/MW
network.add("Generator",
            "solar_FRA",
            bus="bus_FRA",
            p_nom_extendable=True,
            carrier="solar",
            p_nom_max=2*sum(demand_FRA)/8760, #onshore penetration=2
            capital_cost = capital_cost_solar,
            marginal_cost = 0,
            p_max_pu = CF_solar_FRA)

capital_cost_OCGT = annuity(25,0.07)*560000*(1+0.033) # in €/MW
fuel_cost = 21.6 # in €/MWh_th 
marginal_cost_OCGT = fuel_cost/efficiency_OCGT # in €/MWh_el
network.add("Generator",
            "OCGT_FRA",
            bus="bus_FRA",
            p_nom_extendable=True,
            carrier="gas",
            #p_nom_max=sum(demand_FRA)/8760, #onshore penetration=1
            capital_cost = capital_cost_OCGT,
            marginal_cost = marginal_cost_OCGT)

capital_cost_coal = annuity(25,0.07)*1900000*(1+0.033) # in €/MW source: data catalogue
fuel_cost = 11.25 #in €/MWh_th
marginal_cost_coal = fuel_cost/efficiency_coal # in €/MWh_el
network.add("Generator",
            "coal_FRA",
            bus="bus_FRA",
            p_nom_extendable=True,
            carrier="coal",
            #p_nom_max=0,
            capital_cost = capital_cost_coal,
            marginal_cost = marginal_cost_coal)

capital_cost_nuclear = annuity(30,0.07)*3700000*(1+0.033) #  in €/MW
fuel_cost = 11.5 # in €/MWh_th
efficiency_nuclear = 0.39
marginal_cost_nuclear = fuel_cost/efficiency_nuclear # in €/MWh_el
network.add("Generator",
            "nuclear_FRA",
            bus="bus_FRA",
            p_nom_extendable=True,
            carrier="nuclear",
            # p_nom_min=0.5*sum(demand_FRA)/8760, #at least 50% nuclear
            #p_nom_max=0,#60000, #currently installed
            #p_min_pu=1,
            capital_cost = capital_cost_nuclear,
            marginal_cost = marginal_cost_nuclear)


df_hydro_org = pd.read_csv(path5, sep=',', index_col=0)

dict_hydro=[]
for y,(m,d,v) in df_hydro_org.iterrows():
    for h in range(24):
        dict_hydro.append({'utc_time':datetime(int(y), int(m), int(d), hour=h),'Inflow [GWh]':v/24})
df_hydro=pd.DataFrame(dict_hydro).set_index(["utc_time"])  
df_hydro2012=df_hydro[(df_hydro.index >= datetime(2015, 1, 1)) & (df_hydro.index < datetime(2016, 1, 1))]
df_hydro2012.index=pd.to_datetime(df_hydro2012.index,utc=True)  
    
CF_hydro=df_hydro2012/df_hydro2012.max()
CF_hydro=CF_hydro.squeeze()
CF_hydro_FRA=CF_hydro*1000 #convert to MW


capital_cost_offshorewind=annuity(25,0.07)*1930000*(1+0.03) # in €/MW source:data catalogue 2020
network.add("Generator",
            "offshorewind_FRA",
            bus="bus_FRA",
            p_nom_extendable=True,
            carrier="offshorewind",
            p_nom_max= 10*sum(demand_FRA)/8760, #offshore penetration=10
            capital_cost = capital_cost_offshorewind,
            marginal_cost =3,
            p_max_pu = CF_offshorewind_FRA)


# add storages
capital_cost_hydro=annuity(80,0.07)*2000000*(0.01) # in €/MW assuming already built, only maintanence costs.
network.add("StorageUnit",
            'Hydro_Storage_FRA',
            bus='bus_FRA',
            p_nom_extendable=True,
            carrier="hydro",
            p_nom_max=25000,
            efficiency_store=0.87,
            efficiency_dispatch=0.87,
            capital_cost = capital_cost_hydro,
            inflow=CF_hydro_FRA)


network.add("Bus","H2_FRA",carrier = "H2")

#Connect the store to the bus
network.add("Store",
      "H2_Tank_FRA",
      bus = "H2_FRA",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(20, 0.07)*8400*(1))

#Add the link "H2 Electrolysis" that transport energy from the bus_FRA (bus0) to the H2 bus (bus1)
#with 80% efficiency
network.add("Link",
      "H2_Electrolysis_FRA", 
      bus0 = "bus_FRA",
      bus1 = "H2_FRA",     
      p_nom_extendable = True,
      efficiency = 0.8,
      capital_cost = annuity(18, 0.07)*350000*(1+0.04))

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the bus_FRA (bus1)
#with 58% efficiency
network.add("Link",
      "H2_Fuel_Cell_FRA", 
      bus0 = "H2_FRA",
      bus1 = "bus_FRA",     
      p_nom_extendable = True,
      efficiency = 0.58,
      capital_cost = annuity(20, 0.07)*339000*(1+0.03)) 


network.add("Bus","battery_FRA",carrier = "battery")

#Connect the store to the bus
network.add("Store",
      "battery_storage_FRA",
      bus = "battery_FRA",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(15, 0.07)*144600*(1))

#Add the link "battery inverter" that transport energy from the bus_FRA (bus0) to the batttery bus (bus1)
#with 80% efficiency
network.add("Link",
      "battery_inverter_FRA", 
      bus0 = "battery_FRA",
      bus1 = "bus_FRA",     
      p_nom_extendable = True,
      efficiency = 0.9,
      #p_nom_max= 5000,
      p_min_pu=-1,
      capital_cost = annuity(20, 0.07)*310000*(1+0.03))

# #add HVDC link between DEU and FRA

network.add("Link",
      "DEU_FRA", 
      bus0 = "bus_DEU",
      bus1 = "bus_FRA",     
      p_nom_extendable = True,
      efficiency = 1,
      p_nom_max= 0.25*sum(demand_DEU)/8760,
      p_min_pu=-1,
      #marginal_cost=1,
      capital_cost = annuity(40, 0.07)*(150000+500*100)*(1+0.02))

#add HVDC link between DNK and FRA

# network.add("Link",
#       "DNK_FRA", 
#       bus0 = "bus_DNK",
#       bus1 = "bus_FRA",     
#       p_nom_extendable = True,
#       #efficiency = 0.96,
#       #p_nom_max= 400,
#       p_min_pu=-1,
#       #marginal_cost=1000,
#       capital_cost = annuity(40, 0.07)*(150000+500*100)*(1+0.02))

#add carbon constraint
Co2_1990=381*10**6 #tonCO2
co2_goal=90/100; #for 90% reduction put 90/100
co2_limit=(1-co2_goal)*Co2_1990 #tonCO2
network.add("GlobalConstraint",
            "co2_limit",
            type="primary_energy",
            carrier_attribute="co2_emissions",
            sense="<=",
            constant=co2_limit)

# Add Heat Demand

# network.add("Load",
#             "load_heat",
#             bus="bus_DEU",
#             p_set=heat_demand_DEU)
# network.add("Load",
#             "load_heat_DNK",
#             bus="bus_DNK",
#             p_set=heat_demand_DNK)
# network.add("Load",
#             "load_heat_FRA",
#             bus="bus_FRA",
#             p_set=heat_demand_FRA)



# Run optimisation!!

network.lopf(network.snapshots, 
             pyomo=False,
             solver_name='gurobi')


#print some results
space='--------------------------------'
print(space)
print('install capacities in GW')
print(network.generators.p_nom_opt/1000)
print(network.storage_units.p_nom_opt/1000)
print(space)
print('install storage capacity in GW')
print(network.stores.e_nom_opt/1000)
print('install link capacity in GW')
print(network.links.p_nom_opt/1000)

#%% plotting demand
start=24*150
days=24*160
plt.plot(network.loads_t.p['load1'][start:days]/1000, color='black', label='electricity demand [GW]')
#plt.plot(network.loads_t.p['load_heat'][start:days]/1000, color='brown', label='heat demand [GW]')
plt.plot(network.loads_t.p['load1'][start:days]/1000+network.loads_t.p['load_heat'][start:days]/1000, color='pink', label='electricity plus heating demand [GW]')
heat_demand_DEU
plt.legend(fancybox=True, shadow=True, loc='best')
plt.title('Demand DEU', y=1.03)

start=24*0
days=24*365

heating_DEU=network.loads_t.p['load1'][start:days]/1000+network.loads_t.p['load_heat'][start:days]/1000
heating_DNK=network.loads_t.p['load_DNK'][start:days]/1000+network.loads_t.p['load_heat_DNK'][start:days]/1000
heating_FRA=network.loads_t.p['load_FRA'][start:days]/1000+network.loads_t.p['load_heat_FRA'][start:days]/1000


fig, axs=plt.subplots(3,1)#Making a subplot of 2 rows 1 column
fig.subplots_adjust(hspace=0.7)#Setting vertical space separation between subplots
fig.suptitle('Demand with and without heating in every country [GW]')

axs[0].tick_params(labelrotation=0) #set rotation of the axis
axs[0].plot(heating_DEU,color='pink') #plotting the subplot in the 1st row on the subplot
axs[0].plot(network.loads_t.p['load1'][start:days]/1000,color='black')
axs[0].title.set_text('DEU')

axs[1].tick_params(labelrotation=0)#set rotation of the axis
axs[1].plot(heating_DNK,color='pink') #plotting the subplot in the 2nd row on the subplot
axs[1].plot(network.loads_t.p['load_DNK'][start:days]/1000,color='black')
axs[1].title.set_text('DNK')

axs[2].tick_params(labelrotation=0)
axs[2].plot(heating_FRA,color='pink') #plotting the subplot in the 3rd row on the subplot 
axs[2].plot(network.loads_t.p['load_FRA'][start:days]/1000,color='black')
axs[2].title.set_text('FRA')
#%% average capacity factor and variance 
pv_opt=pd.read_csv(path,delimiter=';',parse_dates=['utc_time'],index_col=['utc_time'])
On_wind=pd.read_csv(path1,delimiter=';',parse_dates=['utc_time'],index_col=['utc_time'])
Off_wind=pd.read_csv(path4,delimiter=';',parse_dates=['utc_time'],index_col=['utc_time'])

#pv_opt=pd.read_csv(r'C:/Users/raul_/OneDrive - Aarhus Universitet/Skrivebord/Master/Second Semester/Renewable Energies Systems/Final Project/data/pv_optimal.csv',delimiter=';',parse_dates=['utc_time'],index_col=['utc_time'])
#On_wind=pd.read_csv(r'C:/Users/raul_/OneDrive - Aarhus Universitet/Skrivebord/Master/Second Semester/Renewable Energies Systems/Final Project/data/onshore_wind_1979-2017.csv',delimiter=';',parse_dates=['utc_time'],index_col=['utc_time'])
#Off_wind=pd.read_csv(r'C:/Users/raul_/OneDrive - Aarhus Universitet/Skrivebord/Master/Second Semester/Renewable Energies Systems/Final Project/data/offshore_wind_1979-2017.csv',delimiter=';',parse_dates=['utc_time'],index_col=['utc_time'])

Onwind = On_wind[['DEU']]#assigning data of cf to a variable 
solar= pv_opt[['DEU']]
Offwind = Off_wind[['DEU']]

YearsOnwind=Onwind['2008-01-01':'2015-12-31']
YearsOffwind=Offwind['2008-01-01':'2015-12-31']
YearsSolar=solar['2008-01-01':'2015-12-31']

OnWyears= YearsOnwind.groupby([YearsOnwind.index.year]).mean()
OffWyears= YearsOffwind.groupby([YearsOffwind.index.year]).mean()
Syears= YearsSolar.groupby([YearsSolar.index.year]).mean()

fig, axs=plt.subplots(3,1)#Making a subplot of 2 rows 1 column
fig.subplots_adjust(hspace=0.7)#Setting vertical space separation between subplots
fig.suptitle('Average Capacity Factor 2008-2015')

axs[2].tick_params(labelrotation=0)#set rotation of the axis
axs[2].plot(OffWyears.index,OffWyears,color='teal')#plotting the subplot in the 3rd row in the subplot
axs[2].title.set_text('Offshore Wind')

axs[1].tick_params(labelrotation=0)#set rotation of the axis
axs[1].plot(OnWyears.index,OnWyears,color='green')#plotting the subplot in the 2nd row in the subplot
axs[1].title.set_text('Onshore Wind')

axs[0].tick_params(labelrotation=0)
axs[0].plot(Syears.index,Syears, color='orange')#plotting the subplot in the 1st row in the subplot 
axs[0].title.set_text('Solar')


Var_OnWyears= YearsOnwind.groupby([YearsOnwind.index.year]).var()
Var_OffWyears= YearsOffwind.groupby([YearsOffwind.index.year]).var()
Var_Syears= YearsSolar.groupby([YearsSolar.index.year]).var()

fig, axs=plt.subplots(3,1)#Making a subplot of 2 rows 1 column
fig.subplots_adjust(hspace=0.7)#Setting vertical space separation between subplots
fig.suptitle('Standar Diviation of hourly Capacity Factors 2008-2015')

axs[2].tick_params(labelrotation=0)#set rotation of the axis
axs[2].plot(Var_OffWyears.index,Var_OffWyears**(1/2),color='teal')#plotting the subplot in the 3rd row in the subplot
axs[2].title.set_text('Offshore Wind')

axs[1].tick_params(labelrotation=0)#set rotation of the axis
axs[1].plot(Var_OnWyears.index,Var_OnWyears**(1/2),color='green')#plotting the subplot in the 2nd row in the subplot
axs[1].title.set_text('Onshore Wind')

axs[0].tick_params(labelrotation=0)
axs[0].plot(Var_Syears.index,Var_Syears**(1/2), color='orange')#plotting the subplot in the 1st row in the subplot
axs[0].title.set_text('Solar')
#%% printing some results
print(space)
#print(network.generators_t.status)
# print(space)
# print('generation in every time step')
# print(network.generators_t.p)
print(space)
print('price of electricity in euros per MWh')
print(network.objective/sum(network.loads_t.p.sum()))
print(space)
print('optimal installed capacities as percentage of total')
install_mix=network.generators.p_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100
print(install_mix)
print(network.storage_units.p_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100)
print(network.stores.e_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100)
print(space)
print('total system cost in Billions of Euros')
print(network.objective/10**9)

start=24*150
days=24*170
#plt.plot(network.loads_t.p['load1'][start:days], color='black', label='demand')
#plt.plot(network.loads_t.p['load1'][start:days]+network.loads_t.p['load_heat'][start:days], color='pink', label='electricity plus heating demand [GW]')
#plt.plot(network.generators_t.p['onshorewind'][start:days], color='green', label='onshore wind')
#plt.plot(network.generators_t.p['solar'][start:days], color='orange', label='solar')
#plt.plot(network.generators_t.p['OCGT'][start:days], color='grey', label='gas (OCGT)')
#plt.plot(network.generators_t.p['coal'][start:days], color='brown', label='coal')
#plt.plot(network.generators_t.p['nuclear'][start:days], color='red', label='nuclear')
#plt.plot(network.generators_t.p['offshorewind'][start:days], color='teal', label='offshorewind')
#plt.plot(network.storage_units_t.p['Hydro_Storage'][start:days], color='blue', label='hydro')
#plt.plot(network.stores_t.p['H2_Tank'][start:days], color='purple', label='H2')
plt.plot(network.stores_t.p['battery_storage'][start:days], color='yellow', label='Battery')
#plt.plot(network.links_t.p1['DEU_FRA'][start:days]+network.links_t.p1['DEU_DNK'][start:days], color='lightblue', label='Import from DNK')
plt.legend(fancybox=True, shadow=False, loc='best')
#plt.title('Electricity dispatch May 31st - June 2nd', y=1.03)
#%% pie chart DEU
labels = ['onshore wind', 'solar', 'gas (OCGT)', ' ', ' ', 'offshorewind','hydro','H2','Battery','Imports']#
sizes = [network.generators_t.p['onshorewind'].sum(),
          network.generators_t.p['solar'].sum(),
          network.generators_t.p['OCGT'].sum(),
          network.generators_t.p['coal'].sum(),
          network.generators_t.p['nuclear'].sum(),
          network.generators_t.p['offshorewind'].sum(),
          sum((network.storage_units_t.p['Hydro_Storage']>0)*network.storage_units_t.p['Hydro_Storage']),
          sum((network.links_t.p0['H2_Fuel_Cell']>0)*network.links_t.p0['H2_Fuel_Cell']),
          sum((network.stores_t.p['battery_storage']>0)*network.stores_t.p['battery_storage']),
         sum((network.links_t.p1['DEU_DNK']>0)*network.links_t.p1['DEU_DNK'])+sum((network.links_t.p1['DEU_FRA']>0)*network.links_t.p1['DEU_FRA'])]

colors = ['green', 'orange', 'grey', 'brown', 'red', 'teal', 'blue','purple','yellow','lightblue']

plt.pie(sizes, 
        colors=colors, 
        labels=labels, 
        wedgeprops={'linewidth':0})

plt.title('Electricity mix DEU with heating demand', y=1.07)

# printing more results

# cap=(0.6, 0.65, 0.70, 0.75, 0.80, 0.85, 0.9, 0.95, 0.96, 0.97, 0.975, 0.98, 0.99, 1)
# optimal_wind=(20.4, 20.2, 20, 19, 17.9, 16.7, 15.3, 14, 13.8, 13.7, 13.7, 13.8, 12.4, 12.6 )
# optimal_solar=(20.0, 21, 21.7, 23.2, 26.1, 29.8, 34.3, 39, 39.1, 37.7, 37, 37.7, 41.8, 40.9)
# optimal_gas=(58.9, 54.0, 46.2, 36.8, 27.5,  19.1, 11.7, 5.4, 4.3, 3.6, 2.6, 2, 1, 0 )
# optimal_offshore=(0, 4, 11.2, 15.8, 18.2, 20.4, 19.7, 18.5, 19.2, 21.5, 23.3, 23.1, 20.4, 21.1)
# optimal_hydro=(0.7, 0.7, 0.8, 0.8, 0.7, 0.7, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6)
# optimal_H2=(0, 0, 0, 0, 1.9, 5.8, 8.7, 10.9, 11.4, 12.4, 13.4, 13.4, 12.4, 13.8)
# optimal_battery=(0, 0, 0, 4, 7.6, 7.4, 9.6, 11.7, 11.6, 11, 9.4, 9.3, 11.4, 11)
# el_price=(57.1, 57.4, 58.2, 59.9, 62.5, 66.35, 71.8, 79.1, 81.2, 84.5, 87.4, 91, 99.3, 109.1)
# CO2_Price=(0, 13.7, 31.5, 57.1, 81.6, 124.5, 166.4, 259, 325.9, 620.6, 898.4, 994, 1184.4, 8625.8)

# plt.plot(cap, optimal_wind, color='green', label='onshore wind')
# plt.plot(cap, optimal_solar, color='orange', label='solar')
# plt.plot(cap, optimal_gas, color='grey', label='OCGT')
# plt.plot(cap, optimal_offshore, color='teal', label='offshore wind')
# plt.plot(cap, optimal_hydro, color='blue', label='hydro')
# plt.plot(cap, optimal_H2, color='purple', label='H2')
# plt.plot(cap, optimal_battery, color='yellow', label='battery')
# plt.plot(cap, CO2_Price, color='red', label='carbon price [€/ton]')
# plt.plot(cap, el_price, color='black', label='electricity price [€/MWh]')
# #plt.legend(fancybox=True, shadow=True, loc='best')
# plt.title('Electricity mix with carbon cap')
# plt.axis([0.6,1,0,65])


print(space)
print('capacity factors in %')
capacity_factors=sizes[0:6]/(network.generators.p_nom_opt[0:6]*8760)*100
print(capacity_factors)
print(sizes[6]/(network.storage_units.p_nom_opt*8760)*100)
print(sizes[7:9]/(network.stores.e_nom_opt[0:2]*8760*0.5)*100)
print(space)
print('elextricity mix in %')
print(sizes/sum(sizes)*100)
print(space)
print('CO2 emissions from gas as % of 1990 levels')
print(sizes[2]*gas_emissions/(Co2_1990)*100)
print(space)
print('CO2 emissions from coal as % of 1990 levels')
print(sizes[3]*coal_emissions/(Co2_1990)*100)
print(space)
print('CO2 price')
print(network.global_constraints.mu)
print(space)
print('price of electricity in euros per MWh')
print(network.objective/sum(network.loads_t.p.sum()))
print(space)
print('total power generated (inlcuding from storage) as % of DEU demand')
print(sum(sizes[0:9])/sum(demand_DEU)*100)
#%% printing some results for DNK
print(space)
#print(network.generators_t.status)
# print(space)
# print('generation in every time step')
# print(network.generators_t.p)
print(space)
print('price of electricity in euros per MWh')
print(network.objective/sum(network.loads_t.p.sum()))
print(space)
print('optimal installed capacities as percentage of total')
install_mix=network.generators.p_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100
print(install_mix)
print(network.storage_units.p_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100)
print(network.stores.e_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100)
print(space)
print('total system cost in Billions of Euros')
print(network.objective/10**9)

plt.plot(network.loads_t.p['load_DNK'][start:days], color='black', label='demand')
plt.plot(network.generators_t.p['onshorewind_DNK'][start:days], color='green', label='onshore wind')
plt.plot(network.generators_t.p['solar_DNK'][start:days], color='orange', label='solar')
plt.plot(network.generators_t.p['OCGT_DNK'][start:days], color='grey', label='gas (OCGT)')
plt.plot(network.generators_t.p['coal_DNK'][start:days], color='brown', label='coal')
#plt.plot(network.generators_t.p['nuclear_DNK'][start:days], color='red', label='nuclear')
plt.plot(network.generators_t.p['offshorewind_DNK'][start:days], color='teal', label='offshorewind')
plt.plot(network.storage_units_t.p['Hydro_Storage_DNK'][start:days], color='blue', label='hydro')
plt.plot(network.stores_t.p['H2_Tank_DNK'][start:days], color='purple', label='H2')
plt.plot(network.stores_t.p['battery_storage_DNK'][start:days], color='yellow', label='Battery')
plt.plot(network.links_t.p0['DEU_DNK'][start:days], color='lightblue', label='Import from DEU')
#plt.legend(fancybox=True, shadow=True, loc='best')
#%% pie chart DNK

labels = ['onshore wind', ' ', 'gas (OCGT)', ' ', ' ', 'offshorewind','','H2',' ','Import']
sizes = [network.generators_t.p['onshorewind_DNK'].sum(),
          network.generators_t.p['solar_DNK'].sum(),
          network.generators_t.p['OCGT_DNK'].sum(),
          network.generators_t.p['coal_DNK'].sum(),
          network.generators_t.p['nuclear_DNK'].sum(),
          network.generators_t.p['offshorewind_DNK'].sum(),
          sum((network.storage_units_t.p['Hydro_Storage_DNK']>0)*network.storage_units_t.p['Hydro_Storage_DNK']),
          sum((network.links_t.p0['H2_Fuel_Cell_DNK']>0)*network.links_t.p0['H2_Fuel_Cell_DNK']),
          sum((network.stores_t.p['battery_storage_DNK']>0)*network.stores_t.p['battery_storage_DNK']),
          sum((network.links_t.p0['DEU_DNK']>0)*network.links_t.p0['DEU_DNK'])]

colors = ['green', 'orange', 'grey', 'brown', 'red', 'teal', 'blue','purple','yellow','lightblue']

plt.pie(sizes, 
        colors=colors, 
        labels=labels, 
        wedgeprops={'linewidth':0})

plt.title('Electricity mix DNK with heating demand', y=1.07)

# printing more results


print(space)
print('capacity factors in % [DNK]')
capacity_factors=sizes[0:6]/(network.generators.p_nom_opt[6:12]*8760)*100
print(capacity_factors)
#print(sizes[6]/(network.storage_units.p_nom_opt[1]*8760)*100)
print(sizes[7:9]/(network.stores.e_nom_opt[2:4]*8760*0.5)*100)
print(space)
print('elextricity mix in % [DNK]')
print(sizes/sum(sizes)*100)
print(space)
print('CO2 emissions from [DNK] gas as % of [DEU] 1990 levels')
print(sizes[2]*gas_emissions/(Co2_1990)*100)
print(space)
print('CO2 emissions from [DNK] coal as % of [DEU] 1990 levels')
print(sizes[3]*coal_emissions/(Co2_1990)*100)
print(space)
print('CO2 price')
print(network.global_constraints.mu)
print(space)
print('total power generated in [DNK] (inlcuding from storage) as % of total demand in DNK')
print(sum(sizes[0:9])/sum(demand_DNK)*100)
#%% printing some results for FRA
print(space)
#print(network.generators_t.status)
# print(space)
# print('generation in every time step')
# print(network.generators_t.p)
print(space)
print('price of electricity in euros per MWh')
print(network.objective/sum(network.loads_t.p.sum()))
print(space)
print('optimal installed capacities as percentage of total')
install_mix=network.generators.p_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100
print(install_mix)
print(network.storage_units.p_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100)
print(network.stores.e_nom_opt/(sum(network.generators.p_nom_opt)+sum(network.storage_units.p_nom_opt)+sum(network.stores.e_nom_opt))*100)
print(space)
print('total system cost in Billions of Euros')
print(network.objective/10**9)

plt.plot(network.loads_t.p['load_FRA'][start:days], color='black', label='demand')
plt.plot(network.generators_t.p['onshorewind_FRA'][start:days], color='green', label='onshore wind')
plt.plot(network.generators_t.p['solar_FRA'][start:days], color='orange', label='solar')
plt.plot(network.generators_t.p['OCGT_FRA'][start:days], color='grey', label='gas (OCGT)')
plt.plot(network.generators_t.p['coal_FRA'][start:days], color='brown', label='coal')
plt.plot(network.generators_t.p['nuclear_FRA'][start:days], color='red', label='nuclear')
plt.plot(network.generators_t.p['offshorewind_FRA'][start:days], color='teal', label='offshorewind')
plt.plot(network.storage_units_t.p['Hydro_Storage_FRA'][start:days], color='blue', label='hydro')
plt.plot(network.stores_t.p['H2_Tank_FRA'][start:days], color='purple', label='H2')
plt.plot(network.stores_t.p['battery_storage_FRA'][start:days], color='yellow', label='Battery')
plt.plot(network.links_t.p0['DEU_FRA'][start:days], color='lightblue', label='Imports')
#plt.legend(fancybox=True, shadow=True, loc='best')
#%% pie chart France

labels = ['onshore wind', 'solar', 'gas (OCGT)', ' ', '  ', 'offshore wind','hydro','H2','battery','Imports']
sizes = [network.generators_t.p['onshorewind_FRA'].sum(),
          network.generators_t.p['solar_FRA'].sum(),
          network.generators_t.p['OCGT_FRA'].sum(),
          network.generators_t.p['coal_FRA'].sum(),
          network.generators_t.p['nuclear_FRA'].sum(),
          network.generators_t.p['offshorewind_FRA'].sum(),
          sum((network.storage_units_t.p['Hydro_Storage_FRA']>0)*network.storage_units_t.p['Hydro_Storage_FRA']),
          sum((network.links_t.p0['H2_Fuel_Cell_FRA']>0)*network.links_t.p0['H2_Fuel_Cell_FRA']),
          sum((network.stores_t.p['battery_storage_FRA']>0)*network.stores_t.p['battery_storage_FRA']),
          sum((network.links_t.p0['DEU_FRA']>0)*network.links_t.p0['DEU_FRA'])]

colors = ['green', 'orange', 'grey', 'brown', 'red', 'teal', 'blue','purple','yellow','lightblue']

plt.pie(sizes, 
        colors=colors, 
        labels=labels, 
        wedgeprops={'linewidth':0})

plt.title('Electricity mix FRA with heating demand', y=1.07)

# printing more results


print(space)
print('capacity factors in % [FRA]')
capacity_factors=sizes[0:6]/(network.generators.p_nom_opt[6:12]*8760)*100
print(capacity_factors)
#print(sizes[6]/(network.storage_units.p_nom_opt[1]*8760)*100)
print(sizes[7:9]/(network.stores.e_nom_opt[2:4]*8760*0.5)*100)
print(space)
print('elextricity mix in % [FRA]')
print(sizes/sum(sizes)*100)
print(space)
print('CO2 emissions from [FRA] gas as % of [DEU] 1990 levels')
print(sizes[2]*gas_emissions/(Co2_1990)*100)
print(space)
print('CO2 emissions from [FRA] coal as % of [DEU] 1990 levels')
print(sizes[3]*coal_emissions/(Co2_1990)*100)
print(space)
print('CO2 price')
print(network.global_constraints.mu)
print(space)
print('total power generated in [FRA] (inlcuding from storage) as % of total demand in FRA')
print(sum(sizes[0:9])/sum(demand_FRA)*100)
