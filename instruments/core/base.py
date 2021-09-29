# -*- coding: utf-8 -*-
import os
import sys
import pyvisa
from time import sleep
from .jsonIO import configIO


class Instrument:

    DEVICES = {}
    RM = pyvisa.ResourceManager()

    def __init__(self,
                 inst_name: str = '',
                 inst_address: str = '',
                 timeout: int = 5,            
                 default_inst_extension: dict = {}
                 ):
        """
        Once the user create a object,
        the object will attempt to build a connection
        between this PC and your instrument.

        1.
        reading self-identification for Yokogawa GS200
        with GPIB number "1".
        
        The arguments are required to follow the syntax.
            inst_name = 'YokoDC'
            inst_address = 'GPIB0::1::INSTR'
            timeout: 5(sec)

        2.
        reading self-identification for Tektronix AWG 5208
        with IP address "192.168.20.43"
        
        The arguments are required to follow the syntax.
            inst_name: 'AWG_5208'
            inst_address: 'TCPIP0::192.168.20.43::inst0::INSTR'
            timeout: 5(sec)
        
        3.
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

        Returns
        -------
        None.

        """
        # instrument arguments
        self._inst_name = inst_name
        self._inst_address = inst_address
        self._timeout = timeout
        self.inst = None
        # general instrument properties
        self._properties = {
            'name': self._inst_name,
            'inst_connect': False,
            'interface': self._inst_address.split(':', 1)[0],
            'address': self._inst_address,
            'r_terminate': '\n',
            'w_terminate': None,
            'timeout': self._timeout,
            'extension': {}
            }
        # inst_unique_method
        self.function_mappings = {}
        # implementation of import the config for the instrument automatically
        if self._inst_name == '' and self._inst_address == '':
            self._properties = self.__class__.load_inst_cfg()
            self._properties['inst_connect'] = False
            self._autorun = True
        else:
            self._properties['extension'] = default_inst_extension
            self._autorun = False
    
    def create_extension_template(self, inst_extension: dict):
        """
        

        Parameters
        ----------
        inst_extension : dict
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self.function_mappings == {}:
            return
        else:
            for f in self.function_mappings.values():
                f_args = {}
                annos = f.__annotations__
                for arg, arg_type in annos.items():
                    arg_type = str(arg_type)
                    if 'int' in arg_type:
                        var_init = 0
                    elif 'float' in arg_type:
                        var_init = 0.0
                    elif 'str' in arg_type:
                        var_init = ''
                    elif 'bool' in arg_type:
                        var_init = False
                    elif 'dict' in arg_type:
                        var_init = {}
                    f_args[arg] = var_init
                inst_extension[f.__name__] = f_args
            self._properties['extension'] = inst_extension
    
    def auto_run_inst_extension(self):
        """
        

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self.function_mappings == {}:
            raise Exception(
                'Oops, the inst_extension is still empty')
        else:
            extensions = self._properties['extension']
            for func_name, func_args in extensions.items():
                if func_name not in extensions.keys():
                    # raise Exception('Oops!')
                    continue
                else:
                    func = self.function_mappings[func_name]
                    func(**func_args)
                    print(f'{func_name} ... done.')
                    sleep(1)
                
    def update_inst_extension(self,
                               func_name: str,
                               inst_extension: dict,
                               **extend_properties: dict):
        """
        

        Parameters
        ----------
        func_name : str
            DESCRIPTION.
        inst_extension : dict
            DESCRIPTION.
        **extend_properties : dict
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self._autorun == False:
            if func_name not in self._properties['extension'].keys():
                self._properties['extension'][func_name] = {}
            for quantity, value in extend_properties.items():
                inst_extension[func_name][quantity] = value
                self._properties['extension'] = inst_extension
            
    def update_extension(self,
                         inst_extension: dict,
                         **extend_properties: dict):
        """
        

        Parameters
        ----------
        inst_extension : dict
            DESCRIPTION.
        **extend_properties : dict
            DESCRIPTION.

        Returns
        -------
        None.

        """
        for quantity, value in extend_properties.items():
            inst_extension[quantity] = value
            self._properties['extension'] = inst_extension
        
    @property
    def get_inst_name(self):
        """
        Get its name.

        Returns
        -------
        str
            instrument name.

        """
        return self._inst_name

    @property
    def get_inst_address(self):
        """
        Get its address.

        Returns
        -------
        str
            instrument address.

        """
        return self._inst_address

    @property
    def get_timeout(self):
        """
        Get its timeout.

        Returns
        -------
        TYPE
            instrument timeout.

        """
        return self._timeout

    @property
    def get_properties(self):
        """
        Get its properties.

        Returns
        -------
        str
            instrument properties.

        """
        return self._properties
    
    def connect(self):
        """
        Establish connection between PC and instrument.

        Returns
        -------
        None.

        """
        try:
            
            interface = self._properties['interface']
            insts = self.__class__.DEVICES
            if interface not in insts.keys():
                insts[interface] = []

            if self._inst_in_devices(self._properties):
                print('The instrument has existing in Instrument.DEVICES!')
                return
            else:
                self.__class__.DEVICES[interface].append(self)
                
            self.inst = self.__class__.RM.open_resource(
                self._properties['address'])
            self._properties['inst_connect'] = True
            self.inst.read_termination = self._properties['r_terminate']
            self.inst.write_termination = self._properties['w_terminate']
            self.inst._timeout = self._properties['timeout']
            connect_msg = f'Connect Instrument:\n' +\
                          f'instrument: {self._inst_name}\n' +\
                          f'statement: {self.query("*IDN?")}'
            print(connect_msg)
        except pyvisa.VisaIOError:
            print(f'Check "{self._inst_name}" has plugin your PC')
    
    def _inst_in_devices(self, properties: dict):        
        DEVICES = self.__class__.DEVICES[properties['interface']]
        if properties in DEVICES:
            return True
        return False
    
    def is_connect(self):
        """
        

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return self._properties['inst_connect']
    
    def err_connect(self):
        """
        

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        """
        err_msg = f'Oops, we detect the connection problem of'+\
             f'"{self.get_inst_name}" is due to be turned off.' +\
             f'Thus, reconnecting may solve this problem.'
        raise Exception(err_msg)
        
    def disconnect(self):
        """
        Terminate connection between PC and instrument.

        Returns
        -------
        None.

        """
        # self.inst_properties['inst_obj'] = None
        self.inst.close()
        del self.__class__.DEVICES[self._inst_name]
        print(f'{self._inst_name} has been disconnected by user.')

    def write(self, write_command: str):
        """
        Write the specific command to instrument.

        Parameters
        ----------
        write_command : str
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self.is_connect():
            self.inst.write(write_command)
        else:
            self.err_connect()

    def query(self, read_command: str):
        """
        Get the status of the instrument via giving a command to it. 

        Parameters
        ----------
        read_command : str
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        if self.is_connect():
            return self.inst.query(read_command)
        else:
            self.err_connect()

    def reset(self):
        """
        Reset instrument to factory setting. **Caution** This will disconnect
        instrument from PC and render the instrument unaccessable.

        Returns
        -------
        None.

        """
        sleep(1)
        self.write('*RST')
        sleep(1)

    def save_inst_cfg(self):
        """
        Save the current instrument config to the specific directory.

        Returns
        -------
        None.

        """
        
        from instruments.gui.popup import popup_file_dialog
        fpath = popup_file_dialog(
            'w',
             f'Save {self.__class__.__name__} properties as json file.')
        configIO(fpath, 'w', self._properties)

    @staticmethod
    def load_inst_cfg():
        """
        Load the previous instrument config to the corresponding properties.

        Returns
        -------
        None.

        """

        from instruments.gui.popup import popup_file_dialog
        fpath = popup_file_dialog(
            'r',
            'Open the corresponding config to replace the default properties.'        
             )
        properties = configIO(fpath, 'r')
        return properties
        # self._properties = configIO(fpath, 'r')

    @classmethod
    def list_inst_address(cls):
        """
        List all address of the instruments connected to PC.

        Parameters
        ----------
        cls : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        found_inst_addr_msg = f'Instrument address found:\n' +\
            f'{cls.RM.list_resources()}'
        print(found_inst_addr_msg)


if __name__ == '__main__':
    pass
    # yokoGS = Instrument('YokoDC', 'USB0::0x0B21::0x0039::91WB18861::INSTR')
    # yokoGS.connect()

    # yokoGS = Instrument()
    # yokoGS.load_inst_cfg()
