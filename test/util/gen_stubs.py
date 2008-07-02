#################################### IMPORTS ###################################

from __future__ import with_statement
from optparse import OptionParser
from inspect import isclass, ismodule, getdoc, isgetsetdescriptor, getmembers
from unittest import TestCase

import pygame, sys, datetime, re, types
import relative_indentation

################################ TESTS DIRECTORY ###############################

from os.path import normpath, join, dirname, abspath

sys.path.append( abspath(normpath( join(dirname(__file__), '../') )) )

################################################################################

ROOT_PACKAGE = 'pygame'

#################################### IGNORES ###################################

# pygame.sprite.Sprite.__module__ = 'pygame.sprite' 
# pygame.sprite.Rect.__module__   = 'pygame'

# In [7]: pygame.overlay.Overlay.__name__
# Out[7]: 'overlay'

# Mapping of callable to module where it's defined
REAL_HOMES = {
    pygame.rect.Rect         : pygame.rect,
    pygame.mask.from_surface : pygame.mask,
    pygame.time.get_ticks    : pygame.time,
    pygame.event.Event       : pygame.event,
    pygame.event.event_name  : pygame.event,
    pygame.font.SysFont      : pygame.font,
    pygame.font.get_fonts    : pygame.font,
    pygame.font.match_font   : pygame.font,
}

# Types that need instantiating before inspection
INSTANTIATE = (
    pygame.event.Event,
    pygame.cdrom.CD,
    pygame.joystick.Joystick,
    pygame.time.Clock,
    pygame.mixer.Channel,
    pygame.movie.Movie,
    pygame.mask.Mask,
    pygame.display.Info,
)

##################################### TODO #####################################

"""

1)

    Test

2)

    Properties
    
    Helper functions that return objects, ie time.Clock() etc

"""

################################ STUB TEMPLATES ################################

date = datetime.datetime.now().date()

STUB_TEMPLATE = relative_indentation.Template ( '''
    def ${test_name}(self):

        # __doc__ (as of %s) for ${unitname}:

          ${comments}

        self.assert_(test_not_implemented()) ''' % date, 

        strip_common = 0, strip_excess = 0
)

############################## REGULAR EXPRESSIONS #############################

module_re = re.compile(r"pygame\.([^.]*)\.?")

#################################### OPTIONS ###################################

opt_parser = OptionParser()

opt_parser.add_option (
     "-l",  "--list", dest = "list", action = 'store_true',
     help   = "list only test names not stubs" )

opt_parser.set_usage(
"""
$ %prog ROOT

eg. 

$ %prog sprite.Sprite

def test_add(self):

    # Doc string for pygame.sprite.Sprite:

    ...
"""
)

################################### FUNCTIONS ##################################

def module_in_package(module, pkg):
    return ("%s." % pkg.__name__) in module.__name__

def get_package_modules(pkg):
    modules = (getattr(pkg, x) for x in dir(pkg) if is_public(x))
    return [m for m in modules if ismodule(m) and module_in_package(m, pkg)]
                                                 # Don't want to pick up 
                                                 # string module for example
def py_comment(input_str):
    return '\n'.join (
        [('# ' + l) for l in input_str.split('\n')]
    )

def is_public(obj_name):
    return not obj_name.startswith(('__','_'))

def is_test(f):
    return f.__name__.startswith('test_')

def get_callables(obj, if_of = None, check_where_defined=False):
    publics = (getattr(obj, x) for x in dir(obj) if is_public(x))
    callables = [x for x in publics if callable(x)]
    
    if check_where_defined:
        callables = [ c for c in callables if ROOT_PACKAGE in c.__module__ 
                        and (c not in REAL_HOMES or REAL_HOMES[c] is obj) ]

    if if_of:
        callables = [x for x in callables if if_of(x)] # isclass, ismethod etc
    
    return set(callables)

def get_class_from_test_case(TC):
    TC = TC.__name__
    if 'Type' in TC:
        return '.' + TC[:TC.index('Type')]

def names_of(*args):
    return tuple(map(lambda o: o.__name__, args))

def callable_name(module, c, class_=None):
    if class_:
        return '%s.%s.%s' % names_of(module, class_, c)
    else:
        return '%s.%s' % names_of(module, c)

################################################################################

def test_stub(f, module, parent_class = None):
    test_name = 'test_%s' % f.__name__
    unit_name = callable_name(module, f, parent_class)

    stub = STUB_TEMPLATE.render (

        test_name = test_name,
        comments = py_comment(getdoc(f) or ''),
        unitname = unit_name,
    )

    return unit_name, stub

def make_stubs(seq, module, class_=None):
    return dict( test_stub(f, module, class_) for f in seq )

def module_stubs(module):
    stubs = {}
    all_callables = get_callables(module, check_where_defined = True)
    classes = set(c for c in all_callables if isclass(c))

    for class_ in classes:
        callables = (m[1] for m in getmembers(class_, isgetsetdescriptor))
        callables = set(c for c in callables if is_public(c.__name__))
        stubs.update (
            make_stubs(callables ^ get_callables(class_), module, class_) 
        )

    stubs.update(make_stubs(all_callables - classes, module))

    return stubs

def package_stubs(package):
    stubs = dict()

    for module in get_package_modules(package):
        stubs.update(module_stubs(module))

    return stubs

def already_tested_in_module(module):
    already = []

    mod_name =  module.__name__
    test_name = "%s_test" % mod_name[7:]
    
    try: test_file = __import__(test_name)
    except ImportError:
        return []
    
    classes = get_callables(test_file, isclass)
    test_cases = (t for t in classes if TestCase in t.__bases__)
    
    for class_ in test_cases:
        class_tested = get_class_from_test_case(class_) or ''

        for test in get_callables(class_, is_test):
            fname = test.__name__[5:].split('__')[0]
            already.append("%s%s.%s" % (mod_name, class_tested, fname))
    
    return already

def already_tested_in_package(package):
    already = []

    for module in get_package_modules(package):
        already += already_tested_in_module(module)

    return already

def get_stubs(root):
    module_root = module_re.search(root)
    if module_root:
        module = getattr(pygame, module_root.group(1))
        stubs = module_stubs(module)
        tested = already_tested_in_module(module)
    else:
        stubs = package_stubs(pygame)
        tested = already_tested_in_package(pygame)

    return stubs, tested

if __name__ == "__main__":
    options, args = opt_parser.parse_args()
    if not sys.argv[1:]: 
        sys.exit(opt_parser.print_help())

    root = args and args[0] or ROOT_PACKAGE
    if not root.startswith(ROOT_PACKAGE):
        root = '%s.%s' % (ROOT_PACKAGE, root)

    stubs, tested = get_stubs(root)

    for fname in sorted(s for s in stubs.iterkeys() if s not in tested):
        if not fname.startswith(root): continue  # eg. module.Class
        stub = stubs[fname]
        print options.list and fname or stub

################################################################################