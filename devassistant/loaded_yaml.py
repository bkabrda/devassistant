import os

import six

from devassistant import exceptions
from devassistant import settings

class LoadedYaml(object):
    _yaml_typenames = {dict: 'mapping',
                       list: 'list',
                       six.text_type: 'string',
                       six.binary_type: 'string',
                       int: 'integer',
                       float: 'float',
                       bool: 'boolean'}
    for s in six.string_types:
        _yaml_typenames[s] = 'string'

    @property
    def load_path(self):
        lp = ''
        for d in settings.DATA_DIRECTORIES:
            if d == os.path.commonprefix([self.path, d]): break

        return d

    def default_files_dir_for(self, files_subdir):
        yaml_path = self.path.replace(os.path.join(self.load_path, files_subdir), '')
        yaml_path = os.path.splitext(yaml_path)[0]
        yaml_path = yaml_path.strip(os.sep)
        parts = [self.load_path, 'files']
        if files_subdir == 'snippets':
            parts.append(files_subdir)
        parts.append(yaml_path)
        return os.path.join(*parts)

    def check(self):
        """Checks whether loaded yaml is well-formed according to syntax defined for
        version 0.9.0 and later.

        Raises:
            YamlError: (containing a meaningful message) when the loaded Yaml
                is not well formed
        """
        if not isinstance(self.parsed_yaml, dict):
            msg = 'In {0}:\n'.format(self.path)
            msg += 'Assistants and snippets must be Yaml mappings, not {0}!'.\
                    format(type(self.parsed_yaml))
            raise exceptions.YamlTypeError(msg)
        self._check_fullname(self.path)
        self._check_description(self.path)
        self._check_args(self.path)
        self._check_dependencies(self.path)
        #self._check_run(self.path)

    def _check_fullname(self, source):
        pass

    def _check_description(self, source):
        pass

    def _check_args(self, source):
        path = [source]
        args = self.parsed_yaml.get('args', {})
        self._assert_dict(args, 'args', path)
        path.append('args')
        for argn, argattrs in args.items():
            self._check_one_arg(path, argn, argattrs)

    def _check_one_arg(self, path, argn, argattrs):
        self._assert_dict(argattrs, argn, path)
        path = path + [argn]
        for attrn, attrval in argattrs.items():
            if attrn in ['use', 'help', 'nargs', 'metavar', 'dest']:
                self._assert_str(attrval, attrn, path)
            elif attrn in ['const', 'default']:
                self._assert_struct_type(attrval,
                                         attrn,
                                         (int, float, bool) + six.string_types,
                                         path)
            elif attrn in ['flags', 'choices']:
                self._assert_list(attrval, attrn, path)
            elif attrn == 'action':
                self._assert_struct_type(attrval, attrn, (list, ) + six.string_types, path)
            elif attrn == 'gui_hints':
                # TODO: maybe check this more thoroughly
                self._assert_dict(attrval, attrn, path)

    def _check_dependencies(self, source):
        path = [source]
        depsects = filter(lambda a: a[0].startswith('dependencies'), self.parsed_yaml.items())
        for name, struct in depsects:
            self._check_one_dependencies_section(path, name, struct)

    def _check_one_dependencies_section(self, path, sectname, struct):
        self._assert_list(struct, sectname, path)
        path = path + [sectname]
        for item in struct:
            self._assert_dict(item, item, path)

    def _check_run(self):
        pass

    def _assert_dict(self, struct, name, path=None, extra_info=None):
        self._assert_struct_type(struct, name, (dict,), path, extra_info)

    def _assert_str(self, struct, name, path=None, extra_info=None):
        self._assert_struct_type(struct, name, six.string_types, path, extra_info)

    def _assert_list(self, struct, name, path=None, extra_info=None):
        self._assert_struct_type(struct, name, (list,), path, extra_info)

    def _assert_struct_type(self, struct, name, types, path=None, extra_info=None):
        """Asserts that given structure is of any of given types.

        Args:
            struct: structure to check
            name: displayable name of the checked structure (e.g. "run_foo" for section run_foo)
            types: list/tuple of types that are allowed for given struct
            path: list with a source file as a first element and previous names
                  (as in name argument to this method) as other elements
            extra_info: extra information to print if error is found (e.g. hint how to fix this)
        Raises:
            YamlTypeError: if given struct is not of any given type; error message contains
                           source file and a "path" (e.g. args -> somearg -> flags) specifying
                           where the problem is
        """
        wanted_yaml_typenames = set()
        for t in types:
            wanted_yaml_typenames.add(self._yaml_typenames[t])
        wanted_yaml_typenames = ' or '.join(wanted_yaml_typenames)
        actual_yaml_typename = self._yaml_typenames[type(struct)]
        if not isinstance(struct, types):
            err = []
            if path:
                err.append(self._format_error_path(path + [name]))
            err.append('"{n}" must be of type {w}, not {a}.'.format(n=name,
                                                                    w=wanted_yaml_typenames,
                                                                    a=actual_yaml_typename))
            if extra_info:
                err.append(extra_info)
            raise exceptions.YamlTypeError('\n'.join(err))

    def _format_error_path(self, path):
        err = []
        err.append('Source file {p}:'.format(p=path[0]))
        path2print = ['(top level)'] + [str(x) for x in path[1:]]
        err.append('  Problem in: ' + ' -> '.join(path2print))
        return '\n'.join(err)
