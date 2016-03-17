"""
Attempt to generate templates for module reference with Sphinx

Notes
-----
This parsing is based on import and introspection of modules.

This is a modified version of a script shipped with scikit-image, which was
itself based on similar scripts from PyMVPA and NiPy.
"""

# Stdlib imports
import os
import re

from types import BuiltinFunctionType, FunctionType

# suppress print statements (warnings for empty files)
DEBUG = True


class ApiDocWriter(object):
    ''' Class for automatic detection and parsing of API docs
    to Sphinx-parsable reST format'''

    # only separating first two levels
    rst_section_levels = ['*', '=', '-', '~', '^']

    def __init__(self,
                 package_name,
                 rst_extension='.txt',
                 skip_patterns=['.*__', '.*tests$'],
                 ):
        ''' Initialize package for parsing

        Parameters
        ----------
        package_name : string
            Name of the top-level package.  *package_name* must be the
            name of an importable package
        rst_extension : string, optional
            Extension for reST files, default '.rst'
        skip_patterns : None or sequence
            Sequence of strings giving URIs of modules to be excluded
            Operates on the module name including preceding URI path,
            back to the first dot after *package_name*.  For example
            ``sphinx.util.console`` results in the string to search of
            ``.util.console``
            If is None, gives default. Default is:
            ['\.setup$', '\._']
        '''
        self.package_name = package_name
        self.skip_patterns = skip_patterns
        self.rst_extension = rst_extension
        root_module = self._import(package_name)
        self.root_path = root_module.__path__[-1]

    def _import(self, name):
        ''' Import namespace package '''
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    def _get_object_name(self, line):
        ''' Get second token in line
        >>> docwriter = ApiDocWriter('sphinx')
        >>> docwriter._get_object_name("  def func():  ")
        'func'
        >>> docwriter._get_object_name("  class Klass(object):  ")
        'Klass'
        >>> docwriter._get_object_name("  class Klass:  ")
        'Klass'
        '''
        name = line.split()[1].split('(')[0].strip()
        # in case we have classes which are not derived from object
        # ie. old style classes
        return name.rstrip(':')

    def _parse_module_with_import(self, uri):
        """Look for functions and classes in an importable module.

        Parameters
        ----------
        uri : str
            The name of the module to be parsed. This module needs to be
            importable.

        Returns
        -------
        functions : list of str
            A list of (public) function names in the module.
        classes : list of str
            A list of (public) class names in the module.
        """
        mod = __import__(uri, fromlist=[uri.split('.')[-1]])
        # find all public objects in the module.
        obj_strs = [obj for obj in dir(mod) if not obj.startswith('_')]
        functions = []
        classes = []
        for obj_str in obj_strs:
            # find the actual object from its string representation
            if obj_str not in mod.__dict__:
                continue
            obj = mod.__dict__[obj_str]
            if (hasattr(obj, '__module__') 
                and self.package_name not in obj.__module__):
                continue

            # figure out if obj is a function or class
            if isinstance(obj, (FunctionType, BuiltinFunctionType)):
                functions.append(obj_str)
            else:
                try:
                    issubclass(obj, object)
                    classes.append(obj_str)
                except TypeError:
                    # not a function or class
                    pass
        return functions, classes

    def generate_api_doc(self, uri):
        '''Make autodoc documentation template string for a module

        Parameters
        ----------
        uri : string
            python location of module - e.g 'sphinx.builder'

        Returns
        -------
        S : string
            Contents of API doc
        '''
        # get the names of all classes and functions
        functions, classes = self._parse_module_with_import(uri)
        if not len(functions) and not len(classes) and DEBUG:
            print('WARNING: Empty -', uri)  # dbg
            return ''

        # Make a shorter version of the uri that omits the package name for
        # titles
        uri_short = re.sub(r'^%s\.' % self.package_name,'',uri)

        ad = '.. AUTO-GENERATED FILE -- DO NOT EDIT!\n\n'

        # Set the chapter title to read 'module' for all modules except for the
        # main packages
        if '.' in uri:
            title = 'Module: :mod:`' + uri_short + '`'
        else:
            title = ':mod:`' + uri_short + '`'
        ad += title + '\n' + self.rst_section_levels[1] * len(title)

        ad += '\n.. automodule:: ' + uri + '\n'
        ad += '\n.. currentmodule:: ' + uri + '\n'
        ad += '.. autosummary::\n\n'
        for f in functions:
            ad += '   ' + uri + '.' + f + '\n'
        ad += '\n'
        for c in classes:
            ad += '   ' + uri + '.' + c + '\n'
        ad += '\n'

        for f in functions:
            # must NOT exclude from index to keep cross-refs working
            full_f = uri + '.' + f
            ad += f + '\n'
            ad += self.rst_section_levels[2] * len(f) + '\n'
            ad += '\n.. autofunction:: ' + full_f + '\n\n'
        for c in classes:
            ad += '\n:class:`' + c + '`\n' \
                  + self.rst_section_levels[2] * \
                  (len(c)+9) + '\n\n'
            ad += '\n.. autoclass:: ' + c + '\n'
            # must NOT exclude from index to keep cross-refs working
            ad += '  :members:\n' \
                  '  :undoc-members:\n' \
                  '  :show-inheritance:\n' \
                  '\n' \
                  '  .. automethod:: __init__\n'
        return ad

    def _survives_exclude(self, matchstr):
        ''' Returns True if *matchstr* does not match patterns

        ``self.package_name`` removed from front of string if present
        '''
        for pat in self.skip_patterns:
            if re.compile(pat).search(matchstr):
                return False
        return True

    def _uri2path(self, uri):
        ''' Convert uri to absolute filepath

        Parameters
        ----------
        uri : string
            URI of python module to return path for

        Returns
        -------
        path : None or string
            Returns None if there is no valid path for this URI
            Otherwise returns absolute file system path for URI

        Examples
        --------
        >>> docwriter = ApiDocWriter('sphinx')
        >>> import sphinx
        >>> modpath = sphinx.__path__[0]
        >>> res = docwriter._uri2path('sphinx.builder')
        >>> res == os.path.join(modpath, 'builder.py')
        True
        >>> res = docwriter._uri2path('sphinx')
        >>> res == os.path.join(modpath, '__init__.py')
        True
        >>> docwriter._uri2path('sphinx.does_not_exist')

        '''
        if uri == self.package_name:
            return os.path.join(self.root_path, '__init__.py')
        path = uri.replace(self.package_name + '.', '')
        path = path.replace('.', os.path.sep)
        path = os.path.join(self.root_path, path)
        # XXX maybe check for extensions as well?
        if os.path.exists(path + '.py'): # file
            path += '.py'
        elif os.path.exists(os.path.join(path, '__init__.py')):
            path = os.path.join(path, '__init__.py')
        else:
            return None
        return path

    def _path2uri(self, dirpath):
        ''' Convert directory path to uri '''
        package_dir = self.package_name.replace('.', os.path.sep)
        relpath = dirpath.replace(self.root_path, package_dir)
        if relpath.startswith(os.path.sep):
            relpath = relpath[1:]
        return relpath.replace(os.path.sep, '.')

    def discover_modules(self):
        ''' Return module sequence discovered from ``self.package_name``


        Parameters
        ----------
        None

        Returns
        -------
        mods : sequence
            Sequence of module names within ``self.package_name``

        Examples
        --------
        >>> dw = ApiDocWriter('sphinx')
        >>> mods = dw.discover_modules()
        >>> 'sphinx.util' in mods
        True
        >>> dw.skip_patterns.append('\.util$')
        >>> 'sphinx.util' in dw.discover_modules()
        False
        >>>
        '''
        modules = [self.package_name]
        # raw directory parsing
        for dirpath, dirnames, filenames in os.walk(self.root_path,
                                                    topdown=False):
            # Check directory names for packages
            root_uri = self._path2uri(os.path.join(self.root_path,
                                                   dirpath))
            filenames = [f for f in filenames if f.endswith('.py')]
            uris = [u.strip('.py') for u in dirnames + filenames]
            for uri in uris:
                package_uri = '.'.join((root_uri, uri))
                if (self._uri2path(package_uri) and
                    self._survives_exclude(package_uri)):
                    try:
                        mod = __import__(package_uri, fromlist=['cesium'])
                        mod.__all__
                        modules.append(package_uri)
                    except (ImportError, AttributeError):
                        pass
        return sorted(modules)

    def write_modules_api(self, modules, outdir):
        # write the list
        written_modules = []
        for m in modules:
            api_str = self.generate_api_doc(m)
            if not api_str:
                continue
            # write out to file
            outfile = os.path.join(outdir,
                                   m + self.rst_extension)
            fileobj = open(outfile, 'wt')
            fileobj.write(api_str)
            fileobj.close()
            written_modules.append(m)
        self.written_modules = written_modules

    def write_api_docs(self, outdir):
        """Generate API reST files.

        Parameters
        ----------
        outdir : string
            Directory name in which to store files
            We create automatic filenames for each module

        Returns
        -------
        None

        Notes
        -----
        Sets self.written_modules to list of written modules
        """
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        # compose list of modules
        modules = self.discover_modules()
        self.write_modules_api(modules, outdir)

    def write_index(self, outdir, froot='gen', relative_to=None):
        """Make a reST API index file from written files

        Parameters
        ----------
        path : string
            Filename to write index to
        outdir : string
            Directory to which to write generated index file
        froot : string, optional
            root (filename without extension) of filename to write to
            Defaults to 'gen'.  We add ``self.rst_extension``.
        relative_to : string
            path to which written filenames are relative.  This
            component of the written file path will be removed from
            outdir, in the generated index.  Default is None, meaning,
            leave path as it is.
        """
        if self.written_modules is None:
            raise ValueError('No modules written')
        # Get full filename path
        path = os.path.join(outdir, froot+self.rst_extension)
        # Path written into index is relative to rootpath
        if relative_to is not None:
            relpath = (outdir + os.path.sep).replace(relative_to + os.path.sep, '')
        else:
            relpath = outdir
        print("outdir: ", relpath)
        idx = open(path,'wt')
        w = idx.write
        w('.. AUTO-GENERATED FILE -- DO NOT EDIT!\n\n')

        title = "API Reference"
        w(title + "\n")
        w("=" * len(title) + "\n\n")
        w('.. toctree::\n\n')
        for f in self.written_modules:
            w('   %s\n' % os.path.join(relpath,f))
        idx.close()
