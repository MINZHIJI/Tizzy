"""
Reads in a Graphviz .dot file and generates a Verilog state machine based
on some simple rules.

1) Format the dot file to ...
    1. Remove the comment (Single line and Multi lines)
2) Sort the state types
    1. Create the type list
    2. ...
"""

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


def comment_replacer(match):
    """
    Function Name: comment_replacer
    Function Description:
        Remove comment in file
    """
    start, mid, end = match.group(1, 2, 3)
    if mid is None:
        # single line comment
        # return '' # remove single line
        return match.group(0)  # remain single line
    elif start is not None or end is not None:
        # multi line comment at start or end of a line
        return ''
    elif '\n' in mid:
        # multi line comment with line break
        return '\n'
    else:
        # multi line comment without line break
        return ' '


class Format_Dot_File():
    """
    Class Name: Format_Dot_File
    Class Description:
        Pre-processing dot file to convenient to parser.
    """

    def __init__(self):
        self.__source_dotfile = None
        self.__del_cmt_re = None
        self.__target_dotfile = None

    def Del_Comment(self, filename):
        f = open(filename, 'r')
        self.__source_dotfile = f.read()
        f.close()

        self.__del_cmt_re = re.compile(
            r'(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
            re.DOTALL | re.MULTILINE
        )

        self.__target_dotfile = self.__del_cmt_re.sub(
            comment_replacer, self.__source_dotfile)
        return self.__target_dotfile

class Report_Dot_File():
    """
    Class Name: Report_Dot_File
    Class Description:
        Paser dot file and build state list.
    """

    def __init__(self):
        self.__file_dict = {}
        self.logger = logging.getLogger("Report_Dot_File")

    # Function: Collect state as dict
    def build_state_list_mapping_table(self, file_ptr):
        """
        Format:
        // STATE_START <STATE_TYPE>
        <STATE_NAME>
        ...
        // STATE_END
        Example:
        // STATE_START RAM_DU
        RAM_Get_Test_Value
        RAM_Set_Test_Value
        // STATE_END
        Description:
        State_Collector will create RAM_DU list and record
        the item in this group
        """
        print("Enter State_Collector")

        re_state_start = re.compile(r'([ \t]*//[ \t]*STATE_START[ \t]*(\w+))')
        re_state_end = re.compile(r'([ \t]*//[ \t]*STATE_END*)')
        re_state_name = re.compile(r'^(\w+)\s*(.*)')
        file = file_ptr.split('\n')
        Declare_Flag = False
        state_dict = {}

        for line in file:
            m = re_state_start.search(line)
            if(m is not None):
                group_name = m.group(2)
                Declare_Flag = True
                if group_name not in state_dict:
                    state_dict[group_name] = {}
                continue
            m = re_state_end.search(line)
            if(m is not None):
                Declare_Flag = False
                continue
            if(Declare_Flag):
                if group_name in state_dict:
                    state_name = re_state_name.search(line)
                    if (state_name is not None):
                        name = state_name.group(1)
                        state_dict[group_name][name] = {}
        self.__file_dict = state_dict
        return state_dict

    def print_state_dict(self, dict):
        for state_group,state_list in dict.items():
            print("[%s]" % state_group)
            for cur_state, next_state_list in state_list.items():
                for nxt_state, st_affector  in next_state_list.items():
                    print("    %s -> %s [condition: %s]" %(cur_state, nxt_state, st_affector))
            print("------")

    def build_affector_list(self, dict, file_ptr):
        re_states = re.compile(r'^\s*(\w+)\s*->\s*(\w+)')
        re_affectors = re.compile(r'\[\s*label\s*=\s*\"(.*)\"\s*\]')
        file = file_ptr.split('\n')
        for line in file:
            st = None
            index = file.index(line) + 1
            # Find States and Next States
            m_state = re_states.search(line)
            if(m_state is not None):
                state = m_state.group(1)
                next_state = m_state.group(2)
                m_affector = re_affectors.search(line)
                f_not_exist = False
                f_done = False
                for state_group,cur_state_list in dict.items():
                    if (f_done): # if line is already will go True
                        continue
                    if state not in cur_state_list:
                        f_not_exist = True
                        continue
                    else:
                        f_not_exist = False
                    
                    if next_state in dict[state_group][state]:
                        self.logger.error("line %d: %s \n [Error] next state is duplicate in dictionary"%(index,line))
                        exit()   
                    else:
                        dict[state_group][state][next_state] = "" 
              
                    # Find Transitions
                    if(m_affector is not None):
                        dict[state_group][state][next_state] = m_affector.group(1)
                        
                        affector = m_affector.group(1)
                        # Strip off ~ and ! etc.
                        affector_stripped = re.sub(
                            '[~|!()&^]', '', affector).split()
                        self.logger.debug("Stripped affectors: '%s'" %
                                        affector_stripped)
                    else:
                        affector = None
                    self.logger.debug("Adding transition: %s -> %s (%s)" %
                                    (state, next_state, affector))
                    f_done = True   # Finished fill next state and affector
                if (f_not_exist):
                    self.logger.error("line %d: %s \n [Error] state(%s) not in dictionary"%(index,line,state))
                    exit()
    
    def build_state_transition_list(self, dict, file_ptr):
        re_states = re.compile(r'^\s*(\w+)\s*->\s*(\w+)')
        re_affectors = re.compile(r'\[\s*label\s*=\s*\"(.*)\"\s*\]')
        file = file_ptr.split('\n')
        for line in file:
            st = None
            index = file.index(line) + 1
            # Find States and Next States
            m_state = re_states.search(line)
            if(m_state is not None):
                state = m_state.group(1)
                next_state = m_state.group(2)
                m_affector = re_affectors.search(line)
                f_not_exist = False
                f_done = False
                for state_group,cur_state_list in dict.items():
                    if (f_done): # if line is already will go True
                        continue
                    if state not in cur_state_list:
                        f_not_exist = True
                        continue
                    else:
                        f_not_exist = False
                    
                    if next_state in dict[state_group][state]:
                        self.logger.error("line %d: %s \n [Error] next state is duplicate in dictionary"%(index,line))
                        exit()   
                    else:
                        dict[state_group][state][next_state] = "" 
              
                    # Find Transitions
                    if(m_affector is not None):
                        dict[state_group][state][next_state] = m_affector.group(1)
                        
                        affector = m_affector.group(1)
                        # Strip off ~ and ! etc.
                        affector_stripped = re.sub(
                            '[~|!()&^]', '', affector).split()
                        self.logger.debug("Stripped affectors: '%s'" %
                                        affector_stripped)
                    else:
                        affector = None
                    self.logger.debug("Adding transition: %s -> %s (%s)" %
                                    (state, next_state, affector))
                    f_done = True   # Finished fill next state and affector
                if (f_not_exist):
                    self.logger.error("line %d: %s \n [Error] state(%s) not in dictionary"%(index,line,state))
                    exit()

    # Function: export state table to csv
    def export_state_table_csv(self, dict, output_name):
        # csv_string = "attribute, current state, next state, affector\n"
        csv_string = ""
        for state_group,state_list in dict.items():
            for cur_state, next_state_list in state_list.items():
                for nxt_state, st_affector  in next_state_list.items():
                    csv_string += "%s,%s,%s,%s\n" %(state_group,cur_state, nxt_state, st_affector)
        file = open(output_name, 'w')
        file.write(csv_string)
        file.close

    # Function: import csv as dictionary
    def import_csv_as_dict(self,input_file):
        file = open(input_file,'r')
        file_ptr = file.read().split('\n')
        file.close()
        state_dict = {}
        for line in file_ptr:
            entires = line.split(',')
            if(len(entires) >= 2): # Check entires more than 2 (group and cur_state)
                group_name = entires[0]
                cur_state_name = entires[1]
                next_state_name = entires[2]
                affector_name = entires[3]
                if(group_name not in state_dict):
                    state_dict[group_name] = {}
                if(cur_state_name not in state_dict[group_name]):
                    state_dict[group_name][cur_state_name]={}
                if(next_state_name not in state_dict[group_name][cur_state_name]):
                    state_dict[group_name][cur_state_name][next_state_name] = affector_name
        return state_dict
                
            

    # Function: export state table to dot
    def export_state_table_dot(self,dict,output_name):
        dot_string = "digraph output{\n"
        for state_group,state_list in dict.items():
            dot_string += "\t// STATE_START %s\n"%(state_group)
            for cur_state in state_list:
                dot_string += "\t\t%s\n"%(cur_state)
            dot_string += "\t// STATE_END\n"
        for state_group,state_list in dict.items():
            for cur_state, next_state_list in state_list.items():
                for nxt_state, st_affector  in next_state_list.items():
                    dot_string += "\t\t%s -> %s [label= \"%s\"]\n" %(cur_state, nxt_state, st_affector)  
        dot_string += "}"                    
        file = open(output_name, 'w')
        file.write(dot_string)
        file.close
    

    def search_nested_dict_key(dict):
        pass