# Test code for eblink

import sys
sys.path.append('../python-encapsulation')
import eblink as eb

def test1():
    link = eb.EBlink()
    link.files = ['../test_data/RLData500_1.csv', '../test_data/RLData500_2.csv', '../test_data/RLData500_3.csv']
    link.columns = [['fname_c1','lname_c1', 'by', 'bm', 'bd'], ['fname_c1','lname_c1', 'by', 'bm', 'bd'], ['fname_c1','lname_c1', 'by', 'bm', 'bd']]
    link.match_columns = {'fname_c1':['fname_c1','fname_c1'], 'lname_c1':['lname_c1','lname_c1'], 'by':['by','by'], 'bm':['bm', 'bm'], 'bd':['bd', 'bd']}
    link.indices = ['UID', 'UID', 'UID']
    link.column_types = {'fname_c1':'s', 'lname_c1':'s', 'by':'c', 'bm':'c', 'bd':'c'}
    link.iterations = 500
    link.alpha = 1
    link.beta = 999
    # Carry out process
    link.build()
    link.model()
    link.build_crosswalk()
    

if __name__ == '__main__':
    test1()
