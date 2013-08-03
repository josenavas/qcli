#!/usr/bin/env python

#-----------------------------------------------------------------------------
# Copyright (c) 2013, The BiPy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2013, The QIIME Project"
__credits__ = ["Greg Caporaso", "Daniel McDonald", "Doug Wendel",
               "Jai Ram Rideout"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"

from qcli.interface.core import Interface
from qcli.interface.factory import general_factory
from qcli.core.exception import IncompetentDeveloperError
from qcli.core.command import Parameter
from qcli.option_parsing import (OptionParser, OptionGroup, Option, 
                                 OptionValueError, OptionError, make_option)
import os

CLTypes = set(['float','int','string','existing_filepath', float, int, str,
               None, 'new_filepath','new_dirpath','existing_dirpath'])
CLActions = set(['store','store_true','store_false', 'append'])

def new_filepath(data, path):
    if os.path.exists(path):
        raise IOError("Output path %s already exists." % path)
    f = open(path, 'w')
    f.write(data)
    f.close()

class OutputHandler(object):
    """Handle result output

    OptionName - the long name of an output command line option
    Function   - a Python function that accepts the result name, the 
                 corresponding option value (if tied to a command line option),
                 and the result data
    """
    def __init__(self, OptionName, Function):
        self.OptionName = OptionName
        self.Function = Function

class CLOption(Parameter):
    """An augmented option that expands a Parameter into an Option"""
    _cl_types = {'new_filepath': new_filepath}
    def __init__(self, Type, Help, Name, LongName, CLType, CLAction='store',
                 Required=False, Default=None, DefaultDescription=None,
                 ShortName=None, ResultName=None):
        self.LongName = LongName
        self.CLType = CLType
        self.CLAction = CLAction
        self.ShortName = ShortName
        self.ResultName = ResultName

        if CLType in self._cl_types:
            self._cl_type_action = self._cl_types['new_filepath']

        super(CLOption,self).__init__(Type=Type,Help=Help,Name=Name,
                                      Required=Required,Default=Default,
                                      DefaultDescription=DefaultDescription)
        
    def __str__(self):
        if self.ShortName is None:
            return '--%s' % self.LongName
        else:
            return '-%s/--%s' % (self.ShortName, self.LongName)

    def getOptparseOption(self):
        if self.Required:
            # If the option doesn't already end with [REQUIRED], add it.
            help_text = self.Help
            if not help_text.strip().endswith('[REQUIRED]'):
                help_text += ' [REQUIRED]'

            if self.ShortName is None:
                option = make_option('--' + self.LongName, type=self.CLType,
                                     help=help_text)
            else:
                option = make_option('-' + self.ShortName,
                                     '--' + self.LongName, type=self.CLType,
                                     help=help_text)
        else:
            help_text = '%s [default: %s]' % (self.Help,
                                              self.DefaultDescription)

            if self.ShortName is None:
                option = make_option('--' + self.LongName, type=self.CLType,
                                     help=help_text, default=self.Default)
            else:
                option = make_option('-' + self.ShortName,
                                     '--' + self.LongName, type=self.CLType,
                                     help=help_text, default=self.Default)
        return option

    @classmethod
    def fromParameter(cls, parameter, LongName, CLType, CLAction='store',
                      ShortName=None):
        """Go from an existing ``Parameter`` to a ``CLOption``"""
        result = cls(Type=parameter.Type,
                     Help=parameter.Help,
                     Name=parameter.Name,
                     Required=parameter.Required,
                     LongName=LongName,
                     CLType=CLType,
                     CLAction=CLAction,
                     Default=parameter.Default,
                     DefaultDescription=parameter.DefaultDescription,
                     ShortName=ShortName)
        return result

class UsageExample(object):
    """Provide structure to a usage example"""
    def __init__(self, ShortDesc, LongDesc, Ex):
        self.ShortDesc = ShortDesc
        self.LongDesc = LongDesc
        self.Ex = Ex

class ParameterConversion(object):
    """Validation and structure for converting from a parameter to an option"""
    def __init__(self, LongName, CLType, CLAction=None, InHandler=None, 
                 ShortName=None):
        if CLType not in CLTypes:
            raise IncompetentDeveloperError("Invalid CLType specified: %s" % CLType)
        if CLAction is not None and CLAction not in CLActions:
            raise IncompetentDeveloperError("Invalid CLAction specified: %s" % CLAction)

        self.ShortName = ShortName
        self.LongName = LongName
        self.CLType = CLType
        self.CLAction = CLAction
        self.InHandler = InHandler

class CLInterface(Interface):
    """A command line interface"""
    DisallowPositionalArguments = True
    HelpOnNoArguments = True 
    OptionalInputLine = '[] indicates optional input (order unimportant)'
    RequiredInputLine = '{} indicates required input (order unimportant)'
    
    def __init__(self, **kwargs):
        self.BelovedFunctionality = {}
        self.UsageExamples = []
        self.UsageExamples.extend(self._get_usage_examples())

        if len(self.UsageExamples) < 1:
            raise IncompetentDeveloperError("There are no usage examples "
                                            "associated with this command.")

        self.ParameterConversionInfo = {
                'verbose':ParameterConversion(ShortName='v',
                                              LongName='verbose',
                                              CLType=None,
                                              CLAction='store_true')
                }

        self.ParameterConversionInfo.update(self._get_param_conv_info())
       
        super(CLInterface, self).__init__(**kwargs)

        self.Options.extend(self._get_additional_options())

    def _get_param_conv_info(self):
        """Return the ``ParameterConversion`` objects"""
        raise NotImplementedError("Must define _get_param_conv_info")

    def _get_usage_examples(self):
        """Return the ``UsageExample`` objects"""
        raise NotImplementedError("Must define _get_usage_examples")

    def _get_additional_options(self):
        """Return the ``CLOption`` objects"""
        raise NotImplementedError("Must define _get_additional_options")

    def _get_output_map(self):
        """Return the ``output_map`` objects"""
        raise NotImplementedError("Must define _get_output_map")

    def _the_in_validator(self, in_):
        """Validate input coming from the command line"""
        if not isinstance(in_, list):
            raise IncompetentDeveloperError("Unsupported input '%r'. Input "
                                            "must be a list." % in_)

    def _option_factory(self, parameter):
        """Promote a parameter to a CLOption"""
        name = parameter.Name
        if name not in self.ParameterConversionInfo:
            raise IncompetentDeveloperError("%s does not have parameter "
                    "conversion info (parameter conversions are available for "
                    "%s)" % (name,
                             ' '.join(self.ParameterConversionInfo.keys())))

        return CLOption.fromParameter(parameter,
                     self.ParameterConversionInfo[name].LongName,
                     self.ParameterConversionInfo[name].CLType,
                     ShortName=self.ParameterConversionInfo[name].ShortName)

    def _input_handler(self, in_, *args, **kwargs):
        """Parses command-line input."""
        required_opts = [opt for opt in self.Options if opt.Required]
        optional_opts = [opt for opt in self.Options if not opt.Required]

        # Build the usage and version strings
        usage = self._build_usage_lines(required_opts)
        version = 'Version: %prog ' + __version__

        # Instantiate the command line parser object
        parser = OptionParser(usage=usage, version=version)

        # If no arguments were provided, print the help string (unless the
        # caller specified not to).
        if self.HelpOnNoArguments and len(in_) == 0:
            parser.print_usage()
            return parser.exit(-1)

        if required_opts:
            # Define an option group so all required options are grouped
            # together and under a common header.
            required = OptionGroup(parser, "REQUIRED options",
                                   "The following options must be provided "
                                   "under all circumstances.")
            for ro in required_opts:
                required.add_option(ro.getOptparseOption())
            parser.add_option_group(required)

        # Add the optional options.
        for oo in optional_opts:
            parser.add_option(oo.getOptparseOption())

        # Parse our input.
        opts, args = parser.parse_args(in_)

        # If positional arguments are not allowed, and any were provided, raise
        # an error.
        if self.DisallowPositionalArguments and len(args) != 0:
            parser.error("Positional argument detected: %s\n" % str(args[0]) +
             " Be sure all parameters are identified by their option name.\n" +
             " (e.g.: include the '-i' in '-i INPUT_DIR')")

        # Test that all required options were provided.
        if required_opts:
            required_option_ids = [o.dest for o in required.option_list]
            for required_option_id in required_option_ids:
                if getattr(opts,required_option_id) == None:
                    parser.error('Required option --%s omitted.' %
                                 required_option_id)

        beloved_functionality = opts.__dict__
        self.BelovedFunctionality = beloved_functionality
        for k, v in self.ParameterConversionInfo.items():
            if v.InHandler is not None:
                long_name = v.LongName
                value = self.BelovedFunctionality[long_name]
                self.BelovedFunctionality[long_name] = v.InHandler(value)
            else:
                pass
        return self.BelovedFunctionality

    def _build_usage_lines(self, required_options):
        """ Build the usage string from components """
        line1 = 'usage: %prog [options] ' + \
                '{%s}' % ' '.join(['%s %s' % (str(rp),rp.Name.upper())
                                   for rp in required_options])

        formatted_usage_examples = []
        for usage_example in self.UsageExamples:
            short_description = usage_example.ShortDesc.strip(':').strip()
            long_description = usage_example.LongDesc.strip(':').strip()
            example = usage_example.Ex.strip()

            if short_description:
                formatted_usage_examples.append('%s: %s\n %s' % 
                                                (short_description,
                                                 long_description, example))
            else:
                formatted_usage_examples.append('%s\n %s' %
                                                (long_description,example))

        formatted_usage_examples = '\n\n'.join(formatted_usage_examples)

        lines = (line1,
                 '', # Blank line
                 self.OptionalInputLine,
                 self.RequiredInputLine,
                 '', # Blank line
                 self.CmdInstance.LongDescription,
                 '', # Blank line
                 'Example usage: ',
                 'Print help message and exit',
                 ' %prog -h\n',
                 formatted_usage_examples)

        return '\n'.join(lines)

    def _output_handler(self, results):
        """Deal with things in output if we know how"""
        for k,handler in self._get_output_map().items():
            if k not in results:
                raise IncompetentDeveloperError("Did not find the expected "
                                                "output '%s' in results." % k)

            if handler.OptionName is None:
                handler.Function(k, results[k])
            else:
                opt_value = self.BelovedFunctionality[handler.OptionName]
                handler.Function(k, results[k], opt_value)

def cli(command_constructor, usage_examples, param_conversions, added_options,
        output_map):
    """Command line interface factory
    
    command_constructor - a subclass of ``Command``
    usage_examples - usage examples for using ``command_constructor`` on via a
        command line interface.
    param_conversions - necessary conversion information to converting
        parameters to options.
    added_options - any additional options that are not defined by the 
        ``command_constructor``.
    output_map - result keys to ``OutputHandler``
    """
    return general_factory(command_constructor, usage_examples,
                           param_conversions, added_options, output_map,
                           CLInterface)

def clmain(interface_object, local_argv):
    """Construct and execute an interface object"""
    cli_cmd = interface_object()
    result = cli_cmd(local_argv[1:])
    return 0
