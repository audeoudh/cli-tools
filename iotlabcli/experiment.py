# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB cli-tools
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

""" Implement the 'experiment' requests """

from os.path import basename
import re
import json
import time
from iotlabcli import helpers
from iotlabcli.associations import AssociationsMap
from iotlabcli.associations import associationsmapdict_from_dict

# static name for experiment file : rename by server-rest
EXP_FILENAME = 'new_exp.json'

NODES_ASSOCIATIONS_FILE_ASSOCS = ('firmware',)


def submit_experiment(api, name, duration,  # pylint:disable=too-many-arguments
                      resources, start_time=None, print_json=False):
    """ Submit user experiment with JSON Encoder serialization object
    Experiment and firmware(s). If submission is accepted by scheduler OAR
    we print JSONObject response with id submission.

    :param api: API Rest api object
    :param name: experiment name
    :param duration: experiment duration in minutes
    :param resources: list of 'exp_resources'
    :param print_json: select if experiment should be printed as json instead
        of submitted
    """

    assert resources, 'Empty resources: %r' % resources
    experiment = _Experiment(name, duration, start_time)

    exp_files = helpers.FilesDict()
    for res_dict in resources:
        experiment.add_exp_resources(res_dict)
        exp_files.add_files_from_dict(NODES_ASSOCIATIONS_FILE_ASSOCS, res_dict)

    if print_json:  # output experiment description
        return experiment

    # submit experiment
    exp_files[EXP_FILENAME] = helpers.json_dumps(experiment)  # exp description

    return api.submit_experiment(exp_files)


def stop_experiment(api, exp_id):
    """ Stop user experiment submission.

    :param api: API Rest api object
    :param exp_id: scheduler OAR id submission
    """
    return api.stop_experiment(exp_id)


def get_experiments_list(api, state, limit, offset):
    """ Get the experiment list with the specific restriction:
    :param state: State of the experiment
    :param limit: maximum number of outputs
    :param offset: offset of experiments to start at
    """
    state = helpers.check_experiment_state(state)
    return api.get_experiments(state, limit, offset)


def get_experiment(api, exp_id, option=''):
    """ Get user experiment's description :

    :param api: API Rest api object
    :param exp_id: experiment id
    :param option: Restrict to some values
            * '':          experiment submission
            * 'resources': resources list
            * 'id':        resources id list: (1-34+72 format)
            * 'state':     experiment state
            * 'data':      experiment tar.gz with description and firmwares
            * 'start':     expected start time
    """
    result = api.get_experiment_info(exp_id, option)
    if option == 'data':
        _write_experiment_archive(exp_id, result)
        result = 'Written'

    return result


def get_active_experiments(api, running_only=True):
    """Get active experiments with it's state.

    :param api: API Rest api object
    :param running_only: if False search for a waiting/starting experiment
    :returns: {'Running': [EXP_ID], 'Waiting': [EXP_ID, EXP_ID]}
    """
    states = ['Running'] if running_only else helpers.ACTIVE_STATES
    exp_by_states = helpers.exps_by_states_dict(api, states)
    return exp_by_states


def load_experiment(api, exp_desc_path, files_list=()):
    """ Load and submit user experiment description with firmware(s)

    Firmwares and scripts required for experiment will be loaded from
    current directory, except if their path is given in files_list

    :param api: API Rest api object
    :param exp_desc_path: path to experiment json description file
    :param files_list: list of files path
    """

    # 1. load experiment description
    exp_dict = json.loads(helpers.read_file(exp_desc_path))
    experiment = _Experiment.from_dict(exp_dict)

    # 2. List files and update path with provided path
    files = _files_with_filespath(experiment.filenames(), files_list)

    # Construct experiment files
    exp_files = helpers.FilesDict()
    exp_files[EXP_FILENAME] = helpers.json_dumps(experiment)
    for exp_file in files:
        exp_files.add_file(exp_file)
    return api.submit_experiment(exp_files)


def _files_with_filespath(files, filespath):
    """Return `files` updated with `filespath`.

    Return a `files` list with path taken from `filespath` if basename
    matches one in `files`.

    >>> _files_with_filespath(['a', 'b', 'c', 'a'], ['dir/c', 'dir/a'])
    ['b', 'dir/a', 'dir/c']

    >>> _files_with_filespath(['a', 'b', 'c', 'a'], [])
    ['a', 'b', 'c']

    >>> _files_with_filespath(['a', 'b'], ['dir/a', 'dir/c'])
    Traceback (most recent call last):
    ...
    ValueError: Filespath ['dir/c'] not in files list ['a', 'b']
    """
    # Change filespath to a dict by basename
    filespathdict = dict(((basename(f), f) for f in filespath))

    # Update to full filepath if provided
    updatedfiles = [filespathdict.pop(f, f) for f in set(files)]

    # Error if there are remaining files in filespath
    if filespathdict:
        raise ValueError('Filespath %s not in files list %s' %
                         (list(filespathdict.values()), sorted(set(files))))

    return sorted(updatedfiles)


def reload_experiment(api, exp_id, duration=None, start_time=None):
    """Reload given experiment, duration and start_time can be adapted.

    :param api: API Rest api object
    :param exp_id: experiment id
    :param duration: experiment duration in minutes. None for same duration.
    :param start_time: experiment start time timestamp.
        None for as soon as possible
    """
    exp_json = {}

    # API needs strings and values shoud be absent if None
    if duration is not None:
        exp_json['duration'] = str(duration)
    if start_time is not None:
        exp_json['reservation'] = str(start_time)

    return api.reload_experiment(exp_id, exp_json)


def info_experiment(api, list_id=False, site=None):
    """ Print testbed information for user experiment submission:
    * resources description
    * resources description in short mode

    :param api: API Rest api object
    :param list_id: By default, return full nodes list, if list_id
        return output in exp_list format '3-12+42'
    :param site: Restrict informations collection on site
    """
    return api.get_resources(list_id, site)


def wait_experiment(api, exp_id, states='Running',
                    step=5, timeout=float('+inf')):
    """Wait for the experiment to be in `states`.

    Also returns if Terminated or Error

    :param api: API Rest api object
    :param exp_id: scheduler OAR id submission
    :param states: Comma separated string of states to wait for
    :param step: time to wait between each server check
    :param timeout: timeout if wait takes too long
    """
    def _state_function():
        """Get current user experiment state."""
        return get_experiment(api, exp_id, 'state')['state']
    exp_str = '%s' % (exp_id,)

    return wait_state(_state_function, exp_str, states, step, timeout)


def _states_from_str(states_str):
    """Return list of states from comma separated string.

    Also verify given states are valid.
    """
    return helpers.check_experiment_state(states_str).split(',')


STOPPED_STATES = set(_states_from_str('Terminated,Error'))


def wait_state(state_fct, exp_str, states='Running',
               step=5, timeout=float('+inf')):
    """Wait until `state_fct` returns a state in `states`
    and also Terminated or Error

    :param state_fct: function that returns current state
    :param states: Comma separated string of states to wait for
    :param step: time to wait between each server check
    :param timeout: timeout if wait takes too long
    """
    expected_states = set(_states_from_str(states))
    start_time = time.time()

    while not _timeout(start_time, timeout):
        state = state_fct()

        if state in expected_states:
            return state

        if state in STOPPED_STATES:
            # Terminated or Error
            err = "Experiment {0} already in state '{1!s}'"
            raise RuntimeError(err.format(exp_str, state))

        # Still wait
        time.sleep(step)

    raise RuntimeError('Timeout reached')


def _timeout(start_time, timeout):
    """Return if timeout is reached.

    :param start_time: initial time
    :param timeout: timeout
    :param _now: allow overriding 'now' call
    """
    return time.time() > start_time + timeout


def exp_resources(nodes, firmware_path=None, profile_name=None,
                  **associations):
    """Create an experiment resources dict.

    :param nodes: a list of nodes url or a AliasNodes object
        * ['m3-1.grenoble.iot-lab.info', 'wsn430-2.strasbourg.iot-lab.info']
        * AliasNodes(5, 'grenoble', 'm3:at86rf321', mobile=False)
    :param firmware_path: Firmware association
    :param profile_name: Profile association
    :param **associations: Other name associations
    """

    if isinstance(nodes, AliasNodes):
        exp_type = 'alias'
    else:
        exp_type = 'physical'

    resources = {
        'type': exp_type,
        'nodes': nodes,
        'firmware': firmware_path,
        'profile': profile_name,
        'associations': associations,
    }

    return resources


class AliasNodes(object):  # pylint: disable=too-few-public-methods
    """An AliasNodes class

    >>> AliasNodes(5, 'grenoble', 'm3:at86rf231', False)
    AliasNodes(5, 'grenoble', 'm3:at86rf231', False, _alias='1')
    >>> save = AliasNodes(2, 'strasbourg', 'wsn430:cc1101', True)
    >>> save
    AliasNodes(2, 'strasbourg', 'wsn430:cc1101', True, _alias='2')

    >>> save == AliasNodes(2, 'strasbourg', 'wsn430:cc1101', True, _alias='2')
    True

    >>> AliasNodes(2, 'strasbourg', 'wsn430:cc1100', True)
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ValueError: 'wsn430:cc1100' not in [...]

    """
    _alias = 0  # static count of current alias number
    ARCHIS = ['wsn430:cc1101', 'wsn430:cc2420',
              'm3:at86rf231', 'a8:at86rf231',
              'des:wifi-cc1100', 'custom:.*']
    ARCHI_RE = re.compile(r'|'.join(('(%s)' % archi for archi in ARCHIS)))

    def __init__(self, nbnodes, site, archi, mobile=False, _alias=None):
        """
        {
            "alias":"1",
            "nbnodes":1,
            "properties":{
                "archi":"wsn430:cc2420",
                "site":"devlille",
                "mobile":False
            }
        }
        """
        if not self._valid_archi(archi):
            raise ValueError("%r not in %r" % (archi, self.ARCHIS))

        self.alias = self._alias_uid(_alias)
        self.nbnodes = nbnodes
        self.properties = {
            "archi": archi,
            "site": site,
            "mobile": mobile,
        }

    @classmethod
    def _alias_uid(cls, alias=None):
        """Return an unique uid string.

        if alias is given, return it as a String
        """
        if alias is None:
            cls._alias += 1
            alias = cls._alias
        return str(alias)

    @classmethod
    def _valid_archi(cls, archi):
        """Tests if archi is valid.

        >>> AliasNodes._valid_archi('wsn430:cc1101')
        True

        >>> AliasNodes._valid_archi('des:wifi-cc1100')
        True

        >>> AliasNodes._valid_archi('custom:m3:cc1101')
        True

        >>> AliasNodes._valid_archi('custom:leonardo:')
        True

        >>> AliasNodes._valid_archi('wsn430:cc1100')
        False

        >>> AliasNodes._valid_archi('des')
        False
        """
        return bool(cls.ARCHI_RE.match(archi))

    def __repr__(self):  # pragma: no cover
        return 'AliasNodes(%r, %r, %r, %r, _alias=%r)' % (
            self.nbnodes, self.properties['site'], self.properties['archi'],
            self.properties['mobile'], self.alias)

    def __eq__(self, other):  # pragma: no cover
        return self.__dict__ == other.__dict__


# # # # # # # # # #
# Private methods #
# # # # # # # # # #

# Kwargs to initialize 'AssociationsMap' for nodes sorted.
_NODESMAPKWARGS = dict(resource='nodes', sortkey=helpers.node_url_sort_key)


class _Experiment(object):  # pylint:disable=too-many-instance-attributes
    """ Class describing an experiment """

    ASSOCATTR_FMT = '{0}associations'

    def __init__(self, name, duration, start_time=None):
        self.duration = duration
        self.reservation = start_time
        self.name = name

        self.type = None
        self.nodes = []
        self.firmwareassociations = None
        self.profileassociations = None
        self.associations = None

    def _firmwareassociations(self):
        """Init and return firmwareassociations."""
        return setattr_if_none(self, 'firmwareassociations',
                               AssociationsMap('firmware', **_NODESMAPKWARGS))

    def _profileassociations(self):
        """Init and return profileassociations."""
        return setattr_if_none(self, 'profileassociations',
                               AssociationsMap('profile', **_NODESMAPKWARGS))

    def _associations(self, assoctype):
        """Init and return associations[assoctype]."""
        assocs = setattr_if_none(self, 'associations', {})
        return assocs.setdefault(assoctype,
                                 AssociationsMap(assoctype, **_NODESMAPKWARGS))

    @classmethod
    def from_dict(cls, exp_dict):
        """Create an _Experiment object from given `exp_dict`."""
        experiment = cls(exp_dict.pop('name'), exp_dict.pop('duration'),
                         exp_dict.pop('reservation'))

        experiment.type = exp_dict.pop('type')
        experiment.nodes = exp_dict.pop('nodes')
        experiment._load_assocs(**exp_dict)  # pylint:disable=protected-access
        # No checking
        return experiment

    def _load_assocs(self, firmwareassociations=None, profileassociations=None,
                     associations=None):
        """Load associations to AssociationsMap and set attributes."""
        self.firmwareassociations = AssociationsMap.from_list(
            firmwareassociations, 'firmware', **_NODESMAPKWARGS)
        self.profileassociations = AssociationsMap.from_list(
            profileassociations, 'profile', **_NODESMAPKWARGS)
        self.associations = associationsmapdict_from_dict(associations,
                                                          **_NODESMAPKWARGS)

    def _set_type(self, exp_type):
        """ Set current experiment type.
        If type was already set and is different ValueError is raised
        """
        if self.type is not None and self.type != exp_type:
            raise ValueError(
                "Invalid experiment, should be only physical or only alias")
        self.type = exp_type

    def add_exp_resources(self, resources):
        """ Add 'exp_resources' to current experiment
        It will update node type, nodes, firmware and profile associations
        """
        # Alias/Physical
        self._set_type(resources['type'])

        # register nodes in experiment
        nodes = resources['nodes']
        self._register_nodes(nodes)  # pylint:disable=not-callable
        nodes = self._nodes_to_assoc(nodes)

        # register firmware
        if resources['firmware'] is not None:
            name = nodes_association_name('firmware', resources['firmware'])
            self._firmwareassociations().extendvalues(name, nodes)

        # register profile, may be None
        if resources['profile'] is not None:
            name = nodes_association_name('profile', resources['profile'])
            self._profileassociations().extendvalues(name, nodes)

        # Add other associations
        associations = resources.get('associations', {})
        for assoctype, assocname in associations.items():
            self._add_nodes_association(nodes, assoctype, assocname)

    def _add_nodes_association(self, nodes, assoctype, assocname):
        """Add given association."""
        name = nodes_association_name(assoctype, assocname)
        self._associations(assoctype).extendvalues(name, nodes)

    def _nodes_to_assoc(self, nodes):
        """Returns nodes to use in association."""
        return [nodes.alias] if self.type == 'alias' else nodes

    def set_physical_nodes(self, nodes_list):
        """Set physical nodes list """
        self._set_type('physical')

        # Check that nodes are not already present
        _intersect = list(set(self.nodes) & set(nodes_list))
        if _intersect:
            raise ValueError("Nodes specified multiple times {0}".format(
                _intersect))

        self.nodes.extend(nodes_list)
        # Keep unique values and sorted
        self.nodes = sorted(list(set(self.nodes)),
                            key=helpers.node_url_sort_key)

    def set_alias_nodes(self, alias_nodes):
        """Set alias nodes list """
        self._set_type('alias')
        self.nodes.append(alias_nodes)

    @property
    def _register_nodes(self):
        """Register nodes with the correct method according to exp `type`."""
        _register_fct_dict = {
            'physical': self.set_physical_nodes,
            'alias': self.set_alias_nodes,
        }
        return _register_fct_dict[self.type]

    def filenames(self):
        """Extract list of filenames required."""
        # No need to check nodes associations if there is only 'firmware'
        assert NODES_ASSOCIATIONS_FILE_ASSOCS == ('firmware',)

        files = []
        # Handle None attributes
        files += (self.firmwareassociations or {}).keys()
        return files


def setattr_if_none(obj, attr, default):
    """Set attribute as `default` if None

    :returns: attribute value after update
    """
    # Set default if None
    if getattr(obj, attr) is None:
        setattr(obj, attr, default)

    return getattr(obj, attr)


def _write_experiment_archive(exp_id, data):
    """ Write experiment archive contained in 'data' to 'exp_id.tar.gz' """
    with open('%s.tar.gz' % exp_id, 'wb') as archive:
        archive.write(data)


def nodes_association_name(assoctype, assocname):
    """Adapt assocname depending of assoctype.

    Return basename(assocname) if assoctype is a file-association.
    """
    return _basename_if_in(assocname, assoctype,
                           NODES_ASSOCIATIONS_FILE_ASSOCS)


def _basename_if_in(value, key, container, transform=basename):
    """Return basename if in.

    >>> _basename_if_in('a/b', 1, [1])
    'b'
    >>> _basename_if_in('a/b', 2, (1,))
    'a/b'
    """
    return transform(value) if key in container else value
