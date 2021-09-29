 # 1. QEL_instruments structure
            QEL_instuments/
                ├── Insturments/
                    ├── __pycache__/
                        └── __init__.cpython-38.pyc
                    ├── Antrisu/
                        └── __init__.py                       
                    ├── Tektronix_AWG5208/
                        ├── __init__.py
                        ├── awg_Output.py
                        ├── awg_sequenceEdit_ver1.0.py
                        ├── awg_waveformEdit_ver1.3.py
                        ├── TektronixAWG_core.py
                        ├── TektronixAWG_sequenceEditor.py
                        └── TektronixAWG_waveformEditor.py
                    ├──YokoGS/
                        ├── __pycache__/
                            └── QEL_instrument.cpython-38.pyc
                        ├── __init__.py
                        ├── README_OperatingYokoGS.md
                        └── YokoGS.py
                    └── __init__.py
                ├── Utility
                    ├── __pycache__/
                        └── QEL_instrument.cpython-38.pyc
                    └── QEL_instrument.py
                ├── README_OperatingCode_YokoGS.md
                └── README_QEL_instruments_structure.md
    
# 2. How to activate this code?
            In this tutorial, We can follow the below description to work this script.

                1. Open Windows Terminal and change the current directory to the below address
   
                   For example, you can see this path by commanding "pwd" in Windows Terminal
                        PS C:\\Users\\QEL\\OneDrive - 清華大學\\桌面\\Labber開發\\NTHU_QEL_Python\\QEL\\QEL_instruments> pwd

                        Path
                        ----
                        C:\\Users\\QEL\\OneDrive - 清華大學\\桌面\\Labber開發\\NTHU_QEL_Python\\QEL\\QEL_instruments

                2. Execute the following command on Windows Terminal
   
                        python -m Instruments.YokoGS.YokoGS

                3. Finally, you can see the result.
                        Connect to YokoGS200 successfully
                        Statement: YOKOGAWA,GS210,91T810991,2.02

                        Start to do a mission called microwaveSwitch.
                        Processing.
                        Processing...
                        Processing.....
                        Finish a mission called microwaveSwitch.