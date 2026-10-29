#!/usr/bin/python3

# This is test wrapper around test_terminal binary to automate testing of jitter buffer and Opus codec.
# This script emulates packet losses and jitter, records the incoming audio and compares it with reference using AQuA utility

import subprocess
import typing
import os
import json
import time
import wave
from datetime import datetime
from pathlib import Path


# Played / reference audio file
REFERENCE = Path('reference_audio.wav').resolve()

# Name of terminal test binary file
TEST_BINARY = 'audio-channel'

# Generated report
REPORT : list[str] = []
REPORT_FULL : list[str] = []

# Log file
LOG = None
LOG_PATH = Path('run_test.log')

def log_msg(msg: str):
    global LOG
    if LOG is None:
        if LOG_PATH.exists():
            LOG = open(LOG_PATH, 'a+t')
        else:
            LOG = open(LOG_PATH, 'w+t')
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    LOG.write(f'{current_time} : {msg}\r\n')
    LOG.flush()

    # Print to console
    print(f'{current_time} : {msg}')


class NetworkMode:
    packet_loss:        int                     # Percent
    network_corrupt:    int                     # Percent
    delay_ms_interval:  typing.Tuple[int, int]  # Mean +- value 
    gap:                int                     # Number of packets
    reorder:            int                     # Percents
    disable_plc:        bool                    # Disable Opus FEC and PLC

    def __init__(self, packet_loss, network_corrupt, delay_ms_interval, gap = 0, reorder = 0, disable_plc = False):
        self.packet_loss = packet_loss
        self.network_corrupt = network_corrupt
        self.delay_ms_interval = delay_ms_interval
        self.gap = gap
        self.reorder = reorder
        self.disable_plc = disable_plc

    def __repr__(self) -> str:
        return f'Packet loss: {self.packet_loss}%, network corrupt: {self.network_corrupt}%, delay interval (ms): [{self.delay_ms_interval[0], self.delay_ms_interval[1]}], plc: {"off" if self.disable_plc else "on"}'
    
    def brief(self) -> str:
        return f'pl_{self.packet_loss:02d}_nc_{self.network_corrupt:02d}_di_{self.delay_ms_interval[0]:02d}-{self.delay_ms_interval[1]:02d}_plc_{"off" if self.disable_plc else "on"}'

    def is_empty(self):
        return self.packet_loss == 0 and self.network_corrupt == 0 and self.gap == 0 and self.reorder == 0 and self.disable_plc == False and self.delay_ms_interval[0] == 0 and self.delay_ms_interval[1] == 0



class Result:
    packet_loss: int        # json["packet_loss"] = settings.mPacketLoss;
    received_packets: int   # json["received_packets"] = stats.mReceivedPackets;
    recv_voice_payload: int # json["recv_voice_payload"] = stats.mRecvVoicePayload;
    plc_frames: int         # json["plc_frames"] = stats.mPlcFrames;
    underrun_counter: int   # json["underrun_counter"] = stats.mJBUnderrunCounter;
    network_mos: float      # json["network_mos"]] = stats.mMos;
    max_length: int         # json["max_length"] = stats.mMaxLength;
    prebuffer_count: int    # json["prebuffer_count"] = stats.mPrebufferCount;
    speedup_playouts: int   # json["speedup_playouts"] = stats.mSpeedupPlayouts;
    audio: str              # json["audio"] = settings.mAudioRecorded;
    aqua_mos: float         # this is filled by call to AQuA analyzer

    def __init__(self, json_path: Path = None) -> None:
        if json_path:
            with open(json_path, 'rt') as f:
                stat = json.loads(f.read())

                if 'error' in stat:
                    raise Exception(stat['error'])
                
                self.packet_loss = int(stat['packet_loss'])
                self.received_packets = stat['received_packets']
                self.recv_voice_payload = stat['recv_voice_payload']
                self.plc_frames = stat['plc_frames']
                self.underrun_counter = stat['underrun_counter']
                self.network_mos = stat['network_mos']
                self.max_length = stat['max_length']
                self.prebuffer_count = stat['prebuffer_count']
                self.speedup_playouts = stat['speedup_playouts']
                self.audio = Path(stat['audio'])
                self.aqua_mos = None

    def csv_header() -> str:
        return f'Packet loss, Recvd pkts, Recvd payload, PLCed frames, Underruns, Network MOS, JB max length, Prebuffers, Speedy playouts, Audio, AQuA MOS'


    def to_csv(self) -> str:
        return f'{self.packet_loss}, {self.audio}, {round(self.aqua_mos, 3)}'
    
    
    def assign_from_average(self, results: typing.List):
        if len(results) == 0:
            return
        
        self.packet_loss = sum(item.packet_loss for item in results)
        self.packet_loss /= len(results)

        self.received_packets = sum(item.received_packets for item in results)
        self.received_packets /= len(results)
        
        self.recv_voice_payload = sum(item.recv_voice_payload for item in results)
        self.recv_voice_payload /= len(results)

        self.plc_frames = sum(item.plc_frames for item in results)
        self.plc_frames /= len(results)

        self.underrun_counter = sum(item.underrun_counter for item in results)
        self.underrun_counter /= len(results)

        self.network_mos = sum(item.network_mos for item in results)
        self.network_mos /= len(results)
        
        self.max_length = sum(item.max_length for item in results)
        self.max_length /= len(results)

        self.prebuffer_count = sum(item.prebuffer_count for item in results)
        self.prebuffer_count /= len(results)

        self.speedup_playouts = sum(item.speedup_playouts for item in results)
        self.speedup_playouts /= len(results)

        self.aqua_mos = sum(item.aqua_mos for item in results)
        self.aqua_mos /= len(results)

        self.audio = results[0].audio



def tc_on(network_mode: NetworkMode):
    if network_mode.is_empty():
        return
    
    # Packet loss and corrupt
    netem = f'sudo tc qdisc add dev lo root netem loss {network_mode.packet_loss}% corrupt {network_mode.network_corrupt}%'
    
    # Delay
    netem = netem + f' delay {network_mode.delay_ms_interval[0]}ms {network_mode.delay_ms_interval[1]}ms'

    # Distribution
    # if network_mode.delay_ms_interval[0] != 0:
    #    netem = netem + f' distribution normal'
        
    # if network_mode.gap != 0 and network_mode.reorder != 0:
    #    netem = netem + f' gap {network_mode.gap} reorder {network_mode.reorder}'
    
    # Tune
    log_msg(f'Enable network impairments: {netem}')
    retcode = os.system(netem)
    if retcode != 0:
        log_msg(f'  failed to tune loopback interface to {network_mode}')
        raise SystemExit(retcode)
    

def tc_off(network_mode: NetworkMode):
    if network_mode.is_empty():
        return
    
    # Reset loopback interface
    netem = 'sudo tc qdisc del dev lo root'
    log_msg(f'Disable network impairments: {netem}')
    retcode = os.system(netem)
    if retcode != 0:
        log_msg(f'  failed to reset loopback interface back to normal mode. Please reboot.')
        raise SystemExit(retcode)


def run_test(network_mode: NetworkMode, opus_packet_loss: int, dir_output: Path, iteration_idx: int) -> Result:
    global REFERENCE, REPORT
    try:

        # Find time length
        with open(REFERENCE, 'rb') as f:
            with wave.open(f, 'rb') as w:
                duration = round(w.getnframes() / w.getframerate(), 3)

        # Enable network impairments
        tc_on(network_mode)
        # if network_mode.disable_plc:
        #     # Alter own environment to allow subprocess to inherit this
        #     os.environ['ARENIM_OPUS_PLC_DISABLED'] = 'YES'

        output_filename = f'r_{network_mode.brief()}_opus_{opus_packet_loss:02d}_iteration_{iteration_idx:02d}.wav'
        cmd = f'./{TEST_BINARY} --play {REFERENCE} --record {dir_output}/{output_filename} --duration {duration} --packet-loss {opus_packet_loss} --codec opus'
        log_msg(cmd)

        retcode, output = subprocess.getstatusoutput(cmd)
        log_msg(output)
        
        if retcode != 0:
            log_msg(f'  failed to run loopback test. Return code: {retcode}')
            raise SystemExit(retcode)
    finally:    
        # Disable network impairments        
        tc_off(network_mode)
        # os.environ['ARENIM_OPUS_PLC_DISABLED'] = 'NO'

    # Add to report
    r = Result()

    # Replace the Opus packet loss settings with mode packet loss setting
    r.packet_loss = network_mode.packet_loss
    r.audio = output_filename

    return r



if __name__ == '__main__':
    try:
        if not REFERENCE.exists():
            print(f'There is no reference audio found ( {REFERENCE} ).')

        # Check if output directory exists
        dir_output = Path(__file__).parent / 'jb_output'
        if not dir_output.exists():
            os.mkdir(dir_output)

        
        # Outer loop sets the expected packet losses
        # Inner loop sets the Opus codec expected packet losses setting
        modes = [
            NetworkMode(packet_loss=0, network_corrupt=0, delay_ms_interval=(20, 5)),
            NetworkMode(packet_loss=5, network_corrupt=0, delay_ms_interval=(20, 10)),
            NetworkMode(packet_loss=10, network_corrupt=0, delay_ms_interval=(50, 20)),
            NetworkMode(packet_loss=15, network_corrupt=1, delay_ms_interval=(100, 50)),
            NetworkMode(packet_loss=20, network_corrupt=2, delay_ms_interval=(100, 50)),
            NetworkMode(packet_loss=25, network_corrupt=3, delay_ms_interval=(100, 70)),
            NetworkMode(packet_loss=30, network_corrupt=4, delay_ms_interval=(100, 70)),
        ]
        
        # For every listed network mode 
        for network_mode in modes:
            # Repeat test 10 times to get average values after
            single_test_results = []
            for i in range(0, 10):
                for opus_pl in [5]: # Expected packet losses setting for Opus codec
                    r = run_test(network_mode=network_mode, opus_packet_loss=opus_pl, dir_output=dir_output, iteration_idx=i)

    except Exception as e:
        print(e)
