import sys
sys.path.append('../../')
from time import sleep
from instruments.core.base import Instrument

class YokoGS200(Instrument):

    _rangeVOLT = {
        '30 V': 30E+0,
        '10 V': 10E+0,
        '1 V': 1E+0,
        '100 mV': 100E-3,
        '10 mV': 10E-3
    }

    _rangeCURR = {
        '200 mA': 200E-3,
        '100 mA': 100E-3,
        '10 mA': 10E-3,
        '1 mA': 1E-3
    }

    def __init__(self,
                 inst_name: str = '',
                 inst_address: str = '',
                 timeout: int = 5,
                 dc_mode: str = 'VOLTAGE',
                 range_limit: str = '1 V'):
        """
        reading self-identification for Yokogawa GS200
        with USB address "USB0::0x0B21::0x0039::91WB18861::INSTR"

        The arguments are required to follow the syntax.
            inst_name: 'YokoDC'
            inst_address: 'USB0::0x0B21::0x0039::91WB18861::INSTR'
            timeout: 5(sec)

        Parameters
        ----------
        inst_name : str, optional
            Instrument name to identify. The default is ''.
        inst_address : str, optional
            Instrument VISA address. The default is ''.
        timeout : int, optional
            Timeout. The default is 5 (sec).
        dcState : str, optional
            DESCRIPTION. The default is 'CURRENT'.

        Returns
        -------
        None.

        """
        # unique attributes for yokoGS
        self.__dc_mode = dc_mode
        self._yoko_extension = {}
        super().__init__(
            inst_name, inst_address, timeout, self._yoko_extension)
        self.function_mappings = {
            'set_dc_mode': self.set_dc_mode,
            'set_dc_output': self.set_dc_output,
            'set_range_limit': self.set_range_limit,
            'execute_microwave_switch': self.execute_microwave_switch
            }
        if (self._inst_name != '') and (self._inst_address != ''):
            self.create_extension_template(self._yoko_extension)
        self.connect()

        
    def disconnect(self):
        """
        When the GS200 is in remote mode,
        the user can call its function to return to local mode.

        Returns
        -------
        None.

        """
        self.write(':SYSTem:LOCal')
        del self.__class__.DEVICES[self._inst_name]
        print(f'{self.instName} has been disconnected by user.')

    def query_dc_value(self):
        """
        Get the present DC value.

        Returns
        -------
        float value.

        """
        return self.query('SOUR:LEV?')

    def query_output(self):
        """
        Get the output status

        Returns
        -------
        1. '0': output off
        2. '1': output on

        """
        return self.query(':OUTP?')
    
    def query_dc_mode(self):
        """
        Get the DC source

        Returns
        -------
        1. 'CURR'
        2. 'VOLT'

        """
        return self.query(':SOUR:FUNC?')
    
    def set_dc_value(self, value: float = 0.0):
        """
        Set the present value of the DC source.

        Parameters
        ----------
        value : float
            DC source value.

        Returns
        -------
        None.

        """
        self.write(f':SOUR:LEV {str(value)}')        

    def set_dc_mode(self, dc_mode: str=None):
        """
        Set the present status of DC mode.

        Raises
        ------
        Exception
            SetDCmodeError! Please modify the dcState.

        Returns
        -------
        None.

        """

        if dc_mode is None:
            dc_mode = self.__dc_mode.upper()
        else:
            self.__dc_mode = dc_mode.upper()
        if len(dc_mode) < 4:
                raise Exception(
                    'Required at least 4 letter!'+\
                    'CURR or VOLT')
        if (dc_mode in 'CURRENT') or (dc_mode in 'VOLTAGE'):
            self.write(f':SOUR:FUNC {dc_mode}')
            self.update_inst_extension(
                'set_dc_mode',
                self._yoko_extension, **{'dc_mode': dc_mode})
        else:
            raise Exception('SetDCmodeError! Please modify the dc_mode.')

    def set_dc_output(self, dc_output: bool = 0):
        """
        Turn on or turn off the yoko DC output.

        Parameters
        ----------
        output : bool
            dc_output = 1:
                Turn the output on.
            dc_output = 0:
                Turn the output off.

        Returns
        -------
        None.

        """
        self.write(f':OUTP {str(dc_output)}')
        self.update_inst_extension(
            'set_dc_output',
            self._yoko_extension, **{'dc_output': dc_output})

    def set_range_limit(self, dc_range_limit:str = '10 mA'):
        """
        Set the source limiter to protect connecting mechanism.
        
        Parameters
        ----------
        range_limit : str, optional
            '10 mA': The default is '10 mA'.
            Current Range Limiter
                '200 mA'
                '100 mA'
                '10 mA'
                '1 mA'
            Voltage Range Limiter
                '30 V'
                '10 V': 
                '1 V': 
                '100 mV': 
                '10 mV': 

        Returns
        -------
        None.

        """
        rangeC = self.__class__._rangeCURR
        rangeV = self.__class__._rangeVOLT
        dc_mode = self.__dc_mode.upper()

        if (dc_range_limit in rangeC.keys()) or \
            (dc_range_limit in rangeV.keys()):
            if dc_mode in ('CURRENT'):
                suffix = str(rangeC[dc_range_limit])
            elif dc_mode in ('VOLTAGE'):
                suffix = str(rangeV[dc_range_limit])
            self.write(f':SOUR:RANG {suffix}')
            self.update_inst_extension(
                'set_range_limit',
                self._yoko_extension, **{'dc_range_limit': dc_range_limit})
            print(f'\nrangeMode: "{dc_range_limit}"\nSetting successfully!')
        else:
            if (dc_range_limit in rangeV) and (dc_mode in 'CURRENT'):
                self._err_msg_range_limit(1)
            elif (dc_range_limit in rangeC) and (dc_mode in 'VOLTAGE'):
                self._err_msg_range_limit(1)
            else:
                self._err_msg_range_limit(2)

    def _err_msg_range_limit(self, situation: int = 1):
        """
        Show the corresponding error prompt.

        Parameters
        ----------
        situation : int, optional
            select the specific error description. The default is 1.

        Raises
        ------
        1. case 1
        
        2. case 2
            
        Returns
        -------
        None.

        """
        if situation == 1:
            raise Exception('''Error message for "rangeLimit":
                      dcStateTypeError!
                      > Please check "rangeMode" is matched with "dcState"''')
        elif situation == 2:
            rangeCkeys = self.__class__._rangeCURR.keys()
            rangeVkeys = self.__class__._rangeVOLT.keys()
            raise Exception(f'''Error message for "rangeLimit":\n
            rangeModeTypeError!\n
            > You may want to type the following keywords in rangeMode.\n
            >>>>> The keyword of rangeVOLT: {rangeVkeys}\n
            >>>>> The keyword of rangeCURR: {rangeCkeys}\n''')

    def set_repeat(self, button: bool):
        """
        Turn program repetition mode on or off.

        Parameters
        ----------
        button : bool
            1: turn repetition mode on.
            0: turn repetition mode off.

        Returns
        -------
        None.

        """
        self.write(f':PROG:REP {str(button)}')

    def _set_interval_time(self, interval_time: float):
        """
        Set the program interval time.

        Parameters
        ----------
        interval_time : float
            The range of interval time is from 0.1 to 3600.0 (sec).

        Returns
        -------
        None.

        """
        if 0.1 <= interval_time <= 3600.0:
            self.write(f':PROG:INT {str(interval_time)}')
        else:
            raise Exception(
                'The range of interval time is from 0.1 to 3600.0 (sec).')

    def _set_slope_time(self, slope_time:float):
        """
        Set the program slop time.

        Parameters
        ----------
        slope_time : float
            The range of slope time is from 0.0 to 3600.0 (sec).

        Returns
        -------
        None.

        """
        if 0.0 <= slope_time <= 3600.0:
            self.write(f':PROG:SLOP {str(slope_time)}')
        else:
            raise Exception(
                'The range of slop time is from 0.0 to 3600.0 (sec).')

    def set_sweep_rate(self,
                       sweep_time: float,
                       interval_time: float):
        """
        Set slope time and interval time with the same sweep time.

        Parameters
        ----------
        sweep_time : float
            Sweep time (sec)
        interval_time : float
            Interval time (sec)

        Returns
        -------
        None.

        """
        self.set_repeat(int(0))
        self._set_interval_time(interval_time)
        self._set_slope_time(sweep_time)

    def set_sweep_slope(self, lower: float, higher: float):
        """
        Set the sweep slope. That is, the "dc_value" will be set from "lower"
        to "higher".
        
        1. RisingSlope:
            The "dc_value" of "lower" is smaller than "higher".
        2. FallingSlope:
            The "dc_value" of "lower" is larger than "higher".
        Parameters
        ----------
        lower : float
            The lower dc value.
        higher : float
            The higher dc value.

        Returns
        -------
        None.

        """
        range_limit = str(self.query(':SOUR:RANG?'))
        dc_state = self.query(':SOUR:FUNC?')
        startcmd = f':SOUR:FUNC {dc_state};RANG {range_limit};LEV {lower};'
        endcmd = f':SOUR:FUNC {dc_state};RANG {range_limit};LEV {higher};'

        self.write(':PROG:EDIT:STAR')
        self.write(startcmd)
        self.write(endcmd)
        self.write(':PROG:EDIT:END')
    
    def execute_microwave_switch(self,
                                 sweep_time: float,
                                 interval_time: float,
                                 init_lower: float,
                                 init_higher: float):
        """
        Climb to a high point at a constant rate, when climbing to a high point,
        stay for a fixed "wait_time"; Finally, gradually reduce the voltage 
        value at the same rate until 0V.

        Parameters
        ----------
        sweep_time : float
            Climbing time.
        wait_time : float
            Waitting time.
        init_lower : float
            Initial dc value.
        init_higher : float
            Final dc value.

        Returns
        -------
        None.

        """
        
        
        # Initial settings
        self.set_dc_output(1)
        self.set_sweep_rate(sweep_time, interval_time)
        # Store init_lower and init_higher to properties
        self.update_inst_extension(
            'execute_microwave_switch',
            self._yoko_extension,
            **{'sweep_time': sweep_time,
               'interval_time': interval_time,
               'init_lower': init_lower,
               'init_higher': init_higher})
      
        print('\nStart microwaveSwitch.')
        self.set_sweep_slope(init_lower, init_higher)
        sleep(1)        
        self.write('*OPC')
        self.write(":PROG:RUN;")
        self.write('*OPC')
        self.write(":PROG:HOLD;")
        self.set_sweep_slope(init_higher, init_lower)
        self.write('*OPC')
        self.write(":PROG:RUN;")
        sleep(1)
        print('Finish microwaveSwitch.')


if __name__ == "__main__":
   pass
