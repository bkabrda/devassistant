import pytest
import os

from devassistant.lang import evaluate_expression, exceptions, \
    dependencies_section, format_str, run_section, parse_for

from test.logger import TestLoggingHandler
# TODO: some of the test methods may need splitting into separate classes according to methods
# that they test; also, the classes should be extended to get better coverage of tested methods


class TestDependenciesSection(object):
    @pytest.mark.parametrize('deps, kwargs, result', [
        # simple case
        ([{'rpm': ['foo', '@bar', 'baz']}], {}, None),
        # dependencies in "if" clause apply
        ([{'if $x': [{'rpm': ['foo']}]}, {'else': [{'rpm': ['bar']}]}],
         {'x': 'x'},
         [{'rpm': ['foo']}]),
        # dependencies in "else" clause apply
        ([{'if $x': [{'rpm': ['foo']}]}, {'else': [{'rpm': ['bar']}]}], {}, [{'rpm': ['bar']}])
    ])
    def test_dependencies(self, deps, kwargs, result):
        dependencies_section(deps, kwargs) == deps if result == None else deps


class TestEvaluate(object):
    def setup_class(self):
        self.names = {"true": True,
                      "false": False,
                      "nonempty": "foo",
                      "nonempty2": "bar",
                      "empty": ""}

        # create directories for test_shell
        os.mkdir(os.path.join(os.path.dirname(__file__), "foo"))
        os.mkdir(os.path.join(os.path.dirname(__file__), "foo", "bar"))
        os.chdir(os.path.dirname(__file__))

    def teardown_class(self):
        os.rmdir(os.path.join(os.path.dirname(__file__), "foo", "bar"))
        os.rmdir(os.path.join(os.path.dirname(__file__), "foo"))

    def test_and(self):
        assert evaluate_expression("$true and $true", self.names) == (True, "")
        assert evaluate_expression("$true and $false", self.names) == (False, "")
        assert evaluate_expression("$false and $true", self.names) == (False, "")
        assert evaluate_expression("$false and $false", self.names) == (False, "")

        assert evaluate_expression("$nonempty and $nonempty2", self.names) == (True, "bar")
        assert evaluate_expression("$nonempty2 and $nonempty", self.names) == (True, "foo")

        assert evaluate_expression("$nonempty and $empty", self.names) == (False, "")
        assert evaluate_expression("$empty and $nonempty", self.names) == (False, "")

        assert evaluate_expression("$nonempty and $true", self.names) == (True, "")
        assert evaluate_expression("$true and $nonempty", self.names) == (True, "")

        assert evaluate_expression("$empty and $true", self.names) == (False, "")
        assert evaluate_expression("$true and $empty", self.names) == (False, "")

        assert evaluate_expression("$empty and $empty", self.names) == (False, "")

        assert evaluate_expression("$true and $nonempty and $nonempty2", self.names) == (True, "")
        assert evaluate_expression("$true and $nonempty and $empty", self.names) == (False, "")

    def test_or(self):
        assert evaluate_expression("$true or $true", self.names) == (True, "")
        assert evaluate_expression("$true or $false", self.names) == (True, "")
        assert evaluate_expression("$false or $true", self.names) == (True, "")
        assert evaluate_expression("$false or $false", self.names) == (False, "")

        assert evaluate_expression("$nonempty or $nonempty2", self.names) == (True, "foo")
        assert evaluate_expression("$nonempty2 or $nonempty", self.names) == (True, "bar")

        assert evaluate_expression("$nonempty or $empty", self.names) == (True, "foo")
        assert evaluate_expression("$empty or $nonempty", self.names) == (True, "foo")

        assert evaluate_expression("$nonempty or $true", self.names) == (True, "foo")
        assert evaluate_expression("$true or $nonempty", self.names) == (True, "foo")

        assert evaluate_expression("$empty or $true", self.names) == (True, "")
        assert evaluate_expression("$true or $empty", self.names) == (True, "")

        assert evaluate_expression("$empty or $empty", self.names) == (False, "")

        assert evaluate_expression("$true or $nonempty or $nonempty2", self.names) == (True, "foo")
        assert evaluate_expression("$false or $nonempty or $empty", self.names) == (True, "foo")

    def test_not(self):
        assert evaluate_expression("not $true", self.names) == (False, "")
        assert evaluate_expression("not $false", self.names) == (True, "")
        assert evaluate_expression("not $nonempty", self.names) == (False, "foo")
        assert evaluate_expression("not $empty", self.names) == (True, "")

    def test_in(self):
        assert evaluate_expression('$nonempty in "foobar"', self.names) == (True, "foo")
        assert evaluate_expression('$nonempty2 in "foobar"', self.names) == (True, "bar")
        assert evaluate_expression('$empty in "foobar"', self.names) == (True, "")
        assert evaluate_expression('$nonempty in "FOOBAR"', self.names) == (False, "foo")

    def test_defined(self):
        assert evaluate_expression("defined $nonempty", self.names) == (True, "foo")
        assert evaluate_expression("defined $empty", self.names) == (True, "")
        assert evaluate_expression("defined $notdefined", self.names) == (False, "")

    def test_variable(self):
        assert evaluate_expression("$true", self.names) == (True, "")
        assert evaluate_expression("$false", self.names) == (False, "")
        assert evaluate_expression("$nonempty", self.names) == (True, "foo")
        assert evaluate_expression("$empty", self.names) == (False, "")

    def test_shell(self):
        assert evaluate_expression("$(echo foobar)", self.names) == (True, "foobar")
        assert evaluate_expression("$(test -d /thoushaltnotexist)", self.names) == (False, '')
        assert evaluate_expression("$(false)", self.names) == (False, '')
        assert evaluate_expression("$(true)", self.names) == (True, '')
        # temporarily disabled
        #assert re.match(".*/foo/bar$",
        #               evaluate_expression("$(cd foo; cd bar; pwd; cd ../..)",
        #                                   self.names)[1])
        assert evaluate_expression('$(echo -e "foo\\nbar" | grep "bar")', self.names) == (True, "bar")

    def test_literal(self):
        assert evaluate_expression('"foobar"', self.names) == (True, "foobar")
        assert evaluate_expression("'foobar'", self.names) == (True, "foobar")
        assert evaluate_expression('""', self.names) == (False, "")

    def test_variable_substitution(self):
        assert evaluate_expression('"$nonempty"', self.names) == (True, "foo")
        assert evaluate_expression('"$empty"', self.names) == (False, "")
        assert evaluate_expression('"$true"', self.names) == (True, "True")

    def test_complex_expression(self):
        assert evaluate_expression('defined $empty or $empty and \
                                    $(echo -e foo bar "and also baz") or "else $nonempty"',
                                    self.names) == (True, 'else foo')

    def test_python_struct(self):
        assert evaluate_expression({'foo': 'bar'}, self.names) == (True, {'foo': 'bar'})
        assert evaluate_expression(['foo', 'bar'], self.names) == (True, ['foo', 'bar'])
        assert evaluate_expression({}, self.names) == (False, {})
        assert evaluate_expression([], self.names) == (False, [])

    def test_special_symbols_in_subshell_invocation(self):
        # before fixing this, special symbols inside shell invocation were
        # surrounded by spaces when parsed reconstructed by evaluate_expression
        # (e.g. backticks, colons, equal signs), e.g. the below command returned
        # (True, '` a : s = d `')
        assert evaluate_expression('$(echo \`a:s=d\`)', {}) == (True, '`a:s=d`')

    def test_variables_in_subshell_invocation(self):
        assert evaluate_expression('$(echo $exists $doesnt)', {'exists': 'X'}) == (True, 'X')
        assert evaluate_expression('$(echo ${exists} ${doesnt})', {'exists': 'X'}) == (True, 'X')


class TestRunSection(object):
    def assert_run_section_result(self, actual, expected):
        # "actual" can possibly be a tuple, not a list, so we need to unify the value
        assert list(actual) == list(expected)

    def test_result(self):
        self.assert_run_section_result(run_section([]), [False, ''])
        self.assert_run_section_result(run_section([{'log_i': 'foo'}]), [True, 'foo'])

    def test_run_unkown_command(self):
        with pytest.raises(exceptions.CommandException):
            run_section([{'foo': 'bar'}])

    def test_shell_command(self):
        rs = [{'$foo~': '$(echo asd)'}]
        self.assert_run_section_result(run_section(rs, {}), [True, 'asd'])

    def test_looks_like_shell_command_but_no_exec_flag(self):
        rs = [{'$foo': '$(echo asd)'}]
        self.assert_run_section_result(run_section(rs, {}), [True, '$(echo asd)'])

    def test_if(self):
        rs = [{'if $foo': [{'$foo': 'bar'}, {'$foo': 'baz'}]}]
        self.assert_run_section_result(run_section(rs, {}), [False, ''])
        self.assert_run_section_result(run_section(rs, {'foo': 'yes'}), [True, 'baz'])

    def test_nested_condition(self):
        rs = [{'if $foo': [{'if $bar': 'bar'}, {'else': [{'log_i': 'baz'}]}]}]
        self.assert_run_section_result(run_section(rs, {'foo': 'yes'}), [True, 'baz'])

    def test_else(self):
        rs = [{'if $foo': [{'$foo': 'bar'}]}, {'else': [{'$foo': 'baz'}]}]
        self.assert_run_section_result(run_section(rs, {'foo': 'yes'}), [True, 'bar'])
        self.assert_run_section_result(run_section(rs, {}), [True, 'baz'])

    def test_for(self):
        rs = [{'for $i in $list': [{'$foo~': '$(echo $i)'}]}]
        self.assert_run_section_result(run_section(rs, {'list': '1'}), [True, '1'])
        self.assert_run_section_result(run_section(rs, {'list': '1 2'}), [True, '2'])
        self.assert_run_section_result(run_section(rs, {}), [False, ''])

    def test_for_empty_string(self):
        kwargs = {}
        run_section([{'for $i in $(echo "")': [{'$foo': '$i'}]}], kwargs)
        assert 'foo' not in kwargs

    def test_loop_two_control_vars(self):
        tlh = TestLoggingHandler.create_fresh_handler()
        run_section([{'for $i, $j in $foo': [{'log_i': '$i, $j'}]}],
                    {'foo': {'bar': 'barval', 'spam': 'spamval'}})
        assert ('INFO', 'bar, barval') in tlh.msgs
        assert ('INFO', 'spam, spamval') in tlh.msgs

    def test_loop_two_control_vars_fails_on_string(self):
        with pytest.raises(exceptions.YamlSyntaxError):
            run_section([{'for $i, $j in $(echo "foo bar")': [{'log_i': '$i'}]}])

    @pytest.mark.parametrize('comm', [
        'for foo',
        'for $a foo'])
        # Not sure if 'for $a in $var something' should raise
    def test_parse_for_malformed(self, comm):
        with pytest.raises(exceptions.YamlSyntaxError):
            parse_for(comm)

    @pytest.mark.parametrize(('comm', 'result'), [
        ('for $a in $foo',          (['a'], '$foo')),
        ('for $a in $(expr)',       (['a'], '$(expr)')),
        ('for $a, $b in $foo',      (['a', 'b'], '$foo')),
        ('for $a, $b in $(expr)',   (['a', 'b'], '$(expr)')),
        ('for ${a} in $foo',        (['a'], '$foo')),
        ('for ${a} in $(expr)',     (['a'], '$(expr)')),
        ('for ${a}, ${b} in $foo',  (['a', 'b'], '$foo')),
        ('for ${a}, ${b} in $(expr)', (['a', 'b'], '$(expr)'))])
    def test_parse_for_well_formed(self, comm, result):
        assert(parse_for(comm) == result)

    def test_successful_command_with_no_output_evaluates_to_true(self):
        kwargs = {}
        run_section([{'if $(true)': [{'$success': 'success'}]}], kwargs)
        assert 'success' in kwargs

    def test_assign_in_condition_modifies_outer_scope(self):
        kwargs={'foo': 'foo', 'spam': 'spam'}
        run_section([{'if $foo': [{'$foo': '$spam'}]}], kwargs)
        assert kwargs['foo'] == 'spam'

    def test_assign_existing_nonempty_variable(self):
        kwargs = {'bar': 'bar'}
        run_section([{'$foo': '$bar'}], kwargs)
        assert kwargs['foo'] == 'bar'

        # both logical result and result
        run_section([{'$success, $val': '$bar'}], kwargs)
        assert kwargs['success'] == True
        assert kwargs['val'] == 'bar'

    @pytest.mark.parametrize('exec_flag, lres, res', [
        ('', True, ''), # no exec flag => evals as literal
        ('~', False, '')
    ])
    def test_assign_existing_empty_variable(self, exec_flag, lres, res):
        kwargs = {'bar': ''}
        run_section([{'$foo{0}'.format(exec_flag): '$bar'}], kwargs)
        assert kwargs['foo'] == res

        # both logical result and result
        run_section([{'$success, $val{0}'.format(exec_flag): '$foo'}], kwargs)
        assert kwargs['success'] == lres
        assert kwargs['val'] == res

    @pytest.mark.parametrize('exec_flag, lres, res', [
        ('', True, '$bar'), # no exec flag => evals as literal
        ('~', False, '')
    ])
    def test_assign_nonexisting_variable_depending_on_exec_flag(self, exec_flag, lres, res):
        kwargs = {}
        run_section([{'$foo{0}'.format(exec_flag): '$bar'}], kwargs)
        assert kwargs['foo'] == res

        # both logical result and result
        run_section([{'$success, $val{0}'.format(exec_flag): '$bar'}], kwargs)
        assert kwargs['success'] == lres
        assert kwargs['val'] == res

    def test_assign_defined_empty_variable(self):
        kwargs = {'foo': ''}
        run_section([{'$success, $val~': 'defined $foo'}], kwargs)
        assert kwargs['success'] == True
        assert kwargs['val'] == ''

    def test_assign_defined_variable(self):
        kwargs = {'foo': 'foo'}
        run_section([{'$success, $val~': 'defined $foo'}], kwargs)
        assert kwargs['success'] == True
        assert kwargs['val'] == 'foo'

    def test_assign_defined_nonexistent_variable(self):
        kwargs = {}
        run_section([{'$success, $val~': 'defined $foo'}], kwargs)
        assert kwargs['success'] == False
        assert kwargs['val'] == ''

    def test_assign_successful_command(self):
        kwargs = {}
        run_section([{'$foo~': '$(basename foo/bar)'}, {'log_i': '$foo'}], kwargs)
        assert kwargs['foo'] == u'bar'

        # both logical result and result
        run_section([{'$success, $val~': '$(basename foo/bar)'}], kwargs)
        assert kwargs['success'] == True
        assert kwargs['val'] == 'bar'

    def test_assign_unsuccessful_command(self):
        kwargs = {}
        run_section([{'$foo~': '$(ls spam/spam/spam)'}], kwargs)
        assert kwargs['foo'] == u'ls: cannot access spam/spam/spam: No such file or directory'

        # both logical result and result
        run_section([{'$success, $val~': '$(ls spam/spam/spam)'}], kwargs)
        assert kwargs['val'] == u'ls: cannot access spam/spam/spam: No such file or directory'
        assert kwargs['success'] == False


class TestFormatStr(object):
    files_dir = '/a/b/c'
    files = {'first': {'source': 'f/g'}, 'second': {'source': 's/t'}}

    @pytest.mark.parametrize(('comm', 'arg_dict', 'result'), [
        ('ls -la', {}, 'ls -la'),
        ('touch $foo ${bar} $baz', {'foo': 'a', 'bar': 'b'}, 'touch a b $baz'),
        ('cp *first second', {}, 'cp {0}/f/g second'.format(files_dir)),
        ('cp *{first} *{nothing}', {}, 'cp %s/f/g *{nothing}' % (files_dir)),
        ('cp *{first} $foo', {'foo': 'a'}, 'cp {0}/f/g a'.format(files_dir)),
    ])
    def test_format_str(self, comm, arg_dict, result):
        arg_dict['__files__'] = [self.files]
        arg_dict['__files_dir__'] = [self.files_dir]
        assert format_str(comm, arg_dict) == result

    def test_format_str_handles_bool(self):
        # If command is false/true in yaml file, it gets coverted to False/True
        # which is bool object. format should handle this.
        assert format_str(True, {}) == 'true'
        assert format_str(False, {}) == 'false'

    def test_format_str_preserves_whitespace(self):
        c = "  eggs   spam    beans  "
        assert format_str(c, {}) == c
