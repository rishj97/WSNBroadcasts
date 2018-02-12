import sys
import numpy as np
from datetime import datetime
TOTAL_NODES = 30
DEVICE_NUM_INDEX = 4
BROADCAST_INDEX = 2
TIMESTAMP_INDEX = 0
TIMESTAMP_FORMAT = '%M:%S.%f'
TIME_TO_STABILIZE = datetime.strptime('05:00.000', TIMESTAMP_FORMAT)
POWERTRACE_STR = 'P'
BROADCAST_STR = 'Broadcast'
BRD_SENT_STR = 'sent'
BRD_RECV_STR = 'recv'
POWERTRACE_ID_INDEX = 3

def main():
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = 'Logs/log_full.txt'
    with open(log_file) as log_file:
        dissemination_durations = {}
        dissemination_receivers = {}
        total_power = [0.0] * TOTAL_NODES
        num_power_readings = [0] * TOTAL_NODES
        for log in log_file:
            if len(log) == 0:
                break
            log_values = log.split()
            log_time = datetime.strptime(log_values[TIMESTAMP_INDEX], TIMESTAMP_FORMAT)
            if log_time < TIME_TO_STABILIZE:
                continue
            if log_values[POWERTRACE_ID_INDEX] == POWERTRACE_STR:
                # Incase of powertrace output
                power = calculate_power(log_values)
                device_number = int(float(log_values[DEVICE_NUM_INDEX]))
                total_power[device_number - 1] += power
                num_power_readings[device_number - 1] += 1
            elif log_values[BROADCAST_INDEX] == BROADCAST_STR:
                receiver_id = log_values[1]
                # Incase of broadcast message
                if log_values[4] == BRD_SENT_STR and len(log_values) == 6:
                    # Case of first broadcast message
                    dissemination_id = int(log_values[5])
                    dissemination_durations[dissemination_id] = (log_time, None)
                    dissemination_receivers[dissemination_id] = set()
                    dissemination_receivers[dissemination_id].add(receiver_id)
                elif log_values[3] == BRD_RECV_STR:
                    # Case of some message received
                    dissemination_id = int(log_values[10])
                    if dissemination_id in dissemination_durations:
                        (strt_time, _) = dissemination_durations[dissemination_id]
                        dissemination_durations[dissemination_id] = (strt_time, log_time)
                        dissemination_receivers[dissemination_id].add(receiver_id)
        calc_avg_loss_rate(dissemination_receivers)
        calc_avg_power_consumption(total_power, num_power_readings)
        calc_avg_dissemination_delay(dissemination_durations, dissemination_receivers)


def calc_avg_loss_rate(dissemination_receivers):
    total_msgs = 0
    total_loss_rate = 0.0
    for msg in dissemination_receivers:
        receivers = dissemination_receivers[msg]
        if receivers is not None:
            loss_rate = len(receivers)/float(TOTAL_NODES)
            total_loss_rate += loss_rate
            total_msgs += 1
        else:
            print "Message ", msg, " had error with receiving"
    avg_loss_rate = total_loss_rate / total_msgs * 100
    print "Average end to end loss rate:\t", round(avg_loss_rate, 2), "%"

def calc_avg_power_consumption(total_power, num_power_readings):
    average_powers = [0.0] * TOTAL_NODES

    for device_index in range(TOTAL_NODES):
        if num_power_readings[device_index] is not 0:
            average_powers[device_index] = total_power[device_index]/num_power_readings[device_index]

    print "Average power consumption per node:\t", round(np.mean(average_powers), 2), "mW"

def calc_avg_dissemination_delay(dissemination_durations, dissemination_receivers):
    total_delay = 0.0
    total_msgs = 0
    for msg in dissemination_receivers:
        if len(dissemination_receivers[msg]) == TOTAL_NODES:
            if msg in dissemination_durations:
                (strt, end) = dissemination_durations[msg]
                if end is not None:
                    total_delay += (end - strt).microseconds / 1000
                    total_msgs += 1
    if total_msgs > 0:
        avg_delay = total_delay / total_msgs
    else:
        avg_delay = -1
    print "Average dissemination delay:\t", round(avg_delay, 2), "ms"

def calculate_power(log_values):
    CPU = float(log_values[12]) * 1.8
    LPM = float(log_values[13]) * 0.0545
    TX = float(log_values[14]) * 19.5
    RX = float(log_values[15]) * 21.8
    power = (CPU + LPM + TX + RX) * 3 / 327680
    return power

if __name__ == "__main__":
    main()
