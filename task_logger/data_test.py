import unittest

from data import CompoundDataSet, read_dir, make_data_set


# For now at least,
#    (1) instances of CompoundDataSet go in this file
#    (2) datasets: classes or instances ???

class DataSetTests(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_VirtualChemistry(self):
        VirtualChemistry = CompoundDataSet(
            filepaths = list(read_dir(
                "/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/",
                match="Virtual_Chemistry*.sdf.expanded"
            ))
        )
        base = '/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/' 
        expected = [
            base + 'Virtual_Chemistry_01.sdf.expanded'
        ]
        expected_len = 48
        
        # Test filepaths property
        self.assertEqual(expected[0], VirtualChemistry.filepaths[0])
        self.assertEqual(len(VirtualChemistry.filepaths), expected_len)
        # Test sequence behavior for main object
        self.assertEqual(expected[0], VirtualChemistry[0])
        self.assertEqual(len(VirtualChemistry), expected_len)
        
    def test_DrugLike(self):
        DrugLike = CompoundDataSet(
            filepaths = list(read_dir(
                "/data/htdocs/cccid/build/compounds-db/data-files/druglike/",
                match="Drug-Like*.sdf.expanded"
            ))
        )
        base = '/data/htdocs/cccid/build/compounds-db/data-files/druglike/' 
        expected = [
            base + 'Drug-Like_Compounds_MMFF_Ligprep_01.sdf.expanded'
        ]
        expected_len = 29
        
        self.assertEqual(expected[0], DrugLike.filepaths[0])
        self.assertEqual(len(DrugLike.filepaths), expected_len)
        # Test sequence behavior for main object
        self.assertEqual(expected[0], DrugLike[0])
        self.assertEqual(len(DrugLike), expected_len)
    
    def test_factory(self):
        dl1 = CompoundDataSet(
            name = 'druglike',
            filepaths = list(read_dir(
                "/data/htdocs/cccid/build/compounds-db/data-files/druglike/",
                match="Drug-Like*.sdf.expanded"
            ))
        )
        config = {
            'name':'druglike', 
            'directory':"/data/htdocs/cccid/build/compounds-db/data-files/druglike/", 
            'match':"Drug-Like*.sdf.expanded"
        }
        dl2 = make_data_set(**config)
        
        
        for fp1, fp2 in zip(sorted(dl1.filepaths), sorted(dl2.filepaths)):
            self.assertEqual(fp1, fp2)
        
        
if __name__ == "__main__":
    unittest.main()