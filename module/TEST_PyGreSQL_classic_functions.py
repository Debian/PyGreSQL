#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Test the classic PyGreSQL interface.

Sub-tests for the module functions and constants.

Contributed by Christoph Zwerschke.

These tests do not need a database to test against.

"""


try:
    import unittest2 as unittest  # for Python < 2.7
except ImportError:
    import unittest

import re

import pg  # the module under test

try:
    long
except NameError:  # Python >= 3.0
    long = int

unicode_strings = str is not bytes


class TestAuxiliaryFunctions(unittest.TestCase):
    """Test the auxiliary functions external to the connection class."""

    def testIsQuoted(self):
        f = pg._is_quoted
        self.assertTrue(f('A'))
        self.assertTrue(f('0'))
        self.assertTrue(f('#'))
        self.assertTrue(f('*'))
        self.assertTrue(f('.'))
        self.assertTrue(f(' '))
        self.assertTrue(f('a b'))
        self.assertTrue(f('a+b'))
        self.assertTrue(f('a*b'))
        self.assertTrue(f('a.b'))
        self.assertTrue(f('0ab'))
        self.assertTrue(f('aBc'))
        self.assertTrue(f('ABC'))
        self.assertTrue(f('"a"'))
        self.assertTrue(not f('a'))
        self.assertTrue(not f('a0'))
        self.assertTrue(not f('_'))
        self.assertTrue(not f('_a'))
        self.assertTrue(not f('_0'))
        self.assertTrue(not f('_a_0_'))
        self.assertTrue(not f('ab'))
        self.assertTrue(not f('ab0'))
        self.assertTrue(not f('abc'))
        self.assertTrue(not f('abc'))
        if 'ä'.isalpha():
            self.assertTrue(not f('ä'))
            self.assertTrue(f('Ä'))
            self.assertTrue(not f('käse'))
            self.assertTrue(f('Käse'))
            self.assertTrue(not f('emmentaler_käse'))
            self.assertTrue(f('emmentaler käse'))
            self.assertTrue(f('EmmentalerKäse'))
            self.assertTrue(f('Emmentaler Käse'))

    def testIsUnquoted(self):
        f = pg._is_unquoted
        self.assertTrue(f('A'))
        self.assertTrue(not f('0'))
        self.assertTrue(not f('#'))
        self.assertTrue(not f('*'))
        self.assertTrue(not f('.'))
        self.assertTrue(not f(' '))
        self.assertTrue(not f('a b'))
        self.assertTrue(not f('a+b'))
        self.assertTrue(not f('a*b'))
        self.assertTrue(not f('a.b'))
        self.assertTrue(not f('0ab'))
        self.assertTrue(f('aBc'))
        self.assertTrue(f('ABC'))
        self.assertTrue(not f('"a"'))
        self.assertTrue(f('a0'))
        self.assertTrue(f('_'))
        self.assertTrue(f('_a'))
        self.assertTrue(f('_0'))
        self.assertTrue(f('_a_0_'))
        self.assertTrue(f('ab'))
        self.assertTrue(f('ab0'))
        self.assertTrue(f('abc'))
        if 'ä'.isalpha():
            self.assertTrue(f('ä'))
            self.assertTrue(f('Ä'))
            self.assertTrue(f('käse'))
            self.assertTrue(f('Käse'))
            self.assertTrue(f('emmentaler_käse'))
            self.assertTrue(not f('emmentaler käse'))
            self.assertTrue(f('EmmentalerKäse'))
            self.assertTrue(not f('Emmentaler Käse'))

    def testSplitFirstPart(self):
        f = pg._split_first_part
        self.assertEqual(f('a.b'), ['a', 'b'])
        self.assertEqual(f('a.b.c'), ['a', 'b.c'])
        self.assertEqual(f('"a.b".c'), ['a.b', 'c'])
        self.assertEqual(f('a."b.c"'), ['a', '"b.c"'])
        self.assertEqual(f('A.b.c'), ['a', 'b.c'])
        self.assertEqual(f('Ab.c'), ['ab', 'c'])
        self.assertEqual(f('aB.c'), ['ab', 'c'])
        self.assertEqual(f('AB.c'), ['ab', 'c'])
        self.assertEqual(f('A b.c'), ['A b', 'c'])
        self.assertEqual(f('a B.c'), ['a B', 'c'])
        self.assertEqual(f('"A".b.c'), ['A', 'b.c'])
        self.assertEqual(f('"A""B".c'), ['A"B', 'c'])
        self.assertEqual(f('a.b.c.d.e.f.g'), ['a', 'b.c.d.e.f.g'])
        self.assertEqual(f('"a.b.c.d.e.f".g'), ['a.b.c.d.e.f', 'g'])
        self.assertEqual(f('a.B.c.D.e.F.g'), ['a', 'B.c.D.e.F.g'])
        self.assertEqual(f('A.b.C.d.E.f.G'), ['a', 'b.C.d.E.f.G'])

    def testSplitParts(self):
        f = pg._split_parts
        self.assertEqual(f('a.b'), ['a', 'b'])
        self.assertEqual(f('a.b.c'), ['a', 'b', 'c'])
        self.assertEqual(f('"a.b".c'), ['a.b', 'c'])
        self.assertEqual(f('a."b.c"'), ['a', 'b.c'])
        self.assertEqual(f('A.b.c'), ['a', 'b', 'c'])
        self.assertEqual(f('Ab.c'), ['ab', 'c'])
        self.assertEqual(f('aB.c'), ['ab', 'c'])
        self.assertEqual(f('AB.c'), ['ab', 'c'])
        self.assertEqual(f('A b.c'), ['A b', 'c'])
        self.assertEqual(f('a B.c'), ['a B', 'c'])
        self.assertEqual(f('"A".b.c'), ['A', 'b', 'c'])
        self.assertEqual(f('"A""B".c'), ['A"B', 'c'])
        self.assertEqual(f('a.b.c.d.e.f.g'),
            ['a', 'b', 'c', 'd', 'e', 'f', 'g'])
        self.assertEqual(f('"a.b.c.d.e.f".g'),
            ['a.b.c.d.e.f', 'g'])
        self.assertEqual(f('a.B.c.D.e.F.g'),
            ['a', 'b', 'c', 'd', 'e', 'f', 'g'])
        self.assertEqual(f('A.b.C.d.E.f.G'),
            ['a', 'b', 'c', 'd', 'e', 'f', 'g'])

    def testJoinParts(self):
        f = pg._join_parts
        self.assertEqual(f(('a',)), 'a')
        self.assertEqual(f(('a', 'b')), 'a.b')
        self.assertEqual(f(('a', 'b', 'c')), 'a.b.c')
        self.assertEqual(f(('a', 'b', 'c', 'd', 'e', 'f', 'g')),
            'a.b.c.d.e.f.g')
        self.assertEqual(f(('A', 'b')), '"A".b')
        self.assertEqual(f(('a', 'B')), 'a."B"')
        self.assertEqual(f(('a b', 'c')), '"a b".c')
        self.assertEqual(f(('a', 'b c')), 'a."b c"')
        self.assertEqual(f(('a_b', 'c')), 'a_b.c')
        self.assertEqual(f(('a', 'b_c')), 'a.b_c')
        self.assertEqual(f(('0', 'a')), '"0".a')
        self.assertEqual(f(('0_', 'a')), '"0_".a')
        self.assertEqual(f(('_0', 'a')), '_0.a')
        self.assertEqual(f(('_a', 'b')), '_a.b')
        self.assertEqual(f(('a', 'B', '0', 'c0', 'C0',
            'd e', 'f_g', 'h.i', 'jklm', 'nopq')),
            'a."B"."0".c0."C0"."d e".f_g."h.i".jklm.nopq')

    def testOidKey(self):
        f = pg._oid_key
        self.assertEqual(f('a'), 'oid(a)')
        self.assertEqual(f('a.b'), 'oid(a.b)')


class TestHasConnect(unittest.TestCase):
    """Test existence of basic pg module functions."""

    def testhasPgError(self):
        self.assertTrue(issubclass(pg.Error, Exception))

    def testhasPgWarning(self):
        self.assertTrue(issubclass(pg.Warning, Exception))

    def testhasPgInterfaceError(self):
        self.assertTrue(issubclass(pg.InterfaceError, pg.Error))

    def testhasPgDatabaseError(self):
        self.assertTrue(issubclass(pg.DatabaseError, pg.Error))

    def testhasPgInternalError(self):
        self.assertTrue(issubclass(pg.InternalError, pg.DatabaseError))

    def testhasPgOperationalError(self):
        self.assertTrue(issubclass(pg.OperationalError, pg.DatabaseError))

    def testhasPgProgrammingError(self):
        self.assertTrue(issubclass(pg.ProgrammingError, pg.DatabaseError))

    def testhasPgIntegrityError(self):
        self.assertTrue(issubclass(pg.IntegrityError, pg.DatabaseError))

    def testhasPgDataError(self):
        self.assertTrue(issubclass(pg.DataError, pg.DatabaseError))

    def testhasPgNotSupportedError(self):
        self.assertTrue(issubclass(pg.NotSupportedError, pg.DatabaseError))

    def testhasConnect(self):
        self.assertTrue(callable(pg.connect))

    def testhasEscapeString(self):
        self.assertTrue(callable(pg.escape_string))

    def testhasEscapeBytea(self):
        self.assertTrue(callable(pg.escape_bytea))

    def testhasUnescapeBytea(self):
        self.assertTrue(callable(pg.unescape_bytea))

    def testDefHost(self):
        d0 = pg.get_defhost()
        d1 = 'pgtesthost'
        pg.set_defhost(d1)
        self.assertEqual(pg.get_defhost(), d1)
        pg.set_defhost(d0)
        self.assertEqual(pg.get_defhost(), d0)

    def testDefPort(self):
        d0 = pg.get_defport()
        d1 = 1234
        pg.set_defport(d1)
        self.assertEqual(pg.get_defport(), d1)
        if d0 is None:
            d0 = -1
        pg.set_defport(d0)
        if d0 == -1:
            d0 = None
        self.assertEqual(pg.get_defport(), d0)

    def testDefOpt(self):
        d0 = pg.get_defopt()
        d1 = '-h pgtesthost -p 1234'
        pg.set_defopt(d1)
        self.assertEqual(pg.get_defopt(), d1)
        pg.set_defopt(d0)
        self.assertEqual(pg.get_defopt(), d0)

    def testDefTty(self):
        d0 = pg.get_deftty()
        d1 = 'pgtesttty'
        pg.set_deftty(d1)
        self.assertEqual(pg.get_deftty(), d1)
        pg.set_deftty(d0)
        self.assertEqual(pg.get_deftty(), d0)

    def testDefBase(self):
        d0 = pg.get_defbase()
        d1 = 'pgtestdb'
        pg.set_defbase(d1)
        self.assertEqual(pg.get_defbase(), d1)
        pg.set_defbase(d0)
        self.assertEqual(pg.get_defbase(), d0)


class TestEscapeFunctions(unittest.TestCase):
    """"Test pg escape and unescape functions."""

    def testEscapeString(self):
        f = pg.escape_string
        r = f(b'plain')
        self.assertIsInstance(r, str)
        self.assertEqual(r, 'plain')
        r = f(u'plain')
        self.assertIsInstance(r, str)
        self.assertEqual(r, 'plain')
        r = f(u"das is' käse".encode('utf-8'))
        self.assertIsInstance(r, str)
        self.assertEqual(r, "das is'' käse")
        if unicode_strings:
            r = f("das is' käse")
            self.assertIsInstance(r, str)
            self.assertEqual(r, "das is'' käse")
        r = f(r"It's fine to have a \ inside.")
        self.assertEqual(r, r"It''s fine to have a \\ inside.")

    def testEscapeBytea(self):
        f = pg.escape_bytea
        r = f(b'plain')
        self.assertIsInstance(r, str)
        self.assertEqual(r, 'plain')
        r = f(u'plain')
        self.assertIsInstance(r, str)
        self.assertEqual(r, 'plain')
        r = f(u"das is' käse".encode('utf-8'))
        self.assertIsInstance(r, str)
        self.assertEqual(r, r"das is'' k\\303\\244se")
        if unicode_strings:
            r = f("das is' käse")
            self.assertIsInstance(r, str)
            self.assertEqual(r, r"das is'' k\\303\\244se")
        r = f(b'O\x00ps\xff!')
        self.assertEqual(r, r'O\\000ps\\377!')

    def testUnescapeBytea(self):
        f = pg.unescape_bytea
        r = f(b'plain')
        self.assertIsInstance(r, str)
        self.assertEqual(r, 'plain')
        r = f(u'plain')
        self.assertIsInstance(r, str)
        self.assertEqual(r, 'plain')
        r = f(b"das is' k\\303\\244se")
        self.assertIsInstance(r, str)
        self.assertEqual(r, "das is' käse")
        r = f(u"das is' k\\303\\244se")
        self.assertIsInstance(r, str)
        self.assertEqual(r, "das is' käse")
        r = f(r'O\\000ps\\377!')
        self.assertEqual(r, r'O\000ps\377!')


class TestConfigFunctions(unittest.TestCase):
    """Test the functions for changing default settings.

    The effect of most of these cannot be tested here, because that
    needs a database connection.  So we merely test their existence here.

    """

    def testGetDecimalPoint(self):
        r = pg.get_decimal_point()
        self.assertIsInstance(r, str)
        self.assertEqual(r, '.')

    def testSetDecimalPoint(self):
        point = pg.get_decimal_point()
        pg.set_decimal_point('*')
        r = pg.get_decimal_point()
        self.assertIsInstance(r, str)
        self.assertEqual(r, '*')
        pg.set_decimal_point(point)

    def testSetDecimal(self):
        decimal_class = pg.Decimal
        pg.set_decimal(long)
        pg.set_decimal(decimal_class)

    def testSetNamedresult(self):
        pg.set_namedresult(lambda q: q.getresult())
        pg.set_namedresult(pg._namedresult)


class TestModuleConstants(unittest.TestCase):
    """Test the existence of the documented module constants."""

    def testVersion(self):
        v = pg.version
        self.assertIsInstance(v, str)
        # make sure the version conforms to PEP440
        re_version = r"""^
            (\d[\.\d]*(?<= \d))
            ((?:[abc]|rc)\d+)?
            (?:(\.post\d+))?
            (?:(\.dev\d+))?
            (?:(\+(?![.])[a-zA-Z0-9\.]*[a-zA-Z0-9]))?
            $"""
        match = re.match(re_version, v, re.X)
        self.assertIsNotNone(match)


if __name__ == '__main__':
    unittest.main()
