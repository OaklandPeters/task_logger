import unittest
import operator
import copy
#----
from enum import Enum, EnumGroup, BasicEnumGroup 



class BasicEnumGroupTests(unittest.TestCase):
    constructor = BasicEnumGroup
    def setUp(self):
        self.g1a = self.constructor('attempting')
        self.g1b = self.constructor('attempting')
        self.g1c = self.constructor('attempting')
        self.g2  = self.constructor('attempt')
        
    def test_group_equality(self):

        
        self.assertEqual(self.g1a, self.g1b)
        self.assertEqual(self.g1a, self.g1c)
        self.assertEqual(self.g1b, self.g1c)
        self.assertNotEqual(self.g1a, self.g2)
        
        
        
    def test_contains(self):
        self.assert_(
            'attempt' not in self.g1a
        )
        self.assert_(
            'attempt' in self.g2
        )
        self.assert_(
            'non' not in self.g1a
        )
    def test_name(self):
        self.assertEqual(self.g1a.name, 'attempting')
        self.assertEqual(self.g1b.name, 'attempting')
        self.assertEqual(self.g2.name, 'attempt')
    def test_string_comparison(self):
        pass
    def test_errors(self):
        self.assertRaises(TypeError, lambda: self.g1a['attempting'])
        self.assertRaises(IndexError, lambda: self.g1b[1])
        self.assertRaises(TypeError, lambda: operator.delitem(self.g1c, 0) )


class EnumGroupTests(unittest.TestCase):
    constructor = EnumGroup
    def setUp(self):
        self.g1a = self.constructor(('attempting',))
        self.g1b = self.constructor(['attempting'])
        self.g1c = self.constructor('attempting',)
        self.g2  = self.constructor('attempt',)
    def test_group_equality(self):
        self.assert_(self.g1a == self.g1b)
        self.assert_(self.g1a == self.g1c)
        self.assert_(self.g1b == self.g1c)
        self.assert_(self.g1a != self.g2)
    def test_contains(self):
        self.assert_(
            'attempt' not in self.g1a
        )
        self.assert_(
            'attempt' in self.g2
        )
        self.assert_(
            'non' not in self.g1a
        )
    def test_name(self):
        self.assertEqual(self.g1a.name, 'attempting')
        self.assertEqual(self.g1b.name, 'attempting')
        self.assertEqual(self.g2.name, 'attempt')
    def test_string_comparison(self):
        pass
    def test_errors(self):
        self.assertRaises(TypeError, lambda: self.g1a['attempting'])
        self.assertRaises(IndexError, lambda: self.g1b[1])

        
class EnumTests(unittest.TestCase):
    def setUp(self):
        self.States = Enum((
            ('attempting', 'attempt','attempted'),
            ('errored', 'error'),
            ('completed', 'complete')
        ))
        self.expected = [
            ['attempting', 'attempt','attempted'],
            ['errored', 'error'],
            ['completed', 'complete']
        ]
        self.groups = [
            EnumGroup(['attempting', 'attempt','attempted']),
            EnumGroup(['errored', 'error']),
            EnumGroup(['completed', 'complete'])
        ]
    
    def test_getitem_repr(self):
        state = self.States['attempting']
        self.assert_(isinstance(state, EnumGroup), 
            "Is not instance of EnumGroup"
        )
        self.assertEqual(
            repr(state),
            "['attempting', 'attempt', 'attempted']",
            "States does not match repr of expectation."
        )

    
    def test_iter(self):
        names = ['attempting','errored','completed']
        for state, name, expected in zip(self.States,self.States.names, names):
            self.assert_(
                state.name == name == expected,
                "Inequality among: {0}, {1}, {2}".format(
                    state.name, name, expected
                )
            )
                
    def test_group_comparison(self):
        #For Enum
        self.assertEqual(self.States,self.groups)
        #Group comparison
        self.assertEqual(
            self.States['attempting'],
            EnumGroup(['attempting', 'attempt','attempted']),
            "group comparison"
        ) 
    def test_string_comparison(self):
        #For Enum collection
        self.assertEqual(self.States,self.expected)
        #For single groups
        compared = all(
            (exp == state)
            for exp, state in zip(self.expected, self.States)
        )
        self.assert_(compared, "Iterator failed.")       
        self.assertEqual(
            list(elm for elm in self.States),
            self.expected,
            "Groups from iter do not match expectations."
        )
    def test_aliases_comparison(self):
        States = self.States
        self.assert_('attempting' in States['attempting'])
        self.assert_('attempt' in States['attempting'])
        self.assert_('attempted' in States['attempting'])
        self.assert_('attempting' in States['attempt'])
        self.assert_('attempt' in States['attempt'])
        self.assert_('attempted' in States['attempt'])
        self.assert_('attempting' in States['attempted'])
        self.assert_('attempt' in States['attempted'])
        self.assert_('attempted' in States['attempted'])
        
        self.assert_('attempt' not in States['errored'])
        self.assert_('attempt' not in States['completed'])
        
        self.assertRaises(ValueError, lambda: 'attempt' not in States['foo'])
        
    def test_corner_case(self):
        self.assertRaises(TypeError, lambda: Enum([(2,),('c',)]))


class OldBasicTests(unittest.TestCase):
    """Tests for the old form of Enum().
    Leaving here, because they may be useful to adapt to the new Enum().
    """
    def setUp(self):
        #(input, output)
        self.correct_tests = (
            ('completed','completed'),
            ('Complete', 'completed'),
            ('complete', 'completed'),
            ('COMPLETE', 'completed')
        )
        self.incorrect_tests = (
            ('jabba', KeyError),
            (None, KeyError)
        )
        
        self.States = enum.Enum(
            ('completed',['complete','done','finished', 'completed']),
            ('errored',['error','errored','exception','stopped']),
            ('attempting',['attempting','attempted','in progress','in_progress','running'])
        )
        
        self.expected_groups = dict([
            ('completed',['complete','done','finished', 'completed']),
            ('errored',['error','errored','exception','stopped']),
            ('attempting',['attempting','attempted','in_progress','in_progress','running'])
        ])
        
    def standard_tests(self, States):
        for test in self.correct_tests:
            self.assertEqual(
                test[1],
                States[test[0]],
                "States['{0}']=={1} does not match expectation: {2}".format(
                    test[0], States[test[0]], test[1]
                )
            )
        for test in self.incorrect_tests:
            self.assertRaises(test[1], lambda: States[test[0]])

    def dep_test_Enum(self):
        States = enum.Enum(
            ('completed',['complete','done','finished']),
            ('errored',['error','errored','exception','stopped']),
            ('attempting',['attempting','attempted','in progress','in_progress','running'])
        )
        self.standard_tests(States)
        
    def dep_test_options(self):
        existing = enum.Enum.simplifiers
        States = enum.Enum(
            ('completed',['complete','done','finished']),
            ('errored',['error','errored','exception','stopped']),
            ('attempting',['attempting','attempted','in progress','in_progress','running']),
            simplifiers=enum.Enum._simplifiers+[lambda obj: obj.replace('=','')]
        )
        special_tests = (
            ("compl=eted","completed"),
            ("compl=ete","completed")
        )
        self.standard_tests(States)
        for test in special_tests:
            self.assertEqual(
                test[1],
                States[test[0]],
                "States['{0}']=={1} does not match expectation: {2}".format(
                    test[0], States[test[0]], test[1]
                )
            )
    
    def dep_test_StringEnum(self):
        States = enum.StringEnum(
            ('completed',['complete','done','finished']),
            ('errored',['error','errored','exception','stopped']),
            ('attempting',['attempting','attempted','in progress','in_progress','running'])
        )
        self.standard_tests(States)
    
    def dep_test_mapping(self):
        self.assertEqual(
            self.States.keys(),
            self.expected_groups.keys(),
            "Incorrect keys."
        )
        self.assertEqual(
            self.States.names,
            self.expected_groups.keys(),
            "Incorrect names."
        )
        
        self.assertEqual(
            self.States.values(),
            self.expected_groups.values(),
            "Incorrect values."
        )
        self.assertEqual(
            self.States.aliases,
            self.expected_groups.values(),
            "Incorrect aliases."
        )
        
    def dep_test_magic_methods(self):
        # __contains__
        self.assert_('completed' in self.States, "Incorrect __contains__")
        self.assert_('COMPLETED' in self.States, "Incorrect __contains__")
        self.assert_('jabba' not in self.States, "Incorrect __contains__")
        
        # __len__
        self.assertEqual(len(self.States), 3, "Incorrect __length__")
        
        # __iter__
        names = sorted([name for name in iter(self.States)])
        self.assertEqual(
            names, ['attempting', 'completed', 'errored'],
            "Incorrect __iter__"
        )
        
        # __setitem__
        States = copy.deepcopy(self.States)
        assignment = ['c', 'co', 'c o']
        expected = ('completed', ['c', 'co', 'c_o', 'completed'])
        States['completed'] = assignment
        self.assertEqual(
            States.groups['completed'],
            expected,
            "Incorrect __setitem__"
        )

if __name__ == "__main__":
    unittest.main()