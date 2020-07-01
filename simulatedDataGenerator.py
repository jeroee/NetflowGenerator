from datetime import datetime,timedelta
import numpy as np
import matplotlib.pyplot as plt
import random
from random import randrange
import socket
import struct
import math
import pandas as pd
import networkx as nx


def main():
    print("Netflow Data Simulation\n")
    start_datetime = "23/6/2020 11:00"
    end_datetime = "24/6/2020 11:00"
    total_entries = 30000
    total_ips = 100
    start_datetimeObj, time_diff = timeline(start_datetime,end_datetime)            #get start time and total duration
    output = distribution(start_datetimeObj,time_diff)                              #get proportional distribution based on total duration
    entry_count = entryAllocation(total_entries, output, time_diff)                 #get list of entries per min interval based on distribution
    timestamp = timestamp_generator(entry_count,start_datetimeObj)                  #generating timestamp for entries based on number of entries per min
    source_IP, destination_IP = ip_generator(total_ips,entry_count)                 #generating source IPs and destination IPs based on an ip pool
    protocols = protocol_generator(entry_count)                                     #generating protocols
    bytes, packets = bytes_packets_generator(entry_count)                           #generating packets and bytes
    df = simulate_data(bytes,packets,protocols,source_IP,destination_IP,timestamp)  #simulating data

    #uncomment if you do not wish to view the scatter plot or the network graph
    scatter_plot(output,entry_count,start_datetime,end_datetime,time_diff)          #illustrates the distribution of entry flows after rounding error
    # network_graph(source_IP,destination_IP)                                         # shows the relationship between network of IPS communicating via a network graph (might take a long time to generate the graph)
    save_csv(df,start_datetime,end_datetime)                                        #saves simulated dataframe into a csv file


def save_csv(df,start_datetime,end_datetime):    #saves simulated dataframe into a csv file
    start = start_datetime.replace(' ', '_').replace('/', '').replace(':', '')
    end = end_datetime.replace(' ', '_').replace('/', '').replace(':', '')
    df.to_csv("simulated_data_{}_to_{}.csv".format(start,end))    #save to csv

def scatter_plot(output,entry_count,start_datetime,end_datetime,time_diff):
    #scatter plot to show the distribution of entries with rounding error
    X = np.array([range(len(output))])
    Y = np.array(output)
    Z = np.array(entry_count)
    positions=[]
    for i in range(1,time_diff):
        positions.append(i)
    start_datetimeObj = datetime.strptime(start_datetime, '%d/%m/%Y %H:%M')
    ls1=[]
    ls2=[]
    for i in range(time_diff//5+1):
        ls1.append(i+1)
        time = str(start_datetimeObj.time())[:-3]
        ls2.append(time)
        start_datetimeObj = start_datetimeObj + timedelta(minutes=5)
    plt.xticks(np.arange(0,time_diff+1,5),np.array(ls2))

    # Plotting point using scatter method
    d_proportion= plt.scatter(X,Y)
    d_actualValues = plt.scatter(X,Z)
    plt.legend((d_proportion,d_actualValues),('Distribution based on proportion of flows per min','Distribution of actual number of flows per minute'))
    plt.title('Data distribution: from {} to {}'.format(start_datetime,end_datetime), fontsize = 20)
    plt.ylabel('distribution')
    plt.xlabel('timeline')
    plt.show()

def network_graph(source_IP,destination_IP): #shows the relationship between network of IPS communicating via a network graph
    G = nx.DiGraph()
    for i in range(len(source_IP)):
        G.add_edge(source_IP[i], destination_IP[i])
    nx.draw(G, with_labels=True,font_size=7,node_color= 'g', node_size=150)
    plt.show()

def timeline(start_datetime, end_datetime):    #get start/end datetime objects, get time difference in minutes
    start_datetimeObj = datetime.strptime(start_datetime,'%d/%m/%Y %H:%M')
    end_datetimeObj = datetime.strptime(end_datetime,'%d/%m/%Y %H:%M')

    print("starting at: ",start_datetimeObj)
    print("ending at: ",end_datetimeObj)
    time_diff = int((end_datetimeObj-start_datetimeObj).total_seconds()/60)
    print("Duration is: ",time_diff," minutes")
    return start_datetimeObj, time_diff

def distribution(start_datetimeObj, time_diff):    #generate distribution of flows from the 24hr time distribution based on configurable input datetime
    reference_datetime = "{}/{}/{} 11:00".format(str(start_datetimeObj.day),str(start_datetimeObj.month),str(start_datetimeObj.year))
    reference_datetimeObj = datetime.strptime(reference_datetime,'%d/%m/%Y %H:%M')
    offset = int((start_datetimeObj - reference_datetimeObj).total_seconds())
    if offset<0:
        reference_datetimeObj = reference_datetimeObj - timedelta(days=1)
    startPoint = int((start_datetimeObj-reference_datetimeObj).total_seconds()/60)
    counter = time_diff
    ls = distribution_24hr()      # getting the distribution based on proportion for 24hr timeframe
    output = []                   #new distribution list
    while counter!=0:
        output.append(ls[startPoint])
        startPoint+=1
        counter-=1
        if startPoint==len(ls):
            startPoint=0
    return output

def entryAllocation(total_entries, output, time_diff):  #generate a list of number of flows per minute
    entry_count = []
    for i in output:
        value = i*(total_entries/sum(output))
        entry_count.append(value)
    for i in range(len(entry_count)):
        entry_count[i] = round(entry_count[i])      #rounding up/down entry_count per minute
    threshold = 30000/1440                          # threshold value taken into account to create a decent looking distribution: min of 30000 entries for 24hr period
    if (total_entries/time_diff)< threshold :       # if it does not meet a certain threshold, re-enter number of entries that you want
        new_entry = int(input("Too little entries to simulate data, please key in a higher number: "))
        return entryAllocation(new_entry, output, time_diff)
    # will provide generated entry counts lesser then selected input due to rounding error
    print("number of entries generated in the selected time period is ",sum(entry_count))
    return entry_count

def timestamp_generator(entry_count,start_datetimeObj): #generate the timestamp for each flow
    print(len(entry_count))
    timestamp_total = []
    for i in range(len(entry_count)):
        time_start = start_datetimeObj+timedelta(minutes=i)
        timestamp=[]
        for i in range(entry_count[i]):
                time = time_start + timedelta(milliseconds=randrange(60000))
                time = time.strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]
                timestamp.append(time)
        timestamp.sort()
        timestamp_total = timestamp_total + timestamp
    return timestamp_total

def ip_generator(total_ips, entry_count): #generate ips based on a fixed pool of unique ip addresses (pool size can be configurable by user)

    data = pd.read_csv("majestic_million.csv") 
    print(data.head())
    ip_pool=[]
    dic = {}
    sourceIp_pool=[]
    destinationIp_pool=[]
    for i in range(total_ips):
        ip_pool.append(socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff))))
    for i in range(sum(entry_count)):
        source = random.choice(ip_pool)
        destination = random.choice(ip_pool)
        while source == destination:
            source = random.choice(ip_pool)
            destination = random.choice(ip_pool)
        sourceIp_pool.append(source)
        destinationIp_pool.append(destination)
    return sourceIp_pool, destinationIp_pool

def protocol_generator(entry_count): #generate protocol (Random)
    protocols=[]
    for i in range(sum(entry_count)):
        protocols.append(random.randint(0,143))
    # print("Protocols",protocols)
    # print(len(protocols))
    return protocols

def bytes_packets_generator(entry_count):  #generate byes and packets  (Random)
    bytes=[]
    packets=[]
    packetSize = 1500 #assumption of 1 packet holds an approximate size of 1500 bytes
    for i in range(sum(entry_count)):
        byte = round(random.uniform(1500, 30000), 1)
        packet = math.ceil(byte / packetSize)
        bytes.append(byte)
        packets.append(packet)
    return bytes, packets

def simulate_data(bytes,packets,protocols,source_IP,destination_IP,timestamp):  #simulate data and generate into a dataframe
    df = pd.DataFrame(np.array([bytes,packets,protocols,source_IP,destination_IP,timestamp]).transpose(),\
                               columns=['bytes', 'packets', 'protocol', 'sourceIP','Destination IP','timestamp'])
    pd.set_option('display.max_columns', None)
    print("Displaying first 10 entries of dataframe for viewing")
    print(df.head(10))
    return df

# distribution of flows based on proportion in a 24hr time period 1100-1100
def distribution_24hr():
    ls1100_1200=[3.9516666666666667, 3.953333333333333, 3.9549999999999996, 3.956666666666666, 3.9583333333333326, 3.959999999999999, 3.9616666666666656, 3.963333333333332, 3.9649999999999985, 3.966666666666665, 3.9683333333333315, 3.969999999999998, 3.9716666666666645, 3.973333333333331, 3.9749999999999974, 3.976666666666664, 3.9783333333333304, 3.979999999999997, 3.9816666666666634, 3.98333333333333, 3.9849999999999963, 3.986666666666663, 3.9883333333333293, 3.9899999999999958, 3.9916666666666623, 3.9933333333333287, 3.994999999999995, 3.9966666666666617, 3.998333333333328, 3.9999999999999947, 4.001666666666662, 4.0033333333333285, 4.0049999999999955, 4.006666666666662, 4.008333333333329, 4.009999999999996, 4.011666666666663, 4.01333333333333, 4.014999999999997, 4.016666666666664, 4.018333333333331, 4.019999999999998, 4.021666666666665, 4.023333333333332, 4.024999999999999, 4.0266666666666655, 4.028333333333332, 4.029999999999999, 4.031666666666666, 4.033333333333333, 4.035, 4.036666666666667, 4.038333333333334, 4.040000000000001, 4.041666666666668, 4.043333333333335, 4.045000000000002, 4.046666666666669, 4.048333333333336, 4.0500000000000025]
    ls1200_1300=[4.055, 4.06, 4.0649999999999995, 4.069999999999999, 4.074999999999999, 4.079999999999999, 4.084999999999999, 4.089999999999999, 4.094999999999999, 4.099999999999999, 4.104999999999999, 4.1099999999999985, 4.114999999999998, 4.119999999999998, 4.124999999999998, 4.129999999999998, 4.134999999999998, 4.139999999999998, 4.144999999999998, 4.149999999999998, 4.154999999999998, 4.1599999999999975, 4.164999999999997, 4.169999999999997, 4.174999999999997, 4.179999999999997, 4.184999999999997, 4.189999999999997, 4.194999999999997, 4.199999999999997, 4.2049999999999965, 4.209999999999996, 4.214999999999996, 4.219999999999996, 4.224999999999996, 4.229999999999996, 4.234999999999996, 4.239999999999996, 4.244999999999996, 4.249999999999996, 4.2549999999999955, 4.259999999999995, 4.264999999999995, 4.269999999999995, 4.274999999999995, 4.279999999999995, 4.284999999999995, 4.289999999999995, 4.294999999999995, 4.2999999999999945, 4.304999999999994, 4.309999999999994, 4.314999999999994, 4.319999999999994, 4.324999999999994, 4.329999999999994, 4.334999999999994, 4.339999999999994, 4.3449999999999935, 4.349999999999993]
    ls1300_1400=[4.3549999999999995, 4.359999999999999, 4.364999999999999, 4.369999999999999, 4.374999999999999, 4.379999999999999, 4.384999999999999, 4.389999999999999, 4.394999999999999, 4.399999999999999, 4.4049999999999985, 4.409999999999998, 4.414999999999998, 4.419999999999998, 4.424999999999998, 4.429999999999998, 4.434999999999998, 4.439999999999998, 4.444999999999998, 4.4499999999999975, 4.454999999999997, 4.459999999999997, 4.464999999999997, 4.469999999999997, 4.474999999999997, 4.479999999999997, 4.484999999999997, 4.489999999999997, 4.4949999999999966, 4.4999999999999964, 4.504999999999996, 4.509999999999996, 4.514999999999996, 4.519999999999996, 4.524999999999996, 4.529999999999996, 4.534999999999996, 4.539999999999996, 4.5449999999999955, 4.549999999999995, 4.554999999999995, 4.559999999999995, 4.564999999999995, 4.569999999999995, 4.574999999999995, 4.579999999999995, 4.584999999999995, 4.5899999999999945, 4.594999999999994, 4.599999999999994, 4.604999999999994, 4.609999999999994, 4.614999999999994, 4.619999999999994, 4.624999999999994, 4.629999999999994, 4.634999999999994, 4.6399999999999935, 4.644999999999993, 4.649999999999993]
    ls1400_1500=[4.6741739749305555, 4.695208633055556, 4.715883724375, 4.736199248888889, 4.756155206597223, 4.7757515975, 4.794988421597222, 4.813865678888889, 4.832383369375, 4.850541493055555, 4.868340049930556, 4.88577904, 4.902858463263889, 4.9195783197222225, 4.935938609375, 4.9519393322222225, 4.967580488263889, 4.9828620775, 4.997784099930556, 5.012346555555556, 5.026549444375, 5.040392766388889, 5.053876521597223, 5.06700071, 5.079765331597223, 5.092170386388889, 5.104215874375001, 5.115901795555556, 5.127228149930556, 5.138194937500001, 5.148802158263889, 5.159049812222222, 5.168937899375001, 5.1784664197222225, 5.187635373263889, 5.19644476, 5.2048945799305555, 5.212984833055556, 5.220715519375, 5.22808663888889, 5.235098191597222, 5.2417501775, 5.248042596597222, 5.253975448888889, 5.2595487343750005, 5.264762453055556, 5.2696166049305555, 5.27411119, 5.278246208263889, 5.282021659722222, 5.285437544375, 5.288493862222222, 5.291190613263889, 5.2935277975, 5.295505414930555, 5.297123465555556, 5.298381949375, 5.299280866388889, 5.299820216597222, 5.3]
    ls1500_1600=[5.304166666666666, 5.308333333333333, 5.312499999999999, 5.3166666666666655, 5.320833333333332, 5.324999999999998, 5.329166666666665, 5.333333333333331, 5.337499999999998, 5.341666666666664, 5.3458333333333306, 5.349999999999997, 5.354166666666663, 5.35833333333333, 5.362499999999996, 5.366666666666663, 5.370833333333329, 5.374999999999996, 5.379166666666662, 5.383333333333328, 5.387499999999995, 5.391666666666661, 5.395833333333328, 5.399999999999994, 5.404166666666661, 5.408333333333327, 5.412499999999993, 5.41666666666666, 5.420833333333326, 5.424999999999993, 5.429166666666659, 5.433333333333326, 5.437499999999992, 5.441666666666658, 5.445833333333325, 5.449999999999991, 5.454166666666658, 5.458333333333324, 5.462499999999991, 5.466666666666657, 5.4708333333333234, 5.47499999999999, 5.479166666666656, 5.483333333333323, 5.487499999999989, 5.491666666666656, 5.495833333333322, 5.4999999999999885, 5.504166666666655, 5.508333333333321, 5.512499999999988, 5.516666666666654, 5.520833333333321, 5.524999999999987, 5.5291666666666535, 5.53333333333332, 5.537499999999986, 5.541666666666653, 5.545833333333319, 5.549999999999986]
    ls1600_1700=[5.551552022122222, 5.553346957822223, 5.5550500471, 5.556661289955556, 5.558180686388889, 5.5596082364, 5.560943939988889, 5.562187797155556, 5.5633398079, 5.564399972222223, 5.565368290122223, 5.5662447616, 5.567029386655556, 5.567722165288889, 5.5683230975, 5.568832183288889, 5.569249422655556, 5.5695748156, 5.569808362122222, 5.569950062222222, 5.5699999159, 5.569957923155556, 5.569824083988889, 5.5695983984, 5.5692808663888895, 5.568871487955556, 5.5683702631, 5.5677771918222225, 5.567092274122222, 5.56631551, 5.565446899455556, 5.56448644248889, 5.5634341391, 5.562289989288889, 5.561053993055556, 5.5597261504, 5.558306461322222, 5.5567949258222225, 5.5551915439, 5.553496315555556, 5.551709240788889, 5.549830319600001, 5.547859551988889, 5.545796937955556, 5.543642477500001, 5.541396170622223, 5.539058017322223, 5.5366280176, 5.534106171455556, 5.5314924788888895, 5.528786939900001, 5.5259895544888895, 5.523100322655556, 5.5201192444, 5.517046319722223, 5.513881548622223, 5.510624931100001, 5.507276467155556, 5.503836156788889, 5.500304000000001]
    ls1700_1800=[5.498333333333333, 5.496666666666666, 5.494999999999999, 5.493333333333332, 5.491666666666665, 5.489999999999998, 5.4883333333333315, 5.486666666666665, 5.484999999999998, 5.483333333333331, 5.481666666666664, 5.479999999999997, 5.47833333333333, 5.476666666666663, 5.474999999999996, 5.473333333333329, 5.471666666666662, 5.469999999999995, 5.468333333333328, 5.4666666666666615, 5.4649999999999945, 5.463333333333328, 5.461666666666661, 5.459999999999994, 5.458333333333327, 5.45666666666666, 5.454999999999993, 5.453333333333326, 5.451666666666659, 5.449999999999992, 5.448333333333325, 5.446666666666658, 5.444999999999991, 5.4433333333333245, 5.4416666666666575, 5.439999999999991, 5.438333333333324, 5.436666666666657, 5.43499999999999, 5.433333333333323, 5.431666666666656, 5.429999999999989, 5.428333333333322, 5.426666666666655, 5.424999999999988, 5.423333333333321, 5.421666666666654, 5.4199999999999875, 5.418333333333321, 5.416666666666654, 5.414999999999987, 5.41333333333332, 5.411666666666653, 5.409999999999986, 5.408333333333319, 5.406666666666652, 5.404999999999985, 5.403333333333318, 5.401666666666651, 5.399999999999984]
    ls1800_2000=[5.411484580148705, 5.41187286185012, 5.412274270951728, 5.412689251277266, 5.413118261655689, 5.413561776428482, 5.414020285974124, 5.414494297250277, 5.4149843343543145, 5.415490939102798, 5.416014671630542, 5.416556111009936, 5.417115855891205, 5.417694525164315, 5.418292758643256, 5.4189112177734655, 5.419550586363161, 5.420211571339404, 5.420894903529727, 5.421601338470176, 5.422331657240688, 5.4230866673286995, 5.423867203521954, 5.424674128831504, 5.425508335445903, 5.426370745717673, 5.427262313183116, 5.428184023616601, 5.429136896120506, 5.430121984251996, 5.43114037718791, 5.432193200929021, 5.433281619545015, 5.434406836461566, 5.435570095790914, 5.43677268370744, 5.438015929869743, 5.439301208890795, 5.440629941857801, 5.442003597903446, 5.443423695830262, 5.444891805789913, 5.446409551019258, 5.447978609635102, 5.449600716489638, 5.451277665088599, 5.4530113095742845, 5.454803566775615, 5.4566564183274995, 5.4585719128618635, 5.460552168272745, 5.462599374057973, 5.46471579374002, 5.466903767368701, 5.469165714108475, 5.471504134913234, 5.4739216152915215, 5.47642082816523, 5.47900453682496, 5.481675597985294,
                 5.484436964943357, 5.487291690844179, 5.490242932056444, 5.493293951662377, 5.4964481230656155, 5.499708933721064, 5.503079988990848, 5.506565016130632, 5.510167868410717, 5.51389252937646, 5.517743117252745, 5.521723889497346, 5.52583924750826, 5.530093741490163, 5.534492075485422, 5.539039112575173, 5.54373988025627, 5.548599575999998, 5.553623572998741, 5.558817426106921, 5.564186877982807, 5.56973786543797, 5.575476526001397, 5.581409204705547, 5.587542461101815, 5.59388307651321, 5.600438061532207, 5.607214663772119, 5.614220375880521, 5.621462943823603, 5.628950375450611, 5.636690949347839, 5.644693223991968, 5.652966047212865, 5.661518565976318, 5.670360236497507, 5.679500834696406, 5.688950467006667, 5.6987195815499465, 5.708818979688018, 5.719259827965454, 5.730053670456077, 5.741212441526832, 5.752748479033186, 5.76467453796066, 5.777003804527559, 5.789749910764503, 5.802926949586882, 5.816549490376883, 5.830632595092345, 5.84519183492022, 5.8602433074930875, 5.875803654687729, 5.891890081025458, 5.908520372694548, 5.925712917215784, 5.9434867237728914, 5.961861444230313, 5.980857394861573, 6.0004955788122585]
    ls2000_0000=[6.017753826388889, 6.035348638888889, 6.0527844375, 6.070061222222222, 6.087178993055556, 6.1041377500000005, 6.120937493055556, 6.137578222222222, 6.1540599375000005, 6.170382638888889, 6.186546326388889, 6.202551000000001, 6.218396659722223, 6.234083305555556, 6.2496109375, 6.264979555555556, 6.280189159722223, 6.29523975, 6.310131326388889, 6.324863888888889, 6.339437437500001, 6.353851972222223, 6.368107493055557, 6.382204000000001, 6.3961414930555565, 6.409919972222223, 6.423539437500001, 6.43699988888889, 6.45030132638889, 6.463443750000001, 6.476427159722223, 6.4892515555555565, 6.501916937500001, 6.514423305555557, 6.526770659722223, 6.538959000000001, 6.5509883263888895, 6.56285863888889, 6.574569937500001, 6.586122222222223, 6.597515493055557, 6.608749750000001, 6.619824993055556, 6.630741222222223, 6.641498437500001, 6.65209663888889, 6.66253582638889, 6.672816000000001, 6.682937159722223, 6.692899305555557, 6.702702437500001, 6.712346555555556, 6.721831659722223, 6.731157750000001, 6.74032482638889, 6.7493328888888895, 6.758181937500001, 6.766871972222223, 6.775402993055557, 6.783775000000001, 6.791987993055557,
                 6.800041972222223, 6.807936937500001, 6.81567288888889, 6.823249826388889, 6.830667750000001, 6.837926659722223, 6.845026555555556, 6.851967437500001, 6.858749305555556, 6.865372159722223, 6.871836000000001, 6.87814082638889, 6.88428663888889, 6.890273437500001, 6.896101222222223, 6.901769993055557, 6.907279750000001, 6.912630493055556, 6.917822222222223, 6.9228549375, 6.9277286388888895, 6.932443326388889, 6.936999000000001, 6.941395659722223, 6.945633305555556, 6.949711937500001, 6.953631555555556, 6.957392159722223, 6.960993750000001, 6.964436326388889, 6.967719888888889, 6.9708444375, 6.973809972222223, 6.976616493055556, 6.979264000000001, 6.981752493055556, 6.9840819722222225, 6.9862524375, 6.9882638888888895, 6.990116326388889, 6.99180975, 6.993344159722223, 6.994719555555556, 6.9959359375000005, 6.996993305555556, 6.997891659722223, 6.9986310000000005, 6.999211326388889, 6.9996326388888885, 6.9998949375, 6.999998222222223, 6.999942493055555, 6.99972775, 6.999353993055555, 6.998821222222222, 6.9981294375, 6.997278638888889, 6.996268826388889, 6.9951, 6.993772159722222, 6.992285305555555, 6.9906394375, 6.988834555555555,
                 6.986870659722222, 6.9847477499999995, 6.982465826388888, 6.980024888888889, 6.9774249374999995, 6.974665972222222, 6.971747993055555, 6.968671, 6.965434993055555, 6.962039972222222, 6.9584859375, 6.954772888888888, 6.950900826388889, 6.946869749999999, 6.942679659722222, 6.938330555555555, 6.933822437499999, 6.929155305555555, 6.924329159722221, 6.919344, 6.914199826388888, 6.908896638888888, 6.9034344375, 6.897813222222221, 6.892032993055555, 6.886093749999999, 6.879995493055555, 6.873738222222221, 6.867321937499999, 6.860746638888888, 6.8540123263888875, 6.847118999999999, 6.840066659722221, 6.8328553055555545, 6.825484937499999, 6.817955555555554, 6.810267159722221, 6.8024197499999985, 6.794413326388888, 6.786247888888887, 6.777923437499998, 6.769439972222221, 6.760797493055554, 6.751995999999998, 6.743035493055554, 6.733915972222221, 6.724637437499998, 6.715199888888887, 6.7056033263888875, 6.695847749999998, 6.685933159722221, 6.6758595555555535, 6.665626937499998, 6.6552353055555535, 6.64468465972222, 6.633974999999998, 6.6231063263888865, 6.612078638888887, 6.6008919374999975, 6.58954622222222, 6.5780414930555535,
                 6.566377749999997, 6.554554993055553, 6.542573222222219, 6.530432437499997, 6.518132638888886, 6.505673826388886, 6.4930559999999975, 6.480279159722219, 6.467343305555553, 6.454248437499997, 6.440994555555553, 6.427581659722219, 6.414009749999996, 6.4002788263888855, 6.386388888888885, 6.372339937499997, 6.3581319722222185, 6.343764993055552, 6.329238999999997, 6.314553993055552, 6.299709972222218, 6.284706937499996, 6.269544888888885, 6.254223826388885, 6.238743749999996, 6.223104659722218, 6.207306555555552, 6.191349437499996, 6.175233305555551, 6.158958159722218, 6.142523999999995, 6.125930826388885, 6.109178638888884, 6.092267437499995, 6.075197222222218, 6.05796799305555, 6.040579749999996, 6.023032493055551, 6.005326222222218, 5.9874609374999945, 5.969436638888884, 5.951253326388883, 5.9329109999999945, 5.914409659722217, 5.89574930555555, 5.876929937499995, 5.85795155555555, 5.838814159722217, 5.819517749999994, 5.800062326388883, 5.780447888888883, 5.760674437499993, 5.7407419722222155, 5.720650493055549, 5.700399999999994]
    ls0000_0100=[5.6725, 5.6450000000000005, 5.617500000000001, 5.590000000000001, 5.562500000000001, 5.535000000000001, 5.507500000000001, 5.480000000000001, 5.4525000000000015, 5.425000000000002, 5.397500000000002, 5.370000000000002, 5.342500000000002, 5.315000000000002, 5.287500000000002, 5.2600000000000025, 5.232500000000003, 5.205000000000003, 5.177500000000003, 5.150000000000003, 5.122500000000003, 5.095000000000003, 5.0675000000000034, 5.040000000000004, 5.012500000000004, 4.985000000000004, 4.957500000000004, 4.930000000000004, 4.902500000000004, 4.875000000000004, 4.847500000000005, 4.820000000000005, 4.792500000000005, 4.765000000000005, 4.737500000000005, 4.710000000000005, 4.682500000000005, 4.655000000000006, 4.627500000000006, 4.600000000000006, 4.572500000000006, 4.545000000000006, 4.517500000000006, 4.490000000000006, 4.462500000000007, 4.435000000000007, 4.407500000000007, 4.380000000000007, 4.352500000000007, 4.325000000000007, 4.297500000000007, 4.270000000000008, 4.242500000000008, 4.215000000000008, 4.187500000000008, 4.160000000000008, 4.132500000000008, 4.105000000000008, 4.077500000000009, 4.050000000000009]
    ls0100_0900=[4.031563425625, 4.0104846025, 3.989484530625, 3.96856321, 3.9477206406249996, 3.9269568224999993, 3.9062717556249993, 3.8856654399999995, 3.865137875624999, 3.8446890624999988, 3.8243190006249987, 3.804027689999999, 3.7838151306249985, 3.763681322499999, 3.7436262656249983, 3.7236499599999986, 3.703752405624998, 3.683933602499998, 3.664193550624998, 3.6445322499999984, 3.624949700624998, 3.605445902499998, 3.586020855624998, 3.5666745599999983, 3.547407015624998, 3.528218222499998, 3.509108180624998, 3.4900768899999974, 3.471124350624997, 3.452250562499997, 3.4334555256249972, 3.4147392399999976, 3.3961017056249974, 3.3775429224999973, 3.3590628906249966, 3.340661609999997, 3.322339080624997, 3.304095302499997, 3.285930275624997, 3.2678439999999966, 3.2498364756249964, 3.2319077024999965, 3.2140576806249967, 3.1962864099999964, 3.178593890624996, 3.1609801224999963, 3.143445105624996, 3.125988839999996, 3.108611325624996, 3.091312562499996, 3.0740925506249956, 3.0569512899999958, 3.0398887806249957, 3.0229050224999954, 3.0060000156249957, 2.9891737599999955, 2.9724262556249954, 2.9557575024999956, 2.939167500624995,
                 2.9226562499999953, 2.9062237506249953, 2.889870002499995, 2.873595005624995, 2.8573987599999953, 2.8412812656249953, 2.8252425224999946, 2.809282530624995, 2.793401289999995, 2.777598800624995, 2.761875062499995, 2.746230075624995, 2.7306638399999947, 2.715176355624995, 2.6997676224999942, 2.684437640624995, 2.6691864099999947, 2.6540139306249944, 2.6389202024999943, 2.6239052256249944, 2.6089689999999943, 2.594111525624994, 2.5793328024999944, 2.564632830624994, 2.550011609999994, 2.5354691406249943, 2.521005422499994, 2.506620455624994, 2.492314239999994, 2.478086775624994, 2.463938062499994, 2.449868100624994, 2.435876889999994, 2.421964430624994, 2.408130722499994, 2.3943757656249938, 2.380699559999994, 2.3671021056249937, 2.3535834024999938, 2.3401434506249936, 2.3267822499999937, 2.3134998006249936, 2.3002961024999937, 2.2871711556249936, 2.2741249599999938, 2.2611575156249932, 2.2482688224999934, 2.2354588806249933, 2.2227276899999935, 2.2100752506249934, 2.197501562499993, 2.185006625624993, 2.1725904399999934, 2.1602530056249933, 2.1479943224999936, 2.135814390624993, 2.1237132099999934, 2.1116907806249934,
                 2.099747102499993, 2.0878821756249932, 2.076095999999993, 2.064388575624993, 2.052759902499993, 2.041209980624993, 2.0297388099999933, 2.018346390624993, 2.007032722499993, 1.995797805624993, 1.984641639999993, 1.973564225624993, 1.9625655624999931, 1.951645650624993, 1.940804489999993, 1.9300420806249932, 1.919358422499993, 1.908753515624993, 1.8982273599999933, 1.887779955624993, 1.877411302499993, 1.8671214006249932, 1.8569102499999932, 1.846777850624993, 1.836724202499993, 1.8267493056249933, 1.816853159999993, 1.8070357656249931, 1.7972971224999932, 1.787637230624993, 1.778056089999993, 1.7685537006249932, 1.759130062499993, 1.7497851756249934, 1.7405190399999932, 1.7313316556249934, 1.7222230224999933, 1.7131931406249934, 1.7042420099999933, 1.6953696306249932, 1.6865760024999932, 1.6778611256249933, 1.6692249999999933, 1.6606676256249933, 1.6521890024999935, 1.6437891306249934, 1.6354680099999934, 1.6272256406249934, 1.6190620224999934, 1.6109771556249934, 1.6029710399999935, 1.5950436756249935, 1.5871950624999935, 1.5794252006249936, 1.5717340899999936, 1.5641217306249937, 1.5565881224999938, 1.5491332656249936,
                 1.5417571599999937, 1.5344598056249938, 1.5272412024999937, 1.5201013506249939, 1.5130402499999938, 1.506057900624994, 1.4991543024999938, 1.492329455624994, 1.485583359999994, 1.478916015624994, 1.472327422499994, 1.4658175806249942, 1.4593864899999942, 1.4530341506249942, 1.4467605624999944, 1.4405657256249944, 1.4344496399999944, 1.4284123056249947, 1.4224537224999947, 1.4165738906249947, 1.4107728099999948, 1.405050480624995, 1.399406902499995, 1.3938420756249952, 1.3883559999999953, 1.3829486756249953, 1.3776201024999954, 1.3723702806249956, 1.3671992099999957, 1.3621068906249958, 1.3570933224999957, 1.3521585056249958, 1.347302439999996, 1.342525125624996, 1.337826562499996, 1.3332067506249963, 1.3286656899999962, 1.3242033806249964, 1.3198198224999964, 1.3155150156249964, 1.3112889599999966, 1.3071416556249966, 1.3030731024999969, 1.2990833006249969, 1.295172249999997, 1.291339950624997, 1.287586402499997, 1.283911605624997, 1.2803155599999971, 1.2767982656249972, 1.2733597224999973, 1.2699999306249974, 1.2667188899999975, 1.2635166006249976, 1.2603930624999977, 1.2573482756249976, 1.2543822399999978, 1.251494955624998,
                 1.2486864224999978, 1.245956640624998, 1.243305609999998, 1.2407333306249981, 1.238239802499998, 1.235825025624998, 1.2334889999999983, 1.2312317256249983, 1.2290532024999983, 1.2269534306249983, 1.2249324099999985, 1.2229901406249986, 1.2211266224999986, 1.2193418556249986, 1.2176358399999987, 1.2160085756249988, 1.2144600624999988, 1.212990300624999, 1.211599289999999, 1.210287030624999, 1.209053522499999, 1.207898765624999, 1.2068227599999992, 1.2058255056249991, 1.2049070024999993, 1.2040672506249994, 1.2033062499999994, 1.2026240006249995, 1.2020205024999995, 1.2014957556249997, 1.2010497599999996, 1.2006825156249996, 1.2003940224999998, 1.2001842806249998, 1.2000532899999998, 1.2000010506249998, 1.2000275625, 1.2001328256250001, 1.2003168400000002, 1.2005796056250002, 1.2009211225000003, 1.2013413906250003, 1.2018404100000004, 1.2024181806250005, 1.2030747025000006, 1.2038099756250005, 1.2046240000000006, 1.2055167756250007, 1.2064883025000008, 1.2075385806250007, 1.208667610000001, 1.2098753906250008, 1.211161922500001, 1.212527205625001, 1.2139712400000011, 1.215494025625001, 1.2170955625000013, 1.2187758506250013,
                 1.2205348900000013, 1.2223726806250015, 1.2242892225000015, 1.2262845156250015, 1.2283585600000015, 1.2305113556250016, 1.2327429025000016, 1.2350532006250017, 1.2374422500000017, 1.2399100506250018, 1.242456602500002, 1.245081905625002, 1.247785960000002, 1.2505687656250022, 1.2534303225000023, 1.2563706306250022, 1.2593896900000023, 1.2624875006250025, 1.2656640625000024, 1.2689193756250026, 1.2722534400000025, 1.2756662556250027, 1.2791578225000027, 1.2827281406250026, 1.2863772100000028, 1.2901050306250028, 1.2939116025000028, 1.2977969256250028, 1.3017610000000028, 1.3058038256250029, 1.3099254025000029, 1.314125730625003, 1.318404810000003, 1.322762640625003, 1.327199222500003, 1.3317145556250032, 1.3363086400000033, 1.3409814756250031, 1.3457330625000032, 1.3505634006250034, 1.3554724900000035, 1.3604603306250034, 1.3655269225000035, 1.3706722656250034, 1.3758963600000036, 1.3811992056250035, 1.3865808025000035, 1.3920411506250037, 1.3975802500000036, 1.4031981006250036, 1.4088947025000036, 1.4146700556250038, 1.4205241600000038, 1.4264570156250038, 1.4324686225000038, 1.4385589806250039, 1.444728090000004, 1.450975950625004,
                 1.457302562500004, 1.463707925625004, 1.4701920400000041, 1.4767549056250042, 1.4833965225000043, 1.4901168906250044, 1.4969160100000045, 1.5037938806250046, 1.5107505025000045, 1.5177858756250047, 1.5249000000000048, 1.532092875625005, 1.5393645025000051, 1.546714880625005, 1.5541440100000052, 1.5616518906250052, 1.5692385225000054, 1.5769039056250054, 1.5846480400000056, 1.5924709256250056, 1.6003725625000058, 1.6083529506250058, 1.616412090000006, 1.624549980625006, 1.6327666225000061, 1.6410620156250062, 1.6494361600000063, 1.6578890556250063, 1.6664207025000066, 1.6750311006250067, 1.6837202500000068, 1.692488150625007, 1.701334802500007, 1.7102602056250071, 1.719264360000007, 1.7283472656250072, 1.7375089225000075, 1.7467493306250075, 1.7560684900000076, 1.7654664006250078, 1.7749430625000078, 1.784498475625008, 1.794132640000008, 1.8038455556250081, 1.8136372225000081, 1.8235076406250084, 1.8334568100000084, 1.8434847306250086, 1.8535914025000086, 1.863776825625009, 1.874041000000009, 1.8843839256250092, 1.8948056025000093, 1.9053060306250094, 1.9158852100000094, 1.9265431406250095, 1.9372798225000096, 1.94809525562501,
                 1.95898944000001, 1.96996237562501, 1.98101406250001, 1.9921445006250105, 2.0033536900000106, 2.0146416306250106, 2.0260083225000107, 2.0374537656250107, 2.048977960000011, 2.0605809056250113, 2.072262602500011, 2.0840230506250115, 2.0958622500000117, 2.1077802006250117, 2.119776902500012, 2.131852355625012, 2.144006560000012, 2.1562395156250123, 2.168551222500012, 2.1809416806250126, 2.1934108900000124, 2.205958850625013, 2.218585562500013, 2.231291025625013, 2.2440752400000132, 2.2569382056250133, 2.2698799225000137, 2.282900390625014, 2.2959996100000137, 2.309177580625014, 2.322434302500014, 2.335769775625014, 2.3491840000000144, 2.3626769756250146, 2.376248702500015, 2.3898991806250147, 2.4036284100000147, 2.4174363906250154, 2.4313231225000154, 2.4452886056250156, 2.4593328400000156, 2.473455825625016, 2.487657562500016, 2.501938050625016, 2.5162972900000162, 2.5307352806250165, 2.5452520225000166, 2.559847515625017, 2.574521760000017, 2.5892747556250173, 2.6041065025000174, 2.6190170006250173, 2.6340062500000174, 2.649074250625018, 2.664221002500018, 2.679446505625018, 2.6947507600000185, 2.7101337656250184, 2.7255955225000186,
                 2.741136030625019, 2.7567552900000187, 2.7724533006250187, 2.788230062500019, 2.8040855756250194, 2.8200198400000196, 2.83603285562502, 2.85212462250002, 2.86829514062502, 2.8845444100000206, 2.9008724306250206, 2.917279202500021, 2.9337647256250206, 2.9503290000000213]
    ls0900_1100=[2.966396164930555, 2.979754159722222, 2.993032984374999, 3.0062326388888883, 3.0193531232638877, 3.032394437499999, 3.045356581597221, 3.058239555555554, 3.071043359374998, 3.0837679930555537, 3.09641345659722, 3.108979749999998, 3.121466873263887, 3.133874826388887, 3.1462036093749983, 3.1584532222222204, 3.170623664930554, 3.1827149374999983, 3.194727039930554, 3.2066599722222207, 3.2185137343749988, 3.2302883263888873, 3.2419837482638876, 3.2535999999999987, 3.265137081597221, 3.2765949930555545, 3.287973734374999, 3.2992733055555545, 3.3104937065972213, 3.321634937499999, 3.332696998263888, 3.343679888888888, 3.354583609374999, 3.3654081597222216, 3.376153539930555, 3.3868197499999995, 3.397406789930555, 3.4079146597222216, 3.4183433593749997, 3.4286928888888886, 3.4389632482638888, 3.4491544375, 3.4592664565972218, 3.4692993055555554, 3.479252984375, 3.4891274930555554, 3.498922831597222, 3.508639, 3.518275998263889, 3.527833826388889, 3.537312484375, 3.5467119722222225, 3.5560322899305556, 3.5652734375, 3.574435414930556, 3.5835182222222226, 3.592521859375, 3.6014463263888894, 3.610291623263889, 3.6190577500000005, 3.627744706597223,
                 3.636352493055556, 3.6448811093750004, 3.653330555555556, 3.661700831597223, 3.6699919375000007, 3.6782038732638895, 3.6863366388888896, 3.6943902343750006, 3.702364659722223, 3.7102599149305564, 3.718076000000001, 3.7258129149305566, 3.733470659722223, 3.7410492343750006, 3.74854863888889, 3.75596887326389, 3.7633099375000008, 3.770571831597223, 3.7777545555555565, 3.784858109375001, 3.7918824930555566, 3.798827706597223, 3.805693750000001, 3.8124806232638897, 3.8191883263888897, 3.825816859375001, 3.8323662222222232, 3.8388364149305567, 3.845227437500001, 3.8515392899305567, 3.8577719722222232, 3.863925484375001, 3.8699998263888897, 3.8759949982638897, 3.881911000000001, 3.887747831597223, 3.893505493055556, 3.899183984375001, 3.904783305555556, 3.910303456597223, 3.915744437500001, 3.9211062482638894, 3.9263888888888894, 3.9315923593750006, 3.9367166597222227, 3.941761789930556, 3.9467277500000004, 3.951614539930556, 3.9564221597222224, 3.961150609375, 3.9657998888888892, 3.970369998263889, 3.9748609375000004, 3.9792727065972224, 3.983605305555556, 3.987858734375, 3.9920329930555556, 3.9961280815972224, 4.000144]


    ls_total = ls1100_1200 + ls1200_1300 + ls1300_1400 + ls1400_1500 + ls1500_1600 + ls1600_1700 + ls1700_1800+ ls1800_2000+ ls2000_0000+ ls0000_0100+ ls0100_0900 + ls0900_1100

    return ls_total

if __name__ == "__main__":
    main()

