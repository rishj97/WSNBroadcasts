import sys
import numpy as np
from datetime import datetime
TOTAL_NODES = 30
DEVICE_NUM = 4
BROADCAST_INDEX = 2
TIMESTAMP_INDEX = 0
TIMESTAMP_FORMAT = '%M:%S.%f'
WARMUP_TIME = datetime.strptime('05:00.000', TIMESTAMP_FORMAT)

def main():
    current_message_num = -1
    cur_start_time = None
    last_received_time = None
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = 'log_full.txt'
    with open('Logs/' + log_file) as log_file:
        count = 0
        msg_times = {}
        msg_receivers = {}
        total_power_devices = [0.0] * TOTAL_NODES
        power_readings = [0] * TOTAL_NODES
        for line in log_file:
            if len(line) == 0:
                break
            values = line.split()
            log_time = datetime.strptime(values[TIMESTAMP_INDEX], TIMESTAMP_FORMAT)
            if log_time < WARMUP_TIME:
                continue
            if values[3] == 'P':
                # Incase of powertrace output
                power = calculate_power(values)
                device_number = int(float(values[DEVICE_NUM]))
                total_power_devices[device_number - 1] += power
                power_readings[device_number - 1] += 1
            elif values[BROADCAST_INDEX] == 'Broadcast':
                msg_receiver = values[1]
                # Incase of broadcast message
                if values[4] == 'sent' and len(values) == 6:
                    # Case of first broadcast message
                    msg_num = int(values[5])
                    msg_times[msg_num] = (log_time, None)
                    msg_receivers[msg_num] = set()
                    msg_receivers[msg_num].add(msg_receiver)
                elif values[3] == 'recv':
                    # Case of some message received
                    msg_number = int(values[10])
                    if msg_number in msg_times:
                        (strt_time, _) = msg_times[msg_number]
                        msg_times[msg_number] = (strt_time, log_time)
                        msg_receivers[msg_number].add(msg_receiver)
    calc_avg_loss_rate(msg_receivers)

    calc_avg_power_consumption(total_power_devices, power_readings)

    calc_avg_dissemination_time(msg_times)


def calc_avg_loss_rate(msg_receivers):
    total_msgs = 0
    total_loss_rate = 0.0
    for msg in msg_receivers:
        receivers = msg_receivers[msg]
        if receivers is not None:
            loss_rate = len(receivers)/float(TOTAL_NODES)
            total_loss_rate += loss_rate
            total_msgs += 1
        else:
            print "Message ", msg, " had error with receiving"
    avg_loss_rate = total_loss_rate / total_msgs * 100
    print "Average end to end loss rate:\t", round(avg_loss_rate, 2), "%"

def calc_avg_power_consumption(total_power_devices, power_readings):
    average_powers = [0.0] * TOTAL_NODES

    for device_index in range(TOTAL_NODES):
        if not power_readings[device_index]:
            average_powers[device_index] = total_power_devices[device_index]/power_readings[device_index]

    print "Average power consumption per node:\t", round(np.mean(average_powers), 2), "W"

def calc_avg_dissemination_time(msg_times):
    total_delay = 0.0
    total_msgs = 0
    for msg in msg_times:
        (strt, end) = msg_times[msg]
        if end is not None:
            total_delay += (end - strt).microseconds / 1000
            total_msgs += 1
    avg_delay = total_delay / total_msgs
    print "Average dissemination delay:\t", round(avg_delay, 2), "milliseconds"

def calculate_power(values):
    CPU = float(values[12]) * 1.8
    LPM = float(values[13]) * 0.0545
    TX = float(values[14]) * 19.5
    RX = float(values[15]) * 21.8
    power = (CPU + LPM + TX + RX) * 3 / 327680
    return power

if __name__ == "__main__":
    main()
