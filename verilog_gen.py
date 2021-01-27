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
import math

class RTL_GENERATOR():
    def __init__(self):
        self.__state_dict = None
        self.__output_file = None
        self.__output_str = ""
        self.__module_name = ""
        self.__interface_dict = None
        self.__state_width = 0
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
        tmp_str += "\tinput                                           clk,\n"
        tmp_str += "\tinput                                           rstn,\n"
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
                    if_name = "%s_%s"%(module_name,if_name)
                    if_name = "{:<20}".format(if_name)
                    tmp_str += "\t%s\t%s\t%s,\t// %s\n"%(io_str, width_str,if_name,if_attr["comment"])
        tmp_str += ");\n"
        return tmp_str

    def build_next_output(self):
        tmp_str = ""
        width_str = "[P_ST_WIDTH-1:0]"
        width_str = "{:<24}".format(width_str)
        tmp_str += "\treg\t%s\tnxt_state;\n" %(width_str)
        tmp_str += "\treg\t%s\tcur_state;\n" %(width_str)
        for module_name, items in self.__interface_dict.items():
            for if_name, if_attr in items["interface"].items():
                if(if_attr["io"] == "output"):
                    io_str = "reg"
                    if(if_attr["width"] == "1"):
                        width_str = ""
                    elif(if_attr["width"].isnumeric()):
                        width_str = "[%d:0]"%( int(if_attr["width"])-1) 
                    else:
                        width_str = "[%s-1:0]"%(if_attr["width"])
                    width_str = "{:<24}".format(width_str)
                    next_out_str = "nxt_%s_%s"%(module_name,if_name)
                    tmp_str += "\t%s\t%s\t%s;\n"%(io_str, width_str,next_out_str)
        return tmp_str
    def build_state_names(self,state_dict):
        tmp_str = ""
        state_index = 0
        for state_group,state_list in state_dict.items():
            for cur_state, cur_state_attr in state_list.items():
                state_index += 1
        state_width = math.ceil(math.log(state_index,2))
        self.__state_width = state_width
        tmp_str += "\tlocalparam\tP_ST_WIDTH = %d;\n"%(state_width)
        state_index = 0        
        for state_group,state_list in state_dict.items():
            for cur_state, cur_state_attr in state_list.items():
                cur_state = "P_ST_%s"%(cur_state)
                cur_state = "{:<40}".format(cur_state)
                tmp_str += "\tlocalparam\t%s = %d'd%d;\n"%(cur_state,state_width,state_index)
                state_index += 1
        return tmp_str
    def build_state_trans(self,state_dict):
        tmp_str = "always@(*) begin\n"
        tmp_str += "\tcur_state = %s;\n"%("P_ST_stIDLE") #[TODO] assign IDLE state
        tmp_str += "\tcase(cur_state):\n"
        for state_group,state_list in state_dict.items():
            for cur_state, cur_state_attr in state_list.items():
                tmp_str += "\t\t%s:begin\n"%cur_state
                for next_state in cur_state_attr["next_state"]:
                    if(cur_state_attr["next_state"]):
                        index = cur_state_attr["next_state"].index(next_state)
                        tmp_str += "\t\t\tif(%s)\n"%(cur_state_attr["affector"][index])

                tmp_str += "\t\tend\n"
        tmp_str += "\tendcase\n"
        tmp_str += "end\n"
        return tmp_str
    def import_interface(self,filename):
        #import json
        file_ptr = open(filename, "r")
        interface_dict = json.load(file_ptr)
        # print(interface_dict)
        # for module_group, items in interface_dict.items():
        #     print(module_group)
        #     print(items["interface"])
        self.__interface_dict = interface_dict
