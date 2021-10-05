# -*- coding: utf-8 -*-
import sys
sys.path.append('../../')
import numpy as np
from time import sleep
from instruments.core.base import Instrument

class AWG5208(Instrument):

    MAX_MKR_NUM = 4
    MAX_CH_NUM = 8
    MAX_TRACK_NUM = 8
    MAX_STEP_NUM = 16383
    MAX_RESOLUTION = 16

    def __init__(self,
                 inst_name: str='AWG_5208',
                 inst_address='TCPIP0::192.168.20.43::inst0::INSTR',
                 timeout=5
                 ):
        """
        Establish AWG 5208 connection via TCP/IP protocol.

        Parameters
        ----------
        inst_name : str, optional
            Name of AWG instance. The default is 'Tektronix_AWG_5208'.
        inst_address : str, optional
            Address for connection. The default is
            'TCPIP0::192.168.20.43::inst0::INSTR'.
        timeout : int, optional
            Connection attempt before timeout. The default is 180s.

        """
        super().__init__(inst_name, inst_address, timeout)
        self.connect()
        self._wfmList = {}
        self._wfm_mkr_num = {}
        self._seqList = {}
        self._seq_mkr_num = {}

    # get methods
    @property
    def wfmList(self):
        return self._wfmList.keys()

    @property
    def seqList(self):
        return self._seqList.keys()

    # status
    def __str__(self):
        """
        Returns the error and event query for all the unread items and removes
        them from the query.

        """
        print(f'{self._inst_name} @ {self._inst_address}\n' +
              '---\n'
              f'Waveform list: {self.wfmList}\n' +
              f'Sequence list: {self.seqList}')
        return 'AWG Error state: %s' % (self.query('system:error:all?'))

    def __del__(self):
        """
        Stop and clear sequence list and waveform list in AWG, and disconnect
        AWG from PC control.

        """
        self.stop()
        self.set_ch_output(False, *range(1, 9))
        self.clr_seq()
        self.clr_wfm()
        self.disconnect()

    # assign methods
    def set_wfm(self,
                wfm_name='default',
                wfm=None,
                mkr1=None, mkr2=None, mkr3=None, mkr4=None
                ):
        """
        Initialize a new empty waveform along with corresponding markers.

        Parameters
        ----------
        wfm_name : str, optional
            Name of waveform. The default is 'default'.
        wfm : np.ndarray, optional
            Waveform data. The default is None.
        mkr1 : np.ndarray, optional
            Marker 1 data. The default is None.
        mkr2 : np.ndarray, optional
            Marker 2 data. The default is None.
        mkr3 : np.ndarray, optional
            Marker 3 data. The default is None.
        mkr4 : np.ndarray, optional
            Marker 4 data. The default is None.

        """
        self._wfmList[wfm_name] = [wfm, mkr1, mkr2, mkr3, mkr4]
        wfm_length = len(self._wfmList[wfm_name][0])
        self.write(f'WLIST:WAVEFORM:NEW "{wfm_name}", {wfm_length}')
        # initialize number of needed markers
        self._wfm_mkr_num[wfm_name] = 0

    def upload_wfm(self):
        """
        Upload created waveforms to AWG.

        """
        for wfm_name in self._wfmList.keys():
            wfm_data = self._wfmList[wfm_name][0]
            wfm_length = len(wfm_data)
            string_arg = 'WLIST:WAVEFORM:DATA ' + \
                f'"{wfm_name}", 0, {int(wfm_length)}, '
            # string_arg = 'WLIST:WAVEFORM:DATA "%s", 0, %d, ' % (
            #     wfm_name, wfm_length)
            self.inst.write_binary_values(string_arg, wfm_data)
            # quering whether the intrument is pending
            self.write('*opc')
            # update local marker data
            flag = 0
            mkr_data = None
            for idx in range(len(self._wfmList[wfm_name])-1, 0, -1):
                if not isinstance(self._wfmList[wfm_name][idx], np.ndarray):
                    continue
                if flag == 0:
                    mkr_data = self._wfmList[wfm_name][idx] * 128/2**(idx-1)
                    self._wfm_mkr_num[wfm_name] = idx
                    flag += 1
                    continue
                mkr_data += self._wfmList[wfm_name][idx] * 128/2**(idx-1)
            # initialize the marker placeholder with 0s and input binary values
            if isinstance(mkr_data, np.ndarray):
                self.inst.write_binary_values(
                    f'wlist:waveform:marker:data "{wfm_name}", 0, ' +
                    f'{int(wfm_length)}, ',
                    np.array(mkr_data, dtype=np.uint8),
                    datatype='B')
                # Quering whether the intrument is pending
                self.write('*opc')

    def set_seq(self, seq_name='default', num_track=1, num_step=1):
        """
        Initialize an empty sequence list.

        Parameters
        ----------
        seq_name : str, optional
            Name of sequence. The default is 'default'.
        num_track : int, optional
            Total number of tracks. The default is 1.
        num_step : int, optional
            Total number of steps. The default is 1.

        """
        if num_track > self.__class__.MAX_TRACK_NUM:
            num_track = self.__class__.MAX_TRACK_NUM
        if num_step > self.__class__.MAX_STEP_NUM:
            num_step = self.__class__.MAX_STEP_NUM
        self._seqList[seq_name] = [
            [None for i in range(num_step)] for j in range(num_track)
            ]
        # create a new empty space for sequence data placeholder
        self.write(
            f'SLISt:SEQuence:NEW "{seq_name}",{num_step},{num_track}'
            )
        # initialize number of needed markers
        self._seq_mkr_num[seq_name] = [0]*num_track

    def assign_seq(self, wfm_name, seq_name, track_index, step_index):
        """
        Assign waveform to sequence with specified indices.

        Parameters
        ----------
        wfm_name : str
            Waveform name to be assigned.
        seq_name : str
            Name of assigned sequence.
        track_index : int
            Track index, 1~8.
        step_index : int
            Step index, 1~16383.

        """
        self._seqList[seq_name][track_index-1][step_index-1] = wfm_name

        # Update number of needed markers
        if self._wfm_mkr_num[wfm_name] > self._seq_mkr_num[seq_name][
                track_index-1
                ]:
            self._seq_mkr_num[seq_name][track_index-1
                                        ] = self._wfm_mkr_num[wfm_name]

    def upload_seq(self, seq_name):
        """
        Upload sequence to AWG.

        Parameters
        ----------
        seq_name : str
            Name of assigned sequence.

        """
        seq = self._seqList[seq_name]
        for track_i in range(len(seq)):
            for step_i in range(len(seq[track_i])):
                wfm_name = seq[track_i][step_i]
                if not wfm_name:
                    continue
                command = 'SLISt:SEQuence:' + \
                    'STEP{}:TASSet{}:WAVeform "{}","{}"'.format(
                        step_i+1, track_i+1, seq_name, wfm_name)
                self.write(command)
                self.write('*opc')

    def assign_ch(self, ch, name, track_index=None,
                  auto_output=True, auto_mkr=True):
        """
        Assign waveform/sequence to channel.

        Parameters
        ----------
        ch : int
            Channel index, 1~8.
        name : str
            Name of waveform/sequence.
        track_index : int, optional
            Track to be assigned, 1~8. Assign this argument to assign sequence.
            The default is None for assigning waveform.
        auto_output : boolean, optional
            Auto enable channel output. The default is True.
        auto_mkr : boolean, optional
            Auto channel marker assignment. The default is True.

        """
        command = f'SOURCE{ch}:CASSET:'
        mode = f'WAVEFORM "{name}"'
        suffix = ''
        if track_index:
            mode = f'SEQUENCE "{name}", '
            suffix = f'{track_index}'
        self.write(command + mode + suffix)
        # auto-assign markers to channel
        if auto_mkr:
            if track_index:
                mkr_num = self._seq_mkr_num[name][track_index-1]
            else:
                mkr_num = self._wfm_mkr_num[name]
            self.set_ch_mkr(*([None]*(ch-1)+[mkr_num]+[None]*(
                self.__class__.MAX_CH_NUM - ch
                )))
        if auto_output:
            self.set_ch_output(True, ch)

    def set_ch_amp(
            self, ch,
            wfm_Vpp=None, wfm_offset=None,
            mkr1=None, mkr2=None, mkr3=None, mkr4=None,
            **kwargs
            ):
        """
        Set channel voltage for waveform, markers, waveform offset.

        Parameters
        ----------
        ch : int
            Channel index, 1~8.
        wfm_Vpp : float, optional
            Peak-to-peak voltage for waveform data. The default is None.
        wfm_offset : float, optional
            Offset voltage for waveform data. The default is None.
        mkr1 : float, optional
            Marker 1 voltage. The default is None.
        mkr2 : float, optional
            Marker 2 voltage. The default is None.
        mkr3 : float, optional
            Marker 3 voltage. The default is None.
        mkr4 : float, optional
            Marker 4 voltage. The default is None.
        **kwargs : str
            Use 'dBm' keyword to enable wfm_Vpp assignment in dBm scale.

        """
        command = f'SOURCE{ch}'
        suffix = ':VOLTAGE:LEVel:IMMediate:AMPLITUDE '
        for i, volt in zip(range(self.__class__.MAX_MKR_NUM, 0, -1), [
                mkr4, mkr3, mkr2, mkr1
                ]):
            if not volt:
                continue
            value = f'{volt}V'
            mid = f':MARKER{i}'
            self.write(command + mid + suffix + value)
            self.write('*opc')
        if wfm_Vpp:
            self.write(command + suffix + f'{wfm_Vpp}')
            self.write('*opc')
        if 'dBm' in kwargs.keys():
            suffix = ':POWER:LEVel:IMMediate:AMPLITUDE '
            self.write(command + suffix + f'{kwargs["dBm"]}')
            self.write('*opc')
        if wfm_offset:
            self.write(
                command + f':VOLTAGE:LEVel:IMMediate:OFFSET {wfm_offset}'
                )
            self.write('*opc')

    def set_ch_mkr(self,
                   ch_mkr1=None, ch_mkr2=None, ch_mkr3=None, ch_mkr4=None,
                   ch_mkr5=None, ch_mkr6=None, ch_mkr7=None, ch_mkr8=None
                   ):
        """
        Set marker usage for all channels. This also sets the availible bits
        used by DAC, given by bit_DAC = 16 bit - bit_mkr.

        Parameters
        ----------
        ch_mkr1 : int, optional
            Bits for marker 1, 0~4. The default is None.
        ch_mkr2 : int, optional
            Bits for marker 2, 0~4. The default is None.
        ch_mkr3 : int, optional
            Bits for marker 3, 0~4. The default is None.
        ch_mkr4 : int, optional
            Bits for marker 4, 0~4. The default is None.
        ch_mkr5 : int, optional
            Bits for marker 5, 0~4. The default is None.
        ch_mkr6 : int, optional
            Bits for marker 6, 0~4. The default is None.
        ch_mkr7 : int, optional
            Bits for marker 7, 0~4. The default is None.
        ch_mkr8 : int, optional
            Bits for marker 8, 0~4. The default is None.

        """
        total_bit = self.__class__.MAX_RESOLUTION
        for ch_status, ch_mkr in enumerate([
                ch_mkr1, ch_mkr2, ch_mkr3, ch_mkr4,
                ch_mkr5, ch_mkr6, ch_mkr7, ch_mkr8
                ]):
            if not ch_mkr and ch_mkr != 0:
                continue
            self.write(
                f'SOURce{ch_status+1}:DAC:RESolution {total_bit - ch_mkr};'
                )
            sleep(0.001)

    def set_ch_output(self, output, *args):
        """
        Set the channel output on for specified channel indecies.

        Parameters
        ----------
        output : boolean
            Set True/False to enable/disable output.
        *args : int
            Channel indices with corresponding output to be enabled, indices
            ranges from 1~8.

        """
        for ch in args:
            if output:
                self.write(f'OUTPut{ch}:STATE ON')
                continue
            self.write(f'OUTPut{ch}:STATE OFF')

    # instrument control
    def play(self):
        """
        Initiate the channel output.

        """
        self.write('AWGControl:RUN')

    def stop(self):
        """
        Stop the channel output.

        """
        self.write('AWGControl:STOP')

    def clr_wfm(self):
        """
        Delete all waveforms in AWG.

        """
        self.write('WLISt:WAVeform:DELete ALL')
        self._wfmList.clear()
        self._wfm_mkr_num.clear()

    def clr_seq(self):
        """
        Delete all sequences in AWG.

        """
        self.write('SLISt:SEQuence:DELete ALL')
        self._seqList.clear()
        self._seq_mkr_num.clear()

    # general settings
    def set_sample_rate(self, sample_rate=1.0E9):
        """
        Set DAC sampling rate.

        Parameters
        ----------
        sample_rate : float, optional
            with unit Sample/s, can be set from 298 S/s ~ 2.5 GS/s (for option
            25). The default is 1.0E9.

        """
        self.write('CLOCk:SRATe %d' % (int(sample_rate)))

    def set_extref_source(self, ref_freq=10E6):
        """
        Set referenced external clock frequency.

        Parameters
        ----------
        ref_freq : float, optional
            External clock frequency. The default is 10E6 (10MHz) for fixed
            mode while other frequencies are for variable mode.

        """
        status = 'EFIXed' if ref_freq == 10E6 else f'EVAR{int(ref_freq)}'
        self.write('AWGControl:CLOCk:SOURce %s' % (status))


if __name__ == '__main__':
    pass
