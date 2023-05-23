import time
import os
def follow(thefile):
    '''generator function that yields new lines in a file
    '''
    # seek the end of the file
    thefile.seek(0, os.SEEK_END)
    
    # start infinite loop
    while True:
        # read last line of file
        line = thefile.readline()
        # sleep if file hasn't been updated
        if not line:
            time.sleep(0.1)
            continue

        yield line

if __name__ == '__main__':
    
    logfile = open("/tmp/klippy.log","r")
    loglines = follow(logfile)
    # iterate over the generator

    table = []

    temperature = float(input("Enter temperature:"))
    samples = 10

    while temperature > 0:
        avg = 0.0

        for _ in range(samples):
            with open('/tmp/printer', 'a') as the_file:
                the_file.write('QUERY_ADC NAME=extruder\n')

        
            
            #find next temp
            line = None
            while not line: 
                line = next(loglines)
                if 'ADC object "extruder" has value' not in line:
                    line = None
                else:
                    temp = float(line.split()[5])
                    avg += temp
            
                    print(temp, line)

        avg = avg/samples

        print(avg, temperature)
        table.append((temperature,avg))
        temperature = float(input("Enter temperature:"))

    print
    print("raw table:")
    print(table)

    table.sort(reverse=True)

    print
    print("sheets table:")
    for t,adc in table:
        print t, adc 

    print
    print("klipper table")
    for idx, (t, adc) in enumerate(table):
        print("temperature{0}: {1}".format(idx+1,t))
        vol = adc*4.096
        print("voltage{0}:{1}".format(idx+1,vol))

# # saved table
# conv = [(300.0, 0.074908), (295.0, 0.084035), (287.0, 0.093346), (285.0, 0.095788), (276.0, 0.106013), (272.0, 0.109524), (268.0, 0.117399), (262.0, 0.124267), (256.0, 0.131227), (253.0, 0.139896), (246.0, 0.156746), (242.0, 0.160531), (236.0, 0.176618), (234.0, 0.181807), (225.0, 0.203938), (220.0, 0.222283), (213.0, 0.244261), (208.0, 0.266392), (202.0, 0.290385), (197.0, 0.30928), (190.0, 0.341941), (184.0, 0.369139), (178.0, 0.398291), (172.0, 0.426862), (168.0, 0.45586100000000007), (163.0, 0.48779000000000006), (159.0, 0.514988), (153.0, 0.545696), (149.0, 0.573077), (143.0, 0.6058), (137.0, 0.637302), (132.0, 0.666728), (127.0, 0.699328), (122.0, 0.72732), (110.0, 0.792613), (103.0, 0.821886), (96.0, 0.849512), (91.0, 0.868315), (85.0, 0.881227), (81.0, 0.896154), (76.0, 0.911477), (70.0, 0.927228), (63.0, 0.944933), (55.0, 0.961111), (47.0, 0.972497), (43, 0.969943), (23, 0.9945463333), (22, 0.9947141667), (20, 0.9956806667), (19, 0.996085125)]

# conv.sort(reverse=True)

# print
# print("klipper table2")

# print
# print("klipper table2")
# for idx, (t, adc) in enumerate(conv):
#     print("temperature{0}: {1}".format(idx+1, t))
#     vol = adc*4.096
#     print("voltage{0}:{1}".format(idx+1,vol))