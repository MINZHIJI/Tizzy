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
    start, mid, end = match.group(1, 2, 3)
    if mid is None:
        # single line comment
        return match.group(0)
    elif start is not None or end is not None:
        # multi line comment at start or end of a line
        return ''
    elif '\n' in mid:
        # multi line comment with line break
        return '\n'
    else:
        # multi line comment without line break
        return ' '

# TODO: Remove mutli-line comment
class Format_Dot_File():
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
        
        self.__target_dotfile = self.__del_cmt_re.sub(comment_replacer, self.__source_dotfile)
        return self.__target_dotfile


# TODO: Sort and create status groups
    
class Report_Dot_File():
    def __init__(self, filename):
        self.__source_dotfile = filename
        self.__collect_start_word = "STATE_START"
        self.__collect_end_word = "STATE_END"
    # SUB_TODO: Create the state csv
    def State_Collector(self):
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
        file = self.__source_dotfile.split('\n')
        Declare_Flag = False
        state_group = []
        state_list = []
        stat_dirt = {}
        state_list_index = 0
        # for line in file:
        #     m = re_state_start.search(line)
        #     if(m is not None):
        #         Declare_Flag = True
        #         state_group.append()
        #         state_list.append([])
        #         continue
        #     m = re_state_end.search(line)
        #     if(m is not None):
        #         Declare_Flag = False
        #         state_list_index = state_list_index + 1
        #         continue
        #     if(Declare_Flag):
        #         state_list[state_list_index].append(line)
        # for group in state_list:
        #     tmp_index = state_list.index(group)
        #     print("[%s]"%state_group[tmp_index])
        #     for entry in group:
        #         print (entry)
        #     print("------")
        for line in file:
            m = re_state_start.search(line)
            if(m is not None):
                group_name = m.group(2)
                Declare_Flag = True
                if group_name not in stat_dirt:
                    stat_dirt[group_name] = list()
                continue
            m = re_state_end.search(line)
            if(m is not None):
                Declare_Flag = False
                continue
            if(Declare_Flag):
                if group_name in stat_dirt:
                    stat_dirt[group_name].append(line)
        for state_group, state_list in stat_dirt.items():
            print("[%s]"%state_group)
            for entry in state_list:
                print (entry)
            print("------")