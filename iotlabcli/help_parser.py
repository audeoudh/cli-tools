# -*- coding:utf-8 -*-
"""Help parser messages"""


AUTH_PARSER = """

auth-cli command-line store your credentials.
It creates a file .iotlabrc in your home directory
with username and password options.

"""

NODE_PARSER = """

node-cli command-line manage interaction on resources.
You can launch commands on your experiment's resources.

"""

EXPERIMENT_PARSER = """

experiment-cli command-line manage experiments on testbed.

"""

PROFILE_PARSER = """

profile-cli command-line manage profiles experimentation :
store you favourite resources configuration with combination
of a power supply mode and an automatic measure configuration
(e.g. consumption, radio, ...)

"""


PARSER_EPILOG = """

Authentication :
    * username without any password option : use username option with password prompt
        $ %(cli)s-cli -u login %(option)s ...
    * username and password option : use credentials options
        $ %(cli)s-cli -u login -p password  %(option)s ...
    * without username nor password options : try to use credentials file (e.g. auth-cli command-line) or anonymous request
        $ %(cli)s-cli %(option)s ...
"""

SUBMIT_EPILOG = """

Examples:
    * physical experiment list : site_name,archi,resourceid_list,firmware_path,profile_name
        $ experiment-cli submit -d 20 -l grenoble,m3,1-20,/home/cc1101.hex -l rocquencourt,a8,1-5,,battery
        $ experiment-cli submit -d 20 -l grenoble,wsn430,1-5+8+9-11,cc1101.hex,battery
        $ experiment-cli submit -d 20 -l grenoble,m3,1-20

    * alias experiment list : resources_number,properties,firmware_path,profile_name
        $ experiment-cli submit -d 20 -l 9,archi=wsn430:cc1101+site=grenoble,tp.hex,battery
        $ experiment-cli submit -d 20 -l 9,archi=m3:at86rf231+site=grenoble,gre.elf \\
                                      -l 5,archi=m3:at86rf231+site=strasbourg,stras.elf
"""

LOAD_EPILOG = """

Examples:
    * load experiment :
        $ experiment-cli load -f 192.json
        Note : by default firmwares are searched in the current directory
    * load experiment with firmware list and explicit path:
        $ experiment-cli load -f 192.json -l /home/cc2420.hex,../cc1101.hex
    * reload an experiment :
        $ experiment-cli get -i 192 -a
        $ tar -xzvf 192.tar.gz
        $ cd 192
        $ experiment-cli load -f 192.json
"""

GET_EPILOG = """

Examples:
    * Get an experiment submission
        $ experiment-cli get -e
        Note : with one experiment in the state Running
    * Get an experiment archive with id 1637
        $ experiment-cli get -i 1637 -a
    * Get exeriment resources list with id 1637
        $ experiment-cli get -i 1637 -r
    * Get user's experiment list with filter by state and number
        $ experiment-cli get -l --state Running,Terminated --offset 10 --limit 20
"""


INFO_EPILOG = """

Examples:
    * Get resources description list with filter by site
        $ expriment-cli info -l --site grenoble
    * Get resources id list (e.g. 1-34+72)
        $ experiment-cli info -li

"""


ADD_EPILOG = """

Examples :
    * Add a profile for wsn430 archi and consumption measure configuration
        $ profile-cli addwsn430 -n profile -current -voltage -power -cfreq 5000
    * Add a profile for m3 archi with battery power supply and only voltage consumption
        measure configuration
        $ profile-cli addm3 -n profile -p battery -voltage -period 8244 -avg 1024

"""


COMMAND_EPILOG = """

Examples:
    * update firmware on all experiment resources
        $ node-cli --update /home/tp.hex
        Note : with one experiment in the state Running
    * Launch command stop on experiment resources list
        $ node-cli --sto -l grenoble,m3,1-5+10+12
    * update firmware on all experiment resources except two
        $ node-cli --update /home/tp.hex -e grenoble,m3,1-2
    * commmand list : site_name,archi,nodeid_list
        $ node-cli --reset -l grenoble,wsn430,1-34+72
    * command with several experiments with state Running
        $ node-cli -i <expid> --reset

"""
