import os
script_dir = os.path.dirname(os.path.abspath(__file__))
test_file = os.path.join(script_dir, 'test_write.txt')
with open(test_file, 'w') as f:
    f.write('OK - Python funcionando!')
print('Arquivo criado:', test_file)

