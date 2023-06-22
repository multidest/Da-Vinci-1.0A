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
    
    logfile = open("/home/pi/printer_data/logs/klippy.log","r")
    loglines = follow(logfile)
    # iterate over the generator

    table = []

    temperature = float(input("Enter temperature:"))
    samples = 6
    sensor = "heater_bed"

    while temperature > 0:
        avg = 0.0

        for _ in range(samples):
            with open('/home/pi/printer_data/comms/klippy.serial', 'w') as the_file:
                the_file.write(f'QUERY_ADC NAME="{sensor}"\n')

            #find next temp
            line = None
            while not line: 
                line = next(loglines)
                if f'ADC object "{sensor}" has value' not in line:
                    line = None
                else:
                    temp = float(line.split()[5])
                    avg += temp
            
                    print(temp, line)

        avg = avg/samples

        print(avg, temperature)
        table.append((temperature,avg))
        temperature = float(input("Enter temperature:"))

    print()
    print("raw table:")
    print(table)

    table.sort(reverse=True)
    print()
    print("sheets table:")
    for t,adc in table:
        print(t, adc) 
