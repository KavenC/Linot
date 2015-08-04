import cPickle
import os
# file_path = os.path.join(os.path.dirname(__file__), 'config.p')
file_path = 'config.p'
LinotConfig = cPickle.load(open(file_path,'rb'))
