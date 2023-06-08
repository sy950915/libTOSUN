'''
Author: seven 865762826@qq.com
Date: 2022-12-24 12:29:39
LastEditors: seven 865762826@qq.com
LastEditTime: 2023-06-08 15:28:42
FilePath: \window_linux_Repd:\Envs\python39_32\Lib\site-packages\libTOSUN\libTOSUN.py
'''
import xml.etree.ElementTree as ET
import time
from ctypes import *
import copy
import platform
from typing import Optional
import cantools
from can.message import Message as Message
import can
import os
import queue

# _curr_path = os.path.split(os.path.realpath(__file__))[0]
_curr_path = os.path.dirname(__file__)
_arch, _os = platform.architecture()
_os = platform.system()
_is_windows, _is_linux = False, False
if 'windows' in _os.lower():
    _is_windows = True
    if _arch == '32bit':
        # os.add_dll_directory(os.path.join(_curr_path, 'windows/x86'))
        os.chdir(os.path.join(_curr_path, 'windows/x86'))
        _lib_path = os.path.join(_curr_path, 'windows/x86/libTSCAN.dll')
    else:
        # os.add_dll_directory(os.path.join(_curr_path, 'windows/x64'))
        os.chdir(os.path.join(_curr_path, 'windows/x64'))
        _lib_path = os.path.join(_curr_path, 'windows/x64/libTSCAN.dll')
    # if not os.path.exists(_lib_path):
    #     _lib_path = r"D:\demo\libtosun\libtosun\windows\X64\libTSCAN.dll"
    dll = windll.LoadLibrary(_lib_path)
elif 'linux' in _os.lower():
    _is_linux = True
    if _arch == '64bit':
        # os.add_dll_directory(os.path.join(_curr_path, 'linux'))
        os.chdir(os.path.join(_curr_path, 'linux'))
        _lib_path = os.path.join(_curr_path, 'linux/libTSCANApiOnLinux.so')
    else:
        _lib_path = None
    if _lib_path:
        dll = cdll.LoadLibrary(_lib_path)
else:
    _library = None


# dll = cdll.LoadLibrary("./libTSCANApiOnLinux.so")


class Fibex_parse():
    Cluster = {}
    Frames = {}
    Pdus = {}
    Triggers = {}
    Signals = {}
    Codings = {}
    Ecus = {}
    STATIC_SLOT = 30
    def __init__(self,xmlpath) -> ET:
        self.tree = ET.parse(xmlpath)
        self.parse(self.tree)
    def parse(self,tree):
        root = tree.getroot()
        CODINGS = root.findall('{http://www.asam.net/xml/fbx}PROCESSING-INFORMATION/{http://www.asam.net/xml/fbx}CODINGS/{http://www.asam.net/xml/fbx}CODING')
        if CODINGS!=None:
            for CODING in CODINGS:
                # _Coding = {}
                CODING_ID = CODING.attrib.get('ID',None)
                self.Codings[CODING_ID] = {}
                self.Codings[CODING_ID]['ENCODING'] = CODING.find('{http://www.asam.net/xml}CODED-TYPE').attrib.get('ENCODING','SIGNED')
                self.Codings[CODING_ID]['BIT-LENGTH'] = CODING.find('{http://www.asam.net/xml}CODED-TYPE/{http://www.asam.net/xml}BIT-LENGTH').text
                COMPU_NUMERATOR = CODING.find('{http://www.asam.net/xml}COMPU_NUMERATOR')
                if COMPU_NUMERATOR!= None:
                    self.Codings[CODING_ID]['offset'] = COMPU_NUMERATOR[0].text
                    self.Codings[CODING_ID]['factor'] = COMPU_NUMERATOR[1].text
                else:
                    self.Codings[CODING_ID]['offset'] = '0.0'
                    self.Codings[CODING_ID]['factor'] = '1.0'
        ELEMENTS = root.find('{http://www.asam.net/xml/fbx}ELEMENTS')
        if ELEMENTS!= None:
            CLUSTER = ELEMENTS.find('{http://www.asam.net/xml/fbx}CLUSTERS/{http://www.asam.net/xml/fbx}CLUSTER')
            if CLUSTER != None:
                self.STATIC_SLOT = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}STATIC-SLOT').text)
                self.Cluster['NETWORK_MANAGEMENT_VECTOR_LENGTH'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}NETWORK-MANAGEMENT-VECTOR-LENGTH').text)
                self.Cluster['PAYLOAD_LENGTH_STATIC'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}PAYLOAD-LENGTH-STATIC').text)
                self.Cluster['T_S_S_TRANSMITTER'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}T-S-S-TRANSMITTER').text)
                self.Cluster['CAS_RX_LOW_MAX'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}CAS-RX-LOW-MAX').text)
                self.Cluster['SPEED'] = 0 if CLUSTER.find('{http://www.asam.net/xml/fbx}SPEED').text=='10000000' else 1
                WAKE_UP = CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}WAKE-UP')
                self.Cluster['WAKE_UP_SYMBOL_RX_WINDOW'] = int(WAKE_UP.find('{http://www.asam.net/xml/fbx/flexray}WAKE-UP-SYMBOL-RX-WINDOW').text)
                self.Cluster['WAKE_UP_SYMBOL_RX_IDLE'] = int(WAKE_UP.find('{http://www.asam.net/xml/fbx/flexray}WAKE-UP-SYMBOL-RX-IDLE').text)
                self.Cluster['WAKE_UP_SYMBOL_RX_LOW'] = int(WAKE_UP.find('{http://www.asam.net/xml/fbx/flexray}WAKE-UP-SYMBOL-RX-LOW').text)
                self.Cluster['WAKE_UP_SYMBOL_TX_IDLE'] = int(WAKE_UP.find('{http://www.asam.net/xml/fbx/flexray}WAKE-UP-SYMBOL-TX-IDLE').text)
                self.Cluster['WAKE_UP_SYMBOL_TX_LOW'] = int(WAKE_UP.find('{http://www.asam.net/xml/fbx/flexray}WAKE-UP-SYMBOL-TX-LOW').text)
                self.Cluster['COLD_START_ATTEMPTS'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}COLD-START-ATTEMPTS').text)
                self.Cluster['LISTEN_NOISE'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}LISTEN-NOISE').text)
                self.Cluster['MAX_WITHOUT_CLOCK_CORRECTION_PASSIVE'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}MAX-WITHOUT-CLOCK-CORRECTION-PASSIVE').text)
                self.Cluster['MAX_WITHOUT_CLOCK_CORRECTION_FATAL'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}MAX-WITHOUT-CLOCK-CORRECTION-FATAL').text)
                self.Cluster['MACRO_PER_CYCLE'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}MACRO-PER-CYCLE').text)
                self.Cluster['SYNC_NODE_MAX'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}SYNC-NODE-MAX').text)
                self.Cluster['N_I_T'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}N-I-T').text)
                self.Cluster['OFFSET_CORRECTION_START'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}OFFSET-CORRECTION-START').text)
                self.Cluster['CLUSTER_DRIFT_DAMPING'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}CLUSTER-DRIFT-DAMPING').text)
                self.Cluster['STATIC_SLOT'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}STATIC-SLOT').text)
                self.Cluster['NUMBER_OF_STATIC_SLOTS'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}NUMBER-OF-STATIC-SLOTS').text)
                self.Cluster['MINISLOT'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}MINISLOT').text)
                self.Cluster['NUMBER_OF_MINISLOTS'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}NUMBER-OF-MINISLOTS').text)
                self.Cluster['DYNAMIC_SLOT_IDLE_PHASE'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}DYNAMIC-SLOT-IDLE-PHASE').text)
                self.Cluster['ACTION_POINT_OFFSET'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}ACTION-POINT-OFFSET').text)
                self.Cluster['MINISLOT_ACTION_POINT_OFFSET'] = int(CLUSTER.find('{http://www.asam.net/xml/fbx/flexray}MINISLOT-ACTION-POINT-OFFSET').text)
            CHANNELS = ELEMENTS.find('{http://www.asam.net/xml/fbx}CHANNELS')
            if CHANNELS!= None:
                TRIGGERINGS = ELEMENTS.findall('{http://www.asam.net/xml/fbx}CHANNELS/{http://www.asam.net/xml/fbx}CHANNEL/{http://www.asam.net/xml/fbx}FRAME-TRIGGERINGS/{http://www.asam.net/xml/fbx}FRAME-TRIGGERING')
                for TRIGGERING in TRIGGERINGS:
                    # Trigger = {}
                    TRIGGERING_ID = TRIGGERING.attrib.get('ID',None)
                    FRAME_REF =TRIGGERING.find('{http://www.asam.net/xml/fbx}FRAME-REF')
                    if FRAME_REF != None:
                        ID_REF = FRAME_REF.attrib.get('ID-REF',None)
                        self.Triggers[ID_REF]={}
                        self.Triggers[TRIGGERING_ID]={}
                        self.Triggers[TRIGGERING_ID]['ID_REF']=ID_REF
                        self.Triggers[ID_REF]['TRIGGERING_ID']=TRIGGERING_ID
                    TIMING = TRIGGERING.find('{http://www.asam.net/xml/fbx}TIMINGS/{http://www.asam.net/xml/fbx}ABSOLUTELY-SCHEDULED-TIMING')
                    if TIMING!= None:
                        SLOT_ID = int(TIMING.find('{http://www.asam.net/xml/fbx}SLOT-ID').text)
                        BASE_CYCLE = int(TIMING.find('{http://www.asam.net/xml/fbx}BASE-CYCLE').text)
                        CYCLE_REPETITION =  int(TIMING.find('{http://www.asam.net/xml/fbx}CYCLE-REPETITION').text)
                        self.Triggers[TRIGGERING_ID]['SLOT-ID']=SLOT_ID
                        self.Triggers[ID_REF]['SLOT-ID'] = SLOT_ID
                        self.Triggers[TRIGGERING_ID]['BASE-CYCLE']=BASE_CYCLE
                        self.Triggers[ID_REF]['BASE-CYCLE'] = BASE_CYCLE
                        self.Triggers[TRIGGERING_ID]['CYCLE-REPETITION'] = CYCLE_REPETITION
                        self.Triggers[ID_REF]['CYCLE-REPETITION'] = CYCLE_REPETITION
                    del ID_REF,SLOT_ID,BASE_CYCLE,CYCLE_REPETITION,TRIGGERING_ID,
            SIGNALS = ELEMENTS.findall('{http://www.asam.net/xml/fbx}SIGNALS/{http://www.asam.net/xml/fbx}SIGNAL')
            if SIGNALS != None:
                for SIGNAL in SIGNALS:
                    SIGNAL_ID = SIGNAL.attrib.get('ID',None)
                    self.Signals[SIGNAL_ID] = {}
                    self.Signals[SIGNAL_ID]['SHORT-NAME'] = SIGNAL.find('{http://www.asam.net/xml}SHORT-NAME').text
                    self.Signals[SIGNAL_ID]['CODING-REF'] = SIGNAL.find('{http://www.asam.net/xml/fbx}CODING-REF').attrib['ID-REF']
                    self.Signals[SIGNAL_ID]['BIT-LENGTH'] = int(self.Codings[self.Signals[SIGNAL_ID]['CODING-REF']]['BIT-LENGTH'])
                    self.Signals[SIGNAL_ID]['offset'] = float(self.Codings[self.Signals[SIGNAL_ID]['CODING-REF']]['offset'])
                    self.Signals[SIGNAL_ID]['factor'] = float(self.Codings[self.Signals[SIGNAL_ID]['CODING-REF']]['factor'])
                    self.Signals[SIGNAL_ID]['ENCODING'] = False if self.Codings[self.Signals[SIGNAL_ID]['CODING-REF']]['ENCODING']== 'SIGNED' else True
                    del SIGNAL_ID
            PDUS = ELEMENTS.findall('{http://www.asam.net/xml/fbx}PDUS/{http://www.asam.net/xml/fbx}PDU')
            if len(PDUS) == 0:
                PDUS = ELEMENTS.findall('{http://www.asam.net/xml/fbx}FRAMES/{http://www.asam.net/xml/fbx}FRAME')
            for PDU in PDUS:
                pdu_id = PDU.attrib['ID']
                self.Pdus[pdu_id] = {}
                self.Pdus[pdu_id]['PDU_Name'] = PDU.find('{http://www.asam.net/xml}SHORT-NAME').text
                self.Pdus[pdu_id]['DLC'] = PDU.find('{http://www.asam.net/xml/fbx}BYTE-LENGTH').text
                SIGNAL_INSTANCES = PDU.findall('{http://www.asam.net/xml/fbx}SIGNAL-INSTANCES/{http://www.asam.net/xml/fbx}SIGNAL-INSTANCE')
                if SIGNAL_INSTANCES != None:
                    self.Pdus[pdu_id]['SIGNALS'] = {}
                    for SIGNAL_INSTANCE in SIGNAL_INSTANCES:
                        SIGNAL_REF = SIGNAL_INSTANCE.find('{http://www.asam.net/xml/fbx}SIGNAL-REF').attrib.get('ID-REF',None)
                        _Signal_Name = self.Signals[SIGNAL_REF]['SHORT-NAME']
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name] = {}
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name]['SHORT-NAME'] = self.Signals[SIGNAL_REF]['SHORT-NAME']
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name]['BIT-POSITION'] = int(SIGNAL_INSTANCE.find('{http://www.asam.net/xml/fbx}BIT-POSITION').text)
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name]['BIT-LENGTH'] = self.Signals[SIGNAL_REF]['BIT-LENGTH']
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name]['offset'] = self.Signals[SIGNAL_REF]['offset']
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name]['factor'] = self.Signals[SIGNAL_REF]['factor']
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name]['ENCODING'] = self.Signals[SIGNAL_REF]['ENCODING']
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name]['is_M'] = SIGNAL_INSTANCE.find('{http://www.asam.net/xml/fbx}IS-HIGH-LOW-BYTE-ORDER').text
                        self.Pdus[pdu_id]['SIGNALS'][_Signal_Name]['ub'] = SIGNAL_INSTANCE.find('{http://www.asam.net/xml/fbx}SIGNAL-UPDATE-BIT-POSITION').text if SIGNAL_INSTANCE.find('{http://www.asam.net/xml/fbx}SIGNAL-UPDATE-BIT-POSITION') != None else '-1'
                        del _Signal_Name,SIGNAL_REF
                del pdu_id
            FRAMES = ELEMENTS.findall('{http://www.asam.net/xml/fbx}FRAMES/{http://www.asam.net/xml/fbx}FRAME')
            if FRAMES != None:
                for FRAME in FRAMES:
                    # _Frame ={}
                    FRAME_NAME = FRAME.find('{http://www.asam.net/xml}SHORT-NAME').text
                    self.Frames[FRAME_NAME] ={}
                    FRAME_ID = FRAME.attrib.get('ID',None)
                    self.Frames[FRAME_NAME]['SHORT-NAME'] = FRAME_NAME
                    # self.Frames[FRAME_NAME]['FRAME-ID'] = FRAME.attrib.get('ID',None)
                    self.Frames[FRAME_NAME]['SLOT-ID']= self.Triggers[FRAME_ID]['SLOT-ID']
                    self.Frames[FRAME_NAME]['BASE-CYCLE']= self.Triggers[FRAME_ID]['BASE-CYCLE']
                    self.Frames[FRAME_NAME]['CYCLE-REPETITION']= self.Triggers[FRAME_ID]['CYCLE-REPETITION']
                    _FDLC = int(FRAME.find('{http://www.asam.net/xml/fbx}BYTE-LENGTH').text)
                    self.Frames[FRAME_NAME]['FDLC'] = _FDLC
                    self.Triggers[FRAME_ID]['FDLC'] = _FDLC
                    self.Triggers[self.Triggers[FRAME_ID]['TRIGGERING_ID']]['FDLC'] = _FDLC
                    PDU_INSTANCES = FRAME.findall('{http://www.asam.net/xml/fbx}PDU-INSTANCES/{http://www.asam.net/xml/fbx}PDU-INSTANCE')
                    if len(PDU_INSTANCES) != 0:
                        self.Frames[FRAME_NAME]['PDUS'] = []
                        for PDU_INSTANCE in PDU_INSTANCES:
                            PDU_REF = PDU_INSTANCE.find('{http://www.asam.net/xml/fbx}PDU-REF').attrib.get('ID-REF',None)
                            PDU_1 = {}
                            PDU_1['PDU_Name'] = self.Pdus[PDU_REF]['PDU_Name']
                            PDU_1['BIT-POSITION'] = int(PDU_INSTANCE.find('{http://www.asam.net/xml/fbx}BIT-POSITION').text)
                            PDU_1['SIGNALS'] = self.Pdus[PDU_REF]['SIGNALS']
                            self.Frames[FRAME_NAME]['PDUS'].append(PDU_1)  # store all PDUs in a list for easier
                            # self.Frames[FRAME_NAME][self.Pdus[PDU_REF]['PDU_Name']]={}
                            # self.Frames[FRAME_NAME][self.Pdus[PDU_REF]['PDU_Name']]['BIT-POSITION']=int(PDU_INSTANCE.find('{http://www.asam.net/xml/fbx}BIT-POSITION').text)
                            # self.Frames[FRAME_NAME][self.Pdus[PDU_REF]['PDU_Name']]['SIGNALS'] = self.Pdus[PDU_REF]['SIGNALS']
                            del PDU_REF,PDU_1
                    else:
                        try:
                            self.Frames[FRAME_NAME]['SIGNALS'] = self.Pdus[FRAME_ID]['SIGNALS']
                        except:
                            pass
                    del FRAME_NAME,FRAME_ID,_FDLC
            ECUS = ELEMENTS.findall('{http://www.asam.net/xml/fbx}ECUS/{http://www.asam.net/xml/fbx}ECU')
            if ECUS != None:  
                for ECU in ECUS: 
                    ecu_name = ECU.find('{http://www.asam.net/xml}SHORT-NAME').text
                    self.Ecus[ecu_name] = {}
                    INPUT_PORTS = ECU.findall('{http://www.asam.net/xml/fbx}CONNECTORS/{http://www.asam.net/xml/fbx}CONNECTOR/{http://www.asam.net/xml/fbx}INPUTS/{http://www.asam.net/xml/fbx}INPUT-PORT')
                    OUTPUT_PORTS = ECU.findall('{http://www.asam.net/xml/fbx}CONNECTORS/{http://www.asam.net/xml/fbx}CONNECTOR/{http://www.asam.net/xml/fbx}OUTPUTS/{http://www.asam.net/xml/fbx}OUTPUT-PORT')
                    ECU = ECU.find('{http://www.asam.net/xml/fbx}CONTROLLERS/{http://www.asam.net/xml/fbx}CONTROLLER')
                    self.Ecus[ecu_name]['NETWORK_MANAGEMENT_VECTOR_LENGTH'] = self.Cluster['NETWORK_MANAGEMENT_VECTOR_LENGTH'] 
                    self.Ecus[ecu_name]['PAYLOAD_LENGTH_STATIC'] = self.Cluster['PAYLOAD_LENGTH_STATIC'] 
                    self.Ecus[ecu_name]['T_S_S_TRANSMITTER'] = self.Cluster['T_S_S_TRANSMITTER'] 
                    self.Ecus[ecu_name]['CAS_RX_LOW_MAX'] = self.Cluster['CAS_RX_LOW_MAX'] 
                    self.Ecus[ecu_name]['SPEED'] = self.Cluster['SPEED'] 
                    self.Ecus[ecu_name]['WAKE_UP_SYMBOL_RX_WINDOW'] = self.Cluster['WAKE_UP_SYMBOL_RX_WINDOW'] 
                    self.Ecus[ecu_name]['WAKE_UP_SYMBOL_RX_IDLE'] = self.Cluster['WAKE_UP_SYMBOL_RX_IDLE'] 
                    self.Ecus[ecu_name]['WAKE_UP_SYMBOL_RX_LOW'] = self.Cluster['WAKE_UP_SYMBOL_RX_LOW'] 
                    self.Ecus[ecu_name]['WAKE_UP_SYMBOL_TX_IDLE'] = self.Cluster['WAKE_UP_SYMBOL_TX_IDLE'] 
                    self.Ecus[ecu_name]['WAKE_UP_SYMBOL_TX_LOW'] = self.Cluster['WAKE_UP_SYMBOL_TX_LOW'] 
                    self.Ecus[ecu_name]['COLD_START_ATTEMPTS'] = self.Cluster['COLD_START_ATTEMPTS'] 
                    self.Ecus[ecu_name]['LISTEN_NOISE'] = self.Cluster['LISTEN_NOISE'] 
                    self.Ecus[ecu_name]['MAX_WITHOUT_CLOCK_CORRECTION_PASSIVE'] = self.Cluster['MAX_WITHOUT_CLOCK_CORRECTION_PASSIVE'] 
                    self.Ecus[ecu_name]['MAX_WITHOUT_CLOCK_CORRECTION_FATAL'] = self.Cluster['MAX_WITHOUT_CLOCK_CORRECTION_FATAL'] 
                    self.Ecus[ecu_name]['MACRO_PER_CYCLE'] = self.Cluster['MACRO_PER_CYCLE'] 
                    self.Ecus[ecu_name]['SYNC_NODE_MAX'] = self.Cluster['SYNC_NODE_MAX'] 
                    self.Ecus[ecu_name]['N_I_T'] = self.Cluster['N_I_T'] 
                    self.Ecus[ecu_name]['OFFSET_CORRECTION_START'] = self.Cluster['OFFSET_CORRECTION_START'] 
                    self.Ecus[ecu_name]['CLUSTER_DRIFT_DAMPING'] = self.Cluster['CLUSTER_DRIFT_DAMPING'] 
                    self.Ecus[ecu_name]['STATIC_SLOT'] = self.Cluster['STATIC_SLOT'] 
                    self.Ecus[ecu_name]['NUMBER_OF_STATIC_SLOTS'] = self.Cluster['NUMBER_OF_STATIC_SLOTS'] 
                    self.Ecus[ecu_name]['MINISLOT'] = self.Cluster['MINISLOT'] 
                    self.Ecus[ecu_name]['NUMBER_OF_MINISLOTS'] = self.Cluster['NUMBER_OF_MINISLOTS'] 
                    self.Ecus[ecu_name]['DYNAMIC_SLOT_IDLE_PHASE'] = self.Cluster['DYNAMIC_SLOT_IDLE_PHASE'] 
                    self.Ecus[ecu_name]['ACTION_POINT_OFFSET'] = self.Cluster['ACTION_POINT_OFFSET'] 
                    self.Ecus[ecu_name]['MINISLOT_ACTION_POINT_OFFSET'] = self.Cluster['MINISLOT_ACTION_POINT_OFFSET'] 
                    STARTUP_SYNC = ECU.find('{http://www.asam.net/xml/fbx/flexray}KEY-SLOT-USAGE/{http://www.asam.net/xml/fbx/flexray}STARTUP-SYNC')
                    if STARTUP_SYNC != None:
                        self.Ecus[ecu_name]['startupFrameTransmitted'] = 1
                        self.Ecus[ecu_name]['startupFrame_ID'] =int(STARTUP_SYNC.text) 
                    else:
                        self.Ecus[ecu_name]['startupFrameTransmitted'] = 0 
                        self.Ecus[ecu_name]['startupFrame_ID'] = 0
                    self.Ecus[ecu_name]['ACCEPTED_STARTUP_RANGE'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}ACCEPTED-STARTUP-RANGE').text)
                    self.Ecus[ecu_name]['MAX_DRIFT'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}MAX-DRIFT').text)
                    self.Ecus[ecu_name]['WAKE_UP_PATTERN'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}WAKE-UP-PATTERN').text)
                    self.Ecus[ecu_name]['ALLOW_HALT_DUE_TO_CLOCK'] = 1 if ECU.find('{http://www.asam.net/xml/fbx/flexray}ALLOW-HALT-DUE-TO-CLOCK') == 'true' else 0
                    self.Ecus[ecu_name]['SINGLE_SLOT_ENABLED'] = 1 if ECU.find('{http://www.asam.net/xml/fbx/flexray}SINGLE-SLOT-ENABLED') == 'true' else 0
                    self.Ecus[ecu_name]['ALLOW_PASSIVE_TO_ACTIVE'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}ALLOW-PASSIVE-TO-ACTIVE').text)
                    self.Ecus[ecu_name]['LISTEN_TIMEOUT'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}LISTEN-TIMEOUT').text)
                    self.Ecus[ecu_name]['MICRO_PER_CYCLE'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}MICRO-PER-CYCLE').text)
                    self.Ecus[ecu_name]['LATEST_TX'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}LATEST-TX').text)
                    self.Ecus[ecu_name]['MICRO_INITIAL_OFFSET_A'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}MICRO-INITIAL-OFFSET-A').text)
                    self.Ecus[ecu_name]['MICRO_INITIAL_OFFSET_B'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}MICRO-INITIAL-OFFSET-B').text)
                    self.Ecus[ecu_name]['MACRO_INITIAL_OFFSET_A'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}MACRO-INITIAL-OFFSET-A').text)
                    self.Ecus[ecu_name]['MACRO_INITIAL_OFFSET_B'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}MACRO-INITIAL-OFFSET-B').text)
                    self.Ecus[ecu_name]['DELAY_COMPENSATION_A'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}MACRO-INITIAL-OFFSET-A').text)
                    self.Ecus[ecu_name]['DELAY_COMPENSATION_B'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}MACRO-INITIAL-OFFSET-B').text)
                    self.Ecus[ecu_name]['CLUSTER_DRIFT_DAMPING'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}CLUSTER-DRIFT-DAMPING').text)
                    self.Ecus[ecu_name]['DECODING_CORRECTION'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}DECODING-CORRECTION').text)
                    self.Ecus[ecu_name]['OFFSET_CORRECTION_OUT'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}OFFSET-CORRECTION-OUT').text)
                    self.Ecus[ecu_name]['RATE_CORRECTION_OUT'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}RATE-CORRECTION-OUT').text)
                    self.Ecus[ecu_name]['EXTERN_OFFSET_CORRECTION'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}EXTERN-OFFSET-CORRECTION').text)
                    self.Ecus[ecu_name]['EXTERN_RATE_CORRECTION'] = int(ECU.find('{http://www.asam.net/xml/fbx/flexray}EXTERN-RATE-CORRECTION').text)
                    self.Ecus[ecu_name]['TX_Frame']=[]
                    self.Ecus[ecu_name]['RX_Frame']=[]
                    for INPUT_PORT in INPUT_PORTS:
                        _rx_frame = {}
                        Trgger_ID = INPUT_PORT.find('{http://www.asam.net/xml/fbx}FRAME-TRIGGERING-REF').attrib.get('ID-REF',None)
                        _rx_frame['SLOT-ID'] = self.Triggers[Trgger_ID]['SLOT-ID']
                        _rx_frame['BASE-CYCLE'] = self.Triggers[Trgger_ID]['BASE-CYCLE']
                        _rx_frame['CYCLE-REPETITION'] = self.Triggers[Trgger_ID]['CYCLE-REPETITION']
                        _rx_frame['FDLC'] = self.Triggers[Trgger_ID]['FDLC']
                        self.Ecus[ecu_name]['RX_Frame'].append(_rx_frame)
                        del Trgger_ID,_rx_frame
                    for OUTPUT_PORT in OUTPUT_PORTS:
                        _tx_frame = {}
                        Trgger_ID = OUTPUT_PORT.find('{http://www.asam.net/xml/fbx}FRAME-TRIGGERING-REF').attrib.get('ID-REF',None)
                        _tx_frame['SLOT-ID'] = self.Triggers[Trgger_ID]['SLOT-ID']
                        _tx_frame['BASE-CYCLE'] = self.Triggers[Trgger_ID]['BASE-CYCLE']
                        _tx_frame['CYCLE-REPETITION'] = self.Triggers[Trgger_ID]['CYCLE-REPETITION']
                        _tx_frame['FDLC'] = self.Triggers[Trgger_ID]['FDLC']
                        if self.Ecus[ecu_name]['startupFrame_ID'] == _tx_frame['SLOT-ID'] and len(self.Ecus[ecu_name]['TX_Frame'])!=0  :
                            self.Ecus[ecu_name]['TX_Frame'].append(self.Ecus[ecu_name]['TX_Frame'][0])
                            self.Ecus[ecu_name]['TX_Frame'][0] = _tx_frame
                        else:
                            self.Ecus[ecu_name]['TX_Frame'].append(_tx_frame)
                        del Trgger_ID,_tx_frame
                    del ecu_name

class CHANNEL_INDEX():
    """
    channle index 

    """
    (
        CHN1, CHN2, CHN3, CHN4, CHN5, CHN6, CHN7, CHN8, CHN9, CHN10, CHN11, CHN12, CHN13, CHN14, CHN15, CHN16, CHN17,
        CHN18, CHN19, CHN20, CHN21, CHN22, CHN23, CHN24, CHN25, CHN26, CHN27, CHN28, CHN29, CHN30, CHN31, CHN32) = (
        c_int(0), c_int(1), c_int(2), c_int(3), c_int(4), c_int(
            5), c_int(6), c_int(7), c_int(8), c_int(9), c_int(10),
        c_int(11), c_int(12), c_int(13), c_int(14), c_int(15), c_int(
            16), c_int(17), c_int(18), c_int(19), c_int(20),
        c_int(21), c_int(22), c_int(23), c_int(24), c_int(
            25), c_int(26), c_int(27), c_int(28), c_int(29),
        c_int(30),
        c_int(31)
    )


class READ_TX_RX_DEF():
    '''
    ONLY_RX_MESSAGES:receive msg inclued tx and rx msg   
    TX_RX_MESSAGES: only receive rx msg
    receive function:
    tsfifo_receive_can_msgs           #receive can message
    tsfifo_receive_canfd_msgs         #receive canfd message include can message
    tsfifo_receive_lin_msgs           #receive lin message
    tsfifo_receive_flexray_msgs       #receive flexray message
    '''
    ONLY_RX_MESSAGES = c_int(0)
    TX_RX_MESSAGES = c_int(1)


class LIN_PROTOCOL():
    """
    set LIN protocol include 1.3 2.0 2.1 and j2602
    
    function:
    tsapp_configure_baudrate_lin
    """
    LIN_PROTOCOL_13 = c_int(0)
    LIN_PROTOCOL_20 = c_int(1)
    LIN_PROTOCOL_21 = c_int(2)
    LIN_PROTOCOL_J2602 = c_int(3)


class T_LIN_NODE_FUNCTION():
    """
    set LIN node include MASTER  SLAVE 
    function:
    tslin_set_node_funtiontype
    """
    T_MASTER_NODE = c_int(0)
    T_SLAVE_NODE = c_int(1)
    T_MONITOR_NODE = c_int(2)


class TLIBCANFDControllerType():
    """
    set canfd baudrate and canfd mode : can isocanfd non-isocanfd
    function:
    tsapp_configure_baudrate_canfd
    """
    lfdtCAN = c_int(0)
    lfdtISOCAN = c_int(1)
    lfdtNonISOCAN = c_int(2)


class TLIBCANFDControllerMode():
    """
    set canfd Controller Mode :Normal ACKoff Restricted
    function:
    tsapp_configure_baudrate_canfd
    """
    lfdmNormal = c_int(0)
    lfdmACKOff = c_int(1)
    lfdmRestricted = c_int(2)


class A120():
    """
    set hardware termination resistor 
    function:
    tsapp_configure_baudrate_canfd
    """
    DEABLEA120 = c_int(0)
    ENABLEA120 = c_int(1)


class CONVERTTYPE():
    '''
    log converstion type
    '''
    BLF = 0
    ASC = 1
    CSV = 2
    TXT = 3
    SQL = 4
    LOG = 5


class TLIBCAN(Structure):
    '''
    CAN Structure
    funciton:
    tsapp_transmit_can_async            async send can msg
    tsapp_transmit_can_sync             sync send can msg
    tscan_add_cyclic_msg_can            cyclic send can msg
    tsfifo_receive_can_msgs             receive can msg
    '''
    _pack_ = 1
    _fields_ = [("FIdxChn", c_uint8),           # channel index starting from 0
                ("FProperties", c_uint8),       # [7] 0-normal frame, 1-error frame
                                                # [6] 0-not logged, 1-already logged
                                                # [5-3] tbd
                                                # [2] 0-std frame, 1-extended frame
                                                # [1] 0-data frame, 1-remote frame
                                                # [0] dir: 0-RX, 1-TX 
                ("FDLC", c_uint8),              # dlc from 0 to 8
                ("FReserved", c_uint8),
                ("FIdentifier", c_int32),
                ("FTimeUs", c_uint64),
                ("FData", c_uint8 * 8),
                ]

    def __init__(self, FIdxChn=0, FDLC=8, FIdentifier=0x1, FProperties=1, FData=[]):
        self.FIdxChn = FIdxChn
        self.FDLC = FDLC
        if self.FDLC > 8:
            self.FDLC = 8
        self.FIdentifier = FIdentifier
        self.FProperties = FProperties
        for i in range(len(FData)):
            self.FData[i] = FData[i]

    def set_data(self, data):
        lengh = len(data)
        if lengh > self.FDLC:
            lengh = self.FDLC
        for i in range(lengh):
            self.FData[i] = data[i]

    def __str__(self):
        field_strings = [f"Timestamp: {self.FTimeUs:>15.6f}"]

        field_strings.append(f"Channel: {self.FIdxChn}")

        if (self.FProperties >> 2 & 1) == 1:
            FIdentifier = f"ID: {self.FIdentifier:08x}"
        else:
            FIdentifier = f"ID: {self.FIdentifier:04x}"
        field_strings.append(FIdentifier.rjust(12, " "))
        flag_string = " ".join(
            [
                "ext" if (self.FProperties >> 2 & 1) == 1 else "std",
                "Rx" if (self.FProperties & 1) == 0 else "Tx",
                "E" if self.FProperties == 0x80 else " ",
                "R" if (self.FProperties >> 1 & 1) == 1 else " ",
            ]
        )
        field_strings.append(flag_string)
        field_strings.append(f"DL: {self.FDLC:2d}")
        data_strings = []
        for i in range(self.FDLC):
            data_strings.append(f"{self.FData[i]:02x}")
        field_strings.append(" ".join(data_strings).ljust(24, " "))
        return "    ".join(field_strings).strip()


class TLIBCANFD(Structure):
    _pack_ = 1
    _fields_ = [("FIdxChn", c_uint8),       # channel index starting from 0
                ("FProperties", c_uint8),   # [7] 0-normal frame, 1-error frame
                                            # [6] 0-not logged, 1-already logged
                                            # [5-3] tbd
                                            # [2] 0-std frame, 1-extended frame
                                            # [1] 0-data frame, 1-remote frame
                                            # [0] dir: 0-RX, 1-TX 
                ("FDLC", c_uint8),          # dlc from 0 to 15 (0 to 64)
                ("FFDProperties", c_uint8), # [2] ESI, The E RROR S TATE I NDICATOR (ESI) flag is transmitted dominant by error active nodes, recessive by error passive nodes. ESI does not exist in CAN format frames
                                            # [1] BRS, If the bit is transmitted recessive, the bit rate is switched from the standard bit rate of the A RBITRATION P HASE to the preconfigured alternate bit rate of the D ATA P HASE . If it is transmitted dominant, the bit rate is not switched. BRS does not exist in CAN format frames.
                                            # [0] EDL: 0-normal CAN frame, 1-FD frame, added 2020-02-12, The E XTENDED D 
                ("FIdentifier", c_int32),
                ("FTimeUs", c_ulonglong),
                ("FData", c_ubyte * 64),
                ]

    def __init__(self, FIdxChn=0, FDLC=8, FIdentifier=0x1, FProperties=1, FFDProperties=1, FData=[]):

        self.FIdxChn = FIdxChn
        self.FDLC = FDLC
        if self.FDLC > 15:
            self.FDLC = 15
        self.FIdentifier = FIdentifier
        self.FProperties = FProperties
        self.FFDProperties = FFDProperties
        for i in range(len(FData)):
            self.FData[i] = FData[i]

    def set_data(self, data):
        lengh = len(data)
        if lengh > DLC_DATA_BYTE_CNT(self.FDLC):
            lengh = DLC_DATA_BYTE_CNT(self.FDLC)
        for i in range(lengh):
            self.FData[i] = data[i]

    def __str__(self):
        field_strings = [f"Timestamp: {self.FTimeUs:>15.6f}"]

        field_strings.append(f"Channel: {self.FIdxChn}")

        if (self.FProperties >> 2 & 1) == 1:
            FIdentifier = f"ID: {self.FIdentifier:08x}"
        else:
            FIdentifier = f"ID: {self.FIdentifier:04x}"
        field_strings.append(FIdentifier.rjust(12, " "))
        flag_string = " ".join(
            [
                "ext" if (self.FProperties >> 2 & 1) == 1 else "std",
                "Rx" if (self.FProperties & 1) == 0 else "Tx",
                "E" if self.FProperties == 0x80 else " ",
                "R" if (self.FProperties >> 1 & 1) == 1 else " ",
                "F" if (self.FFDProperties & 1 == 1) else " ",
                "BS" if (self.FFDProperties >> 1 & 1 == 1) else "  ",
                "EI" if (self.FFDProperties >> 2 & 1 == 1) else "  ",
            ]
        )
        field_strings.append(flag_string)
        field_strings.append(f"DL: {self.FDLC:2d}")
        data_strings = []
        for i in range(DLC_DATA_BYTE_CNT[self.FDLC]):
            data_strings.append(f"{self.FData[i]:02x}")
        field_strings.append(" ".join(data_strings).ljust(24, " "))
        return "    ".join(field_strings).strip()


class TLIBLIN(Structure):
    _pack_ = 1
    _fields_ = [("FIdxChn", c_ubyte),           # channel index starting from 0
                ("FErrCode", c_ubyte),          #  0: normal
                ("FProperties", c_ubyte),       # [7] tbd
                                                # [6] 0-not logged, 1-already logged
                                                # [5-4] FHWType #DEV_MASTER,DEV_SLAVE,DEV_LISTENER
                                                # [3] 0-not ReceivedSync, 1- ReceivedSync
                                                # [2] 0-not received FReceiveBreak, 1-Received Break
                                                # [1] 0-not send FReceiveBreak, 1-send Break
                                                # [0] dir: 0-RX, 1-TX
                ("FDLC", c_uint8),              # dlc from 0 to 8
                ("FIdentifier", c_ubyte),
                ("FChecksum", c_ubyte),
                ("FStatus", c_ubyte),
                ("FTimeUs", c_ulonglong),
                ("FData", c_uint8 * 8),
                ]


class TLIBFlexray(Structure):
    _pack_ = 1
    _fields_ = [("FIdxChn", c_uint8),                       # channel index starting from 0
                ("FChannelMask", c_uint8),                  # 0: reserved, 1: A, 2: B, 3: AB 
                ("FDir", c_uint8),                          # 0: Rx, 1: Tx, 2: Tx Request
                ("FPayloadLength", c_uint8),                # payload length in bytes
                ("FActualPayloadLength", c_uint8),          # actual data bytes
                ("FCycleNumber", c_uint8),                  # cycle number: 0~63
                ("FCCType", c_uint8),                       # 0 = Architecture independent, 1 = Invalid CC type, 2 = Cyclone I, 3 = BUSDOCTOR, 4 = Cyclone II, 5 = Vector VN interface, 6 = VN - Sync - Pulse(only in Status Event, for debugging purposes only)
                ("FReserved0", c_uint8),                    
                ("FHeaderCRCA", c_uint16),                  # header crc A
                ("FHeaderCRCB", c_uint16),                  # header crc B
                ("FFrameStateInfo", c_uint16),              # bit 0~15, error flags
                ("FSlotId", c_uint16),                      # static seg: 0~1023
                ("FFrameFlags", c_uint32),                  # bit 0~22
                                                            # 0 1 = Null frame.
                                                            # 1 1 = Data segment contains valid data
                                                            # 2 1 = Sync bit
                                                            # 3 1 = Startup flag
                                                            # 4 1 = Payload preamble bit
                                                            # 5 1 = Reserved bit
                                                            # 6 1 = Error flag(error frame or invalid frame)
                                                            # 7..14 Reserved
                                                            # 15 1 = Async.monitoring has generated this event
                                                            # 16 1 = Event is a PDU
                                                            # 17 Valid for PDUs only.The bit is set if the PDU is valid(either if the PDU has no  # update bit, or the update bit for the PDU was set in the received frame).
                                                            # 18 Reserved
                                                            # 19 1 = Raw frame(only valid if PDUs are used in the configuration).A raw frame may  # contain PDUs in its payload
                                                            # 20 1 = Dynamic segment	0 = Static segment
                                                            # 21 This flag is only valid for frames and not for PDUs.	1 = The PDUs in the payload of  # this frame are logged in separate logging entries. 0 = The PDUs in the payload of this  # frame must be extracted out of this frame.The logging file does not contain separate  # PDU - entries.
                                                            # 22 Valid for PDUs only.The bit is set if the PDU has an update bit
                ("FFrameCRC", c_uint32),                    # frame crc
                ("FReserved1", c_uint64),
                ("FReserved2", c_uint64),
                ("FTimeUs", c_uint64),
                ("FData", c_uint8 * 254),                   # 254 data bytes
                ]
    def __init__(self,FIdxChn=0,FSlotId=1,FChannelMask=1,FActualPayloadLength=32,FCycleNumber=1,FData=[]):
        self.FIdxChn = FIdxChn
        self.FSlotId = FSlotId
        self.FChannelMask = FChannelMask
        self.FActualPayloadLength = FActualPayloadLength
        self.FCycleNumber = FCycleNumber    
        datalen = len(FData)
        if datalen>self.FActualPayloadLength:
            datalen = self.FActualPayloadLength
        for i in range(datalen):
            self.FData[i] = FData[i]
    def set_data(self,data):
        datalen = len(data)
        if datalen>self.FActualPayloadLength:
            datalen = self.FActualPayloadLength
        for i in range(datalen):
            self.FData[i] = data[i]
        

class TLibFlexray_controller_config(Structure):
    """
    Most of the structural parameters are obtained from the database
    """
    _pack_ = 1
    _fields_ = [("NETWORK_MANAGEMENT_VECTOR_LENGTH", c_uint8),
                ("PAYLOAD_LENGTH_STATIC", c_uint8),
                ("FReserved", c_uint16),
                ("LATEST_TX", c_uint16),
                # __ prtc1Control
                ("T_S_S_TRANSMITTER", c_uint16),
                ("CAS_RX_LOW_MAX", c_uint8),
                ("SPEED", c_uint8),                                          #0 for 10m, 1 for 5m, 2 for 2.5m, convert from Database
                ("WAKE_UP_SYMBOL_RX_WINDOW", c_uint16),
                ("WAKE_UP_PATTERN", c_uint8),
                # __ prtc2Control
                ("WAKE_UP_SYMBOL_RX_IDLE", c_uint8),
                ("WAKE_UP_SYMBOL_RX_LOW", c_uint8),
                ("WAKE_UP_SYMBOL_TX_IDLE", c_uint8),
                ("WAKE_UP_SYMBOL_TX_LOW", c_uint8),
                # __ succ1Config
                ("channelAConnectedNode", c_uint8),                          # Enable ChannelA: 0: Disable 1: Enable
                ("channelBConnectedNode", c_uint8),                          # Enable ChannelB: 0: Disable 1: Enable
                ("channelASymbolTransmitted", c_uint8),                      # Enable Symble Transmit function of Channel A: 0: Disable 1: Enable
                ("channelBSymbolTransmitted", c_uint8),                      # Enable Symble Transmit function of Channel B: 0: Disable 1: Enable
                ("ALLOW_HALT_DUE_TO_CLOCK", c_uint8),
                ("SINGLE_SLOT_ENABLED", c_uint8),                            # FALSE_0, TRUE_1
                ("wake_up_idx", c_uint8),                                    # Wake up channe: 0:ChannelA， 1:ChannelB
                ("ALLOW_PASSIVE_TO_ACTIVE", c_uint8),                        
                ("COLD_START_ATTEMPTS", c_uint8),                           
                ("synchFrameTransmitted", c_uint8),                          # Need to transmit sync frame
                ("startupFrameTransmitted", c_uint8),                        # Need to transmit startup frame
                # __ succ2Config
                ("LISTEN_TIMEOUT", c_uint32),
                ("LISTEN_NOISE", c_uint8),                                   #2_16
                # __ succ3Config
                ("MAX_WITHOUT_CLOCK_CORRECTION_PASSIVE", c_uint8),
                ("MAX_WITHOUT_CLOCK_CORRECTION_FATAL", c_uint8),
                ("REVERS0", c_uint8),
                # __ gtuConfig
                # __ gtu01Config
                ("MICRO_PER_CYCLE", c_uint32),
                # __ gtu02Config
                ("Macro_Per_Cycle", c_uint16),
                ("SYNC_NODE_MAX", c_uint8),
                ("REVERS1", c_uint8),
                # __ gtu03Config
                ("MICRO_INITIAL_OFFSET_A", c_uint8),
                ("MICRO_INITIAL_OFFSET_B", c_uint8),
                ("MACRO_INITIAL_OFFSET_A", c_uint8),
                ("MACRO_INITIAL_OFFSET_B", c_uint8),
                # __ gtu04Config
                ("N_I_T", c_uint16),
                ("OFFSET_CORRECTION_START", c_uint16),
                # __ gtu05Config
                ("DELAY_COMPENSATION_A", c_uint8),
                ("DELAY_COMPENSATION_B", c_uint8),
                ("CLUSTER_DRIFT_DAMPING", c_uint8),
                ("DECODING_CORRECTION", c_uint8),
                # __ gtu06Config
                ("ACCEPTED_STARTUP_RANGE", c_uint16),
                ("MAX_DRIFT", c_uint16),
                # __ gtu07Config
                ("STATIC_SLOT", c_uint16),
                ("NUMBER_OF_STATIC_SLOTS", c_uint16),
                # __ gtu08Config
                ("MINISLOT", c_uint8),
                ("REVERS2", c_uint8),
                ("NUMBER_OF_MINISLOTS", c_uint16),
                # __ gtu09Config
                ("DYNAMIC_SLOT_IDLE_PHASE", c_uint8),
                ("ACTION_POINT_OFFSET", c_uint8),
                ("MINISLOT_ACTION_POINT_OFFSET", c_uint8),
                ("REVERS3", c_uint8),
                # __ gtu10Config
                ("OFFSET_CORRECTION_OUT", c_uint16),
                ("RATE_CORRECTION_OUT", c_uint16),
                # __ gtu11Config
                ("EXTERN_OFFSET_CORRECTION", c_uint8),
                ("EXTERN_RATE_CORRECTION", c_uint8),
                ("config1_byte", c_uint8),
                ("config_byte", c_uint8),   # bit0: 1:Channel A set termination resistor  0:Channel A not set termination resistor
                                            # bit1: 1:Channel B set termination resistor  0:Channel B not set termination resistor
                                            # bit2: 1:enable FIFO     0:disable FIFO
                                            # bit4: 1:cha enable Bridging    0:cha disable Bridging
                                            # bit5: 1:chb enable Bridging    0:chb disable Bridging
                                            # bit6: 1:not ignore NULL Frame  0: ignore NULL Frame
                ]
        # self.config_byte = 0x3f
    def set_controller_config(self,xml_,is_open_a=True, is_open_b=True, wakeup_chn=0, enable100_a=True, enable100_b=True,is_show_nullframe=True, is_Bridging=False):
        if isinstance(xml_,dict):
            self.NETWORK_MANAGEMENT_VECTOR_LENGTH = xml_['NETWORK_MANAGEMENT_VECTOR_LENGTH']
            self.PAYLOAD_LENGTH_STATIC = xml_['PAYLOAD_LENGTH_STATIC']
            self.LATEST_TX = xml_['LATEST_TX']
            self.T_S_S_TRANSMITTER = xml_['T_S_S_TRANSMITTER']
            self.CAS_RX_LOW_MAX = xml_['CAS_RX_LOW_MAX']
            self.SPEED = xml_['SPEED']
            self.WAKE_UP_SYMBOL_RX_WINDOW = xml_['WAKE_UP_SYMBOL_RX_WINDOW']
            self.WAKE_UP_PATTERN = xml_['WAKE_UP_PATTERN']
            self.WAKE_UP_SYMBOL_RX_IDLE = xml_['WAKE_UP_SYMBOL_RX_IDLE']
            self.WAKE_UP_SYMBOL_RX_LOW = xml_['WAKE_UP_SYMBOL_RX_LOW']
            self.WAKE_UP_SYMBOL_TX_IDLE = xml_['WAKE_UP_SYMBOL_TX_IDLE']
            self.WAKE_UP_SYMBOL_TX_LOW = xml_['WAKE_UP_SYMBOL_TX_LOW']
            self.channelAConnectedNode = 1 if is_open_a else 0
            self.channelBConnectedNode = 1 if is_open_b else 0
            self.channelASymbolTransmitted = 1  
            self.channelBSymbolTransmitted = 1  
            self.ALLOW_HALT_DUE_TO_CLOCK = xml_['ALLOW_HALT_DUE_TO_CLOCK']
            self.SINGLE_SLOT_ENABLED = xml_['SINGLE_SLOT_ENABLED']
            self.wake_up_idx = wakeup_chn
            self.ALLOW_PASSIVE_TO_ACTIVE = xml_['ALLOW_PASSIVE_TO_ACTIVE']
            self.COLD_START_ATTEMPTS = xml_['COLD_START_ATTEMPTS']
            self.synchFrameTransmitted = 1
            self.startupFrameTransmitted = xml_['startupFrameTransmitted']
            self.LISTEN_TIMEOUT = xml_['LISTEN_TIMEOUT']
            self.LISTEN_NOISE = xml_['LISTEN_NOISE']
            self.MAX_WITHOUT_CLOCK_CORRECTION_PASSIVE = xml_['MAX_WITHOUT_CLOCK_CORRECTION_PASSIVE']
            self.MAX_WITHOUT_CLOCK_CORRECTION_FATAL = xml_['MAX_WITHOUT_CLOCK_CORRECTION_FATAL']
            self.MICRO_PER_CYCLE = xml_['MICRO_PER_CYCLE']
            self.Macro_Per_Cycle = xml_['MACRO_PER_CYCLE']
            self.SYNC_NODE_MAX = xml_['SYNC_NODE_MAX']
            self.MICRO_INITIAL_OFFSET_A = xml_['MICRO_INITIAL_OFFSET_A']
            self.MICRO_INITIAL_OFFSET_B = xml_['MICRO_INITIAL_OFFSET_B']
            self.MACRO_INITIAL_OFFSET_A = xml_['MACRO_INITIAL_OFFSET_A']
            self.MACRO_INITIAL_OFFSET_B = xml_['MACRO_INITIAL_OFFSET_B']
            self.N_I_T = xml_['N_I_T']
            self.OFFSET_CORRECTION_START = xml_['OFFSET_CORRECTION_START']
            self.DELAY_COMPENSATION_A = xml_['DELAY_COMPENSATION_A']
            self.DELAY_COMPENSATION_B = xml_['DELAY_COMPENSATION_B']
            self.CLUSTER_DRIFT_DAMPING = xml_['CLUSTER_DRIFT_DAMPING']
            self.DECODING_CORRECTION = xml_['DECODING_CORRECTION']
            self.ACCEPTED_STARTUP_RANGE = xml_['ACCEPTED_STARTUP_RANGE']
            self.MAX_DRIFT = xml_['MAX_DRIFT']
            self.STATIC_SLOT = xml_['STATIC_SLOT']
            self.NUMBER_OF_STATIC_SLOTS = xml_['NUMBER_OF_STATIC_SLOTS']
            self.MINISLOT = xml_['MINISLOT']
            self.NUMBER_OF_MINISLOTS = xml_['NUMBER_OF_MINISLOTS']
            self.DYNAMIC_SLOT_IDLE_PHASE = xml_['DYNAMIC_SLOT_IDLE_PHASE']
            self.ACTION_POINT_OFFSET = xml_['ACTION_POINT_OFFSET']
            self.MINISLOT_ACTION_POINT_OFFSET = xml_['MINISLOT_ACTION_POINT_OFFSET']
            self.OFFSET_CORRECTION_OUT = xml_['OFFSET_CORRECTION_OUT']
            self.RATE_CORRECTION_OUT = xml_['RATE_CORRECTION_OUT']
            self.EXTERN_OFFSET_CORRECTION = xml_['EXTERN_OFFSET_CORRECTION']
            self.EXTERN_RATE_CORRECTION = xml_['EXTERN_RATE_CORRECTION']
            self.config1_byte = 1
                # if
            self.config_byte = 0xc
            if is_Bridging:
                    self.config_byte = 0x3c
            self.config_byte = self.config_byte | (0x1 if enable100_a else 0x00) | (0x2 if enable100_b else 0x00) | (0x40 if is_show_nullframe else 0x00)
        return self
class TLibTrigger_def(Structure):
    _pack_ = 1
    _fields_ = [("slot_id", c_uint16),      # Slot id
                ("frame_idx", c_uint8),     # frame index

                ("cycle_code", c_uint8),    #BASE-CYCLE + CYCLE-REPETITION
                ("config_byte", c_uint8),   # bit0: enanle A
                                            # bit1: enanle B
                                            # bit2: is NM msg
                                            # bit3: 0 :cycle ，1:Single trigger
                                            # bit4: Whether it is a cold start message, only buffer 0 can be set to 1
                                            # bit5: Whether it is a synchronization message, only the buffer 0/1 can be set to 1
                                            # bit6:
                                            # bit7: 0 - static，1 - Dynamic
                ("recv", c_uint8),
                ]
    def __init__(self, frame_idx=0, slot_id=1, cycle_code=1, config_byte=0x33):
        self.frame_idx = frame_idx
        self.slot_id = slot_id
        self.cycle_code = cycle_code
        self.config_byte = config_byte


DLC_DATA_BYTE_CNT = (
    0, 1, 2, 3, 4, 5, 6, 7,
    8, 12, 16, 20, 24, 32, 48, 64
)


def tosun_convert_msg(msg):
    """
    TLIBCAN  TLIBCANFD msg convert to can.Message
    Easy python-can to use
    """
    if isinstance(msg, TLIBCAN):
        return Message(
            timestamp=blf_start_time + float(msg.FTimeUs) / 1000000,
            arbitration_id=msg.FIdentifier,
            is_extended_id=msg.FProperties & 0x04,
            is_remote_frame=msg.FProperties & 0x02,
            is_error_frame=msg.FProperties & 0x80,
            channel=msg.FIdxChn,
            dlc=msg.FDLC,
            data=bytes(msg.FData),
            is_fd=False,
            is_rx=False if msg.FProperties & 0x01 else True,
        )
    elif isinstance(msg, TLIBCANFD):
        return Message(
            timestamp=blf_start_time + float(msg.FTimeUs) / 1000000,
            arbitration_id=msg.FIdentifier,
            is_extended_id=msg.FProperties & 0x04,
            is_remote_frame=msg.FProperties & 0x02,
            channel=msg.FIdxChn,
            dlc=DLC_DATA_BYTE_CNT[msg.FDLC],
            data=bytes(msg.FData),
            is_fd=msg.FFDProperties & 0x01,
            is_rx=False if msg.FProperties & 0x01 else True,
            bitrate_switch=msg.FFDProperties & 0x02,
            error_state_indicator=msg.FFDProperties & 0x04,
            is_error_frame=msg.FProperties & 0x80
        )
    elif isinstance(msg, Message):
        return msg
    else:
        raise (f'Unknown message type: {type(msg)}')


def msg_convert_tosun(msg):
    """
    can.Message convert to  TLIBCAN  TLIBCANFD msg 
    Easy python-can to use
    """
    if isinstance(msg, TLIBCAN):
        return msg
    elif isinstance(msg, TLIBCANFD):
        return msg
    elif isinstance(msg, TLIBLIN):
        return msg
    elif isinstance(msg, Message):
        if msg.is_fd:
            result = TLIBCANFD()
            result.FFDProperties = 0x01 | (0x02 if msg.bitrate_switch else 0x00) | \
                (0x04 if msg.error_state_indicator else 0x00)
        else:
            result = TLIBCAN()
        result.FIdxChn = msg.channel
        result.FProperties = 0x01 | (0x00 if msg.is_rx else 0x01) | \
            (0x02 if msg.is_remote_frame else 0x00) | \
            (0x04 if msg.is_extended_id else 0x00)
        try:
            result.FDLC = DLC_DATA_BYTE_CNT.index(msg.dlc)
        except:
            if msg.dlc < 0x10:
                result.FDLC = msg.dlc
            else:
                print("Message DLC input error")

        result.FIdentifier = msg.arbitration_id
        result.FTimeUs = int(msg.timestamp)
        for index, item in enumerate(msg.data):
            result.FData[index] = item
        return result
    else:
        raise (f'Unknown message type: {type(msg)}')


start_time = 0


def finalize_lib_tscan():
    """
    Release function 
    There is no need to call now because I will automatically release it at the end of the program
    """
    dll.finalize_lib_tscan()


# 初始化函数（是否使能fifo,是否濢 活极速模式）
def initialize_lib_tsmaster(AEnableFIFO: c_bool, AEnableError: c_bool,AUseHWTime:c_bool):
    """
    Initialization function 
    There is no need to call it now because I will automatically call it when the program loads
    """
    dll.initialize_lib_tscan(AEnableFIFO, AEnableError, AUseHWTime)


# connect hw
def tsapp_connect(ADeviceSerial: str, AHandle: c_size_t):
    """
    Args:
        ADeviceSerial (str): Equipment serial number example: b"1234568798DFE" if ADeviceSerial =='': Connect directly to any device
        AHandle (c_size_t): handle For specified hardware

    Returns:
        r:error_code AHandle:handle For specified hardware
    
    example:
        AHandle = c_size_t(0)
        r = tsapp_connect(b"1234568798DFE",AHandle) or tsapp_connect("",AHandle) 
        if(r==0 or r==5):  #0 or 5 :connect success
            print(AHandle)
    """
    r = dll.tscan_connect(ADeviceSerial, byref(AHandle))
    return r

def tscan_get_can_channel_count(ADeviceSerial):
    """
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
    Returns:
        r:can channel count
    
    example:
        AHandle = c_size_t(0)
        r = tsapp_connect(b"1234568798DFE",AHandle) or tsapp_connect("",AHandle) 
        if(r==0 or r==5):  #0 or 5 :connect success
            print(AHandle)
            can_count = tscan_get_can_channel_count(ADeviceSerial)
    """
    ACount = c_int32(0)
    dll.tscan_get_can_channel_count(ADeviceSerial,byref(ACount))
    return ACount.value

def tscan_get_lin_channel_count(ADeviceSerial):
    """
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
    Returns:
        r:lin channel count
    
    example:
        AHandle = c_size_t(0)
        r = tsapp_connect(b"1234568798DFE",AHandle) or tsapp_connect("",AHandle) 
        if(r==0 or r==5):  #0 or 5 :connect success
            print(AHandle)
            lin_count = tscan_get_lin_channel_count(ADeviceSerial)
    """
    ACount = c_int32(0)
    dll.tscan_get_lin_channel_count(ADeviceSerial,byref(ACount))
    return ACount.value

def tscan_get_flexray_channel_count(ADeviceSerial):
    """
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
    Returns:
        r:flexray channel count
    
    example:
        AHandle = c_size_t(0)
        r = tsapp_connect(b"1234568798DFE",AHandle) or tsapp_connect("",AHandle) 
        if(r==0 or r==5):  #0 or 5 :connect success
            print(AHandle)
            flexray_count = tscan_get_flexray_channel_count(ADeviceSerial)
    """
    ACount = c_int32(0)
    dll.tscan_get_flexray_channel_count(ADeviceSerial,byref(ACount))
    return ACount.value

def tscan_scan_devices(ADeviceCount: c_uint32):
    """
    Args:
        ADeviceCount (c_uint32): _description_ :get devices count 

    Returns:
        r:error_code ADeviceCount:get devices count
    example:
        ADeviceCount = c_uint32(0)
        r = tscan_scan_devices(ADeviceCount)
        if r==0:       #0 :get success   
            print(ADeviceCount)
    """
    r = dll.tscan_scan_devices(byref(ADeviceCount))
    return r

def tscan_get_device_info(ADeviceCount: c_uint32):
    """
    get hw info
    Args:
        ADeviceCount (c_uint32): hw_index 

    Returns:
        FManufacturer, FProduct, FSerial
    example:
        ADeviceCount = c_uint32(0)
        r = tscan_scan_devices(ADeviceCount)
        if r==0:       #0 :get success   
            for i in range(ADeviceCount):
                print(tscan_get_device_info(i))
                
    """
    AFManufacturer = POINTER(POINTER(c_char))()
    AFProduct = POINTER(POINTER(c_char))()
    AFSerial = POINTER(POINTER(c_char))()
    r = dll.tscan_get_device_info(ADeviceCount, byref(
        AFManufacturer), byref(AFProduct), byref(AFSerial))
    if r == 0:
        FManufacturer = string_at(AFManufacturer).decode("utf8")
        FProduct = string_at(AFProduct).decode("utf8")
        FSerial = string_at(AFSerial).decode("utf8")
    else:
        print("查找失败")
        return 0, 0, 0
    return FManufacturer, FProduct, FSerial




def tscan_get_error_description(ACode: int):
    """
    Args:
        ACode (int): _description_ :error code 
    Returns:
        error code  description
    example:
        print(tscan_get_error_description(1))
    """
    errorcode = POINTER(POINTER(c_char))()
    if ACode == 0:
        return "确定"
    else:
        r = dll.tscan_get_error_description(c_int32(ACode), byref(errorcode))
        if r == 0:
            ADesc = string_at(errorcode).decode("utf-8")
            return ADesc
        else:
            return r


def tsflexray_set_controller_frametrigger(AHandle: c_size_t, ANodeIndex: c_uint,
                                          AControllerConfig: TLibFlexray_controller_config,
                                          AFrameLengthArray: bytearray,
                                          AFrameNum: c_int, AFrameTrigger: TLibTrigger_def, AFrameTriggerNum: c_int,
                                          ATimeoutMs: c_int):
    """
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ANodeIndex (c_uint): flexray channle 0 or 1                    
        AControllerConfig (TLibFlexray_controller_config): Controller Config from database config
        AFrameLengthArray (bytearray): Frame Array
        AFrameNum (c_int):  Frame len
        AFrameTrigger (TLibTrigger_def): Triggers 
        AFrameTriggerNum (c_int): Triggers len
        ATimeoutMs (c_int): timeout

    Returns:
        error code
        
    example:
        self = TLibFlexray_controller_config(is_open_a=True, is_open_b=True, enable100_b=True, is_show_nullframe=False,
                                        is_Bridging=True)
        fr_trigger = (TLibTrigger_def * 3)()
        '''(1,0,1)'''
        fr_trigger[0].frame_idx = 0
        fr_trigger[0].slot_id = 35
        fr_trigger[0].cycle_code = 1
        fr_trigger[0].config_byte = 0x33
        fr_trigger[0].recv = 0
        '''(3,0,4)'''
        fr_trigger[1].frame_idx = 1
        fr_trigger[1].slot_id = 3
        fr_trigger[1].cycle_code = 4
        fr_trigger[1].config_byte = 0x03
        fr_trigger[1].recv = 0
        '''(3,3,4)'''
        fr_trigger[2].frame_idx = 2
        fr_trigger[2].slot_id = 3
        fr_trigger[2].cycle_code = 7
        fr_trigger[2].config_byte = 0x03
        fr_trigger[2].recv = 0
        FrameLengthArray = (c_int * 3)(32, 32, 32)
        ret = tsflexray_set_controller_frametrigger(handle, chn0, self, FrameLengthArray, 3, fr_trigger, 3, 1000)
    """
    r = dll.tsflexray_set_controller_frametrigger(AHandle, ANodeIndex, byref(AControllerConfig),
                                                  AFrameLengthArray, AFrameNum, AFrameTrigger,
                                                  AFrameTriggerNum, ATimeoutMs)
    return r


def tsflexray_start_net(AHandle: c_size_t, ANodeIndex: c_int, ATimeoutMs: c_int):
    """
    start flexray network
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ANodeIndex (c_int): flexray channel 
        ATimeoutMs (c_int): timeout in ms
    Returns:
        error code
    example:
        tsflexray_start_net(handle,0,1000)
    """
    r = dll.tsflexray_start_net(AHandle, ANodeIndex, ATimeoutMs)
    return r


def tsflexray_stop_net(AHandle: c_size_t, ANodeIndex: c_int, ATimeoutMs: c_int):
    """
    stop flexray network

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ANodeIndex (c_int): flexray channel 
        ATimeoutMs (c_int): timeout in ms
    Returns:
        error code
    example:
        tsflexray_stop_net(handle,0,1000)
    """
    r = dll.tsflexray_stop_net(AHandle, ANodeIndex, ATimeoutMs)
    return r


def tsfifo_clear_flexray_receive_buffers(AHandle: c_size_t, chn: c_int):
    """
    clear flexray receive buffers

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        chn (c_int): flexray channel 
    Returns:
        error code
    example:
        tsfifo_clear_flexray_receive_buffers(handle,0)
    """
    r = dll.tsfifo_clear_flexray_receive_buffers(AHandle, chn)
    return r


def tsflexray_transmit_async(AHandle: c_size_t, AData: TLIBFlexray):
    """
    async send flexray msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        AData (TLIBFlexray): flexray msg

    Returns:
        error code
    example:
        flexray_1 = TLIBFlexray(FSlotId = 35,FChannelMask=1,FCycleNumber=1,FData=[1,2,3,4,5,6,7,8] )
        ret =  tsflexray_transmit_async(handle, flexray_1) 
    """
    r = dll.tsflexray_transmit_async(AHandle, byref(AData))
    return r


def tsflexray_transmit_sync(AHandle: c_size_t, AData: TLIBFlexray, ATimeoutMs: c_int32):
    """
    async send flexray msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        AData (TLIBFlexray): flexray msg
        ATimeoutMs (c_int32):timeout
    Returns:
        error code
    example:
        flexray_1 = TLIBFlexray(FSlotId = 35,FChannelMask=1,FCycleNumber=1,FData=[1,2,3,4,5,6,7,8] )
        ret =  tsflexray_transmit_sync(handle, flexray_1,c_int32(100)) 
    """
    r = dll.tsflexray_transmit_sync(AHandle, byref(AData), ATimeoutMs)
    return r


def tsfifo_read_flexray_buffer_frame_count(AHandle: c_size_t, AIdxChn: c_int32, ACount: c_int32):
    """
    get flexray buffer frame count

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        AIdxChn (c_int32): flexray channel 
        ACount (c_int32): get count

    Returns:
        error code
    
    example:
        ACount = c_int32(0)
        tsfifo_read_flexray_buffer_frame_count(AHandle,0,ACount)
        print(ACount)
    """
    r = dll.tsfifo_read_flexray_buffer_frame_count(
        AHandle, AIdxChn, byref(ACount))
    return r


def tsfifo_read_flexray_tx_buffer_frame_count(AHandle: c_size_t, AIdxChn: c_int32, ACount: c_int32):
    """
    get flexray buffer tx frame count

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        AIdxChn (c_int32): flexray channel 
        ACount (c_int32): get count

    Returns:
        error code
    
    example:
        ACount = c_int32(0)
        tsfifo_read_flexray_tx_buffer_frame_count(AHandle,0,ACount)
        print(ACount)
    """
    r = dll.tsfifo_read_flexray_tx_buffer_frame_count(
        AHandle, AIdxChn, byref(ACount))
    return r


def tsfifo_read_flexray_rx_buffer_frame_count(AHandle: c_size_t, AIdxChn: c_int32, ACount: c_int32):
    """
    get flexray buffer rx frame count

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        AIdxChn (c_int32): flexray channel 
        ACount (c_int32): get count

    Returns:
        error code
    
    example:
        ACount = c_int32(0)
        tsfifo_read_flexray_rx_buffer_frame_count(AHandle,0,ACount)
        print(ACount)
    """
    r = dll.tsfifo_read_flexray_rx_buffer_frame_count(
        AHandle, AIdxChn, byref(ACount))
    return r


def tsfifo_receive_flexray_msgs(AHandle: c_size_t, ADataBuffers: TLIBFlexray, ADataBufferSize: c_int32, chn: c_int32,
                                ARxTx: c_int8):
    """
    receive flexray msgs

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ADataBuffers (TLIBFlexray): flexray buffer 
        ADataBufferSize (c_int32): flexray buffer size
        chn (c_int32): flexray channel
        ARxTx (c_int8): include tx

    Returns:
        error_code TLIBFlexray_buffer ADataBufferSize
    example:    
        flexray_2 = (TLIBFlexray * 100)()
        size = c_int32(100)
        tsfifo_receive_flexray_msgs(handle, flexray_2, size, 0, 1)
        for i in flexray_2:
            string = ''
            for index in range(i.FActualPayloadLength):
                string += hex(i.FData[index]) + ' '
            print(i.FTimeUs, ' ', i.FSlotId, ' ', i.FCycleNumber, ' ', ('tx' if i.FDir else 'rx'), "  ", string)
    """
    r = dll.tsfifo_receive_flexray_msgs(
        AHandle, ADataBuffers, byref(ADataBufferSize), chn, ARxTx)
    return r


# 断开指定硬件连接
def tsapp_disconnect_by_handle(AHandle: c_size_t):
    """
    disconnect by handle
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle

    Returns:
        error code
    
    example:
        tsapp_disconnect_by_handle(handle)
    """
    r = dll.tscan_disconnect_by_handle(AHandle)
    return r



def tsapp_disconnect_all():
    """
    disconnect all hw

    Returns:
        error code
        
    example:
        tsapp_disconnect_all()
    """
    r = dll.tscan_disconnect_all_devices()
    return r


# 设置can参数
def tsapp_configure_baudrate_can(ADeviceHandle: c_size_t, AChnIdx: CHANNEL_INDEX, ARateKbps: c_double,A120: A120):
    """
    set  AChnIdx can baudrate include termination resistor 

    Args:
        ADeviceHandle (c_size_t): tsapp_connect retrun handle
        AChnIdx (CHANNEL_INDEX): can channle index
        ARateKbps (c_double): baudrate
        A120 (A120): enable termination resistor 

    Returns:
        error code
    example:
        tsapp_configure_baudrate_can(handle,CHANNEL_INDEX.CHN1,500,A120.DEABLEA120)
    """
    if not isinstance(ARateKbps, c_double):
        ARateKbps = c_double(ARateKbps)
    r = dll.tscan_config_can_by_baudrate(
        ADeviceHandle, AChnIdx, ARateKbps, A120)
    return r


# 设置canfd参数
def tsapp_configure_baudrate_canfd(ADeviceHandle: c_size_t, AChnIdx: CHANNEL_INDEX, ARateKbps: c_double,
                                   ADataKbps: c_double,
                                   AControllerType: TLIBCANFDControllerType, AControllerMode: TLIBCANFDControllerMode,
                                   A120: A120):
    """
    set  AChnIdx canfd baudrate include termination resistor

    Args:
        ADeviceHandle (c_size_t): tsapp_connect retrun handle
        AChnIdx (CHANNEL_INDEX): chn_index
        ARateKbps (c_double): Rate baudrate
        ADataKbps (c_double): data baudrate
        AControllerType (TLIBCANFDControllerType): can isocanfd non-isocanfd
        AControllerMode (TLIBCANFDControllerMode): normol ackoff 
        A120 (A120): enable termination resistor 
    Returns:
        error code
    
    example:
        tsapp_configure_baudrate_canfd(handle,CHANNEL_INDEX.CHN1,500,2000,TLIBCANFDControllerType.lfdtCAN,TLIBCANFDControllerMode.lfdmNormal,A120.A120_ENABLE)
    """
    if not isinstance(ARateKbps, c_double):
        ARateKbps = c_double(ARateKbps)
    if not isinstance(ADataKbps, c_double):
        ADataKbps = c_double(ADataKbps)
    r = dll.tscan_config_canfd_by_baudrate(ADeviceHandle, AChnIdx, ARateKbps, ADataKbps, AControllerType,
                                           AControllerMode, A120)
    return r


# can brs 采样率
def tsapp_configure_can_regs(ADeviceHandle: c_size_t, AIdxChn: CHANNEL_INDEX, ABaudrateKbps: float, ASEG1: int,
                             ASEG2: int, APrescaler: int,
                             ASJ2: int, AOnlyListen: c_uint32, A120: c_uint32):
    """
    configure can regs include baudrate and termination resistor
    Args:
        ADeviceHandle (c_size_t): tsapp_connect retrun handle
        AIdxChn (CHANNEL_INDEX): chn_index
        ABaudrateKbps (float): baudrate
        ASEG1 (int): Phase buffer section1
        ASEG2 (int): Phase buffer section2
        APrescaler (int): APrescaler
        ASJ2 (int): BTL count
        AOnlyListen (c_uint32): is only listen
        A120 (c_uint32): enable termination resistor 

    Returns:
        error code
    
    example:
        tsapp_configure_can_regs(handle, CHANNEL_INDEX.CHN1, 500, 63, 16, 1, 80, 0, A120.A120_ENABLE)
    """
    r = dll.tscan_configure_can_regs(ADeviceHandle, AIdxChn, c_float(ABaudrateKbps), c_uint32(ASEG1), c_uint32(ASEG2),
                                     c_uint32(APrescaler), c_uint32(ASJ2), AOnlyListen, A120)
    return r


# canfd brs 采样率
def tsapp_configure_canfd_regs(ADeviceHandle: c_size_t, AIdxChn: CHANNEL_INDEX, AArbBaudrateKbps: float, AArbSEG1: int,
                               AArbSEG2: int,
                               AArbPrescaler: int,
                               AArbSJ2: int, ADataBaudrateKbps: float, ADataSEG1: int, ADataSEG2: int,
                               ADataPrescaler: int,
                               ADataSJ2: int, AControllerType: TLIBCANFDControllerType,
                               AControllerMode: TLIBCANFDControllerMode,
                               AInstallTermResistor120Ohm: c_bool):
    """
    configure canfd regs include baudrate and termination resistor

    Args:
        ADeviceHandle (c_size_t): tsapp_connect retrun handle
        AIdxChn (CHANNEL_INDEX): chn_index
        AArbBaudrateKbps (float): Arbbaudrate
        AArbSEG1 (int): Arb Phase buffer section1
        AArbSEG2 (int): Arb Phase buffer section2
        AArbPrescaler (int): ArbPrescaler
        AArbSJ2 (int): Arb BTL count
        ADataBaudrateKbps (float): Databaudrate
        ADataSEG1 (int): Data Phase buffer section1
        ADataSEG2 (int): Data Phase buffer section2
        ADataPrescaler (int): Data Prescaler
        ADataSJ2 (int): Data BTL count
        AControllerType (TLIBCANFDControllerType): can isocanfd non-isocanfd
        AControllerMode (TLIBCANFDControllerMode): normol ackoff
        AInstallTermResistor120Ohm (c_bool): enable termination resistor 

    Returns:
        error code
    example:
        error = tsapp_canfd_config(handle, CHANNEL_INDEX.CHN1, 500, 63, 16, 1, 80, 2000,63,16,1,80,TLIBCANFDControllerType.lfdtCAN,TLIBCANFDControllerMode.lfdmNormal, A120.A120_ENABLE)
    """
    r = dll.tscan_configure_canfd_regs(ADeviceHandle, AIdxChn, c_float(AArbBaudrateKbps), c_uint32(AArbSEG1),
                                       c_uint32(AArbSEG2),
                                       c_uint32(AArbPrescaler), c_uint32(
                                           AArbSJ2),
                                       c_float(ADataBaudrateKbps), c_uint32(
                                           ADataSEG1),
                                       c_uint32(ADataSEG2), c_uint32(
                                           ADataPrescaler), c_uint32(ADataSJ2),
                                       AControllerType,
                                       AControllerMode,
                                       AInstallTermResistor120Ohm)
    return r


# 设置lin参数
def tsapp_configure_baudrate_lin(ADeviceHandle: c_size_t, AChnIdx: CHANNEL_INDEX, ARateKbps: c_double):
    """
    set lin baudrate
    Args:
        ADeviceHandle (c_size_t): tsapp_connect retrun handle
        AChnIdx (CHANNEL_INDEX): lin chnidx
        ARateKbps (c_double): baudrate

    Returns:
        error code
    example:
        tsapp_configure_baudrate_lin(handle,0,c_double(19.2))
    """
    r = dll.tslin_config_baudrate(ADeviceHandle, AChnIdx, ARateKbps)
    return r


# lin设置主节点
def tsapp_set_node_funtiontype(ADeviceHandle: c_size_t, AChnIdx: CHANNEL_INDEX, AFunctionType: T_LIN_NODE_FUNCTION):
    """
    set lin node funtiontype

    Args:
        ADeviceHandle (c_size_t): tsapp_connect retrun handle
        AChnIdx (CHANNEL_INDEX): lin chnidx
        AFunctionType (T_LIN_NODE_FUNCTION): T_MASTER_NODE T_SLAVE_NODE
    example:
        tsapp_set_node_funtiontype(handle,0,T_LIN_NODE_FUNCTION.T_MASTER_NODE)

    Returns:
        error code
    """
    r = dll.tslin_set_node_funtiontype(ADeviceHandle, AChnIdx, AFunctionType)
    return r


# # 下载ldf
# def tsapp_apply_download_new_ldf(ADeviceHandle: c_size_t, AChnIdx: CHANNEL_INDEX):
#     r = dll.tslin_apply_download_new_ldf(ADeviceHandle, AChnIdx)
#     return r


# 异步发  can报文
def tsapp_transmit_can_async(AHandle: c_size_t, Msg: TLIBCAN):
    """
    sync send can msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBCAN): can msg
    example:    
        msg = TLIBCAN(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tsapp_transmit_can_async(handle,msg)
    Returns:
        error code
    """
    r = dll.tscan_transmit_can_async(AHandle, byref(Msg))
    if r != 0:
        print("msg send failed")
    return r




# 同步发  can报文
def tsapp_transmit_can_sync(AHandle: c_size_t, Msg: TLIBCAN, ATimeoutMS: c_uint32):
    """
    sync send can msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBCAN): can msg
        ATimeoutMS (c_uint32): timeout in ms

    Returns:
        error code
    example:
        msg = TLIBCAN(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tsapp_transmit_can_sync(handle,msg,100)
    """
    if not isinstance(ATimeoutMS, c_uint32):
        ATimeoutMS = c_uint32(ATimeoutMS)
    r = dll.tscan_transmit_can_sync(AHandle, byref(Msg), ATimeoutMS)
    if r != 0:
        print("msg send failed")
    return r


# 异步发  canfd报文
def tsapp_transmit_canfd_async(AHandle: c_size_t, Msg: TLIBCANFD):
    """
    async send canfd msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBCANFD): canfd msg
    example:    
        msg = TLIBCANFD(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tsapp_transmit_canfd_async(handle,msg)
    Returns:
        error code
    """
    r = dll.tscan_transmit_canfd_async(AHandle, byref(Msg))
    if r != 0:
        print("msg send failed")
    return r


# 同步发  canfd报文
def tsapp_transmit_canfd_sync(AHandle: c_size_t, Msg: TLIBCANFD, ATimeoutMS: c_uint32):
    """
    sync send canfd msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBCANFD): canfd msg
        ATimeoutMS (c_int32): timeout in ms
    example:    
        msg = TLIBCANFD(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tsapp_transmit_canfd_sync(handle,msg,100)
    Returns:
        error code
    """
    if not isinstance(ATimeoutMS, c_uint32):
        ATimeoutMS = c_uint32(ATimeoutMS)
    r = dll.tscan_transmit_canfd_sync(AHandle, byref(Msg), ATimeoutMS)
    if r != 0:
        print("msg send failed")
    return r

# 周期发  canfd报文
def tscan_add_cyclic_msg_can(AHandle: c_size_t, Msg: TLIBCAN, ATimeoutMS: c_float):
    """
    cyclic send can msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBCAN): can msg
        ATimeoutMS (c_int32): timeout in ms
    example:    
        msg = TLIBCAN(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tscan_add_cyclic_msg_can(handle,msg,c_float(100))
    Returns:
        error code
    """
    if not isinstance(ATimeoutMS, c_float):
        ATimeoutMS = c_float(ATimeoutMS)
    r = dll.tscan_add_cyclic_msg_can(AHandle, byref(Msg), ATimeoutMS)
    if r != 0:
        print("msg send failed")
    return r
# 循环发  canfd报文
def tscan_add_cyclic_msg_canfd(AHandle: c_size_t, Msg: TLIBCANFD, ATimeoutMS: c_float):
    """
    cyclic send canfd msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBCANFD): canfd msg
        ATimeoutMS (c_int32): timeout in ms
    example:    
        msg = TLIBCANFD(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tscan_add_cyclic_msg_canfd(handle,msg,c_float(100))
    Returns:
        error code
    """
    if not isinstance(ATimeoutMS, c_float):
        ATimeoutMS = c_float(ATimeoutMS)
    r = dll.tscan_add_cyclic_msg_canfd(AHandle, byref(Msg), ATimeoutMS)
    return r


# 删除循环发  canfd报文
def tscan_delete_cyclic_msg_canfd(AHandle: c_size_t, Msg: TLIBCANFD):
    """
    delete cyclic send canfd msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBCANFD): canfd msg
    example:    
        msg = TLIBCANFD(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tscan_delete_cyclic_msg_canfd(handle,msg)
    Returns:
        error code
    """
    r = dll.tscan_delete_cyclic_msg_canfd(AHandle, byref(Msg))
    return r


# 删除循环发  can报文
def tscan_delete_cyclic_msg_can(AHandle: c_size_t, Msg: TLIBCAN):
    """
    delete cyclic send can msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBCAN): can msg
    example:    
        msg = TLIBCAN(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tscan_delete_cyclic_msg_can(handle,msg)
    Returns:
        error code
    """
    r = dll.tscan_delete_cyclic_msg_can(AHandle, byref(Msg))
    return r


# 异步发  lin报文
def tsapp_transmit_lin_async(AHandle: c_size_t, Msg: TLIBLIN):
    """
    async send lin msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBLIN): lin msg
    Returns:
        error code
    example:
        msg = TLIBLIN(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tsapp_transmit_lin_async(handle,msg)
    """
    r = dll.tslin_transmit_lin_async(AHandle, byref(Msg))
    if r != 0:
        print("msg send failed")
    return r


# 同步发  lin报文
def tsapp_transmit_lin_sync(AHandle: c_size_t, Msg: TLIBLIN, ATimeoutMS: c_int32):
    """
    sync send lin msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        Msg (TLIBLIN): lin msg
        ATimeoutMS (c_int32): timeout in ms

    Returns:
        error code
    example:
        msg = TLIBLIN(FIdentifier = 1,FData=[1,2,3,4,5,6,7,8])
        tsapp_transmit_lin_sync(handle,msg,100)
    """
    r = dll.tslin_transmit_lin_sync(AHandle, byref(Msg), ATimeoutMS)
    return r


# can报文接收
def tsapp_receive_can_msgs(AHandle: c_size_t, ACANBuffers: TLIBCAN, ACANBufferSize: c_uint32, AChn: CHANNEL_INDEX,
                           ARxTx: READ_TX_RX_DEF):
    """
    receive can msgs

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ADataBuffers (TLIBCAN): can buffer 
        ADataBufferSize (c_int32): can buffer size
        chn (c_int32): can channel
        ARxTx (c_int8): include tx
    Returns:
        error_code TLIBCAN_buffer TLIBCAN_bufferSize
    example:    
        canbuffer = (TLIBCAN * 100)()
        size = c_int32(100)
        tsapp_receive_can_msgs(handle, canbuffer, size, 0, 1)
        for i in canbuffer:
            string = ''
            for index in range(i.FActualPayloadLength):
                string += hex(i.FData[index]) + ' '
    """
    r = dll.tsfifo_receive_can_msgs(
        AHandle, ACANBuffers, byref(ACANBufferSize), AChn, ARxTx)
    return r


# canfd报文接收
def tsapp_receive_canfd_msgs(AHandle: c_size_t, ACANFDBuffers: TLIBCANFD, ACANFDBufferSize: c_uint32,
                             AChn: CHANNEL_INDEX,
                             ARxTx: READ_TX_RX_DEF):
    """
    receive canfd msgs

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ADataBuffers (TLIBCANFD): can buffer 
        ADataBufferSize (c_int32): can buffer size
        chn (c_int32): can channel
        ARxTx (c_int8): include tx
    Returns:
        error_code TLIBCANFD_buffer TLIBCANFD_bufferSize
    example:    
        canbuffer = (TLIBCANFD * 100)()
        size = c_int32(100)
        tsapp_receive_canfd_msgs(handle, canbuffer, size, 0, 1)
        for i in canbuffer:
            string = ''
            for index in range(i.FActualPayloadLength):
                string += hex(i.FData[index]) + ' '
    """
    r = dll.tsfifo_receive_canfd_msgs(
        AHandle, ACANFDBuffers, byref(ACANFDBufferSize), AChn, ARxTx)

    return r


# lin报文接收
def tsapp_receive_lin_msgs(AHandle: c_size_t, ALINBuffers: TLIBLIN, ALINBufferSize: c_uint, AChn: CHANNEL_INDEX,
                           ARxTx: READ_TX_RX_DEF):
    """
    receive lin msgs

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ADataBuffers (TLIBLIN): can buffer 
        ADataBufferSize (c_int32): can buffer size
        chn (c_int32): can channel
        ARxTx (c_int8): include tx
    Returns:
        error_code TLIBLIN_buffer TLIBLIN_bufferSize
    example:    
        linbuffer = (TLIBLIN * 100)()
        size = c_int32(100)
        tsapp_receive_lin_msgs(handle, linbuffer, size, 0, 1)
        for i in linbuffer:
            string = ''
            for index in range(i.FActualPayloadLength):
                string += hex(i.FData[index]) + ' '
            
    """
    temp = copy.copy(ALINBufferSize)
    data = POINTER(TLIBLIN * len(ALINBuffers)
                   )((TLIBLIN * len(ALINBuffers))(*ALINBuffers))
    r = dll.tsfifo_receive_lin_msgs(AHandle, data, byref(temp), AChn, ARxTx)
    for i in range(len(data.contents)):
        ALINBuffers[i] = data.contents[i]
    return r


# 清除buffer
def tsfifo_clear_can_receive_buffers(AHandle: c_size_t, CHN: CHANNEL_INDEX):
    """
    clear can receive buffers
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        CHN (CHANNEL_INDEX): can channel idnex

    Returns:
        error code
        
    example:
        tsfifo_clear_can_receive_buffers(handle,CHANNEL_INDEX.CHN1)
    """
    return dll.tsfifo_clear_can_receive_buffers(AHandle, CHN)


def tsfifo_clear_canfd_receive_buffers(AHandle: c_size_t, CHN: CHANNEL_INDEX):
    """
    clear canfd receive buffers
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        CHN (CHANNEL_INDEX): canfd channel idnex

    Returns:
        error code
        
    example:
        tsfifo_clear_canfd_receive_buffers(handle,CHANNEL_INDEX.CHN1)
    """
    return dll.tsfifo_clear_canfd_receive_buffers(AHandle, CHN)


def tsfifo_clear_lin_receive_buffers(AHandle: c_size_t, CHN: CHANNEL_INDEX):
    """
    clear lin receive buffers
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        CHN (CHANNEL_INDEX): canfd channel idnex

    Returns:
        error code
        
    example:
        tsfifo_clear_lin_receive_buffers(handle,CHANNEL_INDEX.CHN1)
    """
    return dll.tsfifo_clear_lin_receive_buffers(AHandle, CHN)


# 回调事件
PCAN = POINTER(TLIBCAN)
if 'windows' in _os.lower():
    OnTx_RxFUNC_CAN = WINFUNCTYPE(None, PCAN)
else:
    OnTx_RxFUNC_CAN = CFUNCTYPE(None, PCAN)

PFlexray = POINTER(TLIBFlexray)
if 'windows' in _os.lower():
    OnTx_RxFUNC_Flexray = WINFUNCTYPE(None, PFlexray)
else:
    OnTx_RxFUNC_Flexray = CFUNCTYPE(None, PFlexray)

PLIN = POINTER(TLIBLIN)
if 'windows' in _os.lower():
    OnTx_RxFUNC_LIN = WINFUNCTYPE(None, PLIN)
else:
    OnTx_RxFUNC_LIN = CFUNCTYPE(None, PLIN)

PCANFD = POINTER(TLIBCANFD)
if 'windows' in _os.lower():
    OnTx_RxFUNC_CANFD = WINFUNCTYPE(None, PCANFD)
else:
    OnTx_RxFUNC_CANFD = CFUNCTYPE(None, PCANFD)

ps64 = POINTER(c_int64)
if 'windows' in _os.lower():
    On_Connect_FUNC = WINFUNCTYPE(None,ps64 )
else:
    On_Connect_FUNC = CFUNCTYPE(None, ps64)

if 'windows' in _os.lower():
    On_disConnect_FUNC = WINFUNCTYPE(None, ps64)
else:
    On_disConnect_FUNC = CFUNCTYPE(None, ps64)

blfName = ''
blf_start_time = 0


def blfFile(pathName):
    global blf_start_time
    blf_start_time += time.time()
    blfName = can.BLFWriter(file=pathName, append=False)
    blfName.start_timestamp = blf_start_time
    return blfName


def On_CANFD_EVENT(ACAN):
    global blf_start_time
    msg = tosun_convert_msg(ACAN.contents)
    blfName(msg)


On_LOG_EVENT = OnTx_RxFUNC_CANFD(On_CANFD_EVENT)


def tslog_start(AHandle: c_size_t, filePathName: str):
    """
    logging can msg include canfd msg

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        filePathName (str): save log_file path_name (blf file) Absolute path
    
    example:
        tslog_start(handle,Absolute path)
    """
    global blfName
    blfName = blfFile(filePathName)
    if 0 == tsapp_register_event_canfd(AHandle, On_LOG_EVENT):
        print("start logging")
    else:
        print('start logging failed')


def tslog_stop():
    """
    stop logging
    """
    global blfName
    global blf_start_time
    blfName.stop_timestamp = time.time()
    blfName.stop()
    print("stop logging")
    blf_start_time = 0


def blf_to_convert(oldpathName: str, newpathName: str,
                   convertType: CONVERTTYPE):  # oldpathName:blf location, newpathName: asc location
    """_summary_

    Args:
        oldpathName (str): old log file
        newpathName (str): new log file 
        convertType (CONVERTTYPE): convert type
    
    example:
        blf_to_convert("1.blf","2.asc".CONVERTTYPE.ASC)
    """
    if convertType == CONVERTTYPE.ASC:
        with can.BLFReader(oldpathName) as Reader_file:
            with can.ASCWriter(newpathName) as WriterFile:
                for msg in Reader_file:
                    WriterFile(msg)
                WriterFile.stop()
    elif convertType == CONVERTTYPE.CSV:
        with can.BLFReader(oldpathName) as Reader_file:
            with can.CSVWriter(newpathName) as WriterFile:
                for msg in Reader_file:
                    WriterFile(msg)
                WriterFile.stop()
    elif convertType == CONVERTTYPE.LOG:
        with can.BLFReader(oldpathName) as Reader_file:
            with can.CanutilsLogWriter(newpathName) as WriterFile:
                for msg in Reader_file:
                    WriterFile(msg)
                WriterFile.stop()
    elif convertType == CONVERTTYPE.TXT:
        with can.BLFReader(oldpathName) as Reader_file:
            with can.Printer(newpathName) as WriterFile:
                for msg in Reader_file:
                    WriterFile(msg)
                WriterFile.stop()
    elif convertType == CONVERTTYPE.SQL:
        with can.BLFReader(oldpathName) as Reader_file:
            with can.SqliteWriter(newpathName) as WriterFile:
                for msg in Reader_file:
                    WriterFile(msg)
                WriterFile.stop()
    else:
        print("incorrect format")


def tslog_start_online_replay(handle: c_size_t, PathFileName: str, include_rx: bool):
    """
    online repaly

    Args:
        handle (c_size_t): tsapp_connect retrun handle
        PathFileName (str): blf path name Absolute path
        include_rx (bool): include rx
    exampel:
        tslog_start_online_replay(handle,"/home/1.blf",False)
    """
    messagelist = []
    with can.BLFReader(PathFileName) as Reader_file:
        Reader_file.start_timestamp = 0
        for msg in Reader_file:
            for i in range(len(DLC_DATA_BYTE_CNT)):
                if msg.dlc == DLC_DATA_BYTE_CNT[i]:
                    msg.dlc = i
            if include_rx:
                messagelist.append(msg)
            else:
                if msg.is_rx:
                    continue
                messagelist.append(msg)
        listlen = len(messagelist)
        print(listlen)
        for i in range(listlen):
            if messagelist[i].is_fd:
                TCANFD = TLIBCANFD(FIdxChn=messagelist[i].channel, FIdentifier=messagelist[i].arbitration_id,
                                   FFDProperties=1, FDLC=messagelist[i].dlc,
                                   FData=messagelist[i].data)
                # TCANFD.FTimeUs = msg.timestamp
                tsapp_transmit_canfd_async(handle, TCANFD)
                if i == listlen - 1:
                    break
                time.sleep(messagelist[i + 1].timestamp -
                           messagelist[i].timestamp)
            else:
                TCAN = TLIBCAN(FIdxChn=messagelist[i].channel, FIdentifier=messagelist[i].arbitration_id,
                               FDLC=messagelist[i].dlc,
                               FData=messagelist[i].data)
                # TCAN.FTimeUs = msg.timestamp
                tsapp_transmit_can_async(handle, TCAN)
                if i == listlen - 1:
                    break
                time.sleep(messagelist[i + 1].timestamp -
                           messagelist[i].timestamp)


def Reader_file(PathName, convertType: CONVERTTYPE):
    if convertType == CONVERTTYPE.ASC:
        with can.BLFReader(PathName) as Reader_file:
            Reader_file.start_timestamp = 0
            for msg in Reader_file:
                print(msg)
    elif convertType == CONVERTTYPE.CSV:
        with can.CSVReader(PathName) as Reader_file:
            Reader_file.start_timestamp = 0
            for msg in Reader_file:
                print(msg)
    elif convertType == CONVERTTYPE.LOG:
        with can.CanutilsLogReader(PathName) as Reader_file:
            Reader_file.start_timestamp = 0
            for msg in Reader_file:
                print(msg)
    elif convertType == CONVERTTYPE.TXT:
        with can.CSVReader(PathName) as Reader_file:
            Reader_file.start_timestamp = 0
            for msg in Reader_file:
                print(msg)
    elif convertType == CONVERTTYPE.SQL:
        with can.SqliteReader(PathName) as Reader_file:
            Reader_file.start_timestamp = 0
            for msg in Reader_file:
                print(msg)
    elif convertType == CONVERTTYPE.BLF:
        with can.BLFReader(PathName) as Reader_file:
            Reader_file.start_timestamp = 0
            for msg in Reader_file:
                print(msg)
    else:
        print("incorrect format")


# 注册连接事件
def tscan_register_event_connected(ACallback: On_Connect_FUNC):
    """
    register connect event
    What happens when the device is successfully connected
    
    Args:
        ACallback (On_Connect_FUNC): function

    Returns:
        error code
    example:
        def on_connect(ps64):
            print("connect")
            
        on_connect_event = On_Connect_FUNC(on_connect)
        tscan_register_event_connected(on_connect_event)
    """
    ret = dll.tscan_register_event_connected(ACallback)
    return ret


# 注册断开事件
def tscan_register_event_disconnected(ACallback: On_disConnect_FUNC):
    """
    register disconnect event
    What happens when the device is successfully disconnected
    Args:
        ACallback (On_disConnect_FUNC): function

    Returns:
        error code
    example:
        def on_disconnect(ps64):
            print("disconnect")
            
        on_disconnect_event = On_disConnect_FUNC(on_disconnect)
        tscan_register_event_disconnected(on_disconnect_event)
    """
    ret = dll.tscan_register_event_disconnected(ACallback)
    return ret


# 注册can发接
def tsapp_register_event_can(AHandle: c_size_t, ACallback: OnTx_RxFUNC_CAN):
    """
    register can event
    Triggered when there is message transmission on the bus
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_CAN): function

    Returns:
        error code
    example:
        def on_can(ACAN):
            print(ACAN.contents.FData[0])
            
        on_can_event = OnTx_RxFUNC_CAN(on_can)
        tsapp_register_event_can(Handle,on_can_event)
    """
    r = dll.tscan_register_event_can(AHandle, ACallback)
    return r


# 注销can发接
def tsapp_unregister_event_can(AHandle: c_size_t, ACallback: OnTx_RxFUNC_CAN):
    """
    unregister can event
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_CAN): function

    Returns:
        error code
    example:
        def on_can(ACAN):
            print(ACAN.contents.FData[0])
            
        on_can_event = OnTx_RxFUNC_CAN(on_can)
        tsapp_unregister_event_can(Handle,on_can_event)
    """
    r = dll.tscan_unregister_event_can(AHandle, ACallback)
    return r

def tsapp_register_pretx_event_can(AHandle: c_size_t, ACallback: OnTx_RxFUNC_CAN):
    """
    register pre tx can event
    Sending a message will trigger and can modify the message data
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_CAN): function

    Returns:
        error code
    example:
        def on_can(ACAN):
            ACAN.contents.FData[0] = 1 #All message FData[0] will only be 1
            if ACAN.contents.FIdentifier == 1:
                ACAN.contents.FData[0] = 2  #only id=1 can message FData[0] will  be 2
            
        on_can_event = OnTx_RxFUNC_CAN(on_can)
        tsapp_register_event_can(Handle,on_can_event)
    """
    return dll.tscan_register_pretx_event_can(AHandle, ACallback)

def tsapp_unregister_pretx_event_can(AHandle: c_size_t, ACallback: OnTx_RxFUNC_CAN):
    """
    unregister pre tx can event
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_CAN): function

    Returns:
        error code
    example:
        def on_can(ACAN):
            ACAN.contents.FData[0] = 1 #All message FData[0] will only be 1
            if ACAN.contents.FIdentifier == 1:
                ACAN.contents.FData[0] = 2  #only id=1 can message FData[0] will  be 2
            
        on_can_event = OnTx_RxFUNC_CAN(on_can)
        tsapp_unregister_event_can(Handle,on_can_event)
    """
    return dll.tscan_unregister_pretx_event_can(AHandle, ACallback)

def tsapp_register_pretx_event_canfd(AHandle: c_size_t, ACallback: OnTx_RxFUNC_CANFD):
    """
    register pre tx canfd event
    Sending a message will trigger and can modify the message data
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_CANFD): function

    Returns:
        error code
    example:
        def on_can(ACAN):
            ACAN.contents.FData[0] = 1 #All message FData[0] will only be 1
            if ACAN.contents.FIdentifier == 1:
                ACAN.contents.FData[0] = 2  #only id=1 can message FData[0] will  be 2
            
        on_can_event = OnTx_RxFUNC_CANFD(on_can)
        tsapp_register_pretx_event_canfd(Handle,on_can_event)
    """
    return dll.tscan_register_pretx_event_canfd(AHandle, ACallback)

def tsapp_unregister_pretx_event_canfd(AHandle: c_size_t, ACallback: OnTx_RxFUNC_CANFD):
    """
    unregister pre tx canfd event

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_CANFD): function

    Returns:
        error code
    example:
        def on_can(ACAN):
            ACAN.contents.FData[0] = 1 #All message FData[0] will only be 1
            if ACAN.contents.FIdentifier == 1:
                ACAN.contents.FData[0] = 2  #only id=1 can message FData[0] will  be 2
            
        on_can_event = OnTx_RxFUNC_CANFD(on_can)
        tsapp_unregister_pretx_event_canfd(Handle,on_can_event)
    """
    return dll.tscan_unregister_pretx_event_canfd(AHandle, ACallback)


# 注册canfd发接
def tsapp_register_event_canfd(AHandle: c_size_t, ACallback: OnTx_RxFUNC_CANFD):
    """
    register canfd event
    Triggered when there is message transmission on the bus
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_CANFD): function

    Returns:
        error code
    example:
        def on_can(ACAN):
            print(ACAN.contents.FData[0])
            
        on_can_event = OnTx_RxFUNC_CANFD(on_can)
        tsapp_register_event_canfd(Handle,on_can_event)
    """
    r = dll.tscan_register_event_canfd(AHandle, ACallback)
    return r

# 注销canfd发接
def tsapp_unregister_event_canfd(AHandle: c_size_t, ACallback: OnTx_RxFUNC_CANFD):
    """
    unregister canfd event
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_CANFD): function

    Returns:
        error code
    example:
        def on_can(ACAN):
            print(ACAN.contents.FData[0])
            
        on_can_event = OnTx_RxFUNC_CANFD(on_can)
        tsapp_unregister_event_canfd(Handle,on_can_event)
    """
    r = dll.tscan_unregister_event_canfd(AHandle, ACallback)
    return r

def tsapp_register_event_flexray(AHandle: c_size_t, ACallback: OnTx_RxFUNC_Flexray):
    """
    register flexray event
    Triggered when there is message transmission on the bus
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_Flexray): function

    Returns:
        error code
    example:
        def on_flexray(AFlexray):
            print(AFlexray.contents.FData[0])
            
        on_flexray_event = OnTx_RxFUNC_Flexray(on_flexray)
        tsapp_register_event_flexray(Handle,on_flexray_event)
    """
    r = dll.tsflexray_register_event_flexray(AHandle, ACallback)
    return r


# 注销flexray发接
def tsapp_unregister_event_flexray(AHandle: c_size_t, ACallback: OnTx_RxFUNC_Flexray):
    """
    unregister flexray event

    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_Flexray): function

    Returns:
        error code
    example:
        def on_flexray(AFlexray):
            print(AFlexray.contents.FData[0])
            
        on_flexray_event = OnTx_RxFUNC_Flexray(on_flexray)
        tsapp_unregister_event_flexray(Handle,on_flexray_event)
    """
    r = dll.tsflexray_unregister_event_flexray(AHandle, ACallback)
    return r

def tsapp_register_pretx_event_flexray(AHandle: c_size_t, ACallback: OnTx_RxFUNC_Flexray):
    """
    register pre tx flexray event
    Sending a message will trigger and can modify the message data(use transmit_flexray trigger)
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_Flexray): function

    Returns:
        error code
    example:
        def on_flexray(AFlexray):
            AFlexray.contents.FData[0] = 1 #All transmit tx message FData[0] will only be 1
            if AFlexray.contents.FIdentifier == 1:
                AFlexray.contents.FData[0] = 2  #only id=1 can message FData[0] will  be 2
            
        on_flexray_event = OnTx_RxFUNC_Flexray(on_flexray)
        tsapp_register_pretx_event_flexray(Handle,on_flexray_event)
    """
    r = dll.tsflexray_register_pretx_event_flexray(AHandle, ACallback)
    return r


# 注销flexray预发送事件
def tsapp_unregister_pretx_event_flexray(AHandle: c_size_t, ACallback: OnTx_RxFUNC_Flexray):
    """
    unregister pre tx flexray event
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_Flexray): function

    Returns:
        error code
    example:
        def on_flexray(AFlexray):
            AFlexray.contents.FData[0] = 1 #All transmit tx message FData[0] will only be 1
            if AFlexray.contents.FIdentifier == 1:
                AFlexray.contents.FData[0] = 2  #only id=1 can message FData[0] will  be 2
            
        on_flexray_event = OnTx_RxFUNC_Flexray(on_flexray)
        tsapp_unregister_pretx_event_flexray(Handle,on_flexray_event)
    """
    r = dll.tsflexray_unregister_pretx_event_flexray(AHandle, ACallback)
    return r


# 注册lin发 接事件
def tsapp_register_event_lin(AHandle: c_size_t, ACallback: OnTx_RxFUNC_LIN):
    """
    register lin event
    Triggered when there is message transmission on the bus
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_LIN): function

    Returns:
        error code
    example:
        def on_lin(ALIN):
            print(ALIN.contents.FData[0])
            
        on_lin_event = OnTx_RxFUNC_LIN(on_lin)
        tsapp_register_event_lin(Handle,on_flexray_event)
    """
    r = dll.tslin_register_event_lin(AHandle, ACallback)
    return r


# 注销lin发 接事件
def tsapp_unregister_event_lin(AHandle: c_size_t, ACallback: OnTx_RxFUNC_LIN):
    """
    unregister lin event
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_LIN): function

    Returns:
        error code
    example:
        def on_lin(ALIN):
            print(ALIN.contents.FData[0])
            
        on_lin_event = OnTx_RxFUNC_LIN(on_lin)
        tsapp_unregister_event_lin(Handle,on_flexray_event)
    """
    r = dll.tslin_unregister_event_lin(AHandle, ACallback)
    return r

def tsapp_register_pretx_event_lin(AHandle: c_size_t, ACallback: OnTx_RxFUNC_LIN):
    """
    register pre tx lin event
    Sending a message will trigger and can modify the message data(use transmit_flexray trigger)
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_LIN): function

    Returns:
        error code
    example:
        def on_lin(ALIN):
            ALIN.contents.FData[0] = 1 #All transmit tx message FData[0] will only be 1
            if ALIN.contents.FIdentifier == 1:
                ALIN.contents.FData[0] = 2  #only id=1 can message FData[0] will  be 2
            
        on_lin_event = OnTx_RxFUNC_LIN(on_lin)
        tsapp_register_pretx_event_lin(Handle,on_flexray_event)
    """
    return dll.tslin_register_pretx_event_can(AHandle, ACallback)

def tsapp_unregister_pretx_event_lin(AHandle: c_size_t, ACallback: OnTx_RxFUNC_LIN):
    """
    unregister pre tx lin event
    Sending a message will trigger and can modify the message data(use transmit_flexray trigger)
    
    Args:
        AHandle (c_size_t): tsapp_connect retrun handle
        ACallback (OnTx_RxFUNC_LIN): function

    Returns:
        error code
    example:
        def on_lin(ALIN):
            ALIN.contents.FData[0] = 1 #All transmit tx message FData[0] will only be 1
            if ALIN.contents.FIdentifier == 1:
                ALIN.contents.FData[0] = 2  #only id=1 can message FData[0] will  be 2
            
        on_lin_event = OnTx_RxFUNC_LIN(on_lin)
        tsapp_register_pretx_event_lin(Handle,on_flexray_event)
        
    """
    return dll.tslin_unregister_pretx_event_lin(AHandle, ACallback)

if 'windows' in _os.lower():
    def tsdiag_can_create(HwHandle,pDiagModuleIndex: c_int32, AChnIndex: CHANNEL_INDEX, ASupportFDCAN: c_byte,AMaxDLC: c_byte,ARequestID: c_uint32, ARequestIDIsStd: bool, AResponseID: c_uint32, AResponseIDIsStd: bool,AFunctionID: c_uint32, AFunctionIDIsStd: bool):
        """
        udsHandle = c_int8(0)
        ChnIndex = CHANNEL_INDEX.CHN1
        ASupportFD  = c_byte(1)
        AMaxdlc = c_byte(8)
        reqID = c_int32(0x7e0)
        ARequestIDIsStd = False
        resID = c_int32(0x7e3)
        resIsStd = False
        AFctID = c_int32(0x7df)
        fctIsStd = False
        tsdiag_can_create(HWHandle,udsHandle,ChnIndex,ASupportFD,AMaxdlc,reqID,resIsStd,resID,resIsStd,AFctID,fctIsStd)
        """
        try:
            dlc = DLC_DATA_BYTE_CNT.index(AMaxDLC)
        except:
            dlc = AMaxDLC
        r = dll.tsdiag_can_create(byref(pDiagModuleIndex), AChnIndex, ASupportFDCAN, dlc, ARequestID,
                                    ARequestIDIsStd,
                                    AResponseID, AResponseIDIsStd, AFunctionID, AFunctionIDIsStd)
        dll.tsdiag_can_attach_to_tscan_tool(pDiagModuleIndex, HwHandle)
        return r

    def tsdiag_can_delete(pDiagModuleIndex: c_int32):
        """
        udsHandle = c_int8(0)
        ChnIndex = CHANNEL_INDEX.CHN1
        ASupportFD  = c_byte(1)
        AMaxdlc = c_byte(8)
        reqID = c_int32(0x7e0)
        ARequestIDIsStd = False
        resID = c_int32(0x7e3)
        resIsStd = False
        AFctID = c_int32(0x7df)
        fctIsStd = False
        tsdiag_can_create(HWHandle,udsHandle,ChnIndex,ASupportFD,AMaxdlc,reqID,resIsStd,resID,resIsStd,AFctID,fctIsStd)
        tsdiag_can_delete(udsHandle)
        """
        return dll.tsdiag_can_delete(pDiagModuleIndex)

    def tsdiag_can_delete_all():

        return dll.tsdiag_can_delete_all()

    def tsdiag_can_session_control(pDiagModuleIndex: c_int32,ASubSession:c_uint8):
        """
        10服务
        """
        return dll.tsdiag_can_session_control(pDiagModuleIndex,ASubSession)

    def tsdiag_can_routine_control(pDiagModuleIndex: c_int32,AARoutineControlType:c_uint8,ARoutintID:c_uint16):
        """
        31服务

        tsdiag_can_session_control(udsHandle,c_uint8(1),c_uint16(0xf100)) 

        """
        return dll.tsdiag_can_routine_control(pDiagModuleIndex,AARoutineControlType,ARoutintID)

    def tsdiag_can_security_access_request_seed(pDiagModuleIndex: c_int32,ALevel:c_int32,ASeed:c_char_p,ASeedSize:c_int32):
        """27 01 request seed"""
        return dll.tsdiag_can_security_access_request_seed(pDiagModuleIndex,ALevel,ASeed,byref(ASeedSize))

    def tsdiag_can_security_access_send_key(pDiagModuleIndex: c_int32,ALevel:c_int32,ASeed:c_char_p,ASeedSize:c_int32):
        """27 02 send key"""
        return dll.tsdiag_can_security_access_send_key(pDiagModuleIndex,ALevel,ASeed,ASeedSize)

    def tsdiag_can_request_download(pDiagModuleIndex: c_int32,AMemAddr:c_uint32,AMemSize:c_uint32):
        """34 服务"""
        return dll.tsdiag_can_request_download(pDiagModuleIndex,AMemAddr,AMemSize)

    def tsdiag_can_request_upload(pDiagModuleIndex: c_int32,AMemAddr:c_uint32,AMemSize:c_uint32):
        """35 服务"""
        return dll.tsdiag_can_request_upload(pDiagModuleIndex,AMemAddr,AMemSize)

    def tsdiag_can_transfer_data(pDiagModuleIndex: c_int32,ASourceDatas:c_char_p,ASize:c_int32,AReqCase:c_int32):
        """36 服务"""
        return dll.tsdiag_can_transfer_data(pDiagModuleIndex,ASourceDatas,ASize,AReqCase)

    def tsdiag_can_request_transfer_exit(pDiagModuleIndex:c_int32):
        """37 服务"""
        return dll.tsdiag_can_request_transfer_exit(pDiagModuleIndex)

    def tsdiag_can_write_data_by_identifier(pDiagModuleIndex: c_int32,ADataIdentifier:c_uint16,AWriteData:c_char_p,AWriteDataSize:c_int32):
        """2e 服务"""
        return dll.tsdiag_can_write_data_by_identifier(pDiagModuleIndex,ADataIdentifier,AWriteData,AWriteDataSize)

    def tsdiag_can_read_data_by_identifier(pDiagModuleIndex: c_int32,ADataIdentifier:c_uint16,AReturnArray:c_char_p,AReturnArraySize:c_int32):
        """22 服务"""
        return dll.tsdiag_can_read_data_by_identifier(pDiagModuleIndex,ADataIdentifier,AReturnArray,byref(AReturnArraySize))


class TSuds():
    msg_list = queue.Queue(maxsize=10000)
    def __init__(self, HwHandle, channel=0, dlc=8, request_id=0x1, respond_id=0x2, is_fd=False, is_std=True,
                 fuction_id=0x3, timeout=0.1, bitrate_switch=False):
        self.HwHandle = HwHandle
        self.channel = channel
        try:
            self.dlc = DLC_DATA_BYTE_CNT.index(dlc)
        except:
            if dlc < 0x10:
                self.dlc = dlc
        self.is_fd = is_fd
        if not self.is_fd and self.dlc > 8:
            self.dlc = 8
        self.is_std = is_std
        self.bitrate_switch = bitrate_switch
        self.FFDProperties = 0x00 | (0x01 if self.is_fd else 0x00) | (
            0x02 if self.bitrate_switch else 0x00)
        self.FProperties = 0x01 | (0x04 if not self.is_std else 0x01)
        self.request_id = request_id
        self.respond_id = respond_id
        self.fuction_id = fuction_id
        self.timeout = timeout
        self.msg_data_size = DLC_DATA_BYTE_CNT[self.dlc]
        self.CANFDMsg = TLIBCANFD(FIdxChn=self.channel, FDLC=self.dlc, FIdentifier=self.request_id,
                                  FFDProperties=self.FFDProperties, FProperties=self.FProperties,
                                  FData=[0X30, 0X00, 0X00, 0X00, 0X00, 0X00, 0X00, 0X00])
        self.ONRxTx_Event = OnTx_RxFUNC_CANFD(self.on_tx_rx_event)
        tsapp_register_event_canfd(self.HwHandle, self.ONRxTx_Event)

    def on_tx_rx_event(self, ACAN):
        if ACAN.contents.FIdentifier == self.respond_id and ACAN.contents.FIdxChn == self.channel:
            msgdata = []
            for i in range(DLC_DATA_BYTE_CNT[ACAN.contents.FDLC]):
                msgdata.append(ACAN.contents.FData[i])
            self.msg_list.put(msgdata)

    def receive_can_Response(self):
        Datalist = []
        StartTime = time.perf_counter()
        FristDataLength = self.msg_data_size - 2
        DataLength = self.msg_data_size - 1
        while time.perf_counter() - StartTime < self.timeout:
            time.sleep(0.001)
            if not self.msg_list.empty():
                msgs = self.msg_list.get()
                N_PCItype = msgs[0] >> 4
                if 0 == N_PCItype:
                    if len(msgs) <= 8:
                        ResSize = (msgs[0] & 0xf)
                        if msgs[1] == 0x7f and msgs[3] == 0x78:
                            StartTime = time.perf_counter()
                            continue
                        for i in range(ResSize):
                            Datalist.append(msgs[i + 1])
                        return 0, Datalist
                    else:
                        ResSize = (msgs[1] & 0xff)
                        if msgs[2] == 0x7f and msgs[4] == 0x78:
                            StartTime = time.perf_counter()
                            continue
                        for i in range(ResSize):
                            Datalist.append(msgs[i + 2])
                        return 0, Datalist
                elif 1 == N_PCItype:
                    ResSize = (msgs[0] & 0xf) * 256 + msgs[1]
                    for i in range(len(msgs) - 2):
                        Datalist.append(msgs[i + 2])
                    if 0 == tsapp_transmit_canfd_async(self.HwHandle, self.CANFDMsg):
                        snCnt = 0x1
                        rxIndex = len(msgs) - 2
                        while rxIndex < ResSize and time.perf_counter() - StartTime < self.timeout:
                            if len(Datalist) == ResSize:
                                return 0, Datalist
                            elif not self.msg_list.empty():
                                msgs = self.msg_list.get()
                                N_PCItype = msgs[0] >> 4
                                if N_PCItype != 2:
                                    break
                                rxSN = msgs[0] & 0xf
                                if rxSN != snCnt & 0xf:
                                    break
                                snCnt += 1
                                if len(Datalist) != ResSize:
                                    if len(msgs) - 1 < ResSize - len(Datalist):
                                        for i in range(len(msgs) - 1):
                                            Datalist.append(msgs[i + 1])
                                        StartTime = time.perf_counter()
                                    else:
                                        for i in range(ResSize - len(Datalist)):
                                            Datalist.append(msgs[i + 1])
                                        StartTime = time.perf_counter()
                                    if len(Datalist) == ResSize:
                                        return 0, Datalist
                                else:
                                    return 0, Datalist
        return 161, Datalist

    def tstp_can_send_request(self, SendDatas):
        CANMsg = TLIBCANFD(FIdxChn=self.channel, FDLC=self.dlc, FIdentifier=self.request_id,
                           FFDProperties=self.FFDProperties, FProperties=self.FProperties,
                           )
        txIndex = self.msg_data_size - 2
        Datalengh = self.msg_data_size - 1
        MsgLen = len(SendDatas)
        if MsgLen <= Datalengh:
            if self.msg_data_size == self.dlc:
                CANMsg.FData[0] = MsgLen
                for i in range(MsgLen):
                    CANMsg.FData[i + 1] = SendDatas[i]
                return tsapp_transmit_canfd_async(self.HwHandle, CANMsg)
            else:
                if MsgLen <= Datalengh - 1:
                    for i in range(8, self.dlc):
                        if MsgLen < DLC_DATA_BYTE_CNT[i]:
                            CANMsg.FDLC = i
                            break
                    if CANMsg.FDLC == 8:
                        CANMsg.FData[0] = MsgLen
                        for i in range(MsgLen):
                            CANMsg.FData[i + 1] = SendDatas[i]
                        return tsapp_transmit_canfd_async(self.HwHandle, CANMsg)
                    else:
                        CANMsg.FData[0] = 0x00
                        CANMsg.FData[1] = MsgLen
                        for i in range(MsgLen):
                            CANMsg.FData[i + 2] = SendDatas[i]
                        return tsapp_transmit_canfd_async(self.HwHandle, CANMsg)
        CANMsg.FDLC = self.dlc
        CANMsg.FData[0] = 0x10 + (MsgLen >> 8 & 0xf)
        CANMsg.FData[1] = MsgLen & 0xff
        for i in range(txIndex):
            CANMsg.FData[i + 2] = SendDatas[i]
        if 0 == tsapp_transmit_canfd_async(self.HwHandle, CANMsg):
            Datalist = []
            snCnt = 1
            StartTime = time.perf_counter()
            while time.perf_counter() - StartTime < self.timeout:
                if not self.msg_list.empty():
                    msgs = self.msg_list.get()
                    if msgs[0] == 0x30:
                        while txIndex < MsgLen:
                            CANMsg.FData[0] = (0x20 | (snCnt & 0xf))
                            snCnt += 1
                            txLen = MsgLen - txIndex
                            if txLen > Datalengh:
                                txLen = Datalengh
                            else:
                                for i in range(txLen, Datalengh):
                                    CANMsg.FData[i + 1] = 0xAA
                            for i in range(txLen):
                                CANMsg.FData[i + 1] = SendDatas[i + txIndex]
                            if tsapp_transmit_canfd_async(self.HwHandle, CANMsg) != 0:
                                break
                            txIndex += txLen
                            if txIndex >= MsgLen:
                                return 0
                        return 161
            else:
                return 161

    def tstp_can_request_and_get_response(self, SendDatas):
        self.msg_list.queue.clear()
        ret = self.tstp_can_send_request(SendDatas)
        if ret == 0:
            ret, recv_data = self.receive_can_Response()
        else:
            return ret, []
        return ret, bytes(recv_data)


class DBC_parse():
    dbc_list_by_name = {}
    dbc_signal_list = {}
    filenames = []
    dbc_list_by_id = {}

    def __init__(self, dbcfile=''):
        if dbcfile !='':
            self.load_dbc(dbcfile)

    def load_dbc(self, dbcfile):
        '''return db index'''
        if dbcfile != '':
            data_path, filename = os.path.split(dbcfile)
            if filename not in self.filenames:
                self.filenames.append(filename)
            else:
                print(filename, " already exists")
                return
            try:
                db = cantools.db.load_file(dbcfile)
                for msg in db.messages:
                    if (msg.name not in self.dbc_list_by_name) and (msg.frame_id not in self.dbc_list_by_id):
                        self.dbc_list_by_name[msg.name] = msg
                        self.dbc_list_by_id[msg.frame_id] = msg
                        self.dbc_signal_list[msg.name] = msg.signals
                    else:
                        print(msg.name, ' already exists')

            except Exception as e:
                print(e)

    def __change_signal_value(self, msg, signal_dict: dict):
        try:
            msg_data_dict = self.dbc_list_by_id[msg.arbitration_id].decode(
                data=msg.data)
            for key in signal_dict:
                if key in msg_data_dict:
                    msg_data_dict[key] = signal_dict[key]
                else:
                    print('signal not exist')
                    return msg
            msg.data = self.dbc_list_by_id[msg.arbitration_id].encode(
                msg_data_dict)
            return msg
        except Exception as e:
            print(e)

    def set_signal_value(self, msg:TLIBCAN or TLIBCANFD or Message, signal_dict: dict):
        msg = tosun_convert_msg(msg)
        if msg.arbitration_id in self.dbc_list_by_id:
            return msg_convert_tosun(self.__change_signal_value(msg, signal_dict))

    def get_signal_value(self, msg, signalname):
        try:
            if isinstance(msg, Message):
                signaldict = self.dbc_list_by_id[msg.arbitration_id].decode(
                    data=msg.data)

            elif isinstance(msg, TLIBCAN) or isinstance(msg, TLIBCANFD):
                signaldict = self.dbc_list_by_id[msg.FIdentifier].decode(
                    data=bytes(msg.FData))
            else:
                signaldict = {}
            if signalname:
                if signalname in signaldict:
                    return signaldict[signalname]
                else:
                    print("signal not exist")
                    return None
            else:
                return signaldict
        except Exception as e:
            print(e)


class TSMasterDevice():
    HwHandle = c_size_t(0)
    channel_list = []
    Rate_baudrate = []
    data_baudrate = []
    enable_120hm = []
    configs = {}
    __hw_isconnect = False
    include_own_message = False
    __include_error_message = False
    msg_list = queue.Queue(maxsize=100000)
    error_code = {1: "Index out of range",
                2: "Connect failed",
                3: "Device not found",
                4: "Error code not valid",
                5: "HID device already connected",
                6: "HID write data failed",
                7: "HID read data failed",
                8: "HID TX buffer overrun",
                9: "HID TX buffer too large",
                10: "HID RX packet report ID invalid",
                11: "HID RX packet length invalid",
                12: "Internal test failed",
                13: "RX packet lost",
                14: "SetupDiGetDeviceInterfaceDetai",
                15: "Create file failed",
                16: "CreateFile failed for read handle",
                17: "CreateFile failed for write handle",
                18: "HidD_SetNumInputBuffers",
                19: "HidD_GetPreparsedData",
                20: "HidP_GetCaps",
                21: "WriteFile",
                22: "GetOverlappedResult",
                23: "HidD_SetFeature",
                24: "HidD_GetFeature",
                25: "Send Feature Report DeviceIoContro",
                26: "Send Feature Report GetOverLappedResult",
                27: "HidD_GetManufacturerString",
                28: "HidD_GetProductString",
                29: "HidD_GetSerialNumberString",
                30: "HidD_GetIndexedString",
                31: "Transmit timed out",
                32: "HW DFU flash write failed",
                33: "HW DFU write without erase",
                34: "HW DFU crc check error",
                35: "HW DFU reset before crc check success",
                36: "HW packet identifier invalid",
                37: "HW packet length invalid",
                38: "HW internal test failed",
                39: "HW rx from pc packet lost",
                40: "HW tx to pc buffer overrun",
                41: "HW API parameter invalid",
                42: "DFU file load failed",
                43: "DFU header write failed",
                44: "Read status timed out",
                45: "Callback already exists",
                46: "Callback not exists",
                47: "File corrupted or not recognized",
                48: "Database unique id not found",
                49: "Software API parameter invalid",
                50: "Software API generic timed out",
                51: "Software API set hw config. failed",
                52: "Index out of bounds",
                53: "RX wait timed out",
                54: "Get I/O failed",
                55: "Set I/O failed",
                56: "An active replay is already running",
                57: "Instance not exists",
                58: "CAN message transmit failed",
                59: "No response from hardware",
                60: "CAN message not found",
                61: "User CAN receive buffer empty",
                62: "CAN total receive count <> desired count",
                63: "LIN config failed",
                64: "LIN frame number out of range",
                65: "LDF config failed",
                66: "LDF config cmd error",
                67: "TSMaster envrionment not ready",
                68: "reserved failed",
                69: "XL driver error",
                70: "index out of range",
                71: "string length out of range",
                72: "key is not initialized",
                73: "key is wrong",
                74: "write not permitted",
                75: "16 bytes multiple",
                76: "LIN channel out of range",
                77: "DLL not ready",
                78: "Feature not supported",
                79: "common service error",
                80: "read parameter overflow",
                81: "Invalid application channel mapping",
                82: "libTSMaster generic operation failed",
                83: "item already exists",
                84: "item not found",
                85: "logical channel invalid",
                86: "file not exists",
                87: "no init access, cannot set baudrate",
                88: "the channel is inactive",
                89: "the channel is not created",
                90: "length of the appname is out of range",
                91: "project is modified",
                92: "signal not found in database",
                93: "message not found in database",
                94: "TSMaster is not installed",
                95: "Library load failed",
                96: "Library function not found",
                97: 'cannot find libTSMaster.dll, use \"set_libtsmaster_location\" to set its location before calling initialize_lib_tsmaster',
                98: "PCAN generic operation error",
                99: "Kvaser generic operation error",
                100: "ZLG generic operation error",
                101: "ICS generic operation error",
                102: "TC1005 generic operation error",
                104: "Incorrect system variable type",
                105: "Message not existing, update failed",
                106: "Specified baudrate not available",
                107: "Device does not support sync. transmit",
                108: "Wait time not satisfied",
                109: "Cannot operate while app is connected",
                110: "Create file failed",
                111: "Execute python failed",
                112: "Current multiplexed signal is not active",
                113: "Get handle by logic channel failed",
                114: "Cannot operate while application is Connected, please stop application first",
                115: "File load failed",
                116: "Read LIN Data Failed",
                117: "FIFO not enabled",
                118: "Invalid handle",
                119: "Read file error",
                120: "Read to EOF",
                121: "Configuration not saved",
                122: "IP port open failed",
                123: "TCP connect failed",
                124: "Directory not exists",
                125: "Current library not supported",
                126: "Test is not running",
                127: "Server response not received",
                128: "Create directory failed",
                129: "Invalid argument type",
                130: "Read Data Package from Device Failed",
                131: "Precise replay is running",
                132: "Replay map is already",
                133: "User cancel input",
                134: "API check result is negative",
                135: "CANable generic error",
                136: "Wait criteria not satisfied",
                137: "Operation requires application connected",
                138: "Project path is used by another application",
                139: "Timeout for the sender to transmit data to the receiver",
                140: "Timeout for the receiver to transmit flow control to the sender",
                141: "Timeout for the sender to send first data frame after receiving FC frame",
                142: "Timeout for the receiver to receiving first CF frame after sending FC frame",
                143: "Serial Number Error",
                144: "Invalid flow status of the flow control frame",
                145: "Unexpected Protocol Data Unit",
                146: "Wait counter of the FC frame out of the maxWFT",
                147: "Buffer of the receiver is overflow",
                148: "TP Module is busy",
                149: "There is error from CAN Driver",
                150: "Handle of the TP Module is not exist",
                151: "UDS event buffer is full",
                152: "Handle pool is full, can not add new UDS module",
                153: "Pointer of UDS module is null",
                154: "UDS message is invalid",
                155: "No uds data received",
                156: "Handle of uds is not existing",
                157: "UDS module is not ready",
                158: "Transmit uds frame data failed",
                159: "This uds Service is not supported",
                160: "Time out to send uds request",
                161: "Time out to get uds response",
                162: "Get uds negative response",
                163: "Get uds negative response with expected NRC",
                164: "Get uds negative response with unexpected NRC",
                165: "UDS can tool is not ready",
                166: "UDS data is out of range",
                167: "Get unexpected UDS frame",
                168: "Receive unexpected positive response frame",
                169: "Receive positive response with wrong data",
                170: "Failed to get positive response",
                171: "Reserved UDS Error Code",
                172: "Receive negative response with unexpected NRC",
                173: "UDS service is busy",
                174: "Request download service must be performed before transfer data",
                175: "Length of the uds reponse is wrong",
                176: "Verdict value smaller than specification",
                177: "Verdict value greater than specification",
                178: "Verdict check failed",
                179: "Automation module not loaded, please load it first",
                180: "Panel not found",
                181: "Control not found in panel",
                182: "Panel not loaded, please load it first",
                183: "STIM signal not found",
                184: "Automation sub module not available",
                185: "Automation variant group not found",
                186: "Control not found in panel",
                187: "Panel control does not support this property",
                188: "RBS engine is not running",
                189: "This message does not support PDU container",
                190: "Data not available",
                191: "J1939 not supported",
                192: "Another J1939 PDU is already being transmitted",
                193: "Transmit J1939 PDU failed due to protocol error",
                194: "Transmit J1939 PDU failed due to node inactive",
                195: "API is called without license support",
                196: "Signal range check violation",
                197: "DataLogger read category failed",
                198: "Check Flash Bootloader Version Failed",
                199: "Log file not created",
                200: "Module is being edited by user",
                201: "The Logger device is busy, can not operation at the same time",
                202: "Master node transmit diagnostic package timeout",
                203: "Master node transmit frame failed",
                204: "Master node receive diagnostic package timeout",
                205: "Master node receive frame failed",
                206: "Internal time runs out before reception is completed ",
                207: "Master node received no response ",
                208: "Serial Number Error when receiving multi frames",
                209: "Slave node transmit diagnostic package timeout",
                210: "Slave node receive diagnostic pacakge timeout",
                211: "Slave node transmit frames error",
                212: "Slave node receive frames error",
                }
    db = None
    onRXTX_EVENT = OnTx_RxFUNC_CANFD()
    start_receive = False
    def __init__(self, configs: [dict], hwserial: bytes = b'',
                # is_recv_error: bool = False,
                is_include_tx: bool = False,
                # is_start_recv: bool = False,
                dbc: bytes = b'',
                filter:dict={}):
        self.filter = filter
        self.include_own_message = is_include_tx
        self.configs = configs
        self.hwserial = hwserial
        self.dbc = dbc
        self.db = DBC_parse()
        if isinstance(hwserial, str):
            self.hwserial = hwserial.encode('utf8')
        self.connect()
    def connect(self):
        ret = tsapp_connect(self.hwserial, self.HwHandle)
        if ret == 0 or ret == 5:
            self.__hw_isconnect = True
            for index, congfig in enumerate(self.configs):
                self.channel_list.append(
                    congfig['FChannel'] if 'FChannel' in congfig else index)

                self.Rate_baudrate.append(
                    congfig['rate_baudrate'] if 'rate_baudrate' in congfig else 500)

                self.data_baudrate.append(
                    congfig['data_baudrate'] if 'data_baudrate' in congfig else 2000)

                self.enable_120hm.append(
                    congfig['enable_120hm'] if 'enable_120hm' in congfig else True)

                if 'is_fd' in congfig and congfig['is_fd']:
                    tsapp_configure_baudrate_canfd(self.HwHandle, self.channel_list[index], self.Rate_baudrate[index],
                                                self.data_baudrate[index],
                                                TLIBCANFDControllerType.lfdtISOCAN,
                                                TLIBCANFDControllerMode.lfdmNormal,
                                                self.enable_120hm[index])
                else:
                    tsapp_configure_baudrate_can(self.HwHandle, self.channel_list[index], c_double(self.Rate_baudrate[index]),self.enable_120hm[index])
            # self.ONRxTx_Event = OnTx_RxFUNC_CANFD(self.on_tx_rx_event)
            # tsapp_register_event_canfd(self.HwHandle, self.ONRxTx_Event)
            # self.start_recv_time = time.perf_counter()
            if self.dbc!=b'':
                self.load_dbc(self.dbc)
        else:
            self.__hw_isconnect = False
            raise "HW CONNECT FAILED"
    def load_dbc(self, dbc):
        self.db.load_dbc(dbc)
    def unload_dbc_all(self):
        self.db.dbc_list_by_id.clear()
        self.db.dbc_list_by_name.clear()
        self.db.dbc_signal_list.clear()
    def set_singal_value(self, msg, singaldict:dict):
        return self.db.set_signal_value(msg, singaldict)
    def get_signal_value(self, msg, signal_name):
        return self.db.get_signal_value(msg, signal_name)
    def send_msg(self, msg, timeout: Optional[float] = 0.1, sync: bool = False, is_cyclic: bool = False):
        # timeout = timeout * 1000
        if self.__hw_isconnect:
            if isinstance(msg, TLIBCAN):
                if is_cyclic:
                    # '''timeout is cyclic time when is_cyclic is ture'''
                    tscan_add_cyclic_msg_can(
                        self.HwHandle, msg, timeout * 1000)
                else:
                    if sync:
                        tsapp_transmit_can_sync(
                            self.HwHandle, msg, timeout * 1000)
                    else:
                        tsapp_transmit_can_async(self.HwHandle, msg)
            elif isinstance(msg, TLIBCANFD):
                if is_cyclic:
                    '''timeout is cyclic time when is_cyclic is ture'''
                    tscan_add_cyclic_msg_canfd(
                        self.HwHandle, msg, timeout * 1000)
                else:
                    if sync:
                        tsapp_transmit_canfd_sync(
                            self.HwHandle, msg, timeout * 1000)
                    else:
                        tsapp_transmit_canfd_async(self.HwHandle, msg)
            elif isinstance(msg, Message):
                msg = msg_convert_tosun(msg)
                self.send_msg(msg, timeout, sync, is_cyclic)
            else:
                print("UNKOWN TYRE")
        else:
            raise "HW CONNECT FAILED"

    def recv(self, channel,timeout: Optional[float] = 0.1) -> Message:
        start_time = time.perf_counter()
        while time.perf_counter() - start_time<= timeout:
            ACANFD = (TLIBCANFD*1)()
            buffersize = c_int32(1)
            tsapp_receive_canfd_msgs(self.HwHandle,ACANFD,buffersize,channel,1 if self.include_own_message else 0)
            if buffersize.value==1:
                return tosun_convert_msg(ACANFD[0])
        return None
        return self.msg_list.get() if not self.msg_list.empty() else None

    def on_tx_rx_event(self, ACAN):
        if self.start_receive:
            msg_channel = self.filter.get('msg_channel',None)
            msg_id = self.filter.get('msg_id',None)
            # pass_no = self.filter.get('pass',True)
            if msg_channel != None and ACAN.contents.FIdxChn != msg_channel:
                return
            if msg_id != None and ACAN.contents.FIdentifier != msg_id:
                return
            if ACAN.contents.FProperties == 0x80:
                msg = Message(timestamp=blf_start_time + float(ACAN.contents.FTimeUs) / 1000000,
                            arbitration_id=0xFFFFFFFF,
                            is_error_frame=True, data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])
                if self.__include_error_message:
                    if self.msg_list.full():
                        self.msg_list.get()
                    self.msg_list.put(msg)
            elif ACAN.contents.FProperties & 1 == 1:
                if self.include_own_message:
                    msg = tosun_convert_msg(ACAN.contents)
                    if self.msg_list.full():
                        self.msg_list.get()
                    self.msg_list.put(msg)
            else:
                msg = tosun_convert_msg(ACAN.contents)
                if self.msg_list.full():
                    self.msg_list.get()
                self.msg_list.put(msg)

    def tsdiag_can_create(self, pDiagModuleIndex: c_int32, AChnIndex: CHANNEL_INDEX, ASupportFDCAN: c_byte,
                          AMaxDLC: c_byte,
                          ARequestID: c_uint32, ARequestIDIsStd: bool, AResponseID: c_uint32, AResponseIDIsStd: bool,
                          AFunctionID: c_uint32, AFunctionIDIsStd: bool, timeout=0.1):
        self.timeout = c_int32(int(timeout * 1000))
        try:
            dlc = self.DLC_DATA_BYTE_CNT.index(AMaxDLC)
        except:
            dlc = AMaxDLC
        r = dll.tsdiag_can_create(byref(pDiagModuleIndex), AChnIndex, ASupportFDCAN, dlc, ARequestID,
                                  ARequestIDIsStd,
                                  AResponseID, AResponseIDIsStd, AFunctionID, AFunctionIDIsStd)

        dll.tsdiag_can_attach_to_tscan_tool(pDiagModuleIndex, self.HwHandle)
        return r

    def tsdiag_can_delete(self, pDiagModuleIndex: c_int32):
        r = dll.tsdiag_can_delete(pDiagModuleIndex)
        return r

    def tstp_can_request_and_get_response(self, pDiagModuleIndex: c_int32, AReqDataArray, max_len=4095):
        if not isinstance(AReqDataArray, bytes):
            AReqDataArray = bytes(AReqDataArray)
        AResdata = create_string_buffer(max_len)
        AResponseDataSize = c_uint32(len(AResdata))

        r = dll.tstp_can_request_and_get_response(pDiagModuleIndex, c_char_p(AReqDataArray), len(AReqDataArray),
                                                  AResdata, byref(AResponseDataSize), self.timeout)
        return r, bytes(AResdata[:AResponseDataSize.value])

    def tstp_can_send_functional(self, pDiagModuleIndex: c_int32, AReqDataArray: bytearray,
                                 ):
        r = dll.tstp_can_send_functional(pDiagModuleIndex, c_char_p(AReqDataArray), len(AReqDataArray),
                                         self.timeout)
        return r

    def tscan_get_error_description(self, ACode):

        return self.error_code[ACode]

    def shut_down(self):
        tsapp_disconnect_by_handle(self.HwHandle)
        self.msg_list.queue.clear()

if __name__ == '__main__':
    initialize_lib_tsmaster(True,True,False)
    configs = [{'FChannel': 0, 'rate_baudrate': 500,
    'data_baudrate': 2000, 'enable_120hm': True, 'is_fd': True}, {'FChannel': 1, 'rate_baudrate': 500,
    'data_baudrate': 2000, 'enable_120hm': True, 'is_fd': True}]

    handle =TSMasterDevice(configs,is_include_tx=True,dbc=r'D:\IDE\window_linux_Rep\python\Py_TSMaster\CAN_FD_Powertrain.dbc')

    c = TLIBCANFD(0,12,0x701,1,1,[])

    print(handle.get_signal_value(c,None))

    c = handle.set_singal_value(c,{'FallbackMessage_Byte_00_05': 1000, 'FallbackMessage_Byte_06_10': 2000})

    print(handle.get_signal_value(c,None))

    handle.send_msg(c)

