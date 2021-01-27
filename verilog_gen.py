import sys
import os
import re
import time
import logging
import string
from NullHandler import NullHandler
import help
from vlogTemplate import vlogTemplate
from incTemplate import incTemplate
import json

class RTL_GENERATOR():
    def __init__(self):
        self.__state_dict = None
        self.__output_file = None
        self.__output_str = ""
        self.__module_name = ""
        self.__interface_dict = None
        self.logger = logging.getLogger("RTL_GENERATOR")
    def rename(self, name):
        self.__module_name = name
    def build_initial_data(self):
        # assign module name to self
        pass
    def build_module_io_port(self):
        tmp_str = ""
        # add module name
        tmp_str += "module %s(\n" % (self.__module_name)
        # add IO ports
            # add underlying module interface
        for module_name, items in self.__interface_dict.items():
            
                for if_name, if_attr in items["interface"].items():
                    # print(if_name)
                    # print(if_attr)
                    if(if_attr["io"] == "output"):
                        io_str = "%s reg"%(if_attr["io"])
                    elif(if_attr["io"] == "input"):
                        io_str = "%s"%(if_attr["io"])
                    else:
                        self.logger.error("Exception: IO type error! @(%s of %s is %s)"%(if_name,module_name,if_attr["io"]))
                        exit()
                    io_str = "{:<10}".format(io_str)
                    if(if_attr["width"] == "1"):
                        width_str = ""
                    elif(if_attr["width"].isnumeric()):
                        width_str = "[%d:0]"%( int(if_attr["width"])-1) 
                    else:
                        width_str = "[%s-1:0]"%(if_attr["width"])                        
                    width_str = "{:<24}".format(width_str)
                    print("\t%s\t%s\t%s_%s"%(io_str, width_str,module_name,if_name))
        tmp_str += ");"

    def import_interface(self,filename):
        #import json
        file_ptr = open(filename, "r")
        interface_dict = json.load(file_ptr)
        # print(interface_dict)
        # for module_group, items in interface_dict.items():
        #     print(module_group)
        #     print(items["interface"])
        self.__interface_dict = interface_dict
