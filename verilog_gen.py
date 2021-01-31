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
    def __init__(self,state_dict,source_name):
        self.__state_dict = state_dict
        self.__output_file = None
        self.__output_str = ""
        self.__module_name = source_name
        self.__interface_file = ""
        self.__interface_dict = None
        self.__state_width = 0
        self.__state_num = 0
        self.logger = logging.getLogger("RTL_GENERATOR")
        self.__state_initial = ""
        self.__interface_params = []
        self.__state_flages = []
        self.__affector_list = []
    def rename(self, name):
        self.__module_name = name
    def build_initial_data(self):
        # assign module name to self
        pass
    def build_interface_param_declare(self):
        for module_name, items in self.__interface_dict.items():
            for signal_name, signal_attrs in items["interface"].items():
                if(not signal_attrs["width"].isnumeric()):
                    self.__interface_params.append(signal_attrs["width"])
    def build_module_io_port(self):
        tmp_str = ""
        # add module name
        self.build_interface_param_declare()
        if(self.__interface_params):
            tmp_str += "module %s #(\n" % (self.__module_name)
            for i in range(len(self.__interface_params)):
                if(i != (len(self.__interface_params) -1)):
                    tmp_str += "parameter %s = 0,\n" % (self.__interface_params[i])
                else:
                    tmp_str += "parameter %s = 0\n" % (self.__interface_params[i])
            tmp_str += ")(\n"
        else:
            tmp_str += "module %s (\n" % (self.__module_name)
        # add IO ports
        tmp_str += "\tinput                                           clk,\n"
        tmp_str += "\tinput                                           rstn,\n"
        tmp_str += "\t// Module Interface\n"
            # add underlying module interface
        group_index = 0
        end_line = False
        for module_name, items in self.__interface_dict.items():
            len_group_dict = len(self.__interface_dict)
            group_index += 1
            state_index = 0
            if(group_index == (len_group_dict-1)):
                end_line = True
            for if_name, if_attr in items["interface"].items():
                state_index += 1
                len_state_dict = len(items["interface"])
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
                # print("group_size:%d, group_index:%d, state_size:%d, state_index:%d"%(len_group_dict,group_index,len_state_dict,state_index))
                if(end_line and (len_state_dict == state_index)):
                    tmp_str += "\t%s\t%s\t%s \t// %s\n"%(io_str, width_str,if_name,if_attr["comment"])
                else:
                    tmp_str += "\t%s\t%s\t%s,\t// %s\n"%(io_str, width_str,if_name,if_attr["comment"])
        tmp_str += ");\n"
        return tmp_str
    def build_state_flag_declarations(self):
        tmp_str = "\t// Declare State Flag\n"
        if(self.__affector_list):
            for i in range(len(self.__affector_list)):
                tmp_str += "\treg\t%s;\n" % (self.__affector_list[i])
                tmp_str += "\treg\tnxt_%s;\n" % (self.__affector_list[i])
        else:
            pass
        return tmp_str
    def build_next_output(self):
        tmp_str = "\t// Add next output ports\n"
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
        tmp_str = "\t// Assign state variables\n"
        state_index = 0
        for state_group,state_list in state_dict.items():
            for cur_state, cur_state_attr in state_list.items():
                state_index += 1
        self.__state_num = state_index
        tmp_str += "\tlocalparam\tP_ST_WIDTH = %d;\n"%(state_index)
        state_index = 0        
        for state_group,state_list in state_dict.items():
            for cur_state, cur_state_attr in state_list.items():
                cur_state = "P_ST_%s"%(cur_state)
                cur_state = "{:<40}".format(cur_state)
                tmp_str += "\tlocalparam\t%s = 'd%d;\t// %s\n"%(cur_state,state_index,cur_state_attr["State_Comment"])
                state_index += 1
        return tmp_str
    def build_cur_state(self):
        cur_str = """
// [State Transitions] Flip-flop Logic
always @(posedge clk or negedge rstn) begin
    if(!rstn) begin
        cur_state <= `D %d'b0;
        cur_state[P_ST_%s] <= 1'b1;
    end
    else begin
        cur_state <= `D nxt_state;
    end
end
"""%(self.__state_num,self.__state_initial)
        return cur_str
    def build_state_trans(self,state_dict,state_num):
        str = "// [State Transitions] Combinational Logic\n"
        str += "always@(*) begin\n"
        str += "\tcur_state = %s;\n"%("P_ST_stIDLE") #[TODO] assign IDLE state
        str += "\tcase(1'b1)\n"
        for state_group,state_list in state_dict.items():
            for cur_state, cur_state_attr in state_list.items():
                final_trans = None
                first_trans = None
                other_trans = []
                str  += "        cur_state[P_ST_%s]:\n" % cur_state
                num_trans = len(cur_state_attr["next_state"])
                for i in range(num_trans):
                    # print("Cur State: %s Next state: %s, Affectors: %s"%(cur_state,cur_state_attr["next_state"][i],cur_state_attr["affector"][i]))

                    remaining = num_trans - i
                    trans = (cur_state_attr["next_state"][i],cur_state_attr["affector"][i])
                    self.logger.debug(remaining)
                    if(not trans[1]):
                        if(final_trans is None):
                            self.logger.debug("Final trans: %r %r" % (trans[0], trans[1]))
                            final_trans = trans
                        else:
                            pass
                            # raise MultipleDefaultTransitionsError('genNextStateLogicString', None, None)
                    else:
                        if(not first_trans):
                            self.logger.debug("First trans: %r %r" % (trans[0], trans[1]))
                            first_trans = trans
                        else:
                            self.logger.debug("Other trans: %r %r" % (trans[0], trans[1]))
                            other_trans.append(trans)
                # print(cur_state)
                # print("other_trans\t",other_trans)
                # print("first_trans\t",first_trans)
                # print("final_trans\t",final_trans)
                # print("=====")
                if(first_trans is not None):
                    str += "            if(%s)\n" % first_trans[1]
                    str += "                nxt_state[P_ST_%s] = 1'b1;\n" % first_trans[0]

                if(other_trans is not None):
                    for trans in other_trans:
                        str += "            else if(%s)\n" % trans[1]
                        str += "                nxt_state[P_ST_%s] = 1'b1;\n" % trans[0]

                if(final_trans is not None):
                    if(num_trans != 1):
                        str += "            else\n"
                    str += "                nxt_state[P_ST_%s] = 1'b1;\n\n" % final_trans[0]

        str += "        default:\n"
        str += "            nxt_state[P_ST_%s] = 1'b1;" % self.__state_initial
        # str += "            nxt_state[%d] = 1'b1;" % state_num
        str += "\n\tendcase\n"
        str += "end\n"
        return str

    def import_interface(self,filename):
        #import json
        self.import_interface = filename
        file_ptr = open(filename, "r")
        interface_dict = json.load(file_ptr)
        self.__interface_dict = interface_dict
    
    def build_affector_list(self,state_dict):
        affector_list = []
        for module,state_lists in state_dict.items():
            for cur_state,state_attrs in state_lists.items():
                for cur_affector_list in state_attrs["affector"]:
                    cur_affectors = re.sub('[~|!&^]','',cur_affector_list).split()
                    for cur_affector in cur_affectors:
                        if(cur_affector not in affector_list):
                            affector_list.append(cur_affector)
        # print(affector_list)
        self.__affector_list = affector_list
        return affector_list

    def check_initail_state(self):
        Check_Flag = False
        for state_group,state_list in self.__state_dict.items():
            if (self.__interface_dict["FSM"]["state_initial"] in state_list):
                Check_Flag = True
                break
        if(Check_Flag):
            self.__state_initial = self.__interface_dict["FSM"]["state_initial"]
            return self.__state_initial
        else:
            self.logger.error("Exception: Interface JSON(%s) Initial state(%s) not in state dict"%(self.import_interface,self.__interface_dict["FSM"]["state_initial"]))
            exit()