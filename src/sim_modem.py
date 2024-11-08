from serial_comm import SerialComm
from enum import Enum
from logging import getLogger
import time
import json
import importlib.resources
import res # to get /res directory content

#TODO add __enter__ and __exit__ method to be able to use with Modem('/dev/tty..') as modem: do...

class NetworkMode(Enum):
    """Network mode of the modem (get/set)"""

    AUTOMATIC = 2
    GSM_ONLY = 13
    LTE_ONLY = 38
    ANY_BUT_LTE = 48

class CurNetworkMode(Enum):
    """Current Network mode of the modem (get)"""

    NO_SERVICE = 0
    GSM = 1
    GPRS = 2
    EDGE = 3
    WCDMDA = 4
    HSDPA = 5
    HSUPA = 6
    HSPA = 7
    LTE = 8

class SignalQuality(Enum):
    """Signal quality expressed as ranges"""

    LOW = "LOW"
    FAIR = "FAIR"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"
    UNDETECTABLE = "NOT DETECTABLE"
    UNKNOWN = "UNKNOWN"

class DataMode(Enum):
    """ Current data mode (usbnetmode) (get/set)"""

    RNDIS = '0'
    ECM = '1'

class Modem:
    """Class for interfacing with mobile modem"""

    def __init__(
        self,
        address,
        baudrate=460800,
        timeout=5,
        at_cmd_delay=0.1,
        debug=False,
    ):
        self.comm = SerialComm(
            address=address,
            baudrate=baudrate,
            timeout=timeout,
            at_cmd_delay=at_cmd_delay,
        )
        self.debug = debug
        self.oper_list = self.load_oper_list()
        self.comm.send("ATZ")
        self.comm.send("ATE1")
        read = self.comm.read_lines()
        # ['ATZ', 'OK', 'ATE1', 'OK']
        # ['ATZ', 'OK', 'ATE1', 'OK', '', '+CGEV: ME PDN DEACT 1'] <= When the modem have problem to connect
        try:
            ate1_rtn_idx = read.index('ATE1')
            ok_rtn_idx = ate1_rtn_idx + 1
            if read[ok_rtn_idx] != "OK":
                raise Exception("Modem do not respond", read)
            if self.debug:
                print("Modem connected, debug mode enabled")
        except (Exception, ValueError, IndexError):
            raise Exception("Modem do not respond", read)


    def reconnect(self) -> None:
        try:
            self.comm.close()
        except:
            pass

        self.comm = SerialComm(
            address=self.comm.modem_serial.port,
            baudrate=self.comm.modem_serial.baudrate,
            timeout=self.comm.modem_serial.timeout,
            at_cmd_delay=self.comm.at_cmd_delay,
        )

        self.comm.send("ATZ")
        self.comm.send("ATE1")
        read = self.comm.read_until()
        # ['ATZ', 'OK', 'ATE1', 'OK']
        # ['ATZ', 'OK', 'ATE1', 'OK', '', '+CGEV: ME PDN DEACT 1'] <= When the modem have problem to connect
        try:
            ate1_rtn_idx = read.index('ATE1')
            ok_rtn_idx = ate1_rtn_idx + 1
            if read[ok_rtn_idx] != "OK":
                raise Exception("Connection lost", read)
            if self.debug:
                print("Modem connected, debug mode enabled")
        except (Exception, ValueError, IndexError):
            raise Exception("Modem do not respond", read)

    def close(self) -> None:
        self.comm.close()

    def load_oper_list(self):
        with importlib.resources.open_text(res, "mcc-mnc-list.json") as file:
            data = json.load(file)
        return data
        #keep an eye on this https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package

    # --------------------------------- HARDWARE --------------------------------- #

    def get_manufacturer_identification(self) -> str:
        if self.debug:
            self.comm.send("AT+CGMI=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGMI")

        self.comm.send("AT+CGMI")
        read = self.comm.read_until()

        if self.debug:
            print("Device responded: ", read)
        # ['AT+CGMI', 'SIMCOM INCORPORATED', '', 'OK']

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def get_model_identification(self) -> str:
        if self.debug:
            self.comm.send("AT+CGMM=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGMM")

        self.comm.send("AT+CGMM")
        read = self.comm.read_until()

        # ['AT+CGMM', 'SIM7000E', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def get_serial_number(self) -> str:
        if self.debug:
            self.comm.send("AT+CGSN=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGSN")

        self.comm.send("AT+CGSN")
        read = self.comm.read_until()

        # ['AT+CGSN', '89014103211118510700', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def get_firmware_version(self) -> str:
        if self.debug:
            self.comm.send("AT+CGMR=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGMR")

        self.comm.send("AT+CGMR")
        read = self.comm.read_until()

        # ['AT+CGMR', '+CGMR: LE20B03SIM7600M22', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def get_volume(self) -> str:
        if self.debug:
            self.comm.send("AT+CLVL=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CLVL")

        self.comm.send("AT+CLVL?")
        read = self.comm.read_until()

        # ['AT+CLVL?', '+CLVL: 5', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def set_volume(self, volume: int) -> str:
        if self.debug:
            self.comm.send("AT+CLVL=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CLVL={}".format(volume))

        if int(volume) < 0 or int(volume) > 5:
            raise Exception("Volume must be between 0 and 5")
        self.comm.send("AT+CLVL={}".format(volume))
        read = self.comm.read_until()

        # ['AT+CLVL=5', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def improve_tdd(self) -> str:
        if self.debug:
            self.comm.send("AT+AT+PWRCTL=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+AT+PWRCTL=0,1,3")

        # ['AT+AT+PWRCTL=?', '+PWRCTL: (0-1),(0-1),(0-3)', '', 'OK']
        self.comm.send("AT+PWRCTL=0,1,3")
        read = self.comm.read_until()

        # ['AT+PWRCTL=0,1,3', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def reset_module(self) -> str:
        self.comm.send("AT+CRESET")
        read = self.comm.read_until()
        # ['AT+CRESET', 'OK']
        if read[-1] != "OK":
            raise Exception("Command failed")
        print("Connection lost")
        exit()

    def enable_echo_suppression(self) -> str:
        if self.debug:
            self.comm.send("AT+CECM=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CECM=1")

        self.comm.send("AT+CECM=1")
        read = self.comm.read_until()

        # ['AT+CECM=1', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def disable_echo_suppression(self) -> str:
        if self.debug:
            self.comm.send("AT+CECM=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CECM=0")

        self.comm.send("AT+CECM=0")
        read = self.comm.read_until()

        # ['AT+CECM=0', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def get_temperature(self) -> str:
        """
            Get the modem temperature, in C°
        """
        if self.debug:
            self.comm.send("AT+CPMUTEMP=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CPMUTEMP")

        self.comm.send("AT+CPMUTEMP")
        read = self.comm.read_until()

        # ['AT+CPMUTEMP', '+CPMUTEMP: 28', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def get_autodial_mode(self) -> str:
        """
            Get the current autodial mode, also known as usbnet network
            0 : disabled, usbnet network enabled
            1 : enabled, usbnet network disabled
        """
        if self.debug:
            self.comm.send("AT+DIALMODE=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+DIALMODE?")
        
        self.comm.send("AT+DIALMODE?")
        read = self.comm.read_until()

        # ['AT+DIALMODE?', '+DIALMODE: 0', '', 'OK']
        if self.debug:
            print("Device responded: ", read)
        
        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def set_autodial_mode(self, dialmode) -> str:
        """
            Set the autodial mode
            0 : disabled, usbnet network enabled
            1 : enabled, usbnet network disabled
        """
        if self.debug:
            self.comm.send("AT+DIALMODE=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+DIALMODE={}".format(dialmode))
        
        self.comm.send("AT+DIALMODE={}".format(dialmode))
        read = self.comm.read_until()

        # ['AT+DIALMODE=0', 'OK']
        if self.debug:
            print("Device responded: ", read)
        
        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[-1]

    def get_usbnetip_mode(self) -> str:
        """
            Get the Ip address mode
            0: private
            1: public
        """
        if self.debug:
            self.comm.send("AT+USBNETIP=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+USBNETIP?")
        
        self.comm.send("AT+USBNETIP?")
        read = self.comm.read_until()

        # ['AT+USBNETIP?', '+USBNETIP: 1', 'OK']
        if self.debug:
            print("Device responded: ", read)
        
        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def set_usbnetip_mode(self, ipmode) -> str:
        """
            Set the Ip address mode
            0: private
            1: public
        """
        if self.debug:
            self.comm.send("AT+USBNETIP=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+USBNETIP={}".format(ipmode))
        
        self.comm.send("AT+USBNETIP={}".format(ipmode))
        read = self.comm.read_until()

        # ['AT+USBNETIP=0', 'OK']
        if self.debug:
            print("Device responded: ", read)
        
        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[-1]

    # ---------------------------------- NETWORK --------------------------------- #

    def get_network_registration_status(self) -> str:
        if self.debug:
            self.comm.send("AT+CREG=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CREG?")

        self.comm.send("AT+CREG?")
        read = self.comm.read_until()

        # ['AT+CREG?', '+CREG: 0,1', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def get_eps_network_registration_status(self) -> str:
        """
            Get the eps (lte) network registration status (packet domain).
            The second value is the answer and could be from 0 to 8 :
            0 : not registered and not currently searching an operator to register to
            1 : registered
            2 : not registered but trying to
            3 : registration denied
            4 : n/a
            5 : registered (roaming)
            6 : registered for SMS only
            7 : registered for SMS only (roaming)
            8 : attached for emergency services only
            
        """
        if self.debug:
            self.comm.send("AT+CEREG=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CEREG?")

        self.comm.send("AT+CEREG?")
        read = self.comm.read_until()

        # ['AT+CEREG?', '+CEREG: 0,1', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def get_network_mode(self) -> NetworkMode:
        if self.debug:
            self.comm.send("AT+CNMP=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CNMP?")

        self.comm.send("AT+CNMP?")
        read = self.comm.read_until()

        # ['AT+CNMP?', '+CNMP: 2', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        nm = read[1].split(": ")[1]

        return NetworkMode(int(nm))

    def get_current_network_mode(self) -> CurNetworkMode:
        """
            Get the current network mode used by the modem
            GMS, GPRS, EDGE, LTE, ....
            :return: Current Network mode
            :rtype: CurNetworkMode
        """
        if self.debug:
            try:
                self.comm.send("AT+CNSMOD=?")
                read = self.comm.read_until()
                if read[-1] != "OK":
                    raise SyntaxError()
            except (IndexError, SyntaxError):
                print("DEBUG Unsupported command : ", read)
                return
            print("DEBUG Sending: AT+CNSMOD?")

        self.comm.send('AT+CNSMOD?')
        read = self.comm.read_until()
        
        # ['AT+CNSMOD?', '+CNSMOD: 0,8', '', 'OK']
        if self.debug:
            print("DEBUG Device responded: ", read)
        
        if read[-1] != "OK":
            raise Exception("Command failed")
        nm = read[1].split(": ")[1].split(",")[1]
        return CurNetworkMode(int(nm))

    def get_network_name(self) -> str:
        if self.debug:
            #self.comm.send("AT+COPS=?")
            #read = self.comm.read_until()
            #if read[-1] != "OK":
            #    raise Exception("Unsupported command")
            print("no debug available, answer to AT+COPS=? is too slow")
            print("Sending: AT+COPS?")

        self.comm.send("AT+COPS?")
        read = self.comm.read_until()

        # ['AT+COPS?', '+COPS: 0,0,"Vodafone D2",7', '', 'OK']
        # ['AT+COPS?', '+COPS: 0,2,"20801",7', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(",")[2].strip('"')

    def get_network_operator(self) -> str:
        if self.debug:
            #self.comm.send("AT+COPS=?")
            #read = self.comm.read_until()
            #if read[-1] != "OK":
            #    raise Exception("Unsupported command")
            print("no debug available, answer to AT+COPS=? is too slow")
            print("Sending: AT+COPS?")

        self.comm.send("AT+COPS?")
        read = self.comm.read_until()

        # ['AT+COPS?', '+COPS: 0,0,"Vodafone D2",7', '', 'OK']
        # ['AT+COPS?', '+COPS: 0,2,"20801",7', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        mode, format, operator, act = read[1].strip("+COPS: ").replace('"', '').split(",")
        if int(format) == 2:
            mcc = operator[:3]
            mnc = operator[3:]
            for mccmnc in self.oper_list:
                if mccmnc['mcc'] == mcc and mccmnc['mnc'] == mnc:
                    return mccmnc['brand'] or mccmnc['operator']
            return "Unknown"
        elif int(format) == 0:
            return read[1].split(",")[2].strip('"').split(" ")[0]
    
    def get_eu_system_informations(self) -> str:
        """
            Get European Union system informations
            return
                system mode, operation mode, MCC, MNC, band, ...
            todo : more details
        """
        if self.debug:
            try:
                self.comm.send("AT+CPSI=?")
                read = self.comm.read_until()
                if read[-1] != "OK":
                    raise SyntaxError()
            except (IndexError, SyntaxError):
                print("DEBUG Unsupported command : ", read)
                return
            print("DEBUG Sending: AT+CPSI?")

        self.comm.send("AT+CPSI?")
        read = self.comm.read_until()

        # ['AT+CPSI?', '+CPSI: LTE,Online,208-01,0x3601,14493697,393,EUTRAN-BAND7,3000,5,0,17,31,33,1', 'OK']

        if self.debug:
            print("DEBUG Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def get_signal_quality(self) -> str:
        if self.debug:
            try:
                self.comm.send("AT+CSQ=?")
                read = self.comm.read_until()
                if read[-1] != "OK":
                    raise SyntaxError()
            except (IndexError, SyntaxError):
                print("DEBUG Unsupported command : ", read)
                return
            print("DEBUG Sending: AT+CSQ")

        self.comm.send("AT+CSQ")
        read = self.comm.read_until()

        # ['AT+CSQ', '+CSQ: 19,99', '', 'OK']
        if self.debug:
            print("DEBUG Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def get_signal_quality_db(self) -> int:
        if self.debug:
            self.comm.send("AT+CSQ=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CSQ")

        self.comm.send("AT+CSQ")
        read = self.comm.read_until()

        # ['AT+CSQ', '+CSQ: 19,99', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        raw = read[1].split(": ")[1].split(",")[0]
        return -(111 - (2 * int(raw)))

    def get_signal_quality_range(self) -> SignalQuality:
        if self.debug:
            self.comm.send("AT+CSQ=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CSQ")

        self.comm.send("AT+CSQ")
        read = self.comm.read_until()

        # ['AT+CSQ', '+CSQ: 19,99', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        raw = read[1].split(": ")[1].split(",")[0]
        if int(raw) < 7:
            return SignalQuality.LOW
        elif int(raw) < 15:
            return SignalQuality.FAIR
        elif int(raw) < 20:
            return SignalQuality.GOOD
        elif int(raw) < 32:
            return SignalQuality.EXCELLENT
        elif int(raw) == 99:
            return SignalQuality.UNDETECTABLE
        else:
            return SignalQuality.UNKNOWN
    def get_phone_number(self) -> str:
        if self.debug:
            self.comm.send("AT+CNUM=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CNUM")

        self.comm.send("AT+CNUM")
        read = self.comm.read_until()

        # ['AT+CNUM', '+CNUM: ,"+491234567890",145', '', 'OK']
        # ['AT+CNUM', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK" or read[1] == "OK":
            raise Exception("Command failed")
        return read[1].split(",")[1].strip('"')

    def get_sim_status(self) -> str:
        if self.debug:
            self.comm.send("AT+CPIN=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CPIN?")

        self.comm.send("AT+CPIN?")
        read = self.comm.read_until()

        # ['AT+CPIN?', '+CPIN: READY', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        return read[1].split(": ")[1]

    def set_network_mode(self, mode: NetworkMode) -> str:
        self.comm.send("AT+CNMP={}".format(mode.value))
        read = self.comm.read_until()
        # ['AT+CNMP=2', 'OK']
        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def get_data_connection_mode(self) -> DataMode:
        """
            Get the current data connection mode.
            The result could be ECM or RNDIS
            :return: Current data mode
            :rtype: DataMode
        """
        if self.debug:
            self.comm.send("AT$MYCONFIG=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT$MYCONFIG?")
        
        self.comm.send("AT$MYCONFIG?")
        read = self.comm.read_until()

        # ['AT$MYCONFIG?', '$MYCONFIG: "usbnetmode",1', '', 'OK']
        # or, on newer model
        # ['AT$MYCONFIG?', '$MYCONFIG: "usbnetmode",1,1', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        nm = read[-2].split(": ")[1]
        nm = nm.split(",")[1]
        return DataMode(nm)

    def set_data_connection_mode(self, mode: DataMode) -> DataMode:
        """
            Set the data connection mode
            :param RNDIS or ECM
            :type DataMode
            :Example:

            modem.set_data_connection_mode(DataMode["ECM"])
        """

        if self.debug:
            self.comm.send("AT$MYCONFIG=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT$MYCONFIG={}".format("usbnetmode," + mode.value))
        
        self.comm.send("AT$MYCONFIG={}".format("usbnetmode," + mode.value))
        #When switching mode, the modem get detached. We have to close the connection or
        # the modem will get a new tty port upon reconnection.
        self.close()
        time.sleep(10)
        for i in range(5):
            try:
                self.reconnect()
                break
            except:
                print("Retrying...")
                time.sleep(5)
        time.sleep(5)
        self.comm.modem_serial.flushInput()
        #Yes it's a little hacky
        
        return self.get_data_connection_mode()
    
    def get_ip_address(self):
        """
            Get the public IP address
        """
        if self.debug:
            self.comm.send("AT+CGPADDR=?")
            read =self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGPADDR")

        self.comm.send("AT+CGPADDR")
        read =self.comm.read_until()

        if self.debug:
            print("Device responded: ", read)
        
        return read[1].split(": ")[1].split(",")[1]


    # ------------------------------------ GPS ----------------------------------- #

    def get_gps_status(self) -> str:
        if self.debug:
            self.comm.send("AT+CGPS=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGPS?")

        self.comm.send("AT+CGPS?")
        read = self.comm.read_until()

        # ['AT+CGPS?', '+CGPS: 0,1', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1].split(": ")[1]

    def start_gps(self) -> str:
        if self.debug:
            self.comm.send("AT+CGPS=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGPS=1,1")

        self.comm.send("AT+CGPS=1,1")
        read = self.comm.read_until()

        # ['AT+CGPS=1', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def stop_gps(self) -> str:
        if self.debug:
            self.comm.send("AT+CGPS=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGPS=0")

        self.comm.send("AT+CGPS=0")
        read = self.comm.read_lines()

        # ['AT+CGPS=0', 'OK', '', '+CGPS: 0']
        # ['AT+CGPS=0', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] == "+CGPS: 0" or read[-1] == "OK":
            raise Exception("Command failed")
        return read[1]

    def get_gps_coordinates(self) -> dict:
        if self.debug:
            self.comm.send("AT+CGPS=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CGPS=1,1")
            print("Sending: AT+CGPSINFO")

        self.comm.send("AT+CGPS=1,1")
        self.comm.send("AT+CGPSINFO")
        # self.comm.send("AT+CGPS=0")
        read = self.comm.read_until()

        # +CGPSINFO: [lat],[N/S],[log],[E/W],[date],[UTC time],[alt],[speed],[course]
        # ['AT+CGPS=1', 'OK', 'AT+CGPSINFO', '+CGPSINFO: 1831.991044,N,07352.807453,E,141008,112307.0,553.9,0.0,113', 'OK']
        # ['AT+CGPS=1', 'OK', 'AT+CGPSINFO', '+CGPSINFO: ,,,,,,,,', '', 'OK'] # if no gps signal
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return {
            "latitude": read[3].split(": ")[1].split(",")[0]
            + read[3].split(": ")[1].split(",")[1],
            "longitude": read[3].split(": ")[1].split(",")[2]
            + read[3].split(": ")[1].split(",")[3],
            "altitude": read[3].split(": ")[1].split(",")[6],
            "speed": read[3].split(": ")[1].split(",")[7],
            "course": read[3].split(": ")[1].split(",")[8],
        }

    # ------------------------------------ SMS ----------------------------------- #

    def get_sms_list(self) -> list:
        if self.debug:
            self.comm.send("AT+CMGF=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CMGF=1")
            print('Sending: AT+CMGL="ALL"')

        self.comm.send("AT+CMGF=1")
        self.comm.send('AT+CMGL="ALL"')

        read = self.comm.read_lines()
        sms_lines = [x for x in read if x != ""]  # remove empty lines
        sms_lines = sms_lines[5 : len(sms_lines) - 1]  # remove command and OK
        tuple_list = [
            tuple(sms_lines[i : i + 2]) for i in range(0, len(sms_lines), 2)
        ]  # group sms info with message

        sms_list = []
        for i in tuple_list:
            sms_list.append(
                {
                    "index": i[0].split(":")[1].split(",")[0].strip(),
                    "number": i[0].split('READ","')[1].split('","","')[0],
                    "date": i[0].split('","","')[1].split(",")[0],
                    "time": i[0].split(",")[5].split("+")[0],
                    "message": i[1].replace("\r\n", "").strip(),
                }
            )

        # ['AT+CMGL="ALL"', '+CMGL: 1,"REC READ","+491234567890",,"12/08/14,14:01:06+32"', 'Test', '', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return sms_list

    def empty_sms(self) -> str:
        if self.debug:
            self.comm.send("AT+CMGF=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CMGF=1")
            print("Sending: AT+CMGD=1,4")

        self.comm.send("AT+CMGF=1")
        self.comm.send("AT+CMGD=1,4")
        read = self.comm.read_until()

        # ['AT+CMGF=1', 'OK', 'AT+CMGD=1,4', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")

    def send_sms(self, recipient, message) -> str:
        if self.debug:
            self.comm.send("AT+CMGF=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CMGF=1")
            print('Sending: AT+CMGS="{}"'.format(recipient))
            print("Sending: {}".format(message))
            print("Sending: {}".format(chr(26)))

        self.comm.send("AT+CMGF=1")
        self.comm.send('AT+CMGS="{}"'.format(recipient))
        self.comm.send(message)
        self.comm.send(chr(26))
        read = self.comm.read_until()

        # ['AT+CMGF=1', 'OK', 'AT+CMGS="491234567890"', '', '> Test', chr(26), 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[4]

    def get_sms(self, slot) -> dict:
        if self.debug:
            self.comm.send("AT+CMGF=?")
            self.comm.send("AT+CMGR=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CMGF=1")
            print("Sending: AT+CMGR={}".format(slot))

        self.comm.send("AT+CMGF=1")
        self.comm.send("AT+CMGR={}".format(slot))
        read = self.comm.read_until()

        # ['AT+CMGF=1', 'OK', 'AT+CMGR=1', '+CMGR: "REC READ","+491234567890",,"12/08/14,14:01:06+32"', 'Test', '', 'OK']
        # ['AT+CMGF=1', 'OK'] # if empty
        if self.debug:
            print("Device responded: ", read)

        if len(read) < 3 or read[-1] != "OK":
            raise Exception("Command failed")
        return {
            "slot": read[1].split(":")[1].split(",")[0].strip(),
            "number": read[1].split('READ","')[1].split('","","')[0],
            "date": read[1].split('","","')[1].split(",")[0],
            "time": read[1].split(",")[5].split("+")[0],
            "message": read[4].replace("\r\n", "").strip(),
        }

    def delete_sms(self, slot: int) -> str:
        if self.debug:
            self.comm.send("AT+CMGF=?")
            read = self.comm.read_until()
            if read[-1] != "OK":
                raise Exception("Unsupported command")
            print("Sending: AT+CMGF=1")
            print("Sending: AT+CMGD={}".format(slot))

        self.comm.send("AT+CMGF=1")
        self.comm.send("AT+CMGD={}".format(slot))
        read = self.comm.read_until()

        # ['AT+CMGF=1', 'OK', 'AT+CMGD=1', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    # ----------------------------------- CALLS ---------------------------------- #

    def call(self, number: str) -> str:
        if self.debug:
            print("Sending: ATD{};".format(number))

        self.comm.send("ATD{};".format(number))
        read = self.comm.read_until()

        # ['ATD491234567890;', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def answer(self) -> str:
        if self.debug:
            print("Sending: ATA")

        self.comm.send("ATA")
        read = self.comm.read_until()

        # ['ATA', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    def hangup(self) -> str:
        if self.debug:
            print("Sending: AT+CHUP")

        self.comm.send("AT+CHUP")
        read = self.comm.read_until()

        # ['AT+CHUP', 'OK']
        if self.debug:
            print("Device responded: ", read)

        if read[-1] != "OK":
            raise Exception("Command failed")
        return read[1]

    # ----------------------------------- OTHERS --------------------------------- #

    def custom_read_lines(self, at_cmd) -> str:
        self.comm.send(at_cmd)
        read = self.comm.read_lines()
        return read

    def custom(self, at_cmd) -> str:
        self.comm.send(at_cmd)
        read = self.comm.read_until()
        return read
