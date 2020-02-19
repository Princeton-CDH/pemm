import os

from scripts.macomber_to_csv import MacomberToCSV


class TestMacomberToCSV:

    test_dir = os.path.dirname(__file__)
    data_dir = os.path.join(test_dir, '..', 'data')

    @classmethod
    def setup_class(cls):
        cls.mac = MacomberToCSV()

    def test_init(self):
        # schema should be set
        assert self.mac.schema
        # sanity check contents
        assert self.mac.schema['sheets']
        assert self.mac.schema['sheets'][0]['name'] == 'Story Instance'

    incipit_start = 'በእንተ፡ ዘከመ፡ አስተርአየቶ፡ ለቴዎፍሎስ፡ ሊቀ፡'

    def test_load_incipits(self):
        self.mac.load_incipits(os.path.join(self.data_dir, 'incipits.csv'))
        assert self.mac.incipits
        assert '1-A' in self.mac.incipits
        assert 'EMML' in self.mac.incipits['1-A']
        assert '6938' in self.mac.incipits['1-A']['EMML']
        assert self.mac.incipits['1-A']['EMML']['6938'] \
            .startswith(self.incipit_start)

    def test_get_incipit(self):
        incipit = self.mac.get_incipit('1-A', 'EMML', '6938')
        assert incipit.startswith(self.incipit_start)
        # missing
        assert self.mac.get_incipit('1-A', 'EMML', 'foo') == ''

    def test_add_story_instance(self):
        # load incipits to test incipit logic
        self.mac.load_incipits(os.path.join(self.data_dir, 'incipits.csv'))

        # match on a id + folio in a named collection section
        mac_id = '1-A'
        collection = 'PEth'
        match = self.mac.mss_id_re.match('41.8 (21r-30r)')
        self.mac.add_story_instance(collection, {'Macomber ID': mac_id},
                                    match)
        # check the last added story instance
        story_inst = self.mac.story_instances[-1]
        expected_values = {
            'Manuscript': '%s 41' % self.mac.collection_lookup[collection],
            'Miracle Number': '8',
            'Incipit': '',
            'Macomber Incipit': 0,
            'Confidence Score': '',
            'Canonical Story ID': mac_id,
            'Folio Start': '21r',
            'Folio End': '30r'
        }
        for key, val in expected_values.items():
            assert story_inst[key] == val, 'expected %s to be %s' % (key, val)

        # check incipit included when appropriate
        # mac 1-a EMML,6938,
        collection = 'EMML'
        match = self.mac.mss_id_re.match('6938 (9r)')
        self.mac.add_story_instance(collection, {'Macomber ID': mac_id},
                                    match)
        story_inst = self.mac.story_instances[-1]
        expected_values = {
            'Manuscript': '%s 6938' % self.mac.collection_lookup[collection],
            'Incipit': self.mac.get_incipit(mac_id, collection, '6938'),
            'Macomber Incipit': 1,
            'Confidence Score': 'High',
            'Canonical Story ID': mac_id,
            'Folio Start': '9r',
            'Folio End': '9r'
        }
        for key, val in expected_values.items():
            assert story_inst[key] == val, 'expected %s to be %s' % (key, val)

        # test handling rv notation, e.g.EMIP: 601.13 (12rv)
        mac_id = '46'
        collection = 'EMIP'
        match = self.mac.mss_id_re.match('601.13 (12rv)')
        self.mac.add_story_instance(collection, {'Macomber ID': mac_id},
                                    match)
        story_inst = self.mac.story_instances[-1]
        assert story_inst['Folio Start'] == '12r'
        assert story_inst['Folio End'] == '12v'

        # test mss id not included in regex match, passed in as param
        # e.g. from entry like EMML: 4205 (25v + 51r + 26r)
        mac_id = '19'
        collection = 'EMML'
        match = self.mac.folio_re.match('25v')
        mss_id = '4205'
        self.mac.add_story_instance(collection, {'Macomber ID': mac_id},
                                    match, mss_id)
        story_inst = self.mac.story_instances[-1]
        assert story_inst['Manuscript'] == '%s %s' % (
            self.mac.collection_lookup[collection], mss_id)
        # check folios also
        assert story_inst['Folio Start'] == '25v'
        assert story_inst['Folio End'] == '25v'

        # ignore .? for order, e.g. EMDL: 681.? (103v–104r);
        mac_id = '138'
        collection = 'EMDL'
        match = self.mac.mss_id_re.match('681.? (103v–104r);')
        self.mac.add_story_instance(collection, {'Macomber ID': mac_id},
                                    match)
        story_inst = self.mac.story_instances[-1]
        assert story_inst['Manuscript'] == '%s 681' % (
            self.mac.collection_lookup[collection])
        assert not story_inst['Miracle Number']
        assert story_inst['Folio Start'] == '103v'
        assert story_inst['Folio End'] == '104r'

    def test_parse_manuscripts(self):
        # handles multiple references and adds story instances
        # clear out story instance list
        self.mac.story_instances = []
        mac_id = '1-A'
        collection = 'PEth'
        self.mac.parse_manuscripts(
            collection, '41.29 (61r-62r); 43.26 (33r-34v);',
            {'Macomber ID': mac_id})
        assert len(self.mac.story_instances) == 2, \
            'should add 2 story instances'
        assert all(si['Canonical Story ID'] == mac_id
                   for si in self.mac.story_instances)
        # sanity check handoff to add story instance
        assert self.mac.story_instances[0]['Manuscript'] == \
            '%s 41' % self.mac.collection_lookup[collection]
        assert self.mac.story_instances[0]['Miracle Number'] == '29'
        assert self.mac.story_instances[0]['Folio Start'] == '61r'
        # also adds to manuscript list
        assert collection in self.mac.manuscripts
        assert '41' in self.mac.manuscripts[collection]

        # handle multiple locations in single mss, e.g.
        # EMML: 6938 (43v); 5520 (53r); 4205 (25v + 51r + 26r)
        self.mac.story_instances = []
        mac_id = '19'
        collection = 'EMML'
        self.mac.parse_manuscripts(
            collection, '5520 (53r); 4205 (25v + 51r + 26r)',
            {'Macomber ID': mac_id})
        assert len(self.mac.story_instances) == 4, \
            'should add 4 story instances'
        # first story
        assert self.mac.story_instances[0]['Manuscript'] == \
            '%s 5520' % self.mac.collection_lookup[collection]
        assert self.mac.story_instances[0]['Folio Start'] == '53r'
        # second story
        assert self.mac.story_instances[1]['Manuscript'] == \
            '%s 4205' % self.mac.collection_lookup[collection]
        assert self.mac.story_instances[1]['Folio Start'] == '25v'
        # third story in same mss as second
        assert self.mac.story_instances[2]['Manuscript'] == \
            '%s 4205' % self.mac.collection_lookup[collection]
        assert self.mac.story_instances[2]['Folio Start'] == '51r'
        # fourth story in same mss as second
        assert self.mac.story_instances[3]['Manuscript'] == \
            '%s 4205' % self.mac.collection_lookup[collection]
        assert self.mac.story_instances[3]['Folio Start'] == '26r'

        # handle MSS: style references, e.g. MSS: CRA 53-17; VLVE 298 (151a).
        collection = 'CRA'
        self.mac.parse_manuscripts(collection, '298 (151a)',
                                   {'Macomber ID': 85})
        story_inst = self.mac.story_instances[-1]
        assert story_inst['Manuscript'] == \
            '%s 298' % self.mac.collection_lookup[collection]
        assert story_inst['Folio Start'] == '151a'
        assert story_inst['Folio End'] == '151a'

        # test unparsable
        self.mac.story_instances = []
        self.mac.parse_manuscripts(collection, 'foobar', {'Macomber ID': 85})
        assert not self.mac.story_instances
        assert 'foobar' in self.mac.mss_unparsed